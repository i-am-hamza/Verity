from pydantic import BaseModel


class ReportOut(BaseModel):
    id: int
    institution_id: int
    fiscal_year: int
    language: str
    status: str
    total_word_count: int
    page_count: int
    error_message: str | None = None

    class Config:
        from_attributes = True


class CategoryScoreOut(BaseModel):
    category_id: int
    category_name: str
    raw_weighted_count: float
    density_per_1000_words: float


class ReportScoreOut(BaseModel):
    report_id: int
    fiscal_year: int
    composite_score: float
    pillar_scores: dict[str, float]  # "Environmental"/"Social"/"Governance" -> score
    category_scores: list[CategoryScoreOut]


class MatchEvidenceOut(BaseModel):
    page_number: int
    sentence_text: str
    term_phrase: str


class InstitutionRankingOut(BaseModel):
    institution_id: int
    institution_name: str
    country: str
    institution_score: float
    years_scored: int
    pillar_breakdown: dict[str, float]  # averaged across years, same pillars as above
    category_breakdown: list[CategoryScoreOut]
