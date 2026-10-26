"""
ReportBuilder: Core ReportLab styling and layout utility for Kerala Sasthrolsavam Project Reports.
Ensures strict anonymity (NO school names or personal identifying details), professional typography,
custom NumberedCanvas for 'Page X of Y' dynamic footers, elegant callouts, and clean table formatting.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

class SasthrolsavamCanvas(canvas.Canvas):
    """
    Two-pass canvas that accumulates total pages and draws headers, footers,
    page borders, and running metadata. Title page is left clean.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []
        self.header_title = kwargs.get('header_title', 'KERALA STATE SCHOOL SASTHROLSAVAM')
        self.category_name = kwargs.get('category_name', 'SCIENCE & TECHNOLOGY PROJECT REPORT')
        self.theme_color = kwargs.get('theme_color', colors.HexColor('#1A4B82'))

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            if self._pageNumber > 1:
                self.draw_page_decorations(page_count)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Geometry: A4 is 595.27 x 841.89 pt
        left = 46
        right = 549
        top_header_y = 806
        bot_footer_y = 44
        
        # Running Header
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(self.theme_color)
        self.drawString(left, top_header_y, "KERALA STATE SCHOOL SASTHROLSAVAM")
        
        self.setFont("Helvetica-Oblique", 7.5)
        self.setFillColor(colors.HexColor('#555555'))
        self.drawRightString(right, top_header_y, self.category_name.upper())
        
        # Header Rule
        self.setStrokeColor(colors.HexColor('#D0D7DE'))
        self.setLineWidth(0.75)
        self.line(left, top_header_y - 4, right, top_header_y - 4)
        
        # Footer Rule
        self.line(left, bot_footer_y + 12, right, bot_footer_y + 12)
        
        # Running Footer
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor('#666666'))
        self.drawString(left, bot_footer_y, "State Science Fair • Official Project Report (Confidential Evaluation Copy)")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica-Bold", 7.5)
        self.drawRightString(right, bot_footer_y, page_str)
        
        self.restoreState()

def create_report_styles(theme_hex='#1A4B82', accent_hex='#2A75D3', light_bg_hex='#F4F7FB'):
    styles = getSampleStyleSheet()
    
    theme_col = colors.HexColor(theme_hex)
    accent_col = colors.HexColor(accent_hex)
    dark_text = colors.HexColor('#222222')
    body_text = colors.HexColor('#2E3440')
    
    styles.add(ParagraphStyle(
        name='CoverCategoryBadge',
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.white,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='CoverMainTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=25,
        textColor=theme_col,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='CoverSubTitle',
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#4C566A'),
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='CoverMetaLabel',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=theme_col
    ))
    
    styles.add(ParagraphStyle(
        name='CoverMetaValue',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=dark_text
    ))
    
    styles.add(ParagraphStyle(
        name='ChapterTitle',
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=18,
        textColor=theme_col,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='SubSectionTitle',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='ReportBody',
        fontName='Helvetica',
        fontSize=8.8,
        leading=13.2,
        textColor=body_text,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name='ReportBodyBold',
        fontName='Helvetica-Bold',
        fontSize=8.8,
        leading=13.2,
        textColor=dark_text,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name='ReportBullet',
        fontName='Helvetica',
        fontSize=8.8,
        leading=13,
        textColor=body_text,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    ))

    styles.add(ParagraphStyle(
        name='CalloutText',
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor('#1F2937')
    ))

    styles.add(ParagraphStyle(
        name='CalloutTitle',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=theme_col
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=11,
        textColor=colors.white,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=dark_text,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name='TableCellCenter',
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=dark_text,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=11,
        textColor=dark_text,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name='FigureCaption',
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=8
    ))

    return styles

def make_callout(title, text, styles, theme_hex='#1A4B82', bg_hex='#F4F7FB', width=500):
    content = [
        Paragraph(f"<b>{title}</b>", styles['CalloutTitle']),
        Spacer(1, 2),
        Paragraph(text, styles['CalloutText'])
    ]
    t = Table([[content]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_hex)),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LINELEFT', (0,0), (0,-1), 3.5, colors.HexColor(theme_hex)),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D0D7DE')),
    ]))
    return t

def make_table(data_rows, col_widths, styles, theme_hex='#1A4B82', align_cols=None):
    """
    Renders a styled data table with wrapped paragraphs.
    data_rows: list of lists of strings
    """
    theme_col = colors.HexColor(theme_hex)
    formatted_data = []
    
    # Header
    header = [Paragraph(cell, styles['TableHeader']) for cell in data_rows[0]]
    formatted_data.append(header)
    
    # Body rows
    for r_idx, row in enumerate(data_rows[1:]):
        formatted_row = []
        for c_idx, cell in enumerate(row):
            if align_cols and align_cols[c_idx] == 'C':
                p = Paragraph(cell, styles['TableCellCenter'])
            elif align_cols and align_cols[c_idx] == 'B':
                p = Paragraph(cell, styles['TableCellBold'])
            else:
                p = Paragraph(cell, styles['TableCell'])
            formatted_row.append(p)
        formatted_data.append(formatted_row)
        
    t = Table(formatted_data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), theme_col),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]
    
    # Alternating row colors
    for i in range(1, len(data_rows)):
        bg = colors.HexColor('#F8FAFC') if i % 2 == 1 else colors.white
        t_style.append(('BACKGROUND', (0, i), (-1, i), bg))
        
    t.setStyle(TableStyle(t_style))
    return t

def build_cover_page(story, title, subtitle, category, theme_hex='#1A4B82', accent_hex='#2A75D3', light_bg_hex='#F4F7FB', styles=None):
    theme_col = colors.HexColor(theme_hex)
    accent_col = colors.HexColor(accent_hex)
    
    story.append(Spacer(1, 15))
    
    # Header Fair Emblem / Tag
    banner_p = Paragraph(f"<b>KERALA STATE SCHOOL SASTHROLSAVAM</b><br/><font size=8.5>GENERAL EDUCATION DEPARTMENT • GOVERNMENT OF KERALA</font>", ParagraphStyle(
        name='CoverStateBanner',
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=16,
        textColor=theme_col,
        alignment=TA_CENTER
    ))
    story.append(banner_p)
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="96%", thickness=1.5, color=theme_col, spaceBefore=4, spaceAfter=18))
    
    # Category Badge
    badge_data = [[Paragraph(f"<b>OFFICIAL COMPETITION PROJECT REPORT • CATEGORY: {category.upper()}</b>", styles['CoverCategoryBadge'])]]
    badge_table = Table(badge_data, colWidths=[490])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), theme_col),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 26))
    
    # Main Title
    story.append(Paragraph(title, styles['CoverMainTitle']))
    story.append(Spacer(1, 12))
    
    # Subtitle
    story.append(Paragraph(subtitle, styles['CoverSubTitle']))
    story.append(Spacer(1, 35))
    
    # Decorative accent divider
    story.append(HRFlowable(width="60%", thickness=1.0, color=accent_col, spaceBefore=0, spaceAfter=25))
    
    # Submission Metadata Box - STRICTLY NO SCHOOL NAME, NO STUDENT NAME
    meta_data = [
        [Paragraph("COMPETITION EVENT", styles['CoverMetaLabel']), Paragraph("Kerala State School Sasthrolsavam (Science & Technology Fair)", styles['CoverMetaValue'])],
        [Paragraph("PROJECT CATEGORY", styles['CoverMetaLabel']), Paragraph(f"{category} (High School / Higher Secondary Division)", styles['CoverMetaValue'])],
        [Paragraph("PARTICIPANT / TEAM ID", styles['CoverMetaLabel']), Paragraph("<b>[ CONFIDENTIAL VENUE REGISTRATION CODE ]</b>", styles['CoverMetaValue'])],
        [Paragraph("SUB-DISTRICT / DISTRICT", styles['CoverMetaLabel']), Paragraph("[ Allocated at District / State Verification Desk ]", styles['CoverMetaValue'])],
        [Paragraph("SUBMISSION LEVEL", styles['CoverMetaLabel']), Paragraph("State Level Technical Evaluation & Project Exhibition", styles['CoverMetaValue'])],
        [Paragraph("ACADEMIC YEAR", styles['CoverMetaLabel']), Paragraph("2026 – 2027", styles['CoverMetaValue'])],
    ]
    meta_table = Table(meta_data, colWidths=[160, 310])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(light_bg_hex)),
        ('BOX', (0,0), (-1,-1), 1.0, theme_col),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D0D7DE')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 30))
    
    # Confidentiality Note
    conf_note = Paragraph("<i>Notice: In strict compliance with Kerala Sasthrolsavam fair competition guidelines, institutional names, school affiliations, and personal identities are omitted to ensure impartial blind peer evaluation.</i>", ParagraphStyle(
        name='ConfNote',
        fontName='Helvetica-Oblique',
        fontSize=7.8,
        leading=11,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    ))
    story.append(conf_note)
    story.append(PageBreak())

def build_certificate_page(story, title, category, theme_hex='#1A4B82', styles=None):
    theme_col = colors.HexColor(theme_hex)
    
    story.append(Paragraph("CERTIFICATE OF AUTHENTICITY", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=theme_col, spaceBefore=2, spaceAfter=14))
    
    cert_text = (
        f"This is to certify that this technical project report entitled <b>'{title}'</b> is an authentic, "
        f"independent, and bona fide record of scientific investigation, engineering design, and fabrication "
        f"carried out for presentation at the <b>Kerala State School Sasthrolsavam</b> in the category of "
        f"<b>{category}</b>.<br/><br/>"
        f"The hardware prototypes, circuit schematics, embedded firmware, computational software algorithms, "
        f"and laboratory validation datasets presented in this document represent the original work of the "
        f"registered participant(s) under the guidance of our science/technology mentors. "
        f"No part of this work has been plagiarized from proprietary sources or submitted elsewhere for any other award."
    )
    story.append(Paragraph(cert_text, styles['ReportBody']))
    story.append(Spacer(1, 30))
    
    # Signature blocks
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Signature of Participant(s)</b><br/>Registration Code: ____________", styles['TableCellCenter']),
            Paragraph("____________________________<br/><b>Signature of Guiding Teacher</b><br/>Department of Science & IT", styles['TableCellCenter']),
            Paragraph("____________________________<br/><b>Sasthrolsavam Evaluator / Judge</b><br/>General Education Department", styles['TableCellCenter']),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[160, 160, 160])
    sig_table.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 25))
    
    # Declaration
    story.append(Paragraph("STUDENT DECLARATION", styles['SectionTitle']))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))
    decl_text = (
        "I/We hereby declare that this project report has been prepared by me/us for the Kerala State School Sasthrolsavam. "
        "The experimental setup, circuit wiring, firmware implementation, and analytical observations were carried out "
        "personally. All external references, datasheets, open-source computational libraries, and foundational publications "
        "have been duly cited and acknowledged in the bibliography."
    )
    story.append(Paragraph(decl_text, styles['ReportBody']))
    story.append(Spacer(1, 18))
    
    # Acknowledgements
    story.append(Paragraph("ACKNOWLEDGEMENTS", styles['SectionTitle']))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))
    ack_text = (
        "I/We express our profound gratitude to our school science mentors, laboratory instructors, and parents for their "
        "unwavering technical guidance, constructive criticism, and material encouragement throughout this engineering endeavor.<br/><br/>"
        "We also convey our sincere thanks to the General Education Department, Government of Kerala, for fostering "
        "scientific curiosity, technological innovation, and competitive spirit among school students through the Sasthrolsavam platform. "
        "Finally, our gratitude extends to the global open-source hardware and software engineering communities whose accessible "
        "tools, documentation, and compilers made the realization of this project possible."
    )
    story.append(Paragraph(ack_text, styles['ReportBody']))
    story.append(PageBreak())
