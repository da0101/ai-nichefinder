from pydantic import BaseModel, Field


class EvidenceSignal(BaseModel):
    text: str
    count: int


class ArticleEvidenceBank(BaseModel):
    query: str
    pages_scraped: int = 0
    source_urls: list[str] = Field(default_factory=list)
    recurring_headings: list[EvidenceSignal] = Field(default_factory=list)
    recurring_questions: list[EvidenceSignal] = Field(default_factory=list)
    recurring_phrases: list[EvidenceSignal] = Field(default_factory=list)
    primary_terms: list[str] = Field(default_factory=list)
    secondary_terms: list[str] = Field(default_factory=list)
