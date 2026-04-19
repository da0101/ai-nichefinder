import json
from datetime import date, datetime, timezone

from sqlmodel import Session, func, select

from nichefinder_core.models import (
    ApiUsageRecord,
    Article,
    ArticleVersion,
    CompetitorPage,
    ContentBrief,
    ContentBriefRecord,
    Keyword,
    KeywordCluster,
    KeywordClusterMembership,
    RankingSnapshot,
    SerpResult,
)


class SeoRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_keyword(self, keyword: Keyword) -> Keyword:
        existing = self.session.exec(select(Keyword).where(Keyword.term == keyword.term)).first()
        if existing:
            for field, value in keyword.model_dump().items():
                if value is not None and field != "id":
                    setattr(existing, field, value)
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        self.session.add(keyword)
        self.session.commit()
        self.session.refresh(keyword)
        return keyword

    def get_keyword(self, keyword_id: str) -> Keyword | None:
        return self.session.get(Keyword, keyword_id)

    def list_keywords(self) -> list[Keyword]:
        return list(self.session.exec(select(Keyword).order_by(Keyword.opportunity_score.desc())).all())

    def update_keyword(self, keyword_id: str, **updates) -> Keyword:
        keyword = self.session.get(Keyword, keyword_id)
        if keyword is None:
            raise ValueError(f"Keyword not found: {keyword_id}")
        for field, value in updates.items():
            setattr(keyword, field, value)
        self.session.add(keyword)
        self.session.commit()
        self.session.refresh(keyword)
        return keyword

    def create_serp_result(self, serp_result: SerpResult) -> SerpResult:
        self.session.add(serp_result)
        self.session.commit()
        self.session.refresh(serp_result)
        return serp_result

    def get_latest_serp_result(self, keyword_id: str) -> SerpResult | None:
        statement = (
            select(SerpResult)
            .where(SerpResult.keyword_id == keyword_id)
            .order_by(SerpResult.fetched_at.desc())
        )
        return self.session.exec(statement).first()

    def create_competitor_page(self, competitor_page: CompetitorPage) -> CompetitorPage:
        self.session.add(competitor_page)
        self.session.commit()
        self.session.refresh(competitor_page)
        return competitor_page

    def list_competitor_pages(self, serp_result_id: str) -> list[CompetitorPage]:
        statement = select(CompetitorPage).where(CompetitorPage.serp_result_id == serp_result_id)
        return list(self.session.exec(statement).all())

    def save_content_brief(self, keyword_id: str, brief: ContentBrief) -> ContentBriefRecord:
        record = ContentBriefRecord(keyword_id=keyword_id, brief_json=brief.model_dump_json())
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_latest_content_brief(self, keyword_id: str) -> ContentBrief | None:
        statement = (
            select(ContentBriefRecord)
            .where(ContentBriefRecord.keyword_id == keyword_id)
            .order_by(ContentBriefRecord.created_at.desc())
        )
        record = self.session.exec(statement).first()
        if record is None:
            return None
        return ContentBrief.model_validate_json(record.brief_json)

    def create_article(self, article: Article, content: str) -> Article:
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        version = ArticleVersion(article_id=article.id, content=content)
        self.session.add(version)
        self.session.commit()
        return article

    def list_articles(self) -> list[Article]:
        return list(self.session.exec(select(Article).order_by(Article.created_at.desc())).all())

    def get_article(self, article_id: str) -> Article | None:
        return self.session.get(Article, article_id)

    def update_article(self, article_id: str, **updates) -> Article:
        article = self.get_article(article_id)
        if article is None:
            raise ValueError(f"Article not found: {article_id}")
        for field, value in updates.items():
            setattr(article, field, value)
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def create_ranking_snapshot(self, snapshot: RankingSnapshot) -> RankingSnapshot:
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    def get_published_articles(self) -> list[Article]:
        statement = select(Article).where(Article.status == "published")
        return list(self.session.exec(statement).all())

    def get_latest_ranking_snapshot(self, article_id: str) -> RankingSnapshot | None:
        statement = (
            select(RankingSnapshot)
            .where(RankingSnapshot.article_id == article_id)
            .order_by(RankingSnapshot.checked_at.desc())
        )
        return self.session.exec(statement).first()

    def get_keywords_by_opportunity_score(self, min_score: float, limit: int) -> list[Keyword]:
        statement = (
            select(Keyword)
            .where(Keyword.opportunity_score >= min_score)
            .order_by(Keyword.opportunity_score.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_content_performance_by_type(self) -> list[dict]:
        statement = select(Article.content_type, func.count(Article.id)).group_by(Article.content_type)
        return [
            {"content_type": content_type, "article_count": article_count}
            for content_type, article_count in self.session.exec(statement).all()
        ]

    def get_ranking_progress(self, article_id: str) -> list[RankingSnapshot]:
        statement = (
            select(RankingSnapshot)
            .where(RankingSnapshot.article_id == article_id)
            .order_by(RankingSnapshot.checked_at.asc())
        )
        return list(self.session.exec(statement).all())

    def get_top_opportunities(self, limit: int = 20) -> list[Keyword]:
        statement = select(Keyword).order_by(Keyword.opportunity_score.desc()).limit(limit)
        return list(self.session.exec(statement).all())

    def get_or_create_api_usage(self, provider: str, usage_month: date) -> ApiUsageRecord:
        statement = select(ApiUsageRecord).where(
            ApiUsageRecord.provider == provider,
            ApiUsageRecord.usage_month == usage_month,
        )
        record = self.session.exec(statement).first()
        if record is not None:
            return record
        record = ApiUsageRecord(provider=provider, usage_month=usage_month)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def record_api_usage(
        self,
        *,
        provider: str,
        calls: int = 0,
        spend_usd: float = 0.0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        usage_month: date | None = None,
    ) -> ApiUsageRecord:
        month = usage_month or date.today().replace(day=1)
        record = self.get_or_create_api_usage(provider, month)
        record.call_count += calls
        record.spend_usd = round(record.spend_usd + spend_usd, 4)
        record.tokens_in += tokens_in
        record.tokens_out += tokens_out
        record.updated_at = datetime.now(timezone.utc)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_api_usage(self, provider: str, usage_month: date | None = None) -> ApiUsageRecord | None:
        month = usage_month or date.today().replace(day=1)
        statement = select(ApiUsageRecord).where(
            ApiUsageRecord.provider == provider,
            ApiUsageRecord.usage_month == month,
        )
        return self.session.exec(statement).first()

    def cluster_keywords(self) -> list[KeywordCluster]:
        keywords = self.list_keywords()
        clusters: dict[str, list[Keyword]] = {}
        for keyword in keywords:
            key = keyword.term.split()[0].lower()
            clusters.setdefault(key, []).append(keyword)
        created_clusters: list[KeywordCluster] = []
        for name, group in clusters.items():
            primary = max(group, key=lambda item: item.monthly_volume or 0)
            cluster = KeywordCluster(
                primary_keyword_id=primary.id,
                cluster_name=name,
                total_cluster_volume=sum(item.monthly_volume or 0 for item in group),
            )
            self.session.add(cluster)
            self.session.commit()
            self.session.refresh(cluster)
            for keyword in group:
                self.session.add(
                    KeywordClusterMembership(cluster_id=cluster.id, keyword_id=keyword.id)
                )
            self.session.commit()
            created_clusters.append(cluster)
        return created_clusters
