from pathlib import Path

from pydantic import BaseModel, Field


class SiteConfig(BaseModel):
    site_url: str = "https://danilulmashev.com"
    site_name: str = "Daniil Ulmashev"
    site_description: str = (
        "Personal portfolio - AI tools, SaaS, mobile apps, web design, consulting"
    )
    target_audience: str = "startups, SMBs, entrepreneurs looking for technical help"
    services: list[str] = Field(
        default_factory=lambda: [
            "AI tool development",
            "SaaS development",
            "mobile app development",
            "landing pages",
            "web design",
            "technical consulting",
        ]
    )
    primary_language: str = "en"
    blog_url: str = "https://danilulmashev.com/en/blog/"
    existing_articles: list[str] = Field(default_factory=list)
    seed_keywords: list[str] = Field(default_factory=list)
    target_persona: str = "technical founder or business owner who needs a development partner"
    competitors: list[str] = Field(default_factory=list)
    geographic_focus: list[str] = Field(
        default_factory=lambda: ["global", "north_america", "europe"]
    )


def load_site_config(path: Path) -> SiteConfig:
    return SiteConfig.model_validate_json(path.read_text(encoding="utf-8"))


def save_site_config(path: Path, site_config: SiteConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(site_config.model_dump_json(indent=2), encoding="utf-8")
