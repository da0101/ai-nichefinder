from pydantic import BaseModel, Field


class KeywordSeed(BaseModel):
    """Normalized input for future discovery pipelines."""

    phrase: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=8)
    market: str = Field(min_length=2, max_length=64)

