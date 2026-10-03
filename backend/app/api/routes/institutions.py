from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate, InstitutionOut

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.post("", response_model=InstitutionOut)
def create_institution(payload: InstitutionCreate, db: Session = Depends(get_db)) -> Institution:
    institution = Institution(**payload.model_dump())
    db.add(institution)
    db.commit()
    db.refresh(institution)
    return institution


@router.get("", response_model=list[InstitutionOut])
def list_institutions(db: Session = Depends(get_db)) -> list[Institution]:
    return db.query(Institution).order_by(Institution.name).all()


@router.get("/{institution_id}", response_model=InstitutionOut)
def get_institution(institution_id: int, db: Session = Depends(get_db)) -> Institution:
    institution = db.get(Institution, institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution
