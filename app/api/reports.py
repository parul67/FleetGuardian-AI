import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories import report_repo
from app.schemas.report import ReportResponse, ReportCreate
from app.services.report_service import report_service
from app.services.auth_service import get_current_active_user
from app.models.user import User

router = APIRouter()

read_dependency = Depends(get_current_active_user)

@router.get("/", response_model=List[ReportResponse])
def read_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = read_dependency):
    """Lists generated report history."""
    return report_repo.get_multi(db, skip=skip, limit=limit)

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = read_dependency
):
    """Triggers report compilation (type: pdf or csv) and saves path in DB."""
    if report_in.type.lower() == "pdf":
        return report_service.generate_pdf_report(db, user_id=current_user.id)
    elif report_in.type.lower() == "csv":
        return report_service.generate_csv_report(db, user_id=current_user.id)
    else:
        raise HTTPException(status_code=400, detail="Invalid report type. Supported types: 'pdf', 'csv'")

@router.get("/{id}", response_model=ReportResponse)
def read_report(id: int, db: Session = Depends(get_db), current_user: User = read_dependency):
    """Reads metadata details of a report."""
    report = report_repo.get(db, id=id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/{id}/download")
def download_report(id: int, db: Session = Depends(get_db), current_user: User = read_dependency):
    """Downloads the physical PDF/CSV file for a given report ID."""
    report = report_repo.get(db, id=id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Physical report file not found on server disk")
        
    filename = os.path.basename(report.file_path)
    # Return FileResponse which prompts download dialog
    return FileResponse(
        path=report.file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
