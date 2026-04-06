"""
FIR (First Information Report) PDF Generation Service
Generates Indian police FIR format PDFs using ReportLab
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import random
import logging

logger = logging.getLogger(__name__)


def generate_fir_pdf(data: dict) -> bytes:
    """
    Generate FIR PDF in Indian police format.
    
    Args:
        data: dict with keys:
            - case: Case object
            - missing_person: MissingPerson object
            - match: Match object (optional)
            - sighting: Sighting object (optional)
            - reporter: User/dict with name, phone
            - station: PoliceStation object (optional)
            - signed_by: User object (optional)
            - signed_at: datetime (optional)
    
    Returns:
        bytes: PDF content
    """
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*cm, bottomMargin=0.5*cm)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Get data
    case = data.get("case")
    missing_person = data.get("missing_person")
    match = data.get("match")
    sighting = data.get("sighting")
    reporter = data.get("reporter", {})
    station = data.get("station")
    signed_by = data.get("signed_by")
    signed_at = data.get("signed_at")
    
    fir_number = data.get("fir_number", f"FIR-{datetime.now().year}-{random.randint(100000, 999999)}")
    today = datetime.now().strftime("%d-%m-%Y")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HEADER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,  # Center
        textColor=colors.black
    )
    
    story.append(Paragraph("भारत सरकार / GOVERNMENT OF INDIA", header_style))
    story.append(Spacer(1, 0.1*cm))
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,
        textColor=colors.black,
        spaceAfter=0.2*cm,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph("प्रथम सूचना रिपोर्ट", title_style))
    story.append(Paragraph("FIRST INFORMATION REPORT (F.I.R.)", title_style))
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,
        fontName='Helvetica-Oblique'
    )
    story.append(Paragraph("Under Section 154 Cr.P.C.", subtitle_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Horizontal line
    line_data = [["_" * 120]]
    line_table = Table(line_data, colWidths=[7.5*inch])
    line_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 0.2*cm))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FIR FIELDS TABLE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    year = datetime.now().year
    district = missing_person.last_seen_state if missing_person else "N/A"
    station_name = (
        station.get("name") if isinstance(station, dict)
        else (station.name if station else "—")
    ) or "—"
    datetime_str = datetime.now().strftime("%d-%m-%Y %H:%M")
    
    fir_fields = [
        ["FIR No:", fir_number, "Date & Time:", datetime_str],
        ["District:", district, "Police Station:", station_name],
        ["Year:", str(year), "Offence:", "Missing Person Report (IPC 363)"]
    ]
    
    fir_table = Table(fir_fields, colWidths=[1.5*inch, 2.0*inch, 1.5*inch, 2.0*inch])
    fir_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(fir_table)
    story.append(Spacer(1, 0.3*cm))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 1: COMPLAINANT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        spaceAfter=0.1*cm
    )
    
    story.append(Paragraph("SECTION 1 — COMPLAINANT", section_style))
    
    reporter_name = reporter.get("name", "N/A") if isinstance(reporter, dict) else reporter.name
    reporter_phone = reporter.get("phone", "N/A") if isinstance(reporter, dict) else getattr(reporter, "phone", "N/A")
    
    complainant_text = f"""
    <b>Name:</b> {reporter_name}<br/>
    <b>Nationality:</b> Indian<br/>
    <b>Phone:</b> {reporter_phone}
    """
    story.append(Paragraph(complainant_text, styles['Normal']))
    story.append(Spacer(1, 0.2*cm))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 2: ACCUSED
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    story.append(Paragraph("SECTION 2 — ACCUSED", section_style))
    story.append(Paragraph("<b>Not Applicable</b> — This is a Missing Person Report", styles['Normal']))
    story.append(Spacer(1, 0.2*cm))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 3: MISSING PERSON
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    story.append(Paragraph("SECTION 3 — MISSING PERSON", section_style))
    
    mp_name = missing_person.full_name if missing_person else "Unknown"
    mp_age = missing_person.age if missing_person else "Unknown"
    mp_gender = missing_person.gender if missing_person else "Unknown"
    mp_date = missing_person.last_seen_date if missing_person else "Unknown"
    mp_city = missing_person.last_seen_city if missing_person else "Unknown"
    mp_state = missing_person.last_seen_state if missing_person else "Unknown"
    mp_address = missing_person.last_seen_address if missing_person else "Unknown"
    mp_desc = missing_person.description if missing_person else "N/A"
    mp_lat = missing_person.last_seen_lat if missing_person else 0
    mp_lng = missing_person.last_seen_lng if missing_person else 0
    
    osm_link = f"https://www.openstreetmap.org/?mlat={mp_lat}&mlon={mp_lng}&zoom=15"
    
    missing_person_text = f"""
    <b>Full Name:</b> {mp_name}<br/>
    <b>Age:</b> {mp_age}  |  <b>Gender:</b> {mp_gender}<br/>
    <b>Last Seen Date:</b> {mp_date}<br/>
    <b>Last Seen Location:</b> {mp_address}, {mp_city}, {mp_state}<br/>
    <b>GPS Coordinates:</b> {mp_lat:.4f}, {mp_lng:.4f}<br/>
    <b>Map:</b> <a href="{osm_link}">OpenStreetMap</a><br/>
    <b>Description:</b> {mp_desc}
    """
    story.append(Paragraph(missing_person_text, styles['Normal']))
    story.append(Spacer(1, 0.2*cm))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 4: DIGITAL MATCH (if exists)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if match and sighting:
        story.append(Paragraph("SECTION 4 — DIGITAL FACIAL MATCH", section_style))
        
        confidence_pct = match.confidence * 100 if match else 0
        sighting_city = sighting.sighting_city if sighting else "Unknown"
        sighting_lat = sighting.sighting_lat if sighting else 0
        sighting_lng = sighting.sighting_lng if sighting else 0
        sighting_date = sighting.created_at.strftime("%d-%m-%Y") if sighting else "Unknown"
        
        osm_sighting_link = f"https://www.openstreetmap.org/?mlat={sighting_lat}&mlon={sighting_lng}&zoom=15"
        
        match_text = f"""
        <b>System:</b> Missing Person Tracking System (Facial Recognition)<br/>
        <b>Confidence:</b> {confidence_pct:.1f}%<br/>
        <b>Sighted Date:</b> {sighting_date}<br/>
        <b>Sighted Location:</b> {sighting_city}<br/>
        <b>Sighting GPS:</b> {sighting_lat:.4f}, {sighting_lng:.4f}<br/>
        <b>Map:</b> <a href="{osm_sighting_link}">OpenStreetMap</a>
        """
        story.append(Paragraph(match_text, styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 5: ACTION REQUESTED
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    story.append(Paragraph("SECTION 5 — ACTION REQUESTED", section_style))
    
    search_city = sighting_city if (match and sighting) else mp_city
    if station:
        if isinstance(station, dict):
            station_distance = station.get("distance_km")
            distance_text = f" ({float(station_distance):.1f} km)" if station_distance is not None else ""
            station_info = f"{station.get('name', 'Police Station')}, {station.get('address', 'Unknown address')}{distance_text}"
        else:
            station_info = f"{station.name}, {station.address}"
    else:
        station_info = "Nearest station to be determined"
    
    action_text = f"""
    <b>Immediate Search Location:</b> {search_city}<br/>
    <b>Nearest Police Station:</b> {station_info}<br/>
    <b>Priority:</b> High — Digital facial match detected
    """
    story.append(Paragraph(action_text, styles['Normal']))
    story.append(Spacer(1, 0.3*cm))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SIGNATURES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    story.append(Paragraph("SIGNATURES", section_style))
    
    signed_by_name = signed_by.name if signed_by else "PENDING ADMIN SIGNOFF"
    signed_at_str = signed_at.strftime("%d-%m-%Y %H:%M") if signed_at else "—"
    
    sig_data = [
        ["Complainant Signature: ___________", "", "Reviewing Officer: ___________"],
        [reporter_name, "", signed_by_name],
        [f"Date: {today}", "", f"Date: {signed_at_str}"],
    ]
    
    sig_table = Table(sig_data, colWidths=[2.3*inch, 0.5*inch, 2.3*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FOOTER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,
        textColor=colors.grey
    )
    
    case_number = case.case_number if case else "Unknown"
    footer_text = f"""
    Generated by Missing Person Tracking System<br/>
    Case: {case_number}  |  FIR: {fir_number}<br/>
    Digital document — verify at localhost:8000
    """
    story.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
