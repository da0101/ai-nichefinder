from pydantic import BaseModel


class BuyerProblem(BaseModel):
    problem: str
    audience: str
    why_now: str
    article_angle: str
    keyword_seed: str
    evidence_queries: list[str] = []
