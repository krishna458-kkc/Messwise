"""MessWise Green-Campus Sustainability PDF Report Generator (Module H: H4).

Generates downloadable, executive-grade PDF reports for university administration,
hostel wardens, and sustainability governance committees.
Uses reportlab in-memory generation (io.BytesIO) without hardcoding OS file paths.

Complies strictly with PLAN.md Section 5 (Module H4), Section 10, and Appendix F:
- Clear separation of Synthetic Demonstration vs Real Pilot data.
- Avoided food metrics, Low/Central/High CO₂e emission bands with inspectable citations.
- Meals-equivalent metrics with learned per-head consumption rate basis.
- Zero-Hunger shortage safeguards (service-level preservation).
- Full disclosure of methodology, lifecycle boundaries, and statistical caveats.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        HRFlowable,
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from messwise.impact import GreenCampusImpactSummary


def is_pdf_available() -> bool:
    """Check if ReportLab is installed and PDF generation is available."""
    return HAS_REPORTLAB


def generate_green_campus_pdf(
    summary: GreenCampusImpactSummary,
    report_title: str = "MessWise Green-Campus Sustainability Report",
) -> bytes:
    """Generate in-memory PDF byte stream for Green-Campus monthly report (H4)."""
    if not HAS_REPORTLAB:
        raise RuntimeError(
            "ReportLab library is not installed in the active environment. "
            "Please install it using: python -m pip install reportlab"
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
        pageCompression=0,
    )


    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1b4332"),  # Deep Forest Green
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#495057"),
        spaceAfter=12,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2d6a4f"),
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#212529"),
    )
    bold_body = ParagraphStyle(
        "BoldBody",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    notice_style = ParagraphStyle(
        "NoticeStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#854d0e"),
        alignment=1,  # Centered
    )
    footnote_style = ParagraphStyle(
        "Footnote",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6c757d"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph(report_title, title_style))
    meta_text = (
        f"<b>Reporting Period:</b> {summary.reporting_period} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Scope:</b> {summary.data_basis_label} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    story.append(Paragraph(meta_text, subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2d6a4f"), spaceAfter=10))

    # 2. Prominent Environment / Data-Honesty Warning
    if summary.is_synthetic == 1:
        warn_data = [[
            Paragraph(
                "<b>[!] SYNTHETIC DEMONSTRATION -- NOT REAL-WORLD IMPACT</b><br/>"
                "This report is generated from synthetic simulation data for algorithm verification. "
                "No physical food savings or carbon emissions have been verified from these test runs.",
                notice_style,
            )
        ]]
        t_warn = Table(warn_data, colWidths=[532])
        t_warn.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef9c3")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#eab308")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_warn)
        story.append(Spacer(1, 10))
    elif summary.meals_count == 0:
        info_data = [[
            Paragraph(
                "<b>[*] REAL PILOT DATA COLLECTION IN PROGRESS</b><br/>"
                "0 real pilot meals have been recorded to date. Authentic impact figures will be populated "
                "once the on-campus pilot begins logging actual kitchen measurements.",
                notice_style,
            )
        ]]
        t_info = Table(info_data, colWidths=[532])
        t_info.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e0f2fe")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#38bdf8")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 10))

    # 3. Executive Summary KPI Table
    story.append(Paragraph("1. Executive Summary & Operational Scope", section_heading))
    
    kpi_rows = [
        [
            Paragraph("<b>Metric</b>", bold_body),
            Paragraph("<b>Measured Value</b>", bold_body),
            Paragraph("<b>Operational Status</b>", bold_body),
        ],
        [
            Paragraph("Eligible Meals Sampled", body_style),
            Paragraph(f"{summary.meals_count} meals", body_style),
            Paragraph("Operational record count", body_style),
        ],
        [
            Paragraph("Total Food Cooked (kg)", body_style),
            Paragraph(f"{summary.total_cooked_kg:,.1f} kg", body_style),
            Paragraph("Kitchen scale log sum", body_style),
        ],
        [
            Paragraph("Total Surplus / Leftovers", body_style),
            Paragraph(f"{summary.total_waste_kg:,.1f} kg ({summary.waste_percentage:.1f}%)", body_style),
            Paragraph("Post-service weigh-in", body_style),
        ],
        [
            Paragraph("Estimated Avoided Food", body_style),
            Paragraph(f"<b>{summary.eligible_avoided_kg:,.1f} kg</b>", body_style),
            Paragraph("Assisted reduction vs baseline", body_style),
        ],
        [
            Paragraph("Service-Level Protected", body_style),
            Paragraph(f"<b>{summary.service_level_preserved_pct:.1f}%</b>", body_style),
            Paragraph(f"{summary.shortage_dish_meals} shortage events recorded", body_style),
        ],
    ]

    t_kpi = Table(kpi_rows, colWidths=[180, 150, 202])
    t_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9ecef")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 12))

    # 4. H1 Greenhouse Gas (GHG) Emissions Mitigation
    story.append(Paragraph("2. Greenhouse Gas (GHG) Emissions Mitigation (H1)", section_heading))
    
    co2e = summary.co2e_impact
    if co2e.is_available:
        ghg_intro = (
            f"Based on <b>{co2e.eligible_food_kg:.1f} kg</b> of food waste avoided, greenhouse gas emissions "
            f"mitigation is estimated using a peer-reviewed lifecycle uncertainty band:"
        )
        story.append(Paragraph(ghg_intro, body_style))
        story.append(Spacer(1, 6))

        ghg_rows = [
            [
                Paragraph("<b>Estimate Tier</b>", bold_body),
                Paragraph("<b>Factor (kg CO₂e / kg)</b>", bold_body),
                Paragraph("<b>CO₂e Avoided (kg)</b>", bold_body),
                Paragraph("<b>Tonnes CO₂e</b>", bold_body),
            ],
            [
                Paragraph("Low Bound", body_style),
                Paragraph(f"{co2e.factor_config.low_factor:.2f}", body_style),
                Paragraph(f"{co2e.low_co2e_kg:,.1f} kg", body_style),
                Paragraph(f"{(co2e.low_co2e_kg / 1000.0):.2f} t", body_style),
            ],
            [
                Paragraph("<b>Central Estimate</b>", bold_body),
                Paragraph(f"<b>{co2e.factor_config.central_factor:.2f}</b>", bold_body),
                Paragraph(f"<b>{co2e.central_co2e_kg:,.1f} kg</b>", bold_body),
                Paragraph(f"<b>{(co2e.central_co2e_kg / 1000.0):.2f} t</b>", bold_body),
            ],
            [
                Paragraph("High Bound", body_style),
                Paragraph(f"{co2e.factor_config.high_factor:.2f}", body_style),
                Paragraph(f"{co2e.high_co2e_kg:,.1f} kg", body_style),
                Paragraph(f"{(co2e.high_co2e_kg / 1000.0):.2f} t", body_style),
            ],
        ]
        t_ghg = Table(ghg_rows, colWidths=[130, 130, 136, 136])
        t_ghg.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9ecef")),
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#d8f3dc")),  # highlight central
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_ghg)
    else:
        story.append(Paragraph(f"<i>Status: {co2e.availability_reason}</i>", body_style))

    story.append(Spacer(1, 8))
    citation_text = (
        f"<b>Methodology & Source:</b> {co2e.factor_config.source_name} ({co2e.factor_config.version}).<br/>"
        f"<b>System Boundary:</b> {co2e.factor_config.system_boundary}."
    )
    story.append(Paragraph(citation_text, footnote_style))
    story.append(Spacer(1, 12))

    # 5. H2 Social & Nutrition Equivalent (Meals-Equivalent)
    story.append(Paragraph("3. Social & Meals-Equivalent Impact (H2)", section_heading))
    meals_eq = summary.meals_equivalent

    if meals_eq.is_available:
        meals_text = (
            f"The <b>{meals_eq.eligible_food_kg:.1f} kg</b> of food preserved represents an illustrative "
            f"equivalent of <b>{meals_eq.meals_equivalent:,.0f} student meals</b> "
            f"(computed at a learned rate of {meals_eq.avg_consumption_per_head_kg:.3f} kg/meal)."
        )
        story.append(Paragraph(meals_text, body_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "<i>Note: Labelled as an illustrative equivalent based on learned mess appetite, "
            "not physical cooked leftovers re-served or distributed.</i>",
            footnote_style,
        ))
    else:
        story.append(Paragraph(f"<i>Status: {meals_eq.availability_reason}</i>", body_style))

    story.append(Spacer(1, 12))

    # 6. SDG 12.3 & Resource Efficiency
    if summary.sdg123 and summary.sdg123.is_available:
        story.append(Paragraph("4. SDG Target 12.3 & Resource Footprint (H3, H5)", section_heading))
        sdg_text = (
            f"- <b>SDG 12.3 Waste Halving Progress:</b> Current per-diner waste is <b>{summary.sdg123.current_waste_per_head_g:.1f} g/meal</b> "
            f"(a <b>{summary.sdg123.reduction_pct:.1f}% reduction</b> vs baseline of {summary.sdg123.baseline_waste_per_head_g:.1f} g/meal). "
            f"Progress toward 50% target: <b>{summary.sdg123.target_progress_pct:.1f}%</b> ({summary.sdg123.status_label})."
        )
        story.append(Paragraph(sdg_text, body_style))
        if summary.water_energy and summary.water_energy.is_available:
            we_text = (
                f"- <b>Virtual Water Preserved:</b> ~<b>{summary.water_energy.central_water_litres:,.0f} Litres</b> "
                f"({summary.water_energy.low_water_litres:,.0f} to {summary.water_energy.high_water_litres:,.0f} L band).<br/>"
                f"- <b>Embedded Primary Energy:</b> ~<b>{summary.water_energy.central_energy_mj:,.1f} MJ</b> "
                f"({summary.water_energy.low_energy_mj:,.1f} to {summary.water_energy.high_energy_mj:,.1f} MJ band)."
            )
            story.append(Paragraph(we_text, body_style))
        story.append(Spacer(1, 10))

    # 7. Service-Level Protection & Governance
    story.append(Paragraph("5. Governance, Safety & Zero-Hunger Protections", section_heading))
    gov_text = (
        "- <b>Zero Leftover Re-Serving:</b> MessWise strictly prohibits re-serving cooked leftovers to students.<br/>"
        "- <b>Shortage Protection:</b> Waste reduction was achieved without intentional food shortages. "
        f"Service level was maintained at <b>{summary.service_level_preserved_pct:.1f}%</b>.<br/>"
        "- <b>Privacy by Design:</b> No student names, biometric identifiers, or personal IDs were recorded.<br/>"
        f"- <b>Financial Verification:</b> {summary.cost_status_message}"
    )
    story.append(Paragraph(gov_text, body_style))

    # Build document
    doc.build(story)
    return buffer.getvalue()
