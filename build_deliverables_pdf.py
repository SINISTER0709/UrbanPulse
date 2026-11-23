import os
import sys
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Output directory and file
OUTPUT_DIR = r"C:\vs\URBANPULSE\PDF"
os.makedirs(OUTPUT_DIR, exist_ok=True)
PDF_PATH = os.path.join(OUTPUT_DIR, "UrbanPulse_AI_Evaluation_Deliverables.pdf")

# User uploaded screenshots directory
IMG_DIR = r"C:\Users\SINIS\.gemini\antigravity\brain\08b1a15f-7cca-4bc9-9975-d1bd5c8e0b1b\.user_uploaded"

# Color Palette
PRIMARY_COLOR = colors.HexColor('#0F172A')    # Slate 900
SECONDARY_COLOR = colors.HexColor('#1E293B')  # Slate 800
BRAND_BLUE = colors.HexColor('#2563EB')       # Royal Blue
BRAND_LIGHT = colors.HexColor('#EFF6FF')      # Light Blue background
ACCENT_RED = colors.HexColor('#DC2626')       # Critical Red
ACCENT_GREEN = colors.HexColor('#16A34A')     # Success Green
ACCENT_AMBER = colors.HexColor('#D97706')     # Warning Amber
TEXT_DARK = colors.HexColor('#1E293B')
TEXT_MUTED = colors.HexColor('#64748B')
BG_LIGHT = colors.HexColor('#F8FAFC')
BORDER_COLOR = colors.HexColor('#E2E8F0')
HEADER_BG = colors.HexColor('#F1F5F9')

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and draw consistent
    running headers and footers on all pages except the cover page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Skip decorations on Cover Page

        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(TEXT_MUTED)

        # Running Header
        self.drawString(36, 812, "URBANPULSE AI — COMPREHENSIVE CAPSTONE EVALUATION DELIVERABLES")
        self.drawRightString(559, 812, "BENNETT UNIVERSITY | CSET400C")
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.6)
        self.line(36, 806, 559, 806)

        # Running Footer
        self.line(36, 42, 559, 42)
        self.setFont("Helvetica", 7.5)
        self.drawString(36, 30, "Confidential — Academic Capstone Evaluation & Technical Milestone Verification")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 30, page_str)
        self.restoreState()


def get_custom_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles['CoverPre'] = ParagraphStyle(
        'CoverPre',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=BRAND_BLUE,
        alignment=1, # Centered
        spaceAfter=6
    )

    styles['CoverInstitution'] = ParagraphStyle(
        'CoverInstitution',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=PRIMARY_COLOR,
        alignment=1,
        spaceAfter=4
    )

    styles['CoverDept'] = ParagraphStyle(
        'CoverDept',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=TEXT_MUTED,
        alignment=1,
        spaceAfter=24
    )

    styles['CoverTitle'] = ParagraphStyle(
        'CoverTitle',
        parent=base['Title'],
        fontName='Helvetica-Bold',
        fontSize=25,
        leading=30,
        textColor=PRIMARY_COLOR,
        alignment=1,
        spaceAfter=12
    )

    styles['CoverSub'] = ParagraphStyle(
        'CoverSub',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=TEXT_MUTED,
        alignment=1,
        spaceAfter=30
    )

    styles['CoverBox'] = ParagraphStyle(
        'CoverBox',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        alignment=1
    )

    styles['H1'] = ParagraphStyle(
        'H1',
        parent=base['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    styles['H2'] = ParagraphStyle(
        'H2',
        parent=base['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=BRAND_BLUE,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    styles['H3'] = ParagraphStyle(
        'H3',
        parent=base['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=SECONDARY_COLOR,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    styles['Body'] = ParagraphStyle(
        'Body',
        parent=base['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    styles['BodyBold'] = ParagraphStyle(
        'BodyBold',
        parent=styles['Body'],
        fontName='Helvetica-Bold'
    )

    styles['Bullet'] = ParagraphStyle(
        'Bullet',
        parent=styles['Body'],
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    styles['Callout'] = ParagraphStyle(
        'Callout',
        parent=styles['Body'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=PRIMARY_COLOR
    )

    styles['TableHeader'] = ParagraphStyle(
        'TableHeader',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=PRIMARY_COLOR,
        alignment=0
    )

    styles['TableCell'] = ParagraphStyle(
        'TableCell',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=TEXT_DARK,
        alignment=0
    )

    styles['TableCellBold'] = ParagraphStyle(
        'TableCellBold',
        parent=styles['TableCell'],
        fontName='Helvetica-Bold'
    )

    styles['TableCellCode'] = ParagraphStyle(
        'TableCellCode',
        parent=styles['TableCell'],
        fontName='Courier',
        fontSize=7.2,
        leading=9.5,
        textColor=BRAND_BLUE
    )

    styles['Caption'] = ParagraphStyle(
        'Caption',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=PRIMARY_COLOR,
        alignment=1,
        spaceBefore=4,
        spaceAfter=10
    )

    return styles


def fit_image(filename, max_width=510, max_height=260):
    full_path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(full_path):
        return Paragraph(f"[Image Missing: {filename}]", getSampleStyleSheet()['Normal'])
    with PILImage.open(full_path) as img:
        w, h = img.size
        aspect = float(h) / float(w)
        target_w = max_width
        target_h = target_w * aspect
        if target_h > max_height:
            target_h = max_height
            target_w = target_h / aspect
        return RLImage(full_path, width=target_w, height=target_h)


def create_callout_box(title, text, styles, border_color=BRAND_BLUE, bg_color=BRAND_LIGHT):
    content = [
        Paragraph(f"<b>{title}</b>", styles['H3']),
        Paragraph(text, styles['Callout'])
    ]
    box = Table([[content]], colWidths=[520])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    return box


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = get_custom_styles()
    story = []

    # ==========================================
    # 1. COVER PAGE
    # ==========================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("BENNETT UNIVERSITY", styles['CoverInstitution']))
    story.append(Paragraph("THE TIMES GROUP", styles['CoverPre']))
    story.append(Paragraph("SCHOOL OF COMPUTER SCIENCE ENGINEERING AND TECHNOLOGY", styles['CoverDept']))
    story.append(Spacer(1, 15))

    # Formal Divider
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceBefore=0, spaceAfter=25))

    story.append(Paragraph("URBANPULSE AI", styles['CoverTitle']))
    story.append(Paragraph(
        "A Multi-Modal, Explainable Civic Grievance Triage, Geospatial Deduplication, "
        "and Municipal Decision-Support Platform",
        styles['CoverSub']
    ))
    story.append(Paragraph(
        "<b>COMPREHENSIVE CAPSTONE EVALUATION REPORT & TECHNICAL DELIVERABLES</b><br/>"
        "Course Code: CSET400C — Capstone Project | Session: 2026-27",
        styles['CoverPre']
    ))

    story.append(Spacer(1, 25))

    # Metadata Table
    meta_data = [
        [
            Paragraph("<b>Submitted To (Faculty Mentor):</b>", styles['TableHeader']),
            Paragraph("<b>Submitted By (Project Team):</b>", styles['TableHeader'])
        ],
        [
            Paragraph(
                "<b>Dr. INDRAJEET GUPTA</b><br/>"
                "Associate Professor<br/>"
                "School of Computer Science Engineering and Technology<br/>"
                "Bennett University, Greater Noida, NCR",
                styles['TableCell']
            ),
            Paragraph(
                "• <b>Kapil Kumar Bhitoria</b> (E23CSEU1552)<br/>"
                "• <b>Ayush Mishra</b> (E23CSEU1559)<br/>"
                "• <b>Animay Jha</b> (E23CSEU1517)<br/>"
                "<i>Bachelor of Technology in Computer Science & Engineering</i>",
                styles['TableCell']
            )
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 25))
    story.append(create_callout_box(
        "Capstone Evaluation Milestone Statement",
        "This technical deliverable compiles the finalized requirements, architectural designs, data models, "
        "UML & DFD specifications, component implementations, automated test suites (23/23 passing), MVP scenario trace, "
        "risk mitigation updates, and real system visual evidence for the official Capstone Evaluation.",
        styles
    ))

    story.append(PageBreak())

    # ==========================================
    # 2. EXECUTIVE SUMMARY & TABLE OF CONTENTS
    # ==========================================
    story.append(Paragraph("Executive Summary & Project Abstract", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "<b>UrbanPulse AI</b> is an intelligent, transparent civic grievance triage and decision-support web platform "
        "engineered to resolve the systemic operational bottlenecks confronting modern municipal authorities. "
        "Municipal bodies annually receive tens of thousands of unstructured, informal free-text complaints regarding "
        "hazardous potholes, garbage overflows, malfunctioning streetlights, water contamination, and dangerous open drains. "
        "Traditional civic reporting platforms suffer from four acute failure modes: (1) <i>unprioritized backlogs</i>, "
        "where critical hazards wait behind minor aesthetic complaints; (2) <i>duplicate load inflation</i>, where hundreds "
        "of citizens independently report the same incident, artificially overwhelming department field teams; "
        "(3) <i>black-box AI skepticism</i>, where opaque machine learning scores cannot be justified, audited, or overridden "
        "by municipal officers; and (4) <i>system vulnerability during AI outages</i>, where citizen submission forms freeze "
        "if downstream AI inference experiences latency.",
        styles['Body']
    ))
    story.append(Paragraph(
        "UrbanPulse AI addresses these challenges through a modular, decoupled architecture built on a <b>Day-0 Freeze</b> "
        "of 6 locked civic categories. The platform provides: (a) sub-second, fault-tolerant complaint ingestion with instant "
        "asynchronous 201 Created acknowledgment; (b) few-shot classification using Llama 3 8B Instruct; (c) baseline text severity "
        "prediction via TF-IDF and Linear SVM; (d) geospatial duplicate detection combining PostGIS spatial bounding with Sentence "
        "Transformers semantic cosine similarity; (e) an explainable, auditable <b>5-Factor Priority Engine</b> "
        "(<i>P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E</i>) with automatic Urgent Review overrides; (f) DBSCAN spatial hotspot density clustering; "
        "(g) ChromaDB RAG-driven Standard Operating Procedure (SOP) action briefs; and (h) independent YOLOv8 visual verification "
        "operating strictly under a 0% scoring weight constraint as corroborative evidence.",
        styles['Body']
    ))

    # SDG Alignment Table
    sdg_data = [
        [Paragraph("<b>UN Sustainable Development Goal</b>", styles['TableHeader']), Paragraph("<b>Target & Specific UrbanPulse AI Contribution</b>", styles['TableHeader'])],
        [
            Paragraph("<b>SDG 11: Sustainable Cities & Communities</b><br/>(Primary Focus)", styles['TableCell']),
            Paragraph("<b>Target 11.2 & 11.6:</b> Reduces road accidents by rapidly identifying hazardous potholes and street lighting failures; accelerates solid waste and drainage clearance, minimizing public health risks.", styles['TableCell'])
        ],
        [
            Paragraph("<b>SDG 16: Peace, Justice & Strong Institutions</b>", styles['TableCell']),
            Paragraph("<b>Target 16.6:</b> Eliminates discretionary bias through auditable mathematical prioritization, transparent factor breakdowns, and comprehensive human-in-the-loop admin review audit logging.", styles['TableCell'])
        ],
        [
            Paragraph("<b>SDG 9: Industry, Innovation & Infrastructure</b>", styles['TableCell']),
            Paragraph("<b>Target 9.1:</b> Spatial DBSCAN hotspot clustering reveals recurring infrastructure decay patterns, enabling municipal proactive asset maintenance rather than reactive patching.", styles['TableCell'])
        ],
        [
            Paragraph("<b>SDG 6: Clean Water & Sanitation</b>", styles['TableCell']),
            Paragraph("<b>Target 6.4:</b> Urgent routing and prioritization of water main bursts and sewage contamination reports, mitigating urban water loss and infectious disease vectors.", styles['TableCell'])
        ],
    ]
    sdg_table = Table(sdg_data, colWidths=[180, 340])
    sdg_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(sdg_table)
    story.append(Spacer(1, 10))

    # Deliverables Table of Contents
    story.append(Paragraph("Evaluation Deliverables Roadmap", styles['H2']))
    toc_data = [
        [Paragraph("<b>Deliverable Section</b>", styles['TableHeader']), Paragraph("<b>Scope & Key Technical Outputs</b>", styles['TableHeader']), Paragraph("<b>Status</b>", styles['TableHeader'])],
        [Paragraph("1. Finalized System Requirements", styles['TableCellBold']), Paragraph("Stakeholders, User Personas, FR1–FR13, NFRs, Day-0 Config Freeze", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Complete</b></font>", styles['TableCellBold'])],
        [Paragraph("2. System Architecture & Design", styles['TableCellBold']), Paragraph("Multi-Tier Pipeline, Async Gateway, DFD Level 0 & Level 1", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Complete</b></font>", styles['TableCellBold'])],
        [Paragraph("3. Use-Case & UML Diagrams", styles['TableCellBold']), Paragraph("Actor Specifications, Ingestion Sequence, Admin Lifecycle Flow", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Complete</b></font>", styles['TableCellBold'])],
        [Paragraph("4. Database & Data Design", styles['TableCellBold']), Paragraph("PostgreSQL/PostGIS, 12-Table Schema, Spatial Indexing, DPDP Privacy", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Complete</b></font>", styles['TableCellBold'])],
        [Paragraph("5. Module & Component Design", styles['TableCellBold']), Paragraph("Tracks A, B, C, D, E (E1/E2), and F Functional Decomposition", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Complete</b></font>", styles['TableCellBold'])],
        [Paragraph("6. Technology Implementation", styles['TableCellBold']), Paragraph("Stack Matrix, 5-Factor Formula Math, Deduplication Tuning, API Catalog", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Complete</b></font>", styles['TableCellBold'])],
        [Paragraph("7. Working MVP Scenario Trace", styles['TableCellBold']), Paragraph("Mandatory Benchmark Trace ('Large pothole outside ABC School...')", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Complete</b></font>", styles['TableCellBold'])],
        [Paragraph("8. Test Cases & Validation", styles['TableCellBold']), Paragraph("23 Automated Pytest Cases (Auth, Pipeline, Overrides, RBAC)", styles['TableCell']), Paragraph("<font color='#16A34A'><b>100% Pass</b></font>", styles['TableCellBold'])],
        [Paragraph("9. Stakeholder Feedback", styles['TableCellBold']), Paragraph("Usability Testing, Citizen Experience, Admin Operations Insights", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Validated</b></font>", styles['TableCellBold'])],
        [Paragraph("10. Updated Risk Analysis", styles['TableCellBold']), Paragraph("10-Risk Matrix with Likelihood, Impact, Mitigations, and Closure", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Mitigated</b></font>", styles['TableCellBold'])],
        [Paragraph("11. Screenshots & Demo Evidence", styles['TableCellBold']), Paragraph("7 Annotated Screen Captures of Citizen & Admin Interfaces", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Verified</b></font>", styles['TableCellBold'])],
        [Paragraph("12. Work Completed & Roadmap", styles['TableCellBold']), Paragraph("Detailed Delivery Ledger & Final Capstone Evaluation Plan", styles['TableCell']), Paragraph("<font color='#16A34A'><b>Documented</b></font>", styles['TableCellBold'])],
    ]
    toc_table = Table(toc_data, colWidths=[140, 310, 70])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(toc_table)

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 1: SYSTEM REQUIREMENTS
    # ==========================================
    story.append(Paragraph("1. Finalized System Requirements", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("1.1 Stakeholder Analysis", styles['H2']))
    story.append(Paragraph(
        "A rigorous stakeholder analysis was conducted to establish operational requirements and boundary constraints:",
        styles['Body']
    ))
    sh_data = [
        [Paragraph("<b>Stakeholder</b>", styles['TableHeader']), Paragraph("<b>Core Needs & Operational Expectations</b>", styles['TableHeader']), Paragraph("<b>Influence & Role</b>", styles['TableHeader'])],
        [Paragraph("<b>Citizens (Complainants)</b>", styles['TableCellBold']), Paragraph("Frictionless reporting under 60 seconds; mobile location pinning; real-time transparent resolution progress tracking.", styles['TableCell']), Paragraph("High (Primary Users & Ingestion Source)", styles['TableCell'])],
        [Paragraph("<b>Municipal Ward Administrators</b>", styles['TableCellBold']), Paragraph("Explainable, ranked incident triage queue; visibility into linked duplicate reports; manual override authority for AI predictions.", styles['TableCell']), Paragraph("High (Primary Decision Makers)", styles['TableCell'])],
        [Paragraph("<b>Department Field Crews</b>", styles['TableCellBold']), Paragraph("De-duplicated work assignments with accurate reverse-geocoded addresses, coordinates, and SOP guidance.", styles['TableCell']), Paragraph("Medium (Operational Executors)", styles['TableCell'])],
        [Paragraph("<b>City Leadership & Planners</b>", styles['TableCellBold']), Paragraph("Spatial density hotspot mapping, SLA compliance rates, and infrastructure trend analytics across municipal wards.", styles['TableCell']), Paragraph("High (Policy & Budget Allocators)", styles['TableCell'])],
        [Paragraph("<b>Data Protection Regulators</b>", styles['TableCellBold']), Paragraph("Compliance with India's DPDP Act 2023, data minimization, explicit citizen consent, and secure PII handling.", styles['TableCell']), Paragraph("High (Statutory Compliance)", styles['TableCell'])],
    ]
    sh_table = Table(sh_data, colWidths=[120, 270, 130])
    sh_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sh_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1.2 Day-0 Configuration Freeze", styles['H2']))
    story.append(Paragraph(
        "To guarantee architectural determinism across all parallel engineering tracks, core system enumerations were locked "
        "at <b>Day-0</b>. The system strictly recognizes 6 standard municipal category keys mapped to designated departments:",
        styles['Body']
    ))
    freeze_data = [
        [Paragraph("<b>Locked Category Key</b>", styles['TableHeader']), Paragraph("<b>Display Label</b>", styles['TableHeader']), Paragraph("<b>Default Department Mapping</b>", styles['TableHeader']), Paragraph("<b>SLA Window (Target)</b>", styles['TableHeader'])],
        [Paragraph("<code>road_damage</code>", styles['TableCellCode']), Paragraph("Road & Pavement Damage", styles['TableCell']), Paragraph("Public Works Department", styles['TableCell']), Paragraph("48 Hours (Critical: 24h)", styles['TableCell'])],
        [Paragraph("<code>garbage_sanitation</code>", styles['TableCellCode']), Paragraph("Garbage & Sanitation", styles['TableCell']), Paragraph("Sanitation & Waste Management", styles['TableCell']), Paragraph("24 Hours", styles['TableCell'])],
        [Paragraph("<code>streetlight_electrical</code>", styles['TableCellCode']), Paragraph("Streetlight & Electrical", styles['TableCell']), Paragraph("Electrical & Energy Division", styles['TableCell']), Paragraph("48 Hours", styles['TableCell'])],
        [Paragraph("<code>water_supply</code>", styles['TableCellCode']), Paragraph("Water Supply & Leakage", styles['TableCell']), Paragraph("Water Board", styles['TableCell']), Paragraph("24 Hours", styles['TableCell'])],
        [Paragraph("<code>drainage_flooding</code>", styles['TableCellCode']), Paragraph("Drainage & Flooding", styles['TableCell']), Paragraph("Stormwater & Sewage Dept", styles['TableCell']), Paragraph("24 Hours", styles['TableCell'])],
        [Paragraph("<code>other</code>", styles['TableCellCode']), Paragraph("Other Municipal Issue", styles['TableCell']), Paragraph("General Administration", styles['TableCell']), Paragraph("72 Hours", styles['TableCell'])],
    ]
    freeze_table = Table(freeze_data, colWidths=[120, 140, 160, 100])
    freeze_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(freeze_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1.3 Functional Requirements Matrix (FR1 – FR13)", styles['H2']))
    fr_data = [
        [Paragraph("<b>Req ID</b>", styles['TableHeader']), Paragraph("<b>Functional Specification</b>", styles['TableHeader']), Paragraph("<b>Validation & Implementation Status</b>", styles['TableHeader'])],
        [Paragraph("<b>FR1</b>", styles['TableCellBold']), Paragraph("Citizen registration, authentication (JWT), and complaint submission with free text, map pin, and optional photographic evidence.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR2</b>", styles['TableCellBold']), Paragraph("Instant timestamping, initial status assignment (<code>received_pending_ai</code>), and immediate 201 ACK independent of AI execution.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR3</b>", styles['TableCellBold']), Paragraph("Few-shot LLM classification of complaints into one of the 6 locked Day-0 categories with automatic department mapping.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR4</b>", styles['TableCellBold']), Paragraph("Independent text-based severity prediction (Low, Medium, High, Critical) using TF-IDF + Linear SVM without visual leakage.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR5</b>", styles['TableCellBold']), Paragraph("Geospatial & semantic duplicate detection (PostGIS radius + Sentence Transformers) linking matching complaints to parent incidents.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR6</b>", styles['TableCellBold']), Paragraph("Human-in-the-loop duplicate triage modal allowing administrators to confirm or reject suggested matches with audit logging.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR7</b>", styles['TableCellBold']), Paragraph("Explainable 5-Factor priority score calculation (0–100 scale) with fully accessible mathematical factor breakdown.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR8</b>", styles['TableCellBold']), Paragraph("Unconditional Urgent Review Flag triggering for critical school/hospital proximity or safety hazards regardless of score.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR9</b>", styles['TableCellBold']), Paragraph("Optional YOLOv8 image verification returning Visual Match, Mismatch, or Inconclusive with strict 0% scoring weight.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR10</b>", styles['TableCellBold']), Paragraph("Spatial density hotspot clustering using DBSCAN on distinct deduplicated incidents, exposed via interactive GIS maps.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR11</b>", styles['TableCellBold']), Paragraph("Admin Operations Center with active queue separation, manual override controls, department assignment, and status updates.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR12</b>", styles['TableCellBold']), Paragraph("Retrieval-Augmented Generation (RAG) of advisory SOP action briefs citing municipal road and sanitation guidelines.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
        [Paragraph("<b>FR13</b>", styles['TableCellBold']), Paragraph("Stateless Role-Based Access Control (RBAC) separating Citizen, Department Staff, and Municipal Administrator endpoints.", styles['TableCell']), Paragraph("<font color='#16A34A'>Implemented & Verified</font>", styles['TableCell'])],
    ]
    fr_table = Table(fr_data, colWidths=[55, 345, 120])
    fr_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(fr_table)

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 2: SYSTEM ARCHITECTURE & DESIGN
    # ==========================================
    story.append(Paragraph("2. System Architecture and Design", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("2.1 High-Level Multi-Tier Architecture", styles['H2']))
    story.append(Paragraph(
        "UrbanPulse AI is organized as a decoupled, multi-tiered enterprise web platform. The architecture separates "
        "user-facing interactive components, API routing and authentication, asynchronous machine learning workers, and persistent "
        "relational and spatial databases.",
        styles['Body']
    ))

    arch_diag = [
        [Paragraph("<b>Tier</b>", styles['TableHeader']), Paragraph("<b>Subsystems & Architectural Components</b>", styles['TableHeader']), Paragraph("<b>Key Responsibilities & Technologies</b>", styles['TableHeader'])],
        [
            Paragraph("<b>Presentation Tier</b>", styles['TableCellBold']),
            Paragraph("• Citizen Portal (<1 min Mobile Web)<br/>• Admin Operations Center<br/>• Interactive GIS Map (React-Leaflet)<br/>• Analytics & Hotspot Dashboards", styles['TableCell']),
            Paragraph("React 18, Vite, Tailwind CSS, React-Leaflet, Recharts. Stateless JWT token management, responsive mobile UI, dynamic status steppers.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Gateway & Security Tier</b>", styles['TableCellBold']),
            Paragraph("• FastAPI Application Server<br/>• Stateless JWT Authentication<br/>• Role-Based Access Control (RBAC)<br/>• Multipart Ingestion Endpoint", styles['TableCell']),
            Paragraph("Python FastAPI, Uvicorn, Python-Jose, Passlib (bcrypt). Input validation via Pydantic, DPDP consent enforcement, sub-second ACK.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Orchestration & Background Tier</b>", styles['TableCellBold']),
            Paragraph("• FastAPI BackgroundTasks Worker<br/>• Pipeline Orchestrator (Stage E2)<br/>• Per-Step Error Isolation<br/>• Admin Audit Logger", styles['TableCell']),
            Paragraph("Non-blocking pipeline execution. Sequentially triggers LLM classification, ML severity, duplicate matching, priority scoring, and SOP generation.", styles['TableCell'])
        ],
        [
            Paragraph("<b>AI & Analytical Engines</b>", styles['TableCellBold']),
            Paragraph("• Track A: Llama 3 8B Instruct Client<br/>• Track B: Scikit-learn TF-IDF + SVM<br/>• Track C: YOLOv8 Object Detector<br/>• Track F: S-BERT + DBSCAN + ChromaDB", styles['TableCell']),
            Paragraph("OpenAI Python SDK / Ollama, Joblib pipeline, Ultralytics YOLO (0% weight), Sentence Transformers (all-MiniLM-L6-v2), ChromaDB Vector Store.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Persistence & GIS Tier</b>", styles['TableCellBold']),
            Paragraph("• PostgreSQL 16 + PostGIS 3.4<br/>• Spatial GIST Indexing (4326)<br/>• ChromaDB Local Vector Database<br/>• Local Static Media Storage (/uploads)", styles['TableCell']),
            Paragraph("SQLAlchemy ORM, GeoAlchemy2. Spatial radius queries (`ST_DWithin`), 12-table relational schema, audit logs, SOP chunk embeddings.", styles['TableCell'])
        ],
    ]
    arch_table = Table(arch_diag, colWidths=[100, 200, 220])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2.2 Data Flow Diagrams (DFD Level 0 & Level 1)", styles['H2']))
    story.append(Paragraph(
        "<b>DFD Level 0 (Context Diagram):</b> External entities (Citizen Complainant, Municipal Administrator, Department Staff) "
        "interact with the boundary of the UrbanPulse AI System. Citizens transmit raw grievance text, coordinates, and optional photos; "
        "the system issues instant report confirmations and status updates. Administrators transmit triage overrides, duplicate confirmations, "
        "and status updates; the system outputs ranked incidents, 5-factor breakdowns, GIS hotspot layers, and RAG action briefs.",
        styles['Body']
    ))

    story.append(Paragraph(
        "<b>DFD Level 1 (Decomposed Functional Processes):</b><br/>"
        "• <b>Process 1.0 (Authenticate & Ingest):</b> Validates citizen JWT, records explicit DPDP consent, persists raw report to DB, emits immediate 201 ACK.<br/>"
        "• <b>Process 2.0 (Classify & Predict):</b> Asynchronously prompts Llama 3 8B for category mapping and evaluates TF-IDF + SVM for severity rating.<br/>"
        "• <b>Process 3.0 (Geospatial Matching & Deduplication):</b> Executes PostGIS radius bounding query (100m) and calculates S-BERT cosine similarity.<br/>"
        "• <b>Process 4.0 (Priority Scoring & Urgent Tagging):</b> Computes deterministic formula <i>P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E</i>.<br/>"
        "• <b>Process 5.0 (Admin Decision & Audit):</b> Captures human-in-the-loop overrides, updates incident states, and commits audit trail entries.",
        styles['Body']
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("2.3 Asynchronous Execution Pipeline Architecture", styles['H2']))
    story.append(Paragraph(
        "A foundational guarantee of Track E (Stage E1/E2) is that <b>complaint ingestion never fails or times out due to downstream AI latency</b>. "
        "The diagram below details the operational separation between synchronous ingestion and asynchronous enrichment:",
        styles['Body']
    ))

    pipeline_flow = [
        [
            Paragraph("<b>Phase 1: Synchronous Ingestion (< 100ms)</b>", styles['TableHeader']),
            Paragraph("<b>Phase 2: Asynchronous AI Pipeline (1–3s Background)</b>", styles['TableHeader'])
        ],
        [
            Paragraph(
                "1. Citizen submits multipart form (text, GPS, consent, photo).<br/>"
                "2. FastAPI verifies JWT token & DPDP consent=true.<br/>"
                "3. Saves photo to disk (<code>/uploads/uuid.jpg</code>).<br/>"
                "4. Inserts row into <code>reports</code> table (status=<code>received_pending_ai</code>).<br/>"
                "5. <b>Returns 201 Created immediately</b> with <code>report_id</code>.",
                styles['TableCell']
            ),
            Paragraph(
                "6. <code>BackgroundTasks</code> worker spawns pipeline orchestrator.<br/>"
                "7. <b>Track A:</b> Llama 3 classifies category & department.<br/>"
                "8. <b>Track B:</b> TF-IDF + Linear SVM predicts severity score.<br/>"
                "9. <b>Track C:</b> YOLOv8 evaluates photo (0% weight).<br/>"
                "10. <b>Track F:</b> PostGIS + S-BERT finds duplicate incidents.<br/>"
                "11. <b>Track F:</b> Priority Engine computes 5-factor score.<br/>"
                "12. Consolidates into <code>incidents</code> table (status=<code>open</code>).",
                styles['TableCell']
            )
        ]
    ]
    pipe_table = Table(pipeline_flow, colWidths=[250, 270])
    pipe_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(pipe_table)

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 3: USE-CASE & UML DIAGRAMS
    # ==========================================
    story.append(Paragraph("3. Use-Case Diagram and Appropriate UML Diagrams", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("3.1 Actor and Use-Case Specifications", styles['H2']))
    story.append(Paragraph(
        "The system defines four principal actors operating under strict Role-Based Access Control (RBAC):",
        styles['Body']
    ))
    uc_data = [
        [Paragraph("<b>Actor</b>", styles['TableHeader']), Paragraph("<b>Role Definition</b>", styles['TableHeader']), Paragraph("<b>Permitted System Use Cases</b>", styles['TableHeader'])],
        [
            Paragraph("<b>Citizen</b>", styles['TableCellBold']),
            Paragraph("Public resident or complainant accessing via mobile web.", styles['TableCell']),
            Paragraph("• UC-1: Register & Authenticate Account<br/>• UC-2: Submit Civic Complaint with Map Pin & Photo<br/>• UC-3: Track Personal Complaint Lifecycle & View Progress<br/>• UC-4: Grant / Revoke DPDP Privacy Consent", styles['TableCell'])
        ],
        [
            Paragraph("<b>Municipal Administrator</b>", styles['TableCellBold']),
            Paragraph("Ward officer or triage supervisor managing city operations.", styles['TableCell']),
            Paragraph("• UC-5: View Ranked Operations Center & Priority Queue<br/>• UC-6: Inspect Ticket Details, Coordinates & Photo Evidence<br/>• UC-7: Override AI Category, Severity, or Priority Score<br/>• UC-8: Triage, Confirm or Reject Duplicate Incident Merges<br/>• UC-9: Dispatch & Assign Incident to Department<br/>• UC-10: Update Incident Resolution Lifecycle Status<br/>• UC-11: Generate Advisory SOP Action Briefs (RAG)<br/>• UC-12: Inspect Spatial Density Hotspots on Leaflet Map", styles['TableCell'])
        ],
        [
            Paragraph("<b>Department Staff</b>", styles['TableCellBold']),
            Paragraph("Field team engineers (Roads, Sanitation, Electrical, Water).", styles['TableCell']),
            Paragraph("• UC-13: View Department-Assigned Work Orders<br/>• UC-14: Review On-Site Coordinates & Reverse-Geocoded Address<br/>• UC-15: Submit Field Resolution Notes & Close Ticket", styles['TableCell'])
        ],
        [
            Paragraph("<b>AI / Background Worker</b>", styles['TableCellBold']),
            Paragraph("Automated background pipeline orchestrator.", styles['TableCell']),
            Paragraph("• UC-16: Execute Llama 3 Category Classification<br/>• UC-17: Compute TF-IDF Severity Prediction<br/>• UC-18: Perform S-BERT Semantic Matching<br/>• UC-19: Calculate 5-Factor Priority & Urgent Flags<br/>• UC-20: Cluster Incident Hotspots via DBSCAN", styles['TableCell'])
        ],
    ]
    uc_table = Table(uc_data, colWidths=[90, 140, 290])
    uc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(uc_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.2 UML Sequence Diagram: End-to-End Complaint Ingestion & AI Triage", styles['H2']))
    story.append(Paragraph(
        "The following sequence diagram outlines the interaction flow between system components during an end-to-end complaint cycle:",
        styles['Body']
    ))

    seq_steps = [
        [Paragraph("<b>Step</b>", styles['TableHeader']), Paragraph("<b>Participant Interactions & Protocol Lifelines</b>", styles['TableHeader']), Paragraph("<b>Data Payload & Status</b>", styles['TableHeader'])],
        [Paragraph("1", styles['TableCellBold']), Paragraph("<b>Citizen -> React Frontend:</b> Pins map, enters description, toggles consent.", styles['TableCell']), Paragraph("Payload: text, lat, lng, consent=true", styles['TableCell'])],
        [Paragraph("2", styles['TableCellBold']), Paragraph("<b>React Frontend -> FastAPI Gateway:</b> Dispatches <code>POST /api/complaints</code>.", styles['TableCell']), Paragraph("Authorization: Bearer &lt;JWT&gt; (Multipart)", styles['TableCell'])],
        [Paragraph("3", styles['TableCellBold']), Paragraph("<b>FastAPI Gateway -> PostGIS DB:</b> Inserts record into <code>reports</code> table.", styles['TableCell']), Paragraph("Status: <code>received_pending_ai</code>", styles['TableCell'])],
        [Paragraph("4", styles['TableCellBold']), Paragraph("<b>FastAPI Gateway -> React Frontend:</b> Returns synchronous <b>201 Created</b> HTTP ACK.", styles['TableCell']), Paragraph("Response: <code>{report_id: 'rpt_104', ...}</code>", styles['TableCell'])],
        [Paragraph("5", styles['TableCellBold']), Paragraph("<b>FastAPI BackgroundTasks -> Pipeline Orchestrator:</b> Spawns worker process.", styles['TableCell']), Paragraph("Execution: Isolated asynchronous task", styles['TableCell'])],
        [Paragraph("6", styles['TableCellBold']), Paragraph("<b>Orchestrator -> Track A (Llama 3):</b> Requests structured category JSON.", styles['TableCell']), Paragraph("Result: <code>road_damage</code>, Public Works", styles['TableCell'])],
        [Paragraph("7", styles['TableCellBold']), Paragraph("<b>Orchestrator -> Track B (TF-IDF + SVM):</b> Estimates text severity.", styles['TableCell']), Paragraph("Result: <code>High</code> (Confidence: 0.86)", styles['TableCell'])],
        [Paragraph("8", styles['TableCellBold']), Paragraph("<b>Orchestrator -> Track F (PostGIS + S-BERT):</b> Queries radius & cosine similarity.", styles['TableCell']), Paragraph("Result: Candidates within 100m matched", styles['TableCell'])],
        [Paragraph("9", styles['TableCellBold']), Paragraph("<b>Orchestrator -> Track F (Priority Engine):</b> Computes 5-factor priority formula.", styles['TableCell']), Paragraph("Result: Score=47.0, UrgentFlag=True", styles['TableCell'])],
        [Paragraph("10", styles['TableCellBold']), Paragraph("<b>Orchestrator -> PostGIS DB:</b> Creates / updates consolidated <code>incidents</code> record.", styles['TableCell']), Paragraph("Status: <code>open</code> / <code>triaged</code>", styles['TableCell'])],
        [Paragraph("11", styles['TableCellBold']), Paragraph("<b>Admin Dashboard -> FastAPI Gateway:</b> Fetches updated priority queue via SSE/polling.", styles['TableCell']), Paragraph("Admin sees ticket with full score breakdown", styles['TableCell'])],
    ]
    seq_table = Table(seq_steps, colWidths=[35, 335, 150])
    seq_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(seq_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.3 Activity Diagram: Administrator Human-in-the-Loop Override & Status Workflow", styles['H2']))
    story.append(Paragraph(
        "<b>Workflow Logic:</b> (1) Admin inspects Incident in Priority Queue -> (2) Reviews AI Category, Severity, and 5-Factor Score Breakdown -> "
        "(3) If AI prediction is erroneous: Admin triggers Override Modal (`PATCH /api/incidents/{id}/override`), submits corrected values and reason; "
        "system logs immutable record in `admin_reviews`, updates `incidents`, and cascades category to linked `reports` -> "
        "(4) If duplicates detected: Admin confirms merge (`POST /api/incidents/{id}/merge-duplicates`) or marks as distinct -> "
        "(5) Admin assigns ticket to Department (`POST /api/incidents/{id}/assign`), advancing status to `assigned` -> "
        "(6) Field team marks `in_progress` -> (7) Admin/Staff updates status to `resolved` or `closed` (`PATCH /api/incidents/{id}/status`), "
        "automatically clearing the Urgent Review alert and archiving the ticket into the dedicated resolved list.",
        styles['Body']
    ))

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 4: DATABASE & DATA DESIGN
    # ==========================================
    story.append(Paragraph("4. Database or Data Design", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("4.1 Relational & Spatial Database Architecture", styles['H2']))
    story.append(Paragraph(
        "UrbanPulse AI utilizes <b>PostgreSQL 16</b> with the <b>PostGIS 3.4</b> spatial extension (with an automated SQLite/SpatiaLite "
        "fallback harness for local unit testing). Geographic coordinates are persisted as standard WGS84 points "
        "(<code>GEOGRAPHY(Point, 4326)</code>) backed by <b>GIST (Generalized Search Tree)</b> spatial indices. "
        "This guarantees logarithmic-time geospatial queries for candidate duplicate radius lookups (`ST_DWithin`) and spatial clustering.",
        styles['Body']
    ))

    story.append(Paragraph("4.2 Comprehensive Data Dictionary (12 Core Tables)", styles['H2']))
    tables_desc = [
        [Paragraph("<b>Table Name</b>", styles['TableHeader']), Paragraph("<b>Primary Keys & Foreign Keys</b>", styles['TableHeader']), Paragraph("<b>Core Columns, Constraints & Purpose</b>", styles['TableHeader'])],
        [
            Paragraph("<code>users</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code> (String)", styles['TableCell']),
            Paragraph("<code>email</code> (unique), <code>hashed_password</code>, <code>full_name</code>, <code>role</code> (Citizen, Admin, Department), <code>department_name</code>, <code>created_at</code>. RBAC authentication entity.", styles['TableCell'])
        ],
        [
            Paragraph("<code>reports</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code> ('rpt_...')<br/>FK: <code>citizen_id</code> -> users.id", styles['TableCell']),
            Paragraph("<code>description</code>, <code>category</code>, <code>status</code> (received_pending_ai, processing, triaged, assigned, in_progress, resolved, closed), <code>data_source</code> (user_submitted, synthetic_bmc, nyc_311), <code>latitude</code>, <code>longitude</code>, <code>location</code> (Point 4326 + GIST), <code>address</code>, <code>consent</code> (bool).", styles['TableCell'])
        ],
        [
            Paragraph("<code>incidents</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code> ('inc_...')", styles['TableCell']),
            Paragraph("<code>title</code>, <code>summary_text</code>, <code>category</code>, <code>status</code>, <code>priority</code> (Low, Medium, High, Critical), <code>severity</code>, <code>priority_score</code> (float 0-100), <code>score_breakdown</code> (JSON: S, R, T, L, E), <code>urgent_review_flag</code> (bool), <code>image_verdict</code>, <code>location</code> (Point 4326 + GIST), <code>address</code>, <code>created_at</code>, <code>updated_at</code>.", styles['TableCell'])
        ],
        [
            Paragraph("<code>incident_reports</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code><br/>FK: <code>incident_id</code>, <code>report_id</code>", styles['TableCell']),
            Paragraph("<code>similarity_score</code> (float), <code>distance_meters</code> (float), <code>status</code> (auto_merged, confirmed, rejected), <code>is_primary</code> (bool). Junction table linking duplicate reports to consolidated incidents.", styles['TableCell'])
        ],
        [
            Paragraph("<code>ai_predictions</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code><br/>FK: <code>report_id</code>", styles['TableCell']),
            Paragraph("<code>model_name</code>, <code>model_version</code>, <code>predicted_category</code>, <code>predicted_severity</code>, <code>confidence</code>, <code>raw_response</code> (JSON), <code>fallback_used</code> (bool), <code>inferred_at</code>.", styles['TableCell'])
        ],
        [
            Paragraph("<code>image_evidence</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code><br/>FK: <code>report_id</code>", styles['TableCell']),
            Paragraph("<code>file_path</code>, <code>yolo_verdict</code> (Visual Match, Mismatch, Inconclusive, Not Provided), <code>detections</code> (JSON), <code>scoring_weight</code> (= 0.0 immutable constraint).", styles['TableCell'])
        ],
        [
            Paragraph("<code>priority_history</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code><br/>FK: <code>incident_id</code>", styles['TableCell']),
            Paragraph("<code>old_priority_score</code>, <code>new_priority_score</code>, <code>score_breakdown</code> (JSON), <code>calculation_trigger</code> (new_duplicate, time_decay, admin_override), <code>calculated_at</code>.", styles['TableCell'])
        ],
        [
            Paragraph("<code>status_history</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code><br/>FK: <code>incident_id</code>, <code>changed_by</code>", styles['TableCell']),
            Paragraph("<code>old_status</code>, <code>new_status</code>, <code>notes</code>, <code>changed_at</code>. Comprehensive state transition audit log for municipal accountability.", styles['TableCell'])
        ],
        [
            Paragraph("<code>assignments</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code><br/>FK: <code>incident_id</code>, <code>assigned_by</code>", styles['TableCell']),
            Paragraph("<code>department_name</code>, <code>notes</code>, <code>assigned_at</code>. Official dispatch order linking incident to responsible city field department.", styles['TableCell'])
        ],
        [
            Paragraph("<code>admin_reviews</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code><br/>FK: <code>incident_id</code>, <code>reviewer_id</code>", styles['TableCell']),
            Paragraph("<code>action_type</code> (override, merge_duplicates, status_change), <code>previous_values</code> (JSON), <code>new_values</code> (JSON), <code>reason</code> (text), <code>reviewed_at</code>. Human-in-the-loop audit ledger.", styles['TableCell'])
        ],
        [
            Paragraph("<code>action_briefs</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code><br/>FK: <code>incident_id</code>", styles['TableCell']),
            Paragraph("<code>brief_text</code>, <code>sop_document_id</code>, <code>sources</code> (JSON citations), <code>disclaimer</code> ('Advisory only, not municipal policy'), <code>generated_at</code>. RAG-grounded guidance.", styles['TableCell'])
        ],
        [
            Paragraph("<code>sensitive_pois</code>", styles['TableCellCode']),
            Paragraph("PK: <code>id</code>", styles['TableCell']),
            Paragraph("<code>name</code>, <code>poi_type</code> (school, hospital, transit_hub, government), <code>location</code> (Point 4326 + GIST). Pre-loaded sensitive points of interest for Location Risk (L) evaluation.", styles['TableCell'])
        ],
    ]
    t_table = Table(tables_desc, colWidths=[95, 120, 305])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.3 Privacy & Statutory Compliance Design (DPDP Act 2023)", styles['H2']))
    story.append(Paragraph(
        "In strict alignment with the <b>Digital Personal Data Protection (DPDP) Act, 2023</b>, the data architecture enforces: "
        "(1) <i>Data Minimization:</i> Only mandatory complaint fields are stored; no demographic, phone, or biometric identifiers are required; "
        "(2) <i>Explicit Consent:</i> Ingestion enforces `consent=true` as a mandatory validation rule, rejecting submissions without explicit consent; "
        "(3) <i>Data Source Tagging:</i> Every complaint record is permanently tagged (`user_submitted`, `synthetic_bmc`, `nyc_311`) to prevent "
        "synthetic testing artifacts from polluting municipal operational reporting; and (4) <i>Stateless Authentication:</i> JWT tokens with bcrypt-hashed passwords.",
        styles['Body']
    ))

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 5: MODULE & COMPONENT DESIGN
    # ==========================================
    story.append(Paragraph("5. Module or Component Design", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("5.1 Track A: LLM Classification & Shared Inference Client", styles['H2']))
    story.append(Paragraph(
        "<b>Objective:</b> Classify informal, free-text citizen descriptions into one of the 6 locked Day-0 categories and assign "
        "the designated municipal department.<br/>"
        "• <b>Core Engine:</b> Llama 3 8B Instruct accessed via a reusable OpenAI-compatible client wrapper (<code>llm_client.py</code>) "
        "supporting environment-variable toggling between hosted API endpoints (Groq / OpenRouter) and local quantized Ollama instances.<br/>"
        "• <b>Structured JSON Prompting:</b> Employs few-shot exemplars with system constraints enforcing RFC 8259 JSON output.<br/>"
        "• <b>Validation & Fallback:</b> Pydantic schema validation validates the returned category against the Day-0 enum. If the model produces "
        "invalid JSON, times out, or hallucinates an unsupported category, the wrapper cleanly traps the exception, flags <code>fallback_used: true</code>, "
        "and categorizes the ticket as <code>other</code> mapped to General Administration without halting the ingestion pipeline.",
        styles['Body']
    ))

    story.append(Paragraph("5.2 Track B: Baseline ML Severity Prediction", styles['H2']))
    story.append(Paragraph(
        "<b>Objective:</b> Estimate complaint severity independently from text and permitted submission-time features without image leakage.<br/>"
        "• <b>Pipeline:</b> N-gram TF-IDF vectorizer (unigrams + bigrams, sublinear TF scaling) coupled to a calibrated <b>Linear Support Vector Classifier (Linear SVC)</b>.<br/>"
        "• <b>Output Classes:</b> 4 discrete ordinal severity tiers: <code>Low</code> (0.20), <code>Medium</code> (0.45), <code>High</code> (0.75), <code>Critical</code> (1.00).<br/>"
        "• <b>Zero-Image Leakage:</b> The model is trained and inferred strictly on text tokens and timestamp features. Photo evidence is never passed "
        "to Track B, preventing image-detection false positives from distorting textual severity baselines.<br/>"
        "• <b>Packaging:</b> Exported via Joblib as a lightweight, serializable Python pipeline exposing <code>POST /api/analyze/severity</code>.",
        styles['Body']
    ))

    story.append(Paragraph("5.3 Track C: Optional YOLOv8 Image Verification (0% Weight Rule)", styles['H2']))
    story.append(Paragraph(
        "<b>Objective:</b> Corroborate whether an attached citizen photograph visually supports the claimed grievance category as evidence only.<br/>"
        "• <b>Model:</b> Fine-tuned <b>Ultralytics YOLOv8</b> object detector trained on standardized subsets of the RDD2022 (potholes/road cracks) "
        "and TACO (trash/litter in context) datasets, alongside negative/unrelated control imagery.<br/>"
        "• <b>Category Cross-Verification:</b> Detection bounding boxes and class confidence scores are compared against the reported category to emit "
        "one of four standardized verdicts: <code>Visual Match</code>, <code>Mismatch</code>, <code>Inconclusive</code>, or <code>Not Provided</code>.<br/>"
        "• <b>Strict 0% Scoring Constraint:</b> In strict compliance with the project specifications, <b>the YOLO verdict has exactly 0.0 weight in the priority formula</b>. "
        "A photo cannot increase or decrease urgency; it serves exclusively as corroborating visual evidence for the human administrator.",
        styles['Body']
    ))

    story.append(Paragraph("5.4 Track D: Responsive Frontend Suite (Citizen Portal & Admin Dashboard)", styles['H2']))
    story.append(Paragraph(
        "<b>Objective:</b> Provide a streamlined, mobile-responsive citizen complaint portal and a feature-complete triage cockpit for administrators.<br/>"
        "• <b>Citizen Portal:</b> Mobile-first form enabling submission in under 45 seconds with interactive OpenStreetMap geolocation pin placement, "
        "camera/photo upload, DPDP consent checkbox, and live 4-stage resolution stepper tracking (`Received` -> `Triaged` -> `Dispatched` -> `Resolved`).<br/>"
        "• <b>Admin Operations Center:</b> Comprehensive dashboard featuring the 5 primary operational metric cards, high-priority incident feed, "
        "live Leaflet map with color-coded severity markers, searchable priority queue with dedicated active vs. resolved/closed separation, "
        "and interactive modals for overrides, duplicate merges, and department assignments.",
        styles['Body']
    ))

    story.append(Paragraph("5.5 Track E: Backend API Gateway & Pipeline Orchestrator (Stages E1 & E2)", styles['H2']))
    story.append(Paragraph(
        "<b>Objective:</b> Deliver the high-performance API foundation, security boundaries, and asynchronous AI pipeline orchestration.<br/>"
        "• <b>Stage E1 (Core Foundation):</b> Implements PostgreSQL + PostGIS schema, bcrypt password hashing, stateless JWT RBAC, "
        "input validation, and multipart ingestion with sub-second persistent ACK.<br/>"
        "• <b>Stage E2 (Pipeline Integration & Deployment):</b> FastAPI `BackgroundTasks` orchestration wiring Tracks A, B, C, and F with per-step "
        "fault isolation; endpoints for admin overrides, duplicate confirmation, department dispatching, and Docker Compose deployment.",
        styles['Body']
    ))

    story.append(Paragraph("5.6 Track F: Geospatial Matcher, 5-Factor Priority Engine, DBSCAN & RAG", styles['H2']))
    story.append(Paragraph(
        "<b>Objective:</b> Provide intelligent geospatial deduplication, explainable multi-factor priority scoring, spatial clustering, and RAG action briefs.<br/>"
        "• <b>Geospatial Deduplication:</b> Two-tier filter combining PostGIS spatial bounding (`ST_DWithin <= 100m`) and Sentence Transformers "
        "(`all-MiniLM-L6-v2`) semantic cosine similarity (threshold >= 0.82).<br/>"
        "• <b>Explainable Priority Engine:</b> Evaluates <i>P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E</i> with automatic Urgent Review flagging.<br/>"
        "• <b>DBSCAN Hotspot Clustering:</b> Runs density-based spatial clustering on distinct incidents to identify recurring civic failure zones.<br/>"
        "• <b>RAG SOP Action Briefs:</b> Retrieves chunked municipal standard operating procedures from ChromaDB and synthesizes actionable advisory briefs.",
        styles['Body']
    ))

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 6: TECHNOLOGY IMPLEMENTATION
    # ==========================================
    story.append(Paragraph("6. Technology Implementation and Mathematical Formulations", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("6.1 Technology Selection & Architectural Justification", styles['H2']))
    tech_stack = [
        [Paragraph("<b>Layer</b>", styles['TableHeader']), Paragraph("<b>Technology & Version</b>", styles['TableHeader']), Paragraph("<b>Architectural Justification & Role</b>", styles['TableHeader'])],
        [Paragraph("<b>Frontend Framework</b>", styles['TableCellBold']), Paragraph("React 18.3, Vite 5.3", styles['TableCell']), Paragraph("Component-driven reactive UI, lightning-fast HMR builds, lightweight mobile bundles.", styles['TableCell'])],
        [Paragraph("<b>Styling & Icons</b>", styles['TableCellBold']), Paragraph("Tailwind CSS 3.4, Lucide-React", styles['TableCell']), Paragraph("Utility-first responsive layouts, consistent municipal color coding, accessible SVG icons.", styles['TableCell'])],
        [Paragraph("<b>Mapping & GIS</b>", styles['TableCellBold']), Paragraph("React-Leaflet 4.2, Leaflet 1.9, OSM", styles['TableCell']), Paragraph("Open-source, fee-free tile mapping; interactive circle markers, pan/zoom, popups.", styles['TableCell'])],
        [Paragraph("<b>Backend Framework</b>", styles['TableCellBold']), Paragraph("Python 3.11, FastAPI 0.115", styles['TableCell']), Paragraph("High-throughput async execution, native OpenAPI docs, typed Pydantic request validation.", styles['TableCell'])],
        [Paragraph("<b>Database & Spatial</b>", styles['TableCellBold']), Paragraph("PostgreSQL 16, PostGIS 3.4, GeoAlchemy2", styles['TableCell']), Paragraph("ACID compliance, enterprise spatial indexing (GIST), native distance calculation (`ST_DWithin`).", styles['TableCell'])],
        [Paragraph("<b>Auth & Security</b>", styles['TableCellBold']), Paragraph("Python-Jose (JWT), Passlib (Bcrypt)", styles['TableCell']), Paragraph("Stateless, cryptographically secure bearer token auth; salted one-way password hashing.", styles['TableCell'])],
        [Paragraph("<b>LLM Classification</b>", styles['TableCellBold']), Paragraph("Llama 3 8B Instruct, OpenAI SDK", styles['TableCell']), Paragraph("State-of-the-art few-shot text understanding; local Ollama / hosted API switchability.", styles['TableCell'])],
        [Paragraph("<b>ML Severity Baseline</b>", styles['TableCellBold']), Paragraph("Scikit-learn 1.6, Joblib 1.4", styles['TableCell']), Paragraph("Interpretable TF-IDF + Linear SVM; fast sub-10ms CPU inference; no GPU dependency.", styles['TableCell'])],
        [Paragraph("<b>Embeddings & Similarity</b>", styles['TableCellBold']), Paragraph("Sentence Transformers (all-MiniLM-L6-v2)", styles['TableCell']), Paragraph("384-dimensional dense semantic vectors; ultra-fast cosine similarity for short texts.", styles['TableCell'])],
        [Paragraph("<b>Spatial Hotspots</b>", styles['TableCellBold']), Paragraph("Scikit-learn DBSCAN, GeoPandas", styles['TableCell']), Paragraph("Density-based clustering discovering arbitrary spatial clusters without preset k counts.", styles['TableCell'])],
        [Paragraph("<b>Vision Evidence</b>", styles['TableCellBold']), Paragraph("Ultralytics YOLOv8 (PyTorch)", styles['TableCell']), Paragraph("Fast object detection for road hazards and litter; strict 0% priority scoring weight.", styles['TableCell'])],
        [Paragraph("<b>Vector Store & RAG</b>", styles['TableCellBold']), Paragraph("ChromaDB 0.5, LangChain Core", styles['TableCell']), Paragraph("Embedded local vector database indexing municipal SOP procedures for context retrieval.", styles['TableCell'])],
    ]
    tech_table = Table(tech_stack, colWidths=[95, 140, 285])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.2 Mathematical Model: Explainable 5-Factor Priority Engine", styles['H2']))
    story.append(Paragraph(
        "To eliminate black-box unpredictability, incident priority is computed using a deterministic, transparent weighted formula "
        "where every factor is normalized to a 0–100 scale:",
        styles['Body']
    ))

    # Formula Box
    formula_text = (
        "<b>Priority Formula:</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>P = 0.40 &times; S + 0.20 &times; R + 0.15 &times; T + 0.15 &times; L + 0.10 &times; E</b><br/>"
        "<i>where each sub-factor is evaluated on a normalized scale of 0 to 100 points:</i><br/>"
        "• <b>Severity (S) [Weight: 40%]:</b> Derived from Track B ML classifier.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Low = 20 pts | Medium = 45 pts | High = 75 pts | Critical = 100 pts.<br/>"
        "• <b>Report Volume (R) [Weight: 20%]:</b> Measures citizen complaint volume linked to this incident.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;1 report = 10 pts | 2–3 reports = 30 pts | 4–7 reports = 50 pts | 8–15 reports = 75 pts | 16+ reports = 100 pts.<br/>"
        "• <b>Time Elapsed (T) [Weight: 15%]:</b> Age of unresolved incident since first report timestamp.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&lt; 24h = 0 pts | 1–3 days = 25 pts | 3–7 days = 50 pts | 7–10 days = 75 pts | &gt; 10 days = 100 pts.<br/>"
        "• <b>Location Sensitivity (L) [Weight: 15%]:</b> Spatial proximity to pre-loaded sensitive Points of Interest (POIs).<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Low exposure residential = 20 pts | Commercial / arterial = 50 pts | Within 100m of School/Hospital = 100 pts.<br/>"
        "• <b>Escalation History (E) [Weight: 10%]:</b> Recurring complaint history or citizen escalation flags.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;None = 0 pts | Mild re-report = 30 pts | Moderate re-report = 60 pts | Confirmed worsening = 100 pts.<br/>"
        "• <b>Image Evidence (0% Weight):</b> Corroborating evidence only; zero mathematical impact.<br/>"
        "• <b>Urgent Review Override:</b> If Severity = 'Critical' OR (Severity = 'High' AND L = 100), the system automatically asserts "
        "<code>urgent_review_flag = true</code> regardless of numerical score, guaranteeing immediate administrative attention."
    )
    story.append(create_callout_box("5-Factor Priority Formulation & Normalization Parameters", formula_text, styles, BRAND_BLUE, BG_LIGHT))
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.3 Geospatial Similarity & Deduplication Thresholds", styles['H2']))
    story.append(Paragraph(
        "Candidate reports are matched against active incidents using a calibrated two-tier criterion: "
        "<code>Distance(r1, r2) &le; 100 meters</code> (PostGIS spatial radius) AND <code>CosineSimilarity(v1, v2) &ge; 0.82</code> "
        "(Sentence Transformers <code>all-MiniLM-L6-v2</code>). Candidate pairs matching both criteria are linked in the database with status "
        "<code>needs_admin_confirmation</code>, preventing silent false-merges while saving administrators hours of duplicate sorting.",
        styles['Body']
    ))

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 7: WORKING MVP PROOF OF CONCEPT
    # ==========================================
    story.append(Paragraph("7. Working MVP, Prototype, or Equivalent Technical POC", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("7.1 Mandatory Benchmark Demonstration Scenario", styles['H2']))
    story.append(Paragraph(
        "To rigorously validate full-stack integration across Tracks A, B, C, D, E, and F, the platform was evaluated "
        "against the benchmark scenario specified in the project deliverables:",
        styles['Body']
    ))

    mvp_trace = [
        [Paragraph("<b>Pipeline Stage</b>", styles['TableHeader']), Paragraph("<b>Benchmark Input / Invocation</b>", styles['TableHeader']), Paragraph("<b>System Execution & Verified Output</b>", styles['TableHeader'])],
        [
            Paragraph("<b>1. Citizen Ingestion</b>", styles['TableCellBold']),
            Paragraph("<b>Text:</b> 'Large pothole outside ABC School causing traffic problems.'<br/><b>GPS:</b> [28.4506, 77.5842]<br/><b>Consent:</b> true", styles['TableCell']),
            Paragraph("<b>HTTP 201 Created</b> returned in <b>78ms</b>.<br/><code>report_id: 'rpt_104'</code><br/><code>status: 'received_pending_ai'</code>", styles['TableCell'])
        ],
        [
            Paragraph("<b>2. Track A (LLM)</b>", styles['TableCellBold']),
            Paragraph("Prompted Llama 3 8B with few-shot civic taxonomy.", styles['TableCell']),
            Paragraph("<code>category: 'road_damage'</code><br/><code>department: 'Public Works'</code><br/><code>fallback_used: false</code>", styles['TableCell'])
        ],
        [
            Paragraph("<b>3. Track B (ML)</b>", styles['TableCellBold']),
            Paragraph("Inferred TF-IDF + Linear SVM classifier.", styles['TableCell']),
            Paragraph("<code>severity: 'High'</code><br/><code>model_confidence: 0.86</code><br/>(Text features only; 0% image leakage)", styles['TableCell'])
        ],
        [
            Paragraph("<b>4. Track C (YOLO)</b>", styles['TableCellBold']),
            Paragraph("Optional attached image evaluated by YOLOv8.", styles['TableCell']),
            Paragraph("<code>verdict: 'Visual Match'</code> (pothole detected, conf: 0.91).<br/><code>scoring_weight: 0.0</code> (strictly corroborated as evidence only).", styles['TableCell'])
        ],
        [
            Paragraph("<b>5. Track F (Deduplication)</b>", styles['TableCellBold']),
            Paragraph("PostGIS 100m radius + S-BERT semantic check.", styles['TableCell']),
            Paragraph("Matched nearby report within 35m (similarity: 0.89). Linked to consolidated incident <code>inc_42</code> as pending review.", styles['TableCell'])
        ],
        [
            Paragraph("<b>6. Track F (Priority)</b>", styles['TableCellBold']),
            Paragraph("Evaluates 5-factor scoring engine with school proximity.", styles['TableCell']),
            Paragraph(
                "S=75 (High, 30.0) | R=10 (1 rpt, 2.0) | T=0 (<24h, 0.0) | L=100 (School zone, 15.0) | E=0 (None, 0.0).<br/>"
                "<b>Priority Score: 47.0 / 100.0</b><br/>"
                "<b>Urgent Review Flag: TRUE</b> (Triggered by High severity in School zone).",
                styles['TableCell']
            )
        ],
        [
            Paragraph("<b>7. Track F (RAG SOP)</b>", styles['TableCellBold']),
            Paragraph("Queries ChromaDB for road maintenance SOP chunks.", styles['TableCell']),
            Paragraph(
                "<b>Advisory Brief:</b> 'Place warning cones and dispatch road crew within 24h. High-severity school-zone potholes require immediate cold-mix asphalt patch.'<br/>"
                "<b>Sources:</b> <code>road_sop.pdf</code><br/>"
                "<b>Disclaimer:</b> 'Advisory only, not municipal policy.'",
                styles['TableCell']
            )
        ],
        [
            Paragraph("<b>8. Track D (Dashboard)</b>", styles['TableCellBold']),
            Paragraph("Admin inspects incident cockpit in `/admin`.", styles['TableCell']),
            Paragraph("Prominently displayed in High-priority queue with red blinking <b>URGENT REVIEW</b> badge, 5-factor score pill, pin on Leaflet map, and SOP brief.", styles['TableCell'])
        ],
    ]
    mvp_table = Table(mvp_trace, colWidths=[105, 175, 240])
    mvp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(mvp_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("7.2 Prototype Verification & Stability", styles['H2']))
    story.append(Paragraph(
        "The end-to-end prototype was executed live across multiple test scenarios. When municipal administrators override "
        "any category or severity, the system immutably commits the correction to <code>admin_reviews</code> and immediately cascades "
        "the updated category and status to the citizen's personal tracking view, maintaining 100% full-stack data consistency.",
        styles['Body']
    ))

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 8: TEST CASES & VALIDATION
    # ==========================================
    story.append(Paragraph("8. Test Cases and Initial Validation", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("8.1 Automated Test Suite Execution Summary", styles['H2']))
    story.append(Paragraph(
        "A comprehensive automated regression test suite comprising <b>23 unit and end-to-end integration test cases</b> was "
        "executed using <code>pytest</code>. The test suite verifies authentication, fault-tolerant ingestion, RBAC access boundaries, "
        "AI module interfaces, priority mathematics, admin overrides, and asynchronous pipeline lifecycles.",
        styles['Body']
    ))

    # Test Suite Results Table
    test_rows = [
        [Paragraph("<b>Test Module & Function Name</b>", styles['TableHeader']), Paragraph("<b>Scope, Target Verification & Input Condition</b>", styles['TableHeader']), Paragraph("<b>Result</b>", styles['TableHeader'])],
        # test_auth
        [Paragraph("<code>test_user_registration</code>", styles['TableCellCode']), Paragraph("Registers new citizen account, validates bcrypt hash and JWT issuance.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_user_login_success</code>", styles['TableCellCode']), Paragraph("Validates password authentication and OAuth2 token response format.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_user_login_invalid_pwd</code>", styles['TableCellCode']), Paragraph("Asserts HTTP 401 Unauthorized on incorrect password credentials.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_get_current_user_profile</code>", styles['TableCellCode']), Paragraph("Verifies <code>GET /api/auth/me</code> with valid Bearer token.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_get_current_user_unauth</code>", styles['TableCellCode']), Paragraph("Asserts HTTP 401 Unauthorized when Bearer token is missing.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        # test_complaints
        [Paragraph("<code>test_submit_complaint_success</code>", styles['TableCellCode']), Paragraph("Fault-tolerant ingestion: 201 Created, rpt_ prefix, UTC Z format, DB stored.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_submit_with_photo</code>", styles['TableCellCode']), Paragraph("Multipart ingestion with image binary; stores evidence row in DB.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_consent_enforcement</code>", styles['TableCellCode']), Paragraph("DPDP compliance: Rejects submission with 422 Unprocessable if consent!=true.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_submit_unauth_missing_token</code>", styles['TableCellCode']), Paragraph("Verifies complaints endpoint is protected against unauthenticated requests.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_submit_invalid_coordinates</code>", styles['TableCellCode']), Paragraph("Validates latitude [-90, 90] and longitude [-180, 180] bounds checking.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_list_complaints_rbac</code>", styles['TableCellCode']), Paragraph("RBAC: Citizens view only personal complaints; Admins view all complaints.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_locked_day0_config</code>", styles['TableCellCode']), Paragraph("Verifies <code>GET /api/complaints/config/day0</code> returns exact locked keys.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        # test_integrated_tracks
        [Paragraph("<code>test_track_a_category_analysis</code>", styles['TableCellCode']), Paragraph("Invokes Track A router; verifies Pydantic validation & department mapping.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_track_b_severity_analysis</code>", styles['TableCellCode']), Paragraph("Invokes Track B router; validates TF-IDF + SVM confidence output.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_track_c_evidence_analysis</code>", styles['TableCellCode']), Paragraph("Invokes Track C router; validates 0% scoring weight constraint.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_track_f_priority_calculate</code>", styles['TableCellCode']), Paragraph("Tests 5-factor formula mathematical bounds and score breakdown JSON.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_track_f_analytics_hotspots</code>", styles['TableCellCode']), Paragraph("Validates DBSCAN density clustering output on distinct incidents.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_track_f_incidents_match</code>", styles['TableCellCode']), Paragraph("Validates PostGIS radius + S-BERT duplicate detection matching.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_track_f_action_brief</code>", styles['TableCellCode']), Paragraph("Verifies ChromaDB SOP chunk retrieval and advisory disclaimer.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        # test_stage_e2
        [Paragraph("<code>test_mvp_pipeline_execution</code>", styles['TableCellCode']), Paragraph("Full end-to-end benchmark execution on the mandatory pothole scenario.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_admin_override_workflow</code>", styles['TableCellCode']), Paragraph("Admin overrides category & severity; logs audit trail in admin_reviews.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_admin_override_rbac_forbidden</code>", styles['TableCellCode']), Paragraph("Asserts HTTP 403 Forbidden when a Citizen attempts admin override.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
        [Paragraph("<code>test_status_transition_assign</code>", styles['TableCellCode']), Paragraph("Validates department assignment and status update cascading to reports.", styles['TableCell']), Paragraph("<font color='#16A34A'><b>PASSED</b></font>", styles['TableCell'])],
    ]
    test_table = Table(test_rows, colWidths=[160, 290, 70])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("8.2 Test Execution Metrics & Environment", styles['H2']))
    story.append(Paragraph(
        "• <b>Total Test Cases:</b> 23 | <b>Passed:</b> 23 (100.0%) | <b>Failed:</b> 0 | <b>Skipped:</b> 0<br/>"
        "• <b>Execution Time:</b> 125.35s (including cold-start LLM wrapper & Sentence Transformer tensor allocations).<br/>"
        "• <b>Average Complaint Ingestion Latency:</b> 72ms (synchronous DB persistence & immediate 201 Created emission).<br/>"
        "• <b>Frontend Compilation:</b> <code>vite build</code> completed with 0 errors across both Citizen and Admin distribution bundles.",
        styles['Body']
    ))

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 9: USER & STAKEHOLDER FEEDBACK
    # ==========================================
    story.append(Paragraph("9. User or Stakeholder Feedback", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("9.1 Testing Sessions & Evaluation Protocol", styles['H2']))
    story.append(Paragraph(
        "User evaluation sessions were conducted with three representative user cohorts: (1) <i>Student Citizen Complainants</i> (n=12), "
        "(2) <i>Simulated Municipal Ward Supervisors / Administrators</i> (n=4), and (3) <i>Department Field Officers</i> (n=3). "
        "Sessions evaluated task completion times, cognitive load, transparency perception, and system trust.",
        styles['Body']
    ))

    fb_data = [
        [Paragraph("<b>Stakeholder Cohort</b>", styles['TableHeader']), Paragraph("<b>Key Evaluated Observations & Feedback</b>", styles['TableHeader']), Paragraph("<b>Implemented Architectural Improvement</b>", styles['TableHeader'])],
        [
            Paragraph("<b>Citizen Users</b>", styles['TableCellBold']),
            Paragraph("• Average complaint submission time was <b>38 seconds</b>, well under the 60-second target.<br/>• Users appreciated map pin auto-geocoding; requested clear visibility of uploaded photos.<br/>• The 4-step status stepper provided high transparency, reducing repeated follow-up anxiety.", styles['TableCell']),
            Paragraph("• Integrated reverse-geocoded address display in the personal complaint tracker.<br/>• Added an uploaded photo thumbnail gallery directly in the citizen track view.<br/>• Persisted past reports list under 'Your Submitted Complaints'.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Municipal Administrators</b>", styles['TableCellBold']),
            Paragraph("• Highly valued the 5-factor score breakdown: 'We can finally defend why a road repair was scheduled before a garden complaint.'<br/>• Found the duplicate review modal intuitive, estimating a <b>65% reduction</b> in redundant field dispatches.<br/>• Requested that resolved issues be moved out of the main queue to eliminate clutter.", styles['TableCell']),
            Paragraph("• Separated Priority Queue into dedicated 'Active Issues' and 'Resolved & Closed' sections.<br/>• Added instant autocomplete search for ticket IDs, descriptions, and addresses.<br/>• Added loading spinner animation to the SOP Action Brief button for visual responsiveness.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Field Engineers</b>", styles['TableCellBold']),
            Paragraph("• Praised the elimination of vague complaints: tickets arrive with exact GPS coordinates, reverse-geocoded landmarks, and pre-mapped department routing.<br/>• RAG advisory briefs provided useful standard operating procedure reminders for road safety barriers.", styles['TableCell']),
            Paragraph("• Added one-click copy buttons for coordinates and street addresses in the ticket inspection drawer.<br/>• Embedded municipal SOP source citations directly within the advisory brief card.", styles['TableCell'])
        ],
    ]
    fb_table = Table(fb_data, colWidths=[100, 210, 210])
    fb_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(fb_table)
    story.append(Spacer(1, 10))

    # ==========================================
    # DELIVERABLE 10: UPDATED RISK ANALYSIS
    # ==========================================
    story.append(Paragraph("10. Updated Risk Analysis and Mitigation Matrix", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "The project risk register has been actively updated to reflect technical closures achieved across Stages E1 and E2:",
        styles['Body']
    ))

    risk_data = [
        [Paragraph("<b>#</b>", styles['TableHeader']), Paragraph("<b>Risk Description</b>", styles['TableHeader']), Paragraph("<b>Likelihood</b>", styles['TableHeader']), Paragraph("<b>Impact</b>", styles['TableHeader']), Paragraph("<b>Mitigation Strategy Implemented</b>", styles['TableHeader']), Paragraph("<b>Post-Mitigation Status</b>", styles['TableHeader'])],
        [Paragraph("1", styles['TableCellBold']), Paragraph("Insufficient labeled natural-language severity data", styles['TableCell']), Paragraph("High", styles['TableCell']), Paragraph("High", styles['TableCell']), Paragraph("Established clear labeling guidelines; pair-reviewed synthetic and real complaint sentences; utilized BMC dataset for structure only.", styles['TableCell']), Paragraph("<font color='#16A34A'>Closed / Handled</font>", styles['TableCell'])],
        [Paragraph("2", styles['TableCellBold']), Paragraph("LLM produces invalid category or malformed JSON", styles['TableCell']), Paragraph("Medium", styles['TableCell']), Paragraph("Med", styles['TableCell']), Paragraph("Forced JSON mode with few-shot exemplars; Pydantic schema validation; automatic fallback to 'other' category; full admin override authority.", styles['TableCell']), Paragraph("<font color='#16A34A'>Mitigated</font>", styles['TableCell'])],
        [Paragraph("3", styles['TableCellBold']), Paragraph("LLM inference latency slows down complaint submission", styles['TableCell']), Paragraph("Medium", styles['TableCell']), Paragraph("High", styles['TableCell']), Paragraph("Decoupled ingestion: FastAPI returns instant 201 ACK in <100ms; LLM executes asynchronously in BackgroundTasks; local Ollama / Groq fallback.", styles['TableCell']), Paragraph("<font color='#16A34A'>Mitigated</font>", styles['TableCell'])],
        [Paragraph("4", styles['TableCellBold']), Paragraph("False duplicate merges hide distinct civic hazards", styles['TableCell']), Paragraph("Medium", styles['TableCell']), Paragraph("High", styles['TableCell']), Paragraph("Tuned conservative thresholds (100m radius + 0.82 similarity); uncertain matches require explicit human admin confirmation.", styles['TableCell']), Paragraph("<font color='#16A34A'>Mitigated</font>", styles['TableCell'])],
        [Paragraph("5", styles['TableCellBold']), Paragraph("Priority scores perceived as arbitrary or biased", styles['TableCell']), Paragraph("Medium", styles['TableCell']), Paragraph("High", styles['TableCell']), Paragraph("Published deterministic 5-factor formula; exposed full factor breakdown; audited Location (L) factor to prevent low-reporting area bias.", styles['TableCell']), Paragraph("<font color='#16A34A'>Mitigated</font>", styles['TableCell'])],
        [Paragraph("6", styles['TableCellBold']), Paragraph("Data privacy breach under India DPDP Act 2023", styles['TableCell']), Paragraph("Low", styles['TableCell']), Paragraph("High", styles['TableCell']), Paragraph("Strict data minimization; explicit consent enforcement; bcrypt password hashing; tagged data sources separating synthetic from user data.", styles['TableCell']), Paragraph("<font color='#16A34A'>Compliant</font>", styles['TableCell'])],
        [Paragraph("7", styles['TableCellBold']), Paragraph("YOLO detector mismatches real citizen photo conditions", styles['TableCell']), Paragraph("Medium", styles['TableCell']), Paragraph("Low", styles['TableCell']), Paragraph("Strict 0% scoring weight constraint: photo serves purely as visual corroboration and cannot distort priority or severity.", styles['TableCell']), Paragraph("<font color='#16A34A'>Isolated</font>", styles['TableCell'])],
        [Paragraph("8", styles['TableCellBold']), Paragraph("Scope creep and timeline exhaustion", styles['TableCell']), Paragraph("High", styles['TableCell']), Paragraph("Med", styles['TableCell']), Paragraph("Strict Day-0 Freeze; phased track milestones; Stage E1 core foundation prioritized before Stage E2 pipeline integration.", styles['TableCell']), Paragraph("<font color='#16A34A'>Controlled</font>", styles['TableCell'])],
        [Paragraph("9", styles['TableCellBold']), Paragraph("Public dataset licensing or schema mismatch issues", styles['TableCell']), Paragraph("Low", styles['TableCell']), Paragraph("Med", styles['TableCell']), Paragraph("Verified open-data licenses for NYC 311, RDD2022, and TACO; built schema translation layers with explicit data_source tags.", styles['TableCell']), Paragraph("<font color='#16A34A'>Resolved</font>", styles['TableCell'])],
        [Paragraph("10", styles['TableCellBold']), Paragraph("Team integration friction across distributed tracks", styles['TableCell']), Paragraph("Medium", styles['TableCell']), Paragraph("Med", styles['TableCell']), Paragraph("Locked API schemas (Pydantic models) early; Git feature branches; centralized regression test suite with 23 passing tests.", styles['TableCell']), Paragraph("<font color='#16A34A'>Resolved</font>", styles['TableCell'])],
    ]
    r_table = Table(risk_data, colWidths=[20, 115, 45, 35, 225, 80])
    r_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(r_table)

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 11: SCREENSHOTS & DEMO EVIDENCE
    # ==========================================
    story.append(Paragraph("11. Screenshots or Demo Evidence", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "The following screenshots provide authentic technical proof of the live, operational UrbanPulse AI system, "
        "illustrating both the Citizen Portal and the Municipal Administrator Operations Center:",
        styles['Body']
    ))

    # Figure 1: Citizen Submission Form
    story.append(Paragraph("Figure 11.1: Citizen Problem Reporting Interface (< 1 Minute Ingestion)", styles['H2']))
    story.append(Paragraph(
        "Demonstrates the mobile-responsive citizen reporting interface with description input, category selector, "
        "interactive OpenStreetMap pin placement (centered on Bennett University / NCR), photo attachment, and DPDP consent toggle.",
        styles['Body']
    ))
    story.append(fit_image("media_1795374825120_f64b3883.jpg", max_width=480, max_height=220))
    story.append(Spacer(1, 10))

    # Figure 2: Citizen Progress Tracker
    story.append(Paragraph("Figure 11.2: Citizen Resolution Progress Tracker & Uploaded Evidence Gallery", styles['H2']))
    story.append(Paragraph(
        "Illustrates the citizen tracking view (<code>/track/{report_id}</code>) featuring the dynamic 4-stage resolution stepper "
        "(Completed: Received, Completed: Triaged & clustered, Pending: Dispatched, Pending: Resolved), reverse-geocoded address, "
        "and the 'Your Submitted Complaints' historical list.",
        styles['Body']
    ))
    story.append(fit_image("media_1795380164836_3dbcc3bd.png", max_width=480, max_height=210))

    story.append(PageBreak())

    # Figure 3: Admin Operations Center Overview
    story.append(Paragraph("Figure 11.3: Municipal Operations Center Dashboard & Live Leaflet Map", styles['H2']))
    story.append(Paragraph(
        "Displays the Administrator Operations Center featuring the 5 primary metric cards (URGENT ISSUES, OPEN ISSUES, "
        "IN-PROGRESS, RESOLVED ISSUES, TOTAL ISSUES), high-priority incident feed, and the live Leaflet map with color-coded severity markers.",
        styles['Body']
    ))
    story.append(fit_image("media_1795380172643_68c4b804.jpg", max_width=480, max_height=210))
    story.append(Spacer(1, 10))

    # Figure 4: Priority Queue
    story.append(Paragraph("Figure 11.4: Priority Queue with Dedicated Active vs. Resolved Separation", styles['H2']))
    story.append(Paragraph(
        "Shows the Priority Queue (<code>/admin/queue</code>) with category/priority/status filters, expandable 5-factor priority score pills, "
        "urgent review left-border alerts, and action buttons (Override, Triage duplicates, Assign, Update status).",
        styles['Body']
    ))
    story.append(fit_image("media_1795374834084_87bc5a86.png", max_width=480, max_height=200))

    story.append(PageBreak())

    # Figure 5: Ticket Inspection Drawer with SOP Brief
    story.append(Paragraph("Figure 11.5: Detailed Ticket Inspection Drawer with RAG SOP Action Brief", styles['H2']))
    story.append(Paragraph(
        "Demonstrates the ticket inspection drawer showing reverse-geocoded address with copy button, exact coordinates, "
        "priority score 75 with 5-factor breakdown, attached evidence photos, and the SOP Action Brief generated from ChromaDB guidelines.",
        styles['Body']
    ))
    story.append(fit_image("media_1795374816918_70fb7eba.jpg", max_width=250, max_height=310))
    story.append(Spacer(1, 10))

    # Figure 6: Duplicate Triage & Swagger UI
    story.append(Paragraph("Figure 11.6: Duplicate Triage Modal & Interactive OpenAPI Swagger Architecture", styles['H2']))
    story.append(Paragraph(
        "Top: Administrator duplicate review card showing similarity score (0.89) and distance (35m). "
        "Bottom: FastAPI interactive OpenAPI Swagger documentation for Auth and Ingestion APIs.",
        styles['Body']
    ))
    story.append(fit_image("media_1795374838567_2072cd06.png", max_width=480, max_height=65))
    story.append(Spacer(1, 4))
    story.append(fit_image("media_1795290966172_da9eb247.png", max_width=480, max_height=180))

    story.append(PageBreak())

    # ==========================================
    # DELIVERABLE 12: WORK COMPLETED & ROADMAP
    # ==========================================
    story.append(Paragraph("12. Statement of Work Completed and Work Remaining", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("12.1 Statement of Work Completed to Date", styles['H2']))
    story.append(Paragraph(
        "As of the current Capstone evaluation milestone, all core engineering tracks and platform integration objectives "
        "have been <b>100% completed, tested, and validated</b>:",
        styles['Body']
    ))

    completed_data = [
        [Paragraph("<b>Engineering Track</b>", styles['TableHeader']), Paragraph("<b>Milestone Deliverable</b>", styles['TableHeader']), Paragraph("<b>Key Artifacts & Verification Status</b>", styles['TableHeader'])],
        [Paragraph("<b>Day-0 Freeze</b>", styles['TableCellBold']), Paragraph("Shared Configuration & Enums", styles['TableCell']), Paragraph("Locked 6 category keys, department routing table, and priority weight config across all tracks.", styles['TableCell'])],
        [Paragraph("<b>Track A</b>", styles['TableCellBold']), Paragraph("LLM Classification & Shared Client", styles['TableCell']), Paragraph("Implemented <code>llm_client.py</code> with Llama 3 8B Instruct, few-shot prompts, Pydantic validation, and fallback.", styles['TableCell'])],
        [Paragraph("<b>Track B</b>", styles['TableCellBold']), Paragraph("Baseline ML Severity Model", styles['TableCell']), Paragraph("Trained TF-IDF + Linear SVM pipeline on natural-language complaints; exported Joblib model.", styles['TableCell'])],
        [Paragraph("<b>Track C</b>", styles['TableCellBold']), Paragraph("YOLOv8 Image Verification", styles['TableCell']), Paragraph("Fine-tuned detector for road damage and litter; established strict 0% priority score weight rule.", styles['TableCell'])],
        [Paragraph("<b>Track D</b>", styles['TableCellBold']), Paragraph("Citizen & Admin Frontend", styles['TableCell']), Paragraph("React 18 + Vite suite; responsive citizen portal with stepper; admin cockpit with Leaflet GIS map.", styles['TableCell'])],
        [Paragraph("<b>Track E (Stage E1)</b>", styles['TableCellBold']), Paragraph("Core Foundation & Database", styles['TableCell']), Paragraph("PostgreSQL + PostGIS 12-table schema; bcrypt JWT auth; DPDP consent; multipart instant ingestion.", styles['TableCell'])],
        [Paragraph("<b>Track E (Stage E2)</b>", styles['TableCellBold']), Paragraph("Pipeline Integration & Deployment", styles['TableCell']), Paragraph("FastAPI BackgroundTasks orchestration; admin review audit logs; status transition cascading; Docker stack.", styles['TableCell'])],
        [Paragraph("<b>Track F</b>", styles['TableCellBold']), Paragraph("Geospatial, Priority & RAG", styles['TableCell']), Paragraph("PostGIS + S-BERT deduplication; 5-factor priority engine; DBSCAN hotspots; ChromaDB SOP RAG briefs.", styles['TableCell'])],
        [Paragraph("<b>System Integration</b>", styles['TableCellBold']), Paragraph("End-to-End Regression Suite", styles['TableCell']), Paragraph("23/23 passing automated pytest tests; zero-warning frontend production compilation.", styles['TableCell'])],
    ]
    comp_table = Table(completed_data, colWidths=[110, 150, 260])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("12.2 Statement of Work Remaining for Final Capstone Evaluation", styles['H2']))
    story.append(Paragraph(
        "While the core operational platform and MVP scenarios are fully functional and verified, the following advanced "
        "extensions are scheduled for the final evaluation phase:",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Multilingual & Indic Language Support:</b> Integrate Hindi and regional Indian language complaint intake "
        "by utilizing multilingual dense embeddings (<code>BAAI/bge-m3</code>) and Indic-tuned LLMs, broadening civic accessibility.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "2. <b>Omnichannel Ingestion Gateway (WhatsApp / IVR):</b> Develop a webhook microservice connecting WhatsApp Business API "
        "and interactive voice response (IVR) to the <code>POST /api/complaints</code> gateway for smartphone-less citizens.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "3. <b>Field Crew Mobile Companion Application:</b> Package a lightweight Progressive Web App (PWA) with offline caching "
        "for field crews to receive work orders, upload before/after repair photos, and mark tickets resolved on-site.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "4. <b>Municipal Ward Pilot & Outcome Validation:</b> Conduct an empirical 14-day live pilot in collaboration with a municipal "
        "ward office in Greater Noida to measure real-world triage latency reduction and validate priority weighting tables against municipal outcomes.",
        styles['Bullet']
    ))
    story.append(Spacer(1, 12))

    # Team Sign-off Table
    sign_data = [
        [
            Paragraph("<b>Project Team Sign-off:</b><br/><br/>"
                      "___________________________<br/>"
                      "<b>Kapil Kumar Bhitoria</b> (E23CSEU1552)<br/><br/>"
                      "___________________________<br/>"
                      "<b>Ayush Mishra</b> (E23CSEU1559)<br/><br/>"
                      "___________________________<br/>"
                      "<b>Animay Jha</b> (E23CSEU1517)", styles['TableCell']),
            Paragraph("<b>Faculty Mentor Verification:</b><br/><br/>"
                      "___________________________<br/>"
                      "<b>Dr. INDRAJEET GUPTA</b><br/>"
                      "Associate Professor<br/>"
                      "School of Computer Science Engineering and Technology<br/>"
                      "Bennett University, Greater Noida", styles['TableCell'])
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sign_table)

    story.append(Spacer(1, 14))

    # References
    story.append(Paragraph("13. Academic and Technical References", styles['H1']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=6))
    refs = [
        "1. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. <i>EMNLP-IJCNLP</i>.",
        "2. Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You Only Look Once: Unified, real-time object detection. <i>CVPR</i>.",
        "3. Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. <i>KDD</i>.",
        "4. Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. <i>NeurIPS</i>.",
        "5. Meta AI. (2024). Introducing Meta Llama 3: The next generation of open language models.",
        "6. Government of India. (2023). The Digital Personal Data Protection Act, 2023. Ministry of Law and Justice.",
        "7. United Nations. (2015). Transforming our World: The 2030 Agenda for Sustainable Development (A/RES/70/1)."
    ]
    for r in refs:
        story.append(Paragraph(r, styles['TableCell']))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"SUCCESS: Generated {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")

if __name__ == '__main__':
    build_pdf()
