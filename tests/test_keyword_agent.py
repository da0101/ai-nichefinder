from datetime import date, datetime, timezone
from types import SimpleNamespace

from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.agents.keyword_agent import KeywordAgent, KeywordAgentInput
from nichefinder_core.models import BuyerProblem, Keyword, KeywordLifecycleStatus, SearchConsoleRecord, SearchIntent
from nichefinder_core.free_article_evidence import collect_free_article_evidence
from nichefinder_core.free_validation_context import (
    load_free_validation_context,
    save_free_validation_context,
    thaw_shortlist,
)
from nichefinder_core.pre_serp_ddgs import apply_ddgs_validation
from nichefinder_core.pre_serp import PreSerpCandidateScore, build_pre_serp_shortlist
from nichefinder_core.pre_serp_external import (
    ExternalEvidenceResult,
    ExternalEvidenceValidation,
    apply_external_validation,
)
from nichefinder_core.research_overlap import apply_overlap_confidence, summarize_cross_source_patterns
from nichefinder_core.pre_serp_tavily import apply_tavily_validation
from nichefinder_core.pre_serp_trends import build_trend_assisted_shortlist
from nichefinder_core.settings import Settings
from nichefinder_db.crud import SeoRepository

class FakeSerpAPIClient:
    async def get_related_searches(self, keyword: str, location: str = "Montreal, Quebec, Canada"):
        return []


class FakeGeminiClient:
    async def analyze(self, system_prompt: str, user_content: str):
        if "identify REAL buyer problems" in system_prompt:
            return {
                "items": [
                    {
                        "problem": "Founders do not know whether they need an app or a web app first.",
                        "audience": "startup founders",
                        "why_now": "They are budgeting a first product build.",
                        "article_angle": "comparison guide",
                        "keyword_seed": "mobile app vs web app for startup",
                        "evidence_queries": [],
                    }
                ]
            }
        if "Generate article-worthy keyword" in system_prompt:
            return {
                "items": [
                    {"keyword": "mobile app vs web app for startup"},
                    {"keyword": "how much does an app cost for a startup"},
                ]
            }
        return {
            "items": [
                {"keyword": "ai consultant", "intent": "commercial"},
                {"keyword": "mobile app vs web app for startup", "intent": "commercial"},
                {"keyword": "how much does an app cost for a startup", "intent": "commercial"},
            ]
        }


def _repository():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    return SeoRepository(session)


class FreeTierSerpAPIClient:
    async def get_related_searches(self, keyword: str, location: str = "Montreal, Quebec, Canada"):
        related = {
            "ai consultant": ["ai strategy consultant", "ai consultant pricing"],
            "ai consultant for startups": ["startup ai consultant"],
            "hire ai consultant": ["best ai consultant for business"],
        }
        return related.get(keyword, [])


class FakeTrendAgent:
    def __init__(self, repository, directions: dict[str, str]):
        self.repository = repository
        self.directions = directions

    async def run(self, payload):
        direction = self.directions.get(payload.keyword_term, "stable")
        self.repository.update_keyword(
            payload.keyword_id,
            trend_direction=direction,
            trend_data_12m="[0,0,0,0,0,0,0,0,0,0,0,0]",
            trend_fresh_at=datetime.now(timezone.utc),
            trend_source="test",
        )


class FakeTavilyClient:
    class _Settings:
        tavily_ready = True

    def __init__(self, responses: dict[str, dict]):
        self.responses = responses
        self.settings = self._Settings()

    async def search(self, query: str, *, max_results: int = 3, search_depth: str = "basic", topic: str = "general"):
        return self.responses.get(query, {"results": []})


class FakeDDGSClient:
    class _Settings:
        ddgs_ready = True

    def __init__(self, responses: dict[str, dict]):
        self.responses = responses
        self.settings = self._Settings()

    async def search(self, query: str, *, max_results: int = 3):
        return self.responses.get(query, {"results": []})


async def test_keyword_agent_creates_keywords_from_gemini_output_only():
    repository = _repository()
    settings = Settings(
        min_monthly_volume=100,
        max_keyword_difficulty=50,
    )
    agent = KeywordAgent(
        settings=settings,
        gemini_client=FakeGeminiClient(),
        serpapi_client=FreeTierSerpAPIClient(),
        repository=repository,
    )
    output = await agent.run(
        KeywordAgentInput(
            seed_keyword="ai consultant",
            site_config={
                "site_description": "AI development consultancy",
                "target_audience": "startup founders",
                "services": ["AI consulting", "AI development"],
                "primary_language": "en",
            },
            max_keywords=10,
        )
    )
    keywords = repository.list_keywords()
    terms = {keyword.term for keyword in keywords}
    assert output.keywords_saved >= 3
    assert "ai consultant" in terms
    assert "mobile app vs web app for startup" in terms
    assert "ai strategy consultant" not in terms
    assert output.buyer_problems[0].keyword_seed == "mobile app vs web app for startup"
    assert all(keyword.source == "gemini_serpapi" for keyword in keywords)
    assert all(keyword.lifecycle_status == KeywordLifecycleStatus.DISCOVERED for keyword in keywords)
    assert all(keyword.locale == "en" for keyword in keywords)
    assert all(keyword.market == "North America" for keyword in keywords)
    assert all(keyword.metrics_source == "gemini_serpapi" for keyword in keywords)


def test_pre_serp_shortlist_prefers_article_winnable_terms_and_caps_results():
    repository = _repository()
    keyword_ids = [
        repository.upsert_keyword(
            Keyword(
                term="react hooks best practices",
                seed_keyword="seed",
                source="test",
                search_intent=SearchIntent.INFORMATIONAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="hire web developer montreal",
                seed_keyword="seed",
                source="test",
                search_intent=SearchIntent.TRANSACTIONAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="how much does a website cost montreal",
                seed_keyword="seed",
                source="test",
                search_intent=SearchIntent.COMMERCIAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="how long does a website take to build montreal",
                seed_keyword="seed",
                source="test",
                search_intent=SearchIntent.COMMERCIAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="hire web developer montreal pricing",
                seed_keyword="seed",
                source="test",
                search_intent=SearchIntent.COMMERCIAL,
            )
        ).id,
    ]

    shortlist = build_pre_serp_shortlist(
        keyword_ids,
        repository,
        site_config={
            "site_description": "Web design and app development for small businesses",
            "target_audience": "small business owners",
            "services": ["web design", "app development", "technical consulting"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=3,
    )

    selected_terms = [item.term for item in shortlist if item.selected]

    assert set(selected_terms[:2]) == {
        "how much does a website cost montreal",
        "how long does a website take to build montreal",
    }
    assert selected_terms[2] in {
        "hire web developer montreal",
        "hire web developer montreal pricing",
    }
    assert shortlist[-1].term == "react hooks best practices"
    assert shortlist[-1].breakdown["developer_penalty"] < 0
    hire_query = next(item for item in shortlist if item.term == "hire web developer montreal")
    assert hire_query.breakdown["query_penalty"] < 0


def test_pre_serp_shortlist_uses_exact_gsc_history_as_boost():
    repository = _repository()
    boosted = repository.upsert_keyword(
        Keyword(
            term="hire web developer montreal",
            seed_keyword="seed",
            source="test",
            search_intent=SearchIntent.TRANSACTIONAL,
        )
    )
    plain = repository.upsert_keyword(
        Keyword(
            term="hire app developer montreal",
            seed_keyword="seed",
            source="test",
            search_intent=SearchIntent.TRANSACTIONAL,
        )
    )
    repository.save_search_console_record(
        SearchConsoleRecord(
            keyword_id=boosted.id,
            query=boosted.term,
            page_url="https://example.com/web-dev",
            impressions=240,
            clicks=18,
            ctr=0.075,
            position=9.5,
            snapshot_date=date(2026, 4, 19),
            property_id="sc-domain:example.com",
        )
    )

    shortlist = build_pre_serp_shortlist(
        [plain.id, boosted.id],
        repository,
        site_config={
            "site_description": "Web design and app development for small businesses",
            "target_audience": "small business owners",
            "services": ["web design", "app development", "technical consulting"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=1,
    )

    assert shortlist[0].term == "hire web developer montreal"
    assert shortlist[0].breakdown["gsc_history"] > 0


def test_pre_serp_shortlist_preserves_mvp_timeline_seed_intent():
    repository = _repository()
    keyword_ids = [
        repository.upsert_keyword(
            Keyword(
                term="how long does it take to build an MVP",
                seed_keyword="how long does it take to build an MVP",
                source="test",
                search_intent=SearchIntent.INFORMATIONAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="cost to build MVP Montreal",
                seed_keyword="how long does it take to build an MVP",
                source="test",
                search_intent=SearchIntent.COMMERCIAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="local MVP developer Montreal",
                seed_keyword="how long does it take to build an MVP",
                source="test",
                search_intent=SearchIntent.COMMERCIAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="custom web app pricing Montreal",
                seed_keyword="how long does it take to build an MVP",
                source="test",
                search_intent=SearchIntent.COMMERCIAL,
            )
        ).id,
    ]

    shortlist = build_pre_serp_shortlist(
        keyword_ids,
        repository,
        site_config={
            "site_description": "Web design and app development for small businesses",
            "target_audience": "small business owners",
            "services": ["web design", "app development", "technical consulting"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=2,
    )

    selected_terms = [item.term for item in shortlist if item.selected]
    assert selected_terms[0] == "how long does it take to build an MVP"
    assert "custom web app pricing Montreal" not in selected_terms
    pricing_drift = next(item for item in shortlist if item.term == "custom web app pricing Montreal")
    assert pricing_drift.breakdown["query_drift"] < 0


def test_pre_serp_shortlist_preserves_project_brief_subject():
    repository = _repository()
    keyword_ids = [
        repository.upsert_keyword(
            Keyword(
                term="what should be in a project brief",
                seed_keyword="what should be in a project brief",
                source="test",
                search_intent=SearchIntent.INFORMATIONAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="project brief checklist for website build",
                seed_keyword="what should be in a project brief",
                source="test",
                search_intent=SearchIntent.INFORMATIONAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="getting comparable web developer quotes Montreal",
                seed_keyword="what should be in a project brief",
                source="test",
                search_intent=SearchIntent.COMMERCIAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="how to compare web development proposals",
                seed_keyword="what should be in a project brief",
                source="test",
                search_intent=SearchIntent.INFORMATIONAL,
            )
        ).id,
    ]

    shortlist = build_pre_serp_shortlist(
        keyword_ids,
        repository,
        site_config={
            "site_description": "Web design and app development for small businesses",
            "target_audience": "small business owners",
            "services": ["web design", "app development", "technical consulting"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=2,
    )

    selected_terms = [item.term for item in shortlist if item.selected]
    assert set(selected_terms) == {
        "project brief checklist for website build",
        "what should be in a project brief",
    }
    quote_query = next(item for item in shortlist if item.term == "getting comparable web developer quotes Montreal")
    assert quote_query.breakdown["query_drift"] < 0


def test_pre_serp_shortlist_preserves_decision_seed_and_collapses_duplicates():
    repository = _repository()
    keyword_ids = [
        repository.upsert_keyword(
            Keyword(
                term="should i build an ai chatbot for my business",
                seed_keyword="should i build an ai chatbot for my business",
                source="test",
                search_intent=SearchIntent.INFORMATIONAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="AI chatbot development cost Montreal",
                seed_keyword="should i build an ai chatbot for my business",
                source="test",
                search_intent=SearchIntent.COMMERCIAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="when do I need a custom CRM",
                seed_keyword="when do i need a custom CRM",
                source="test",
                search_intent=SearchIntent.INFORMATIONAL,
            )
        ).id,
        repository.upsert_keyword(
            Keyword(
                term="when do i need a custom CRM",
                seed_keyword="when do i need a custom CRM",
                source="test",
                search_intent=SearchIntent.INFORMATIONAL,
            )
        ).id,
    ]

    shortlist = build_pre_serp_shortlist(
        keyword_ids,
        repository,
        site_config={
            "site_description": "Web design, automation, and AI development for small businesses",
            "target_audience": "small business owners",
            "services": ["automation consulting", "AI development", "custom software"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=3,
    )

    chatbot_seed = next(
        item for item in shortlist if item.term == "should i build an ai chatbot for my business"
    )
    cost_query = next(item for item in shortlist if item.term == "AI chatbot development cost Montreal")
    assert chatbot_seed.score > cost_query.score
    assert cost_query.breakdown["query_drift"] < 0

    crm_variants = [item for item in shortlist if item.term.lower() == "when do i need a custom crm"]
    assert len(crm_variants) == 2
    assert any(item.breakdown.get("duplicate_penalty", 0.0) < 0 for item in crm_variants)


async def test_trend_assisted_shortlist_uses_fresh_trend_signal_before_selection():
    repository = _repository()
    exact_seed = repository.upsert_keyword(
        Keyword(
            term="do i need a mobile app or a website",
            seed_keyword="do i need a mobile app or a website",
            source="test",
            search_intent=SearchIntent.INFORMATIONAL,
        )
    )
    cost_variant = repository.upsert_keyword(
        Keyword(
            term="cost of mobile app vs website Montreal",
            seed_keyword="do i need a mobile app or a website",
            source="test",
            search_intent=SearchIntent.COMMERCIAL,
        )
    )

    shortlist = await build_trend_assisted_shortlist(
        [exact_seed.id, cost_variant.id],
        repository,
        FakeTrendAgent(
            repository,
            {
                "do i need a mobile app or a website": "rising",
                "cost of mobile app vs website Montreal": "declining",
            },
        ),
        site_config={
            "site_description": "Web design, automation, and AI development for small businesses",
            "target_audience": "small business owners",
            "services": ["automation consulting", "AI development", "custom software"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=1,
    )

    assert shortlist[0].term == "do i need a mobile app or a website"
    assert shortlist[0].breakdown["historical_trend"] > 0
    declining = next(item for item in shortlist if item.term == "cost of mobile app vs website Montreal")
    assert declining.breakdown["historical_trend"] < 0


async def test_tavily_validation_boosts_supported_seed_and_keeps_problem_validations():
    repository = _repository()
    exact_seed = repository.upsert_keyword(
        Keyword(
            term="should i build an ai chatbot for my business",
            seed_keyword="should i build an ai chatbot for my business",
            source="test",
            search_intent=SearchIntent.INFORMATIONAL,
        )
    )
    cost_variant = repository.upsert_keyword(
        Keyword(
            term="AI chatbot development cost Montreal",
            seed_keyword="should i build an ai chatbot for my business",
            source="test",
            search_intent=SearchIntent.COMMERCIAL,
        )
    )
    shortlist = build_pre_serp_shortlist(
        [exact_seed.id, cost_variant.id],
        repository,
        site_config={
            "site_description": "Web design, automation, and AI development for small businesses",
            "target_audience": "small business owners",
            "services": ["automation consulting", "AI development", "custom software"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=1,
    )

    shortlist, keyword_validations, problem_validations = await apply_tavily_validation(
        shortlist,
        [{"problem": "Need help deciding if an AI chatbot is worth building", "keyword_seed": "should i build an ai chatbot for my business"}],
        FakeTavilyClient(
            {
                "should i build an ai chatbot for my business": {
                    "results": [
                        {"title": "Should You Build an AI Chatbot for Your Business?", "content": "Deciding whether to build an AI chatbot for your business depends on support load and ROI.", "url": "https://example.com/chatbot"},
                        {"title": "AI chatbot ROI for business", "content": "Business owners should evaluate AI chatbot ROI before building.", "url": "https://example.com/roi"},
                    ]
                },
                "AI chatbot development cost Montreal": {
                    "results": [
                        {"title": "AI development services Montreal", "content": "Agency pricing for AI software projects.", "url": "https://example.com/cost"},
                    ]
                },
            }
        ),
        max_keywords=1,
        max_keyword_validations=2,
        max_problem_validations=1,
    )

    assert shortlist[0].term == "should i build an ai chatbot for my business"
    assert keyword_validations[0].query == "should i build an ai chatbot for my business"
    assert keyword_validations[0].results[0].url == "https://example.com/chatbot"
    assert shortlist[0].breakdown["tavily_validation"] > 0
    cost_variant = next(item for item in shortlist if item.term == "AI chatbot development cost Montreal")
    assert shortlist[0].breakdown["tavily_validation"] > cost_variant.breakdown["tavily_validation"]
    assert shortlist[0].breakdown["tavily_validation_raw"] >= cost_variant.breakdown["tavily_validation_raw"]
    assert problem_validations[0].score > 0


async def test_ddgs_validation_adds_support_without_overpowering_seed_fidelity():
    repository = _repository()
    exact = repository.upsert_keyword(
        Keyword(
            term="should i build an AI chatbot for my business",
            seed_keyword="should i build an AI chatbot for my business",
            source="test",
            search_intent=SearchIntent.INFORMATIONAL,
        )
    )
    drift = repository.upsert_keyword(
        Keyword(
            term="custom AI chatbot development montreal",
            seed_keyword="should i build an AI chatbot for my business",
            source="test",
            search_intent=SearchIntent.COMMERCIAL,
        )
    )

    shortlist = build_pre_serp_shortlist(
        [drift.id, exact.id],
        repository,
        site_config={
            "site_description": "AI consulting and custom software for service businesses",
            "target_audience": "small business owners",
            "services": ["AI consulting", "custom software", "automation"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=1,
    )

    ddgs = FakeDDGSClient(
        {
            "should i build an AI chatbot for my business": {
                "results": [
                    {"title": "Should your small business build an AI chatbot?", "href": "https://example.com/decision", "body": "Decision guide for business owners deciding whether they need a chatbot."},
                    {"title": "When does a business need a chatbot?", "href": "https://example.org/chatbot-guide", "body": "Explains when a chatbot helps a service business and when it does not."},
                ]
            },
            "custom AI chatbot development montreal": {
                "results": [
                    {"title": "Custom AI chatbot development services", "href": "https://agency.example.com/services", "body": "Agency services for chatbot builds."},
                    {"title": "Montreal chatbot agency", "href": "https://agency.example.org/montreal", "body": "Local chatbot development company."},
                ]
            },
            "should i build an AI chatbot for my business?": {
                "results": [
                    {"title": "Should your small business build an AI chatbot?", "href": "https://example.com/decision", "body": "Decision guide for business owners deciding whether they need a chatbot."},
                    {"title": "When does a business need a chatbot?", "href": "https://example.org/chatbot-guide", "body": "Explains when a chatbot helps a service business and when it does not."},
                ]
            },
        }
    )

    shortlist, keyword_validations, problem_validations = await apply_ddgs_validation(
        shortlist,
        [{"problem": "Owners are unsure whether an AI chatbot is worth building.", "keyword_seed": "should i build an AI chatbot for my business?"}],
        ddgs,
        max_keywords=1,
        max_keyword_validations=2,
        max_problem_validations=1,
    )

    custom_variant = next(item for item in shortlist if item.term == "custom AI chatbot development montreal")
    assert shortlist[0].term == "should i build an AI chatbot for my business"
    assert keyword_validations[0].results[0].url == "https://example.com/decision"
    assert shortlist[0].breakdown["ddgs_validation"] > 0
    assert shortlist[0].breakdown["ddgs_validation"] >= custom_variant.breakdown["ddgs_validation"]
    assert shortlist[0].breakdown["ddgs_validation_raw"] >= custom_variant.breakdown["ddgs_validation_raw"]
    assert problem_validations[0].source == "ddgs"
    assert problem_validations[0].score > 0


class FakeScraper:
    def __init__(self, pages: dict[str, object]):
        self.pages = pages

    async def fetch_article(self, url: str):
        return self.pages.get(url)


async def test_collect_free_article_evidence_builds_keyword_bank_from_ddgs_results():
    repository = _repository()
    validation = FakeDDGSClient(
        {
            "how much does a website cost in montreal": {
                "results": [
                    {
                        "title": "How much does a website cost in Montreal?",
                        "href": "https://example.com/cost-guide",
                        "body": "Website cost, pricing factors, and project scope in Montreal.",
                    },
                    {
                        "title": "Website pricing in Montreal",
                        "href": "https://example.org/pricing",
                        "body": "How website pricing changes with features and maintenance.",
                    },
                ]
            }
        }
    )
    keyword = repository.upsert_keyword(
        Keyword(
            term="how much does a website cost in montreal",
            seed_keyword="how much does a website cost in montreal",
            source="test",
            search_intent=SearchIntent.COMMERCIAL,
        )
    )
    shortlist = build_pre_serp_shortlist(
        [keyword.id],
        repository,
        site_config={
            "site_description": "Web design and app development for small businesses",
            "target_audience": "small business owners",
            "services": ["web design", "app development", "technical consulting"],
        },
        location="Montreal, Quebec, Canada",
        max_keywords=1,
    )
    shortlist, keyword_validations, _ = await apply_ddgs_validation(
        shortlist,
        [],
        validation,
        max_keywords=1,
        max_keyword_validations=1,
        max_problem_validations=0,
    )

    class Scraped:
        def __init__(self, url, title, h1, h2_list, h3_list, word_count):
            self.url = url
            self.title = title
            self.h1 = h1
            self.h2_list = h2_list
            self.h3_list = h3_list
            self.word_count = word_count

    scraper = FakeScraper(
        {
            "https://example.com/cost-guide": Scraped(
                "https://example.com/cost-guide",
                "How much does a website cost in Montreal?",
                "Website Cost in Montreal",
                ["What affects website cost?", "How to define project scope"],
                ["Should you use a template or custom build?"],
                1500,
            ),
            "https://example.org/pricing": Scraped(
                "https://example.org/pricing",
                "Website pricing in Montreal",
                "Website Pricing in Montreal",
                ["What affects website cost?", "Website maintenance costs"],
                ["How long does a website project take?"],
                1300,
            ),
        }
    )

    evidence = await collect_free_article_evidence(
        keyword_validations,
        scraper,
        max_keywords=1,
        max_pages_per_keyword=2,
    )

    assert evidence[0].query == "how much does a website cost in montreal"
    assert evidence[0].pages_scraped == 2
    assert "What affects website cost?" in evidence[0].recurring_headings
    assert evidence[0].question_bank
    assert evidence[0].suggested_primary_keyword == "how much does a website cost in montreal"
    assert evidence[0].suggested_secondary_keywords


async def test_collect_free_article_evidence_requires_two_scraped_pages():
    validations = [
        ExternalEvidenceValidation(
            source="ddgs",
            query="website cost montreal",
            score=8.0,
            result_count=3,
            top_domains=["example.com"],
            results=[
                ExternalEvidenceResult(
                    title="Website cost",
                    url="https://example.com/cost",
                    content="Pricing page",
                )
            ],
        )
    ]

    class Scraped:
        def __init__(self, url, title, h1, h2_list, h3_list, word_count):
            self.url = url
            self.title = title
            self.h1 = h1
            self.h2_list = h2_list
            self.h3_list = h3_list
            self.word_count = word_count

    scraper = FakeScraper(
        {
            "https://example.com/cost": Scraped(
                "https://example.com/cost",
                "Website cost",
                "Website Cost",
                ["How much does a website cost?"],
                [],
                900,
            )
        }
    )

    evidence = await collect_free_article_evidence(
        validations,
        scraper,
        max_keywords=1,
        max_pages_per_keyword=2,
    )

    assert evidence == []


async def test_collect_free_article_evidence_filters_marketing_copy_headings():
    validations = [
        ExternalEvidenceValidation(
            source="yahoo",
            query="how to choose a web developer montreal",
            score=8.0,
            result_count=3,
            top_domains=["example.com", "example.org"],
            results=[
                ExternalEvidenceResult(
                    title="Choose a Montreal Web Developer",
                    url="https://example.com/one",
                    content="Guide one",
                ),
                ExternalEvidenceResult(
                    title="Montreal Developer Selection Guide",
                    url="https://example.org/two",
                    content="Guide two",
                ),
            ],
        )
    ]

    class Scraped:
        def __init__(self, url, title, h1, h2_list, h3_list, word_count):
            self.url = url
            self.title = title
            self.h1 = h1
            self.h2_list = h2_list
            self.h3_list = h3_list
            self.word_count = word_count

    scraper = FakeScraper(
        {
            "https://example.com/one": Scraped(
                "https://example.com/one",
                "How to Choose a Montreal Web Developer",
                "Choose a Montreal Web Developer",
                ["Don't want to guess?", "What to look for in a Montreal web developer"],
                ["Red flags to avoid"],
                1400,
            ),
            "https://example.org/two": Scraped(
                "https://example.org/two",
                "Montreal Web Developer Selection Guide",
                "Montreal Web Developer Selection Guide",
                ["Frequently Asked Questions", "What to look for in a Montreal web developer"],
                ["Red flags to avoid"],
                1350,
            ),
        }
    )

    evidence = await collect_free_article_evidence(
        validations,
        scraper,
        max_keywords=1,
        max_pages_per_keyword=2,
    )

    assert evidence
    assert "What to look for in a Montreal web developer" in evidence[0].recurring_headings
    assert "Don't want to guess?" not in evidence[0].recurring_headings
    assert "Frequently Asked Questions" not in evidence[0].recurring_headings
    assert all("don't want to guess" not in item.lower() for item in evidence[0].question_bank)


async def test_collect_free_article_evidence_uses_body_signals_for_secondary_keywords():
    validations = [
        ExternalEvidenceValidation(
            source="ddgs",
            query="website cost montreal",
            score=8.0,
            result_count=3,
            top_domains=["example.com", "example.org"],
            results=[
                ExternalEvidenceResult(title="Website Cost Guide", url="https://example.com/one", content="Pricing guide"),
                ExternalEvidenceResult(title="Montreal Pricing", url="https://example.org/two", content="Pricing guide"),
            ],
        )
    ]

    class Scraped:
        def __init__(self, url, title, h1, h2_list, h3_list, clean_text, word_count):
            self.url = url
            self.title = title
            self.h1 = h1
            self.h2_list = h2_list
            self.h3_list = h3_list
            self.clean_text = clean_text
            self.word_count = word_count

    scraper = FakeScraper(
        {
            "https://example.com/one": Scraped(
                "https://example.com/one",
                "Website Cost Guide",
                "Website Cost Guide",
                ["What affects website cost?"],
                [],
                "Project scope discovery workshop is often the first step. Project scope discovery workshop helps avoid rework and hidden costs.",
                1200,
            ),
            "https://example.org/two": Scraped(
                "https://example.org/two",
                "Montreal Pricing",
                "Montreal Pricing",
                ["Website maintenance costs"],
                [],
                "A project scope discovery workshop can reduce revision risk. Many agencies price a project scope discovery workshop separately.",
                1100,
            ),
        }
    )

    evidence = await collect_free_article_evidence(
        validations,
        scraper,
        max_keywords=1,
        max_pages_per_keyword=2,
    )

    assert evidence
    assert "project scope discovery" in evidence[0].body_signal_terms
    assert "project scope discovery" in evidence[0].suggested_secondary_keywords


def test_summarize_cross_source_patterns_aggregates_repeated_domains_and_questions():
    validations = [
        ExternalEvidenceValidation(
            source="ddgs",
            query="how much does a website cost in montreal",
            score=10.0,
            result_count=3,
            top_domains=["clevrsolutions.ca", "fivesquaredesign.com", "www.aurolys.ca"],
        ),
        ExternalEvidenceValidation(
            source="bing",
            query="how much does a website cost in montreal",
            score=8.0,
            result_count=3,
            top_domains=["clevrsolutions.ca", "elitics.io", "fivesquaredesign.com"],
        ),
        ExternalEvidenceValidation(
            source="yahoo",
            query="how much does a website cost in montreal",
            score=8.0,
            result_count=3,
            top_domains=["clevrsolutions.ca", "elitics.io", "www.aurolys.ca"],
        ),
    ]
    article_evidence = [
        SimpleNamespace(
            query="how much does a website cost in montreal",
            source="ddgs",
            suggested_secondary_keywords=["web design", "montreal web design"],
            question_bank=["Why Montreal Web Design Costs More Than Other Cities?"],
        ),
        SimpleNamespace(
            query="how much does a website cost in montreal",
            source="bing",
            suggested_secondary_keywords=["web design", "pricing guide"],
            question_bank=["Why Montreal Web Design Costs More Than Other Cities?"],
        ),
        SimpleNamespace(
            query="how much does a website cost in montreal",
            source="yahoo",
            suggested_secondary_keywords=["web design", "montreal web design"],
            question_bank=["Building an e-commerce store in Quebec?"],
        ),
    ]

    summaries = summarize_cross_source_patterns(validations, article_evidence)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.sources == ["DDGS", "BING", "YAHOO"]
    assert summary.agreement == "3-source"
    assert "clevrsolutions.ca" in summary.repeated_domains
    assert "web design" in summary.repeated_secondary_keywords
    assert "Why Montreal Web Design Costs More Than Other Cities?" in summary.repeated_questions


def test_summarize_cross_source_patterns_falls_back_to_single_source_items():
    validations = [
        ExternalEvidenceValidation(
            source="bing",
            query="how to compare web design quotes montreal",
            score=8.0,
            result_count=3,
            top_domains=["designrush.com", "clutch.co", "sortlist.com"],
        )
    ]

    summaries = summarize_cross_source_patterns(validations)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.agreement == "single-source"
    assert summary.repeated_domains == ["clutch.co", "designrush.com", "sortlist.com"]


async def test_apply_external_validation_splits_problem_seed_variants():
    shortlist = [
        SimpleNamespace(
            keyword_id="k1",
            term="website cost montreal",
            score=70.0,
            breakdown={"seed_fidelity": 30.0, "query_drift": 0.0, "developer_penalty": 0.0, "local_intent": 2.0},
            canonical_key="website cost",
            selected=True,
            notes=[],
        )
    ]
    buyer_problems = [
        BuyerProblem(
            problem="Pricing confusion",
            audience="owners",
            why_now="budgeting",
            article_angle="pricing guide",
            keyword_seed="website cost montreal, web app cost montreal",
            evidence_queries=[],
        )
    ]

    async def fake_search(query: str) -> dict:
        if query == "website cost montreal":
            return {
                "results": [
                    {"title": "Website cost Montreal", "url": "https://example.com/cost", "content": "website cost montreal"},
                    {"title": "Montreal pricing", "url": "https://example.org/cost", "content": "website cost montreal"},
                ]
            }
        if query == "web app cost montreal":
            return {
                "results": [
                    {"title": "Web app cost Montreal", "url": "https://example.net/app", "content": "web app cost montreal"},
                    {"title": "Montreal app pricing", "url": "https://example.edu/app", "content": "web app cost montreal"},
                ]
            }
        return {"results": []}

    _, _, problem_validations = await apply_external_validation(
        shortlist,
        buyer_problems,
        source="ddgs",
        ready=True,
        search=fake_search,
        max_keywords=1,
        max_keyword_validations=1,
        max_problem_validations=1,
        concurrency=1,
        base_weight=0.28,
    )

    assert len(problem_validations) == 1
    validation = problem_validations[0]
    assert validation.query == "website cost montreal, web app cost montreal"
    assert validation.query_variants == ["website cost montreal", "web app cost montreal"]
    assert "ddgs variant agreement" in validation.notes


def test_free_validation_context_round_trips_shortlist(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    shortlist = [
        PreSerpCandidateScore(
            keyword_id="k1",
            term="how much does a website cost in montreal",
            score=120.0,
            breakdown={"seed_fidelity": 35.0},
            canonical_key="how much website cost",
            selected=True,
            notes=["intent"],
        )
    ]
    save_free_validation_context(
        settings,
        seed_keyword="website cost montreal",
        location="Montreal, Quebec, Canada",
        site_config={"site_name": "Test", "services": ["web development"]},
        keywords_found=10,
        keywords_saved=8,
        buyer_problems=[
            BuyerProblem(
                problem="Pricing confusion",
                audience="owners",
                why_now="budgeting",
                article_angle="pricing guide",
                keyword_seed="website cost montreal",
                evidence_queries=[],
            )
        ],
        shortlist=shortlist,
    )

    context = load_free_validation_context(
        settings,
        seed_keyword="website cost montreal",
        location="Montreal, Quebec, Canada",
        site_config={"site_name": "Test", "services": ["web development"]},
    )

    assert context is not None
    thawed = thaw_shortlist(context)
    assert thawed[0].term == "how much does a website cost in montreal"
    assert thawed[0].breakdown["seed_fidelity"] == 35.0


def test_apply_overlap_confidence_uses_exact_and_family_patterns():
    shortlist = [
        SimpleNamespace(
            keyword_id="k1",
            term="how much does a website cost in montreal",
            score=100.0,
            breakdown={},
            canonical_key="website cost",
            selected=True,
            notes=[],
        )
    ]
    exact_patterns = summarize_cross_source_patterns(
        [
            ExternalEvidenceValidation(source="ddgs", query="how much does a website cost in montreal", score=8, result_count=3, top_domains=["a.com", "b.com"]),
            ExternalEvidenceValidation(source="yahoo", query="how much does a website cost in montreal", score=8, result_count=3, top_domains=["a.com", "c.com"]),
        ]
    )
    family_patterns = summarize_cross_source_patterns(
        [
            ExternalEvidenceValidation(source="ddgs", query="website cost montreal", score=8, result_count=3, top_domains=["a.com", "b.com"]),
            ExternalEvidenceValidation(source="yahoo", query="how much does a website cost in montreal", score=8, result_count=3, top_domains=["a.com", "c.com"]),
        ],
        grouping="family",
    )

    adjusted = apply_overlap_confidence(shortlist, exact_patterns, family_patterns)

    assert adjusted[0].score > 100.0
    assert adjusted[0].breakdown["free_overlap_bonus"] > 0
