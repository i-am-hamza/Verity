from pydantic import BaseModel


class InstitutionCreate(BaseModel):
    name: str
    country: str
    sector: str = "banking"


class InstitutionOut(InstitutionCreate):
    id: int

    class Config:
        from_attributes = True
