from pydantic import BaseModel


class TermCreate(BaseModel):
    phrase: str
    weight: float = 1.0
    lemma_based: bool = True


class TermOut(TermCreate):
    id: int
    category_id: int

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    pillar: str  # "Environmental" | "Social" | "Governance"
    weight: float = 1.0


class CategoryOut(CategoryCreate):
    id: int
    terms: list[TermOut] = []

    class Config:
        from_attributes = True
