from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.taxonomy import PILLARS, Category, Term
from app.schemas.taxonomy import CategoryCreate, CategoryOut, TermCreate, TermOut

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


@router.post("/categories", response_model=CategoryOut)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    existing = db.query(Category).filter(Category.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Category '{payload.name}' already exists")
    if payload.pillar not in PILLARS:
        raise HTTPException(status_code=400, detail=f"pillar must be one of {PILLARS}")
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return db.query(Category).all()


@router.post("/categories/{category_id}/terms", response_model=TermOut)
def add_term(category_id: int, payload: TermCreate, db: Session = Depends(get_db)) -> Term:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    term = Term(category_id=category_id, **payload.model_dump())
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


@router.delete("/terms/{term_id}", status_code=204)
def delete_term(term_id: int, db: Session = Depends(get_db)) -> None:
    term = db.get(Term, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    db.delete(term)
    db.commit()
