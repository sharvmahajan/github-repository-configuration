# scripts/reporting.py
"""
Generates compliance report and score after enforcement runs.
Saves JSON and PDF reports in reports/ folder.
Calculates clamped score (0–100) with status label.
"""

import json
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

PARTIAL_COMPLIANCE_THRESHOLD = 70
PENALTY_PER_CHANGE = 5
MAX_SCORE = 100


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def is_meaningful_change(change: str) -> bool:
    c = change.lower()
    return (
        not change.startswith("[DRY-RUN]") and
        "already exists" not in c and
        "skipping" not in c and
        "would" not in c
    )


# -------------------------------------------------------------------
# Scoring
# -------------------------------------------------------------------

def calculate_compliance_score(changes: List[str]) -> int:
    meaningful_changes = [c for c in changes if is_meaningful_change(c)]
    score = MAX_SCORE - (len(meaningful_changes) * PENALTY_PER_CHANGE)
    return max(0, min(MAX_SCORE, score))


# -------------------------------------------------------------------
# Report generation
# -------------------------------------------------------------------

def generate_report(
    repo_name: str,
    changes: List[str],
    dry_run: bool,
    timestamp: str = None,
) -> Dict:
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    meaningful_changes = [c for c in changes if is_meaningful_change(c)]
    score = calculate_compliance_score(changes)

    if score == 100:
        status = "Fully Compliant"
    elif score >= PARTIAL_COMPLIANCE_THRESHOLD:
        status = "Partially Compliant"
    else:
        status = "Non-Compliant"

    return {
        "timestamp_utc": timestamp,
        "repo": repo_name,
        "dry_run": dry_run,
        "total_changes_detected": len(changes),
        "meaningful_changes": len(meaningful_changes),
        "compliance_score": score,
        "status": status,
        "changes": changes,
        "summary": (
            f"{status} ({score}%) - "
            f"{'No changes needed' if score == 100 else 'Some fixes applied/would be applied'}"
        ),
    }


# -------------------------------------------------------------------
# PDF generation
# -------------------------------------------------------------------

def save_pdf_report(report: Dict, filename: Path) -> None:
    styles = getSampleStyleSheet()
    story = []

    title_style = styles["Heading1"]
    title_style.alignment = TA_CENTER

    story.append(Paragraph("Compliance Report", title_style))
    story.append(Spacer(1, 12))

    meta_table = Table(
        [
            ["Repository", report["repo"]],
            ["Timestamp (UTC)", report["timestamp_utc"]],
            ["Dry-run", str(report["dry_run"])],
            ["Status", report["status"]],
            ["Compliance Score", f'{report["compliance_score"]}%'],
            ["Meaningful Changes", str(report["meaningful_changes"])],
        ],
        colWidths=[160, 360],
    )

    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONT", (0, 0), (-1, -1), "Helvetica"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(meta_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
    story.append(Paragraph(report["summary"], styles["Normal"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("<b>Changes</b>", styles["Heading2"]))

    if report["changes"]:
        for change in report["changes"]:
            story.append(Paragraph(f"- {change}", styles["Normal"]))
    else:
        story.append(Paragraph("No changes detected.", styles["Normal"]))

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    doc.build(story)


# -------------------------------------------------------------------
# Persistence & output
# -------------------------------------------------------------------

def save_and_print_report(report: Dict) -> Dict[str, str]:
    timestamp_clean = report["timestamp_utc"].replace(":", "-").split(".")[0]
    safe_repo = report["repo"].replace("/", "_")

    json_path = REPORTS_DIR / f"compliance-report-{safe_repo}-{timestamp_clean}.json"
    pdf_path = REPORTS_DIR / f"compliance-report-{safe_repo}-{timestamp_clean}.pdf"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    save_pdf_report(report, pdf_path)

    logger.info(f"Report saved: {json_path}")
    logger.info(f"PDF saved: {pdf_path}")

    print("\n" + "=" * 60)
    print(f"Compliance Report for {report['repo']}")
    print("=" * 60)
    print(f"Status: {report['status']}")
    print(f"Score:  {report['compliance_score']}%")
    print(f"PDF:    {pdf_path}")
    print("=" * 60 + "\n")

    return {
        "json": str(json_path),
        "pdf": str(pdf_path),
    }
