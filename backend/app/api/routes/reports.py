import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.institution import Institution
from app.models.report import Report
from app.models.score import MatchEvidence
from app.models.taxonomy import Term
from app.schemas.score import MatchEvidenceOut, ReportOut
from app.services.pipeline import process_report
from app.services.storage import write_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut)
def upload_report(
    institution_id: int = Form(...),
    fiscal_year: int = Form(...),
    language: str = Form("en"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Report:
    institution = db.get(Institution, institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Session 9: manual uploads go to R2 under an "uploads/" prefix so
    # they don't collide with crawler-sourced keys (which are grouped
    # by slug). Stored key is what Report.file_path holds.
    body = file.file.read()
    key = f"uploads/{institution_id}_{fiscal_year}_{uuid.uuid4().hex[:8]}.pdf"
    write_pdf(key, body)

    report = Report(
        institution_id=institution_id,
        fiscal_year=fiscal_year,
        language=language,
        file_path=key,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Synchronous for the pilot. Swap for a background task/queue at scale
    # (see docstring in services/pipeline.py) so this endpoint returns instantly.
    process_report(db, report)

    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)) -> Report:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{report_id}/reprocess", response_model=ReportOut)
def reprocess_report(report_id: int, db: Session = Depends(get_db)) -> Report:
    """Re-run scoring — useful after editing the taxonomy."""
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return process_report(db, report)


@router.get("/{report_id}/evidence", response_model=list[MatchEvidenceOut])
def get_evidence(
    report_id: int, term_id: int | None = None, db: Session = Depends(get_db)
) -> list[MatchEvidenceOut]:
    query = db.query(MatchEvidence).filter(MatchEvidence.report_id == report_id)
    if term_id is not None:
        query = query.filter(MatchEvidence.term_id == term_id)

    results: list[MatchEvidenceOut] = []
    for m in query.all():
        term = db.get(Term, m.term_id)
        results.append(MatchEvidenceOut(
            page_number=m.page_number,
            sentence_text=m.sentence_text,
            term_phrase=term.phrase if term else "",
        ))
    return results
