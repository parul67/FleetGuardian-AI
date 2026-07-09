import os
import csv
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.core.config import settings
from app.models.driver import Driver
from app.models.alert import Alert
from app.models.report import Report
from app.repositories import report_repo

class ReportService:
    def _get_reports_dir(self) -> str:
        reports_dir = os.path.join(settings.DATASET_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        return reports_dir

    def generate_csv_report(self, db: Session, user_id: int) -> Report:
        """Generates a CSV report summarizing driver scores and infractions."""
        reports_dir = self._get_reports_dir()
        filename = f"driver_safety_report_{int(datetime.now().timestamp())}.csv"
        file_path = os.path.join(reports_dir, filename)

        drivers = db.query(Driver).all()

        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Driver ID", "Employee ID", "Name", "License Plate/Number", "Safety Score", "Total Trips", "Total Violations", "Current Status"])
            for d in drivers:
                writer.writerow([d.id, d.employee_id, d.name, d.license_number, d.safety_score, d.total_trips, d.total_violations, d.current_status])

        # Record in db
        report = Report(
            name=f"Driver Safety CSV Report - {datetime.now().strftime('%Y-%m-%d')}",
            type="csv",
            file_path=file_path,
            created_by=user_id
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def generate_pdf_report(self, db: Session, user_id: int) -> Report:
        """Generates a publication-grade PDF report using reportlab."""
        reports_dir = self._get_reports_dir()
        filename = f"driver_safety_report_{int(datetime.now().timestamp())}.pdf"
        file_path = os.path.join(reports_dir, filename)

        drivers = db.query(Driver).order_by(Driver.safety_score.desc()).all()
        total_alerts = db.query(Alert).count()
        critical_alerts = db.query(Alert).filter(Alert.severity == "critical").count()
        avg_score = sum(d.safety_score for d in drivers) / len(drivers) if drivers else 100.0

        # Build document
        doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1A365D"),
            alignment=0, # Left-aligned
            spaceAfter=20
        )
        subtitle_style = ParagraphStyle(
            name="SubTitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=30
        )
        header2_style = ParagraphStyle(
            name="H2Style",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=15,
            spaceAfter=10
        )
        cell_style = ParagraphStyle(
            name="CellStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12
        )

        # Header
        story.append(Paragraph("FleetGuardian AI Safety Report", title_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Fleet Guardian Admin Operations", subtitle_style))
        story.append(Spacer(1, 10))

        # Metrics overview grid
        overview_data = [
            [
                Paragraph("<b>Average Safety Score</b>", cell_style),
                Paragraph("<b>Total Violations Logged</b>", cell_style),
                Paragraph("<b>Critical Violations</b>", cell_style)
            ],
            [
                Paragraph(f"{avg_score:.2f} / 100.0", cell_style),
                Paragraph(str(total_alerts), cell_style),
                Paragraph(str(critical_alerts), cell_style)
            ]
        ]
        
        t_overview = Table(overview_data, colWidths=[180, 180, 180])
        t_overview.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_overview)
        story.append(Spacer(1, 20))

        # Driver details section
        story.append(Paragraph("Fleet Driver Safety Scores", header2_style))
        
        # Table of driver info
        table_data = [
            ["ID", "Employee ID", "Driver Name", "Safety Score", "Violations", "Status"]
        ]
        for d in drivers:
            table_data.append([
                str(d.id),
                d.employee_id,
                d.name,
                f"{d.safety_score:.1f}",
                str(d.total_violations),
                d.current_status
            ])
            
        t_drivers = Table(table_data, colWidths=[40, 90, 180, 80, 70, 80])
        t_drivers.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_drivers)

        # Build PDF file
        doc.build(story)

        # Record in db
        report = Report(
            name=f"Driver Safety PDF Report - {datetime.now().strftime('%Y-%m-%d')}",
            type="pdf",
            file_path=file_path,
            created_by=user_id
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

report_service = ReportService()
