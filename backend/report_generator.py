"""
PDF Report Generator for MediScan AI.
Generates structured, downloadable clinical decision-support summaries
from analysis findings without inventing any unverified patient or diagnostic data.
"""

from datetime import datetime, timezone
import io
from typing import Dict, Any, List, Optional
from fpdf import FPDF


class MediScanReportPDF(FPDF):
    """Custom FPDF layout for MediScan AI analysis reports."""

    def header(self):
        # Header banner
        self.set_fill_color(24, 32, 47)  # Dark slate blue
        self.rect(0, 0, 210, 28, 'F')

        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 15)
        self.set_xy(14, 7)
        self.cell(0, 8, "MediScan AI  Medical Image Analysis Report", ln=True)

        self.set_font('Helvetica', '', 9)
        self.set_text_color(180, 195, 215)
        self.set_xy(14, 16)
        self.cell(0, 6, "Computer-Aided Medical Diagnostic Screening Assistance", ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "CONFIDENTIAL  For clinical and educational decision-support only. Not a standalone diagnosis.", align='C', ln=True)
        self.cell(0, 4, f"Page {self.page_no()} of {{nb}}", align='C')


def generate_analysis_pdf(analysis_data: Dict[str, Any]) -> bytes:
    """
    Generate a formatted PDF report from prediction results.

    Args:
        analysis_data: Dictionary containing:
            - results: List of result dicts (disease, confidence, status, description, etc.)
            - model_used: Name of model used (e.g. 'CheXNet', 'MURA')
            - scan_type: Scan type or modality (optional)
            - request_id: Tracking request ID (optional)
            - generated_at: ISO timestamp (optional)

    Returns:
        bytes: Complete PDF document binary stream.
    """
    pdf = MediScanReportPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=24)
    pdf.alias_nb_pages()
    pdf.add_page()

    results: List[Dict[str, Any]] = analysis_data.get('results') or []
    model_name = str(analysis_data.get('model_used') or 'Auto-Detect').strip()
    scan_type = str(analysis_data.get('scan_type') or 'Medical Radiograph').title()
    request_id = str(analysis_data.get('request_id') or 'N/A').strip()

    gen_time_str = analysis_data.get('generated_at')
    if not gen_time_str:
        gen_time_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # ── METADATA SECTION ────────────────────────────────────────────────
    pdf.set_xy(14, 34)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(40, 50, 70)
    pdf.cell(0, 6, "REPORT SUMMARY & SCAN DETAILS", ln=True)

    pdf.set_fill_color(248, 249, 251)
    pdf.set_draw_color(220, 226, 235)
    pdf.rect(14, 41, 182, 24, 'FD')

    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(100, 110, 125)

    pdf.set_xy(18, 44)
    pdf.cell(45, 5, "Report Reference:")
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(30, 40, 55)
    pdf.cell(45, 5, request_id)

    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(35, 5, "Analysis Date:")
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(30, 40, 55)
    pdf.cell(50, 5, gen_time_str, ln=True)

    pdf.set_xy(18, 52)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(45, 5, "Scan Modality:")
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(30, 40, 55)
    pdf.cell(45, 5, scan_type)

    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(35, 5, "Model Engine:")
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(30, 40, 55)
    pdf.cell(50, 5, model_name, ln=True)

    pdf.ln(12)

    # ── PRIMARY FINDING ─────────────────────────────────────────────────
    pdf.set_x(14)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(40, 50, 70)
    pdf.cell(0, 6, "PRIMARY AI FINDING", ln=True)

    if results and len(results) > 0:
        primary = results[0]
        disease = str(primary.get('disease') or 'Unspecified finding')
        confidence = primary.get('confidence', 0)
        status = str(primary.get('status') or 'healthy').lower()
        description = str(primary.get('description') or 'No narrative description provided.')
        uncertainty = primary.get('uncertainty_pct')
        regions = primary.get('regions') or []
        final_assessment = primary.get('final_assessment')
        likelihood_label = primary.get('likelihood_label') or (
            'Normal' if status == 'healthy' else 'Moderate Likelihood' if status == 'warning' else 'High Likelihood'
        )

        # Status background colors
        if status == 'critical':
            bg_r, bg_g, bg_b = 254, 242, 242
            border_r, border_g, border_b = 239, 68, 68
            tag_r, tag_g, tag_b = 185, 28, 28
        elif status == 'warning':
            bg_r, bg_g, bg_b = 254, 252, 232
            border_r, border_g, border_b = 234, 179, 8
            tag_r, tag_g, tag_b = 161, 98, 7
        else:
            bg_r, bg_g, bg_b = 240, 253, 244
            border_r, border_g, border_b = 34, 197, 94
            tag_r, tag_g, tag_b = 21, 128, 61

        start_y = pdf.get_y() + 2
        card_h = 38 + (10 if regions else 0) + (10 if final_assessment else 0)
        pdf.set_fill_color(bg_r, bg_g, bg_b)
        pdf.set_draw_color(border_r, border_g, border_b)
        pdf.rect(14, start_y, 182, card_h, 'FD')

        # Disease headline
        pdf.set_xy(18, start_y + 4)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(tag_r, tag_g, tag_b)
        pdf.cell(100, 6, disease)

        # Likelihood & Confidence Badge
        pdf.set_font('Helvetica', 'B', 9)
        conf_str = f"Confidence: {confidence}%"
        if uncertainty:
            conf_str += f" (+/-{uncertainty}%)"
        conf_str += f" | {likelihood_label}"
        pdf.cell(75, 6, conf_str, align='R', ln=True)

        # Description
        pdf.set_xy(18, start_y + 13)
        pdf.set_font('Helvetica', '', 8.5)
        pdf.set_text_color(50, 60, 75)
        pdf.multi_cell(174, 4.5, description)

        current_y = pdf.get_y() + 2

        if final_assessment:
            pdf.set_xy(18, current_y)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(tag_r, tag_g, tag_b)
            pdf.cell(32, 4.5, "Clinical Assessment: ")
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(40, 50, 65)
            pdf.cell(140, 4.5, str(final_assessment), ln=True)
            current_y += 6

        if regions:
            pdf.set_xy(18, current_y)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(tag_r, tag_g, tag_b)
            pdf.cell(32, 4.5, "Identified Regions: ")
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(40, 50, 65)
            pdf.cell(140, 4.5, ", ".join(str(r) for r in regions), ln=True)
            current_y += 6

        pdf.set_y(start_y + card_h + 6)

        # ── SECONDARY POSSIBILITIES ─────────────────────────────────────
        if len(results) > 1:
            pdf.set_x(14)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(40, 50, 70)
            pdf.cell(0, 6, "SECONDARY DIFFERENTIAL FINDINGS", ln=True)
            pdf.ln(2)

            # Table Header
            pdf.set_x(14)
            pdf.set_fill_color(230, 235, 245)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(50, 60, 80)
            pdf.cell(110, 6, "  Condition / Finding", border=1, fill=True)
            pdf.cell(36, 6, "  Confidence", border=1, fill=True)
            pdf.cell(36, 6, "  Classification", border=1, ln=True, fill=True)

            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(40, 50, 65)
            for item in results[1:5]:  # limit to top secondary
                pdf.set_x(14)
                item_disease = str(item.get('disease', 'Unspecified'))
                item_conf = f"{item.get('confidence', 0)}%"
                item_status = str(item.get('status', 'healthy')).capitalize()
                pdf.cell(110, 6, f"  {item_disease}", border=1)
                pdf.cell(36, 6, f"  {item_conf}", border=1)
                pdf.cell(36, 6, f"  {item_status}", border=1, ln=True)

            pdf.ln(6)

        # ── QUALITY / VALIDATION WARNINGS ───────────────────────────────
        warnings = primary.get('warnings') or []
        if warnings:
            pdf.set_x(14)
            pdf.set_fill_color(255, 251, 235)
            pdf.set_draw_color(245, 158, 11)
            pdf.rect(14, pdf.get_y(), 182, 14, 'FD')

            pdf.set_xy(18, pdf.get_y() + 2)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(180, 83, 9)
            pdf.cell(0, 4, "Quality & Confidence Warnings Noted:", ln=True)
            pdf.set_font('Helvetica', '', 7.5)
            pdf.set_x(18)
            warning_labels = {
                'low_image_quality': 'Low image resolution or sharpness detected; scores may have lower reliability.',
                'low_medical_confidence': 'Image passed validation with borderline medical feature characteristics.'
            }
            notes = [warning_labels.get(w, w) for w in warnings]
            pdf.cell(0, 4, "; ".join(notes), ln=True)
            pdf.ln(8)

    else:
        pdf.set_x(14)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(100, 110, 120)
        pdf.cell(0, 6, "No diagnostic findings recorded for this analysis session.", ln=True)
        pdf.ln(6)

    # ── CLINICAL DISCLAIMER BANNER ──────────────────────────────────────
    pdf.ln(4)
    disc_y = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(14, disc_y, 182, 34, 'FD')

    pdf.set_xy(18, disc_y + 3)
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(185, 28, 28)
    pdf.cell(0, 4, "IMPORTANT CLINICAL & REGULATORY DISCLAIMER", ln=True)

    pdf.set_xy(18, disc_y + 8)
    pdf.set_font('Helvetica', '', 7.5)
    pdf.set_text_color(71, 85, 105)
    disclaimer_text = (
        "This automated report was produced by the MediScan AI computer-aided screening system for informational "
        "and investigative purposes only. THIS REPORT DOES NOT CONSTITUTE A MEDICAL DIAGNOSIS, RADIOLOGICAL INTERPRETATION, "
        "OR TREATMENT PRESCRIPTION. Diagnostic imaging must be evaluated in comprehensive clinical context by a licensed physician "
        "or board-certified radiologist. The underlying artificial intelligence models provide probabilistic assistive scores and "
        "may not detect all medical abnormalities or subtle pathologies."
    )
    pdf.multi_cell(174, 3.8, disclaimer_text)

    # Output raw PDF bytes
    output_buf = pdf.output()
    if isinstance(output_buf, (bytes, bytearray)):
        return bytes(output_buf)
    return str(output_buf).encode('latin1')
