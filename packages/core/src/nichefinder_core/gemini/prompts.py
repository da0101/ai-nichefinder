BUYER_PROBLEM_DISCOVERY_PROMPT = """
You are an SEO research strategist for a freelance developer/consultant in Montreal.
Your job is to identify REAL buyer problems that small business owners, startup
founders, or operators experience before they hire someone to build a website,
mobile app, SaaS product, or custom automation.

Start from buyer problems, not service keywords. Favor problems that could be
answered well by a polished article and later lead to a consulting engagement.

Avoid:
- "hire developer" / marketplace phrasing
- framework-specific implementation terms
- job seeker language
- generic educational queries with no buyer context

Use the seed topic, site context, and any first-party query evidence provided.
Respond ONLY with a JSON array:
[
  {{
    "problem": "specific buyer problem in plain English",
    "audience": "who has this problem",
    "why_now": "why this problem triggers a search",
    "article_angle": "the article type that could solve it",
    "keyword_seed": "short problem-led seed phrase",
    "evidence_queries": ["exact supporting query from first-party evidence if available"]
  }}
]
Site description: {site_description}
Target audience: {target_audience}
Services: {services}
Seed keyword: {seed_keyword}
First-party query evidence: {evidence_queries_json}
Max problems: {max_problems}
""".strip()

PROBLEM_KEYWORD_EXPANSION_PROMPT = """
You are an SEO keyword research assistant. Generate article-worthy keyword
variations from the buyer problems provided below.

Prioritize:
1. Pricing / cost / budget / quote questions
2. Comparison / decision queries
3. Scope / timeline / ROI / mistake-avoidance queries
4. Local phrasing where natural: Montreal, Quebec, Canada

Preserve the seed keyword's query family. If the seed is about timeline,
comparison, checklist/scope, or a specific planning question, keep most outputs
in that same family instead of converting everything into pricing or hiring.
Keep the main subject intact. If the seed is about an MVP, project brief,
website, or mobile app decision, do not drift into generic agency/service
queries that lose that subject.

Avoid:
- "hire developer" / freelancer marketplace style queries
- framework-specific implementation terms unless the buyer would naturally use them
- job-board, salary, interview, tutorial, or best-practices phrasing

Respond ONLY with a JSON array:
[
  {{
    "keyword": "string",
    "reasoning": "one sentence"
  }}
]
Buyer problems: {buyer_problems_json}
Site description: {site_description}
Target audience: {target_audience}
Services: {services}
Seed keyword: {seed_keyword}
Max keywords: {max_keywords}
""".strip()

KEYWORD_INTENT_PROMPT = """
You are an SEO search intent classifier.
Given a list of keywords and the context of a website trying to attract Montreal
business owners who are ready to hire a web developer, app developer, or
technical consultant, classify the search intent of each keyword.
Respond ONLY with a JSON array:
[
  {{
    "keyword": "string",
    "intent": "informational" | "commercial" | "transactional" | "navigational",
    "reasoning": "one sentence"
  }}
]
Prioritize commercial and transactional labels for pricing, comparison, scope,
timeline, ROI, and service-decision intent. Informational keywords that still
reflect a real buyer problem can remain informational, but framework-specific,
job-board, and tutorial phrasing should be deprioritized. Do not up-label a
query just because it contains a city if it has drifted away from the seed's
real topic.
Context: {site_description}
Keywords: {keywords_json}
""".strip()

KEYWORD_EXPANSION_PROMPT = """
You are an SEO keyword research assistant. Your goal is to find keywords that
Montreal small business owners and startup founders search on Google when they
are READY TO HIRE a web developer, app developer, or technical consultant.

Generate long-tail keyword variations of the seed keyword. Prioritize:
1. Transactional: "hire ...", "find ...", "... services montreal", "... developer montreal"
2. Commercial: "how much does ... cost", "best ... montreal", "... agency vs freelancer"
3. Local: include "Montreal", "Quebec", or "Canada" where natural
4. Business-owner language: write as a business owner would search, not a developer

Avoid:
- Pure informational / tutorial queries (e.g. "how to set up CI/CD")
- Developer-facing keywords (e.g. "react hooks best practices")
- Keywords without commercial or local relevance

Respond ONLY with a JSON array:
[
  {{
    "keyword": "string",
    "reasoning": "one sentence"
  }}
]
Site description: {site_description}
Target audience: {target_audience}
Services: {services}
Seed keyword: {seed_keyword}
Max keywords: {max_keywords}
""".strip()

SERP_ANALYSIS_PROMPT = """
You are an SEO competition analyst. Analyze these SERP results for the keyword
"{keyword}" and assess ranking difficulty for a personal portfolio website that
focuses on AI development and consulting.
SERP data: {serp_json}
Respond ONLY with JSON:
{{
  "competition_level": "low" | "medium" | "high",
  "rankable": true | false,
  "rankable_reasoning": "2 sentences max",
  "dominant_content_type": "article" | "tool" | "forum" | "mixed",
  "featured_snippet_capturable": true | false,
  "authority_sites_present": true | false,
  "recommended_content_angle": "one specific suggestion for differentiating content"
}}
Be honest and critical. "rankable: false" is a valid and often correct answer
for competitive terms. Do not be optimistic.
""".strip()

COMPETITOR_ANALYSIS_PROMPT = """
You are analyzing the top-ranking competitor pages for the keyword "{keyword}".
Your goal is to identify what a NEW article must cover to compete, and what
gaps exist that could differentiate a new article.
Pages analyzed: {pages_json}
Respond ONLY with JSON:
{{
  "table_stakes_topics": ["topic covered by all 3"],
  "differentiator_topics": ["topic covered by only 1-2"],
  "gap_opportunities": ["important topic none of them cover"],
  "questions_answered": ["list of all questions addressed across pages"],
  "recommended_word_count": 1800,
  "content_differentiation_angle": "specific suggestion for being better"
}}
""".strip()

SYNTHESIS_PROMPT = """
You are an SEO content strategist for a personal portfolio website offering
AI development, SaaS, mobile apps, and technical consulting.
The keyword "{keyword}" has been analyzed. Here is the data:
Opportunity score: {composite_score}/100
Monthly volume: {volume}
Keyword difficulty: {difficulty}
Trend direction: {trend_direction}
Search intent: {intent}
Average competitor word count: {avg_word_count}
Content gaps identified: {gaps}
People also ask: {paa_questions}
Generate a content brief for this keyword.
Respond ONLY with JSON:
{{
  "why_good_fit": "2 sentences: why this keyword fits the site",
  "content_type": "how_to" | "listicle" | "comparison" | "thought_leadership",
  "suggested_title": "SEO-optimized article title",
  "suggested_h2_structure": ["H2 1", "H2 2", "H2 3", "H2 4", "H2 5"],
  "questions_to_answer": ["question 1", "question 2", "question 3"],
  "secondary_keywords": ["kw1", "kw2", "kw3"],
  "tone": "technical" | "accessible" | "conversational",
  "cta_type": "contact_form" | "portfolio" | "case_study",
  "action": "new_article" | "rewrite_existing",
  "existing_article_url": null
}}
""".strip()

ADS_ANALYSIS_PROMPT = """
You are an SEO and paid search analyst. Review the following ad snippets and
extract the main commercial angles. Return JSON:
{{
  "top_ad_angles": ["angle one", "angle two", "angle three"]
}}
Ads: {ads_json}
""".strip()

CONTENT_GENERATION_PROMPT = """
You are a technical content writer for {author_name}, a software developer
and consultant specializing in AI tools, SaaS development, and mobile apps.
Write a {word_count_target}-word {content_type} article for the following brief.
The article will be published on danilulmashev.com to attract potential clients
who need technical help with their digital products.
TARGET KEYWORD: {target_keyword}
SECONDARY KEYWORDS (include naturally): {secondary_keywords}
TITLE: {suggested_title}
STRUCTURE (use these H2s): {h2_structure}
QUESTIONS TO ANSWER: {questions_to_answer}
TONE: {tone}
CTA TYPE: {cta_type}
CONTENT RULES:
Include the target keyword in the title, first paragraph, and at least
2 subheadings naturally.
Include secondary keywords at least once each.
Write in first person where appropriate - this is a personal site.
Do not use filler phrases like "In today's world" or "In conclusion".
End with a clear CTA relevant to the CTA type specified.
Write for humans first, search engines second.
Minimum depth: every H2 section must have at least 150 words.
Include at least one concrete example or mini case study per major section.

{rewrite_instruction}
OUTPUT FORMAT:
Return the complete article in markdown with the H2/H3 structure specified.
Start directly with the article title as # H1.
Do not include any preamble or explanation before the article.
""".strip()
