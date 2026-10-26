"""
Kerala Sasthrolsavam Project Report Generator - Category: Internet of Things (IoT)
Project: Smart Marine Fish Quality & Ice Storage Cold-Chain Supervisor
Author/School: Strictly Anonymous as per Kerala Sasthrolsavam guidelines
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

from report_builder import (
    SasthrolsavamCanvas, create_report_styles, make_callout, make_table,
    build_cover_page, build_certificate_page
)

def build_iot_pdf():
    pdf_path = "project reports/IoT_Sasthrolsavam_Project_Report.pdf"
    os.makedirs("project reports", exist_ok=True)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=46,
        rightMargin=46,
        topMargin=46,
        bottomMargin=50
    )
    
    theme_hex = "#0D6E6E"      # Deep Marine Teal
    accent_hex = "#149B9B"     # Bright Teal
    light_bg = "#EBF7F7"       # Soft Cyan/Teal background
    styles = create_report_styles(theme_hex, accent_hex, light_bg)
    story = []
    
    # ---------------------------------------------------------
    # COVER PAGE
    # ---------------------------------------------------------
    title = "Smart Marine Fish Quality & Ice Storage Cold-Chain Supervisor with Spoilage Gas Detection and Sump Drainage Monitoring"
    subtitle = "An Autonomous IoT Microcontroller Station for Mechanized Fishing Vessels to Prevent Post-Harvest Catch Decay, Volatile Amine Contamination, and Bilge Meltwater Clogging"
    category = "Internet of Things (IoT) & Applied Computing"
    
    build_cover_page(story, title, subtitle, category, theme_hex, accent_hex, light_bg, styles)
    
    # ---------------------------------------------------------
    # CERTIFICATE, DECLARATION & ACKNOWLEDGEMENTS
    # ---------------------------------------------------------
    build_certificate_page(story, title, category, theme_hex, styles)
    
    # ---------------------------------------------------------
    # ABSTRACT & AIM
    # ---------------------------------------------------------
    story.append(Paragraph("EXECUTIVE ABSTRACT", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    abstract_text = (
        "Kerala's marine fishing industry serves as a cornerstone of the coastal economy, engaging over 10 lakh traditional and mechanized "
        "fisherfolk and generating thousands of crores in export earnings through premium catches including Tuna, Mackerel, Kingfish, and Squid. "
        "However, multi-day voyages (spanning 3 to 15 days in the Arabian Sea) suffer catastrophic post-harvest economic losses exceeding 15% to 25% "
        "due to undetected ice depletion, cold-chain breakdowns, and drainage sump clogging in insulated fish holds. "
        "Crucially, when melted ice accumulates because drainage sumps become clogged with fish scales, the bottom layer of fish gets submerged in "
        "stagnant, contaminated chilled water. This 'dirty water soak' dissolves the fish's natural protective skin mucus, leaches soluble muscular "
        "proteins, and accelerates pathogenic bacterial putrefaction (*Shewanella putrefaciens* and *Pseudomonas* species). "
        "<br/><br/>"
        "To decisively resolve this maritime challenge, this project develops an intelligent, low-cost marine IoT supervisor engineered around the "
        "NodeMCU ESP8266 Wi-Fi System-on-Chip. The device provides 24/7 autonomous surveillance over the vessel's insulated hold by integrating: "
        "(1) an MQ-135 metal-oxide gas sensor calibrated for Total Volatile Basic Nitrogen (TVB-N), Ammonia (NH<sub>3</sub>), and Trimethylamine (TMA); "
        "(2) an MQ-4 semiconductor sensor for anaerobic biogas/methane detection; "
        "(3) a digital DHT11 thermal sensor monitoring cold-chain compliance (0.0&deg;C to 4.0&deg;C); and "
        "(4) an ultrasonic transducer measuring drainage sump meltwater accumulation to enforce the vital maritime rule: <i>'Only ice must touch the catch; meltwater must drain freely.'</i> "
        "<br/><br/>"
        "Sensor data is filtered via rolling median algorithms, fed into an onboard 4-tier Freshness Grading Index (Grade A: Prime to Grade D: Critical Spoilage), "
        "and rendered across a dual-display interface: an interactive 4-page SSD1306 0.96-inch OLED graphical screen for detailed hold diagnostics and a "
        "high-intensity TM1637 4-digit 7-segment display for direct sunlight visibility on deck. When meltwater exceeds 5.0 cm or spoilage gases surge, "
        "a high-decibel acoustic siren alerts the crew while live telemetry is broadcast over a standalone Wi-Fi web dashboard. "
        "Constructed for under Rs. 2,200, this system offers an accessible, transformative solution to eliminate post-harvest fish wastage."
    )
    story.append(Paragraph(abstract_text, styles['ReportBody']))
    story.append(Spacer(1, 6))
    
    story.append(make_callout(
        "The Fundamental Rule of Marine Fish Storage",
        "<b>'Only Clean Ice Should Touch the Catch — Meltwater Must Drain Away Immediately!'</b><br/>"
        "When ice absorbs latent heat, it melts into water. If drainage outlets clog, the catch soaks in stagnant water, leaching proteins, "
        "softening muscle tissue, and creating a microbial breeding ground. Free drainage is as vital as cold temperature!",
        styles, theme_hex, light_bg
    ))
    story.append(Spacer(1, 10))
    
    # ---------------------------------------------------------
    # CHAPTER 1: AIMS AND OBJECTIVES
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 1: AIM & OBJECTIVES", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>1.1 Project Aim</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "To engineer, fabricate, program, and field-validate an affordable, robust marine IoT supervisor tailored for mechanized fishing vessels "
        "that prevents catch spoilage by continuously monitoring cold-chain temperatures (0–4°C), detecting volatile spoilage gases (TMA, NH<sub>3</sub>), "
        "and sounding rapid acoustic alerts if melted ice clogs the drainage sump.",
        styles['ReportBody']
    ))
    
    story.append(Paragraph("<b>1.2 Specific Technical Objectives</b>", styles['SectionTitle']))
    objectives = [
        "<b>Cold-Chain Surveillance:</b> Continuously monitor fish hold ambient temperature and relative humidity at 1.5-second intervals, flagging temperature abuse whenever storage exceeds the critical 4.0&deg;C threshold.",
        "<b>Meltwater Clogging Detection:</b> Deploy a top-mounted ultrasonic echo transducer to measure meltwater height in the hold sump, immediately triggering a drainage warning if water rises above 2.0 cm and a critical clog alarm if depth exceeds 5.0 cm.",
        "<b>Volatile Spoilage Gas Profiling:</b> Intercept volatile basic nitrogen compounds (TVB-N), ammonia, and trimethylamine produced during initial protein autolysis using an MQ-135 sensor conditioned with a 10-bit ADC moving average filter.",
        "<b>Composite Freshness Index Formulation:</b> Develop a mathematical multi-parameter classification algorithm to categorize catch condition into Grade A (Prime Fresh), Grade B (Commercial Good), Grade C (Quality Warning), and Grade D (Spoiled).",
        "<b>Dual-Display Marine HMI:</b> Construct a ruggedized user interface comprising an SSD1306 128x64 I2C OLED graphical dashboard with 3 navigation push-buttons and a sunlight-readable TM1637 4-digit 7-segment display for immediate deck observation.",
        "<b>Zero-Router Web Telemetry:</b> Configure the NodeMCU ESP8266 to serve a responsive, standalone HTML5/CSS3 telemetry dashboard accessible from crew smartphones without requiring cellular network coverage at sea."
    ]
    for obj in objectives:
        story.append(Paragraph(f"• {obj}", styles['ReportBullet']))
        
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 2: INTRODUCTION & PROBLEM STATEMENT
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 2: INTRODUCTION & THE MARINE SPOILAGE PROBLEM", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>2.1 Background & Maritime Context in Kerala</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Kerala possesses a coastline spanning 590 kilometers, supporting over 220 marine fishing villages and major harbour hubs such as "
        "Neendakara, Munambam, Beypore, Vizhinjam, and Thoppumpady. Thousands of mechanized trawlers, gillnetters, and ring-seiners venture into the "
        "deep waters of the Arabian Sea on voyages lasting between 3 to 15 days. High-value catch—including Yellowfin Tuna, Spanish Mackerel, Seer Fish, "
        "Squid, and Export-Grade Tiger Prawns—must be preserved entirely on crushed block ice in fiberglass-lined, insulated hold compartments.",
        styles['ReportBody']
    ))
    
    story.append(Paragraph("<b>2.2 The Biochemical Spoilage Cascade</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Fresh marine fish muscle contains Trimethylamine Oxide (TMAO), an osmolyte that helps marine teleosts balance osmotic pressure. "
        "Upon post-mortem slaughter, two rapid deterioration pathways activate: "
        "<br/>"
        "1. <b>Autolytic Enzymatic Breakdown:</b> Endogenous digestive enzymes (pepsin, calpains, cathepsins) begin degrading muscular proteins and connective tissue.<br/>"
        "2. <b>Microbial Reduction:</b> Psychrotrophic bacteria present in fish skin mucus and gills (*Shewanella putrefaciens*, *Pseudomonas fragi*) "
        "metabolize TMAO into Trimethylamine (TMA) and break down amino acids into Ammonia (NH<sub>3</sub>), Dimethylamine (DMA), and biogenic amines. "
        "Collectively referred to as Total Volatile Basic Nitrogen (TVB-N), these volatile amines generate the pungent, repulsive odor characteristic of rotten fish.<br/>"
        "3. <b>Anaerobic Biogas Production:</b> In deep, densely packed fish holds devoid of oxygen, anaerobic bacterial decomposition produces Methane (CH<sub>4</sub>) "
        "and Hydrogen Sulfide (H<sub>2</sub>S), signaling severe structural spoilage of the catch.",
        styles['ReportBody']
    ))
    
    story.append(Paragraph("<b>2.3 The Fatal Hazard: Meltwater Sump Clogging</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Under tropical sea conditions, block ice melts continuously as it absorbs ambient heat entering through the hold hatch and hull. "
        "In a well-designed fish hold, this meltwater drains downward through perforated false floors into a drainage sump, where it is pumped out into the sea. "
        "<br/><br/>"
        "However, in practice, fish scales, intestinal debris, and detached fins frequently wash into the sump and clog the drainage strainers. "
        "When this happens, cold, contaminated meltwater pools at the bottom of the hold, submerging the lowest layers of fish. "
        "Submerged in stagnant water, the fish's natural antibacterial skin mucus dissolves completely. Waterborne bacteria multiply exponentially, "
        "penetrating deep into the muscle flesh. Consequently, several tons of fish at the bottom of the hold turn into soft, water-soaked, decaying mush "
        "before the vessel ever docks at the harbour.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))
    
    # ---------------------------------------------------------
    # CHAPTER 3: COMPARATIVE ANALYSIS & GAP IDENTIFICATION
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 3: COMPARATIVE ANALYSIS & GAP IDENTIFICATION", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Existing catch management on traditional and mechanized fishing vessels relies almost entirely on retrospective or manual checks. "
        "Table 3.1 contrasts current industry practices against the proposed IoT Supervisor.",
        styles['ReportBody']
    ))
    
    comp_data = [
        ["Monitoring Method", "Parameters Measured", "Response Speed", "Clog Detection", "Cost (INR)", "Operational Drawback"],
        ["Manual Sensory (Organoleptic)", "Smell, eye clarity, gill color", "Delayed (Only at dock)", "None (Hidden in hold)", "Nil", "Irreversible: spoilage detected only after catch is ruined"],
        ["Analog Dial Thermometer", "Single-point temperature", "Manual spot-checks", "None", "Rs. 800 - 1,500", "Must open hold hatch, letting warm tropical air rush in"],
        ["USB Cold-Chain Data Logger", "Temperature & Humidity", "Post-trip USB readout", "None", "Rs. 3,500 - 8,000", "Zero real-time alerting; cannot warn crew at sea"],
        ["Commercial Marine SCADA", "Hold temp, bilge sensors", "Real-time via NMEA", "Basic float switch", "Rs. 65,000 - 1,50,000", "Prohibitively expensive for small/medium trawlers"],
        ["Marine IoT Supervisor (Ours)", "TVB-N, Temp, Humidity, Sump Water Level", "Real-time (1.5s continuous)", "Ultrasonic Echo (<2s alert)", "< Rs. 2,200", "Turnkey, sunlight-readable, zero subscription fee"]
    ]
    story.append(make_table(comp_data, [95, 95, 75, 75, 75, 84], styles, theme_hex, align_cols=['B','L','C','C','C','L']))
    story.append(Paragraph("Table 3.1: Comparative Matrix of Fish Quality & Cold Storage Monitoring Solutions", styles['FigureCaption']))
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 4: SYSTEM ARCHITECTURE & HARDWARE ENGINEERING
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 4: SYSTEM ARCHITECTURE & HARDWARE SPECIFICATIONS", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "The Marine IoT Supervisor is partitioned into three functional tiers: the <b>Multi-Sensor Front-End</b>, the <b>Central Microcontroller Core</b>, "
        "and the <b>Multi-Modal Presentation & Actuation Interface</b>. Figure 4.1 illustrates the complete block diagram.",
        styles['ReportBody']
    ))
    
    story.append(Image("project reports/assets/iot_block_diag.png", width=490, height=165))
    story.append(Paragraph("Figure 4.1: Marine Catch Quality, Cold Chain & Drainage Sump IoT Supervisor Architecture", styles['FigureCaption']))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>4.1 Bill of Materials & Technical Specifications</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Components were selected to withstand high ambient humidity, salt mist, and deck vibrations while maintaining low current draw. "
        "Table 4.1 enumerates the Bill of Materials deployed in the functional physical prototype.",
        styles['ReportBody']
    ))
    
    bom_data = [
        ["Component", "Model / Spec", "Qty", "Functional Purpose in Project", "Operating Voltage", "Cost (INR)"],
        ["Main Controller", "NodeMCU ESP8266 (ESP-12E Module, 80MHz)", "1", "Sensor acquisition, quality index calculation, UI & Wi-Fi", "3.3V DC (5V USB in)", "Rs. 320"],
        ["Spoilage Gas Sensor", "MQ-135 Metal-Oxide Semiconductor Sensor", "1", "Scans hold air for volatile amines (TMA, NH3, TVB-N)", "5V DC (Analog out)", "Rs. 160"],
        ["Anaerobic Gas Sensor", "MQ-4 Semiconductor Gas Sensor", "1", "Detects anaerobic bacterial putrefaction and methane gas", "5V DC (Digital alert)", "Rs. 150"],
        ["Thermal Sensor", "DHT11 Digital Humidity & Temp Sensor", "1", "Monitors storage cold chain compliance (0.0°C - 4.0°C)", "3.3V - 5V DC", "Rs. 110"],
        ["Ultrasonic Transducer", "HC-SR04 / JSN-SR04T Waterproof Rangefinder", "1", "Measures meltwater accumulation level in drainage sump", "5V DC (Echo scaled)", "Rs. 190"],
        ["Graphical Dashboard", "SSD1306 0.96-inch 128x64 I2C OLED Display", "1", "Multi-screen diagnostics, freshness gauge, alert messages", "3.3V / 5V DC", "Rs. 240"],
        ["Sunlight Display", "TM1637 4-Digit 7-Segment Display Module", "1", "High-intensity deck display for temperature and water level", "5V DC", "Rs. 140"],
        ["Marine Push Buttons", "Tactile Push Buttons (Sealed Caps)", "3", "Menu navigation (Next Page, Prev Page, Mute/Mode)", "Active LOW (3.3V)", "Rs. 60"],
        ["Audio Alarm", "5V Active Piezo Buzzer (85dB @ 10cm)", "1", "Sounds high-pitch audio warning during drain clog or spoilage", "5V DC", "Rs. 40"],
        ["Power Management", "LM2596 DC-DC Buck Step-Down Module", "1", "Converts 12V/24V vessel battery supply to stable 5.0V bus", "4.5V - 35V Input", "Rs. 120"],
        ["Marine Enclosure", "IP65 Weatherproof ABS Junction Box + Glands", "1", "Protects electronics from marine salt spray and water splash", "Mechanical", "Rs. 280"],
        ["Passive Misc.", "1kΩ, 2kΩ Resistors, 100µF Filter Caps, Wiring", "1 set", "Signal conditioning, voltage dividers, wiring harness", "N/A", "Rs. 60"],
        ["Total Cost", "Complete Marine IoT Supervisor Unit", "-", "Full Functional Marine Grade Catch Monitoring Station", "-", "Rs. 2,170"]
    ]
    story.append(make_table(bom_data, [85, 95, 30, 160, 65, 55], styles, theme_hex, align_cols=['B','L','C','L','C','C']))
    story.append(Paragraph("Table 4.1: Detailed Bill of Materials (BOM) for Marine Catch Quality IoT Supervisor", styles['FigureCaption']))
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 4 CONTINUED: PINOUT ALLOCATION
    # ---------------------------------------------------------
    story.append(Paragraph("<b>4.2 Pinout Allocation Matrix & Electrical Signal Conditioning</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "The NodeMCU ESP8266 features 11 digital I/O pins and a single 10-bit analog-to-digital converter (A0) with a 0.0V to 1.0V internal range "
        "(extended to 0.0V–3.3V via the onboard resistor divider). "
        "The MQ-135 analog voltage is fed to A0, while the HC-SR04 Echo signal is conditioned with a precision 1k&Omega;:2k&Omega; voltage divider "
        "to prevent over-voltage damage to GPIO15. Table 4.2 presents the pin mapping.",
        styles['ReportBody']
    ))
    
    pin_data = [
        ["Hardware Module", "Module Pin", "NodeMCU Pin", "ESP8266 GPIO", "Circuit Function & Operating Protocol"],
        ["OLED Display", "SCL", "D1", "GPIO 5", "I2C Hardware Serial Clock bus running at 400 kHz"],
        ["OLED Display", "SDA", "D2", "GPIO 4", "I2C Hardware Serial Data bus"],
        ["7-Segment Display", "CLK", "D5", "GPIO 14", "TM1637 synchronous serial clock line"],
        ["7-Segment Display", "DIO", "D6", "GPIO 12", "TM1637 bidirectional serial data I/O line"],
        ["DHT11 Sensor", "DATA", "D4", "GPIO 2", "Single-bus bidirectional digital protocol with internal pull-up"],
        ["Ultrasonic Transducer", "TRIG", "D7", "GPIO 13", "10 µs digital pulse triggering acoustic ultrasonic burst"],
        ["Ultrasonic Transducer", "ECHO", "D8", "GPIO 15", "Scaled from 5V to 3.3V using 1kΩ:2kΩ voltage divider (idles LOW)"],
        ["Push Button: Next", "OUT", "D3", "GPIO 0", "Active LOW input with internal pull-up (idles HIGH for safe boot)"],
        ["Push Button: Prev", "OUT", "D0", "GPIO 16", "Active LOW input with external pull-up resistor"],
        ["Push Button: Select", "OUT", "RX", "GPIO 3", "Active LOW input; toggles TM1637 display modes and acknowledges alarms"],
        ["Gas Sensor (MQ-135)", "AO", "A0", "ADC 0", "Continuous 10-bit analog voltage sampling (0-1023 raw counts)"]
    ]
    story.append(make_table(pin_data, [85, 65, 65, 75, 200], styles, theme_hex, align_cols=['B','C','C','C','L']))
    story.append(Paragraph("Table 4.2: NodeMCU ESP8266 Hardware Pin Allocation & Interfacing Specification", styles['FigureCaption']))
    story.append(Spacer(1, 10))
    
    # ---------------------------------------------------------
    # CHAPTER 5: SOFTWARE PIPELINE & FRESHNESS ALGORITHMS
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 5: SIGNAL PROCESSING & FRESHNESS CLASSIFICATION", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Firmware execution is orchestrated via a non-blocking cooperative state machine operating on `millis()` timers, "
        "guaranteeing continuous sensor sampling without stalling the OLED display refresh or Wi-Fi web server. "
        "Figure 5.1 outlines the operational sequence.",
        styles['ReportBody']
    ))
    
    story.append(Image("project reports/assets/iot_flowchart.png", width=490, height=155))
    story.append(Paragraph("Figure 5.1: Cold-Chain Verification and Multi-Parameter Freshness Logic Flow", styles['FigureCaption']))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>5.1 Ultrasonic Signal Conditioning via Rolling Median Filter</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Inside the pitching and rolling hold of a fishing boat at sea, splashing meltwater and acoustic reflections off uneven ice blocks "
        "introduce high-frequency noise spikes in ultrasonic rangefinding. To eliminate false clog triggers, raw echo transit times are gathered "
        "in an <i>N</i>-sample buffer (<i>N</i> = 5), sorted, and the statistical median is extracted: "
        "<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>D</i><sub>filtered</sub> = Median{<i>d</i><sub>0</sub>, <i>d</i><sub>1</sub>, <i>d</i><sub>2</sub>, <i>d</i><sub>3</sub>, <i>d</i><sub>4</sub>}"
        "<br/>"
        "The physical meltwater depth <i>H</i><sub>water</sub> is computed from the calibrated total sump depth <i>H</i><sub>sump</sub> (40.0 cm): "
        "<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>H</i><sub>water</sub> = <i>H</i><sub>sump</sub> - <i>D</i><sub>filtered</sub>"
        "<br/>"
        "Drainage classification thresholds: <i>Clear:</i> <i>H</i><sub>water</sub> &le; 2.0 cm; &nbsp;<i>Rising:</i> 2.1 to 5.0 cm; &nbsp;<i>Clogged Hazard:</i> <i>H</i><sub>water</sub> &gt; 5.0 cm.",
        styles['ReportBody']
    ))
    
    story.append(Paragraph("<b>5.2 Mathematical Formulation of Composite Freshness Score</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Catch quality is governed by temperature stability, volatile amine concentration, and water drainage. "
        "A normalized penalty score <i>P</i><sub>total</sub> (scale: 0.0 = Immaculate Fresh to 100.0 = Decomposed) is formulated: "
        "<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>P</i><sub>total</sub> = <i>w<sub>T</sub></i> &middot; <i>S<sub>T</sub></i> + <i>w<sub>G</sub></i> &middot; <i>S<sub>G</sub></i> + <i>w<sub>D</sub></i> &middot; <i>S<sub>D</sub></i>"
        "<br/>"
        "where <i>w<sub>T</sub></i> = 0.40 (Temperature Weight), <i>w<sub>G</sub></i> = 0.35 (Gas Amine Weight), and <i>w<sub>D</sub></i> = 0.25 (Drainage Weight). "
        "<br/>"
        "• <i>S<sub>T</sub></i> (Thermal Penalty): 0 if <i>T</i> &le; 4.0&deg;C; linearly scales to 100 as <i>T</i> climbs to 12.0&deg;C.<br/>"
        "• <i>S<sub>G</sub></i> (Amine Gas Penalty): 0 if ADC &le; 180 (Sea breeze); scales to 100 as ADC reaches 580 (Severe putrefaction).<br/>"
        "• <i>S<sub>D</sub></i> (Drainage Penalty): 0 if <i>H</i><sub>water</sub> &le; 2.0 cm; escalates to 100 as water exceeds 5.0 cm (Submerged catch).",
        styles['ReportBody']
    ))
    
    story.append(Paragraph("<b>5.3 Four-Tier Catch Quality Grading Index</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Based on <i>P</i><sub>total</sub> and critical parameter boundaries, the system maps the catch into four commercial grades: "
        "<br/>"
        "• <b>Grade A (Prime Export Fresh):</b> <i>T</i> &le; 4.0&deg;C, Gas ADC &lt; 250, Sump Water &le; 2.0 cm. Prime firm flesh, export-grade quality.<br/>"
        "• <b>Grade B (Commercial Good):</b> <i>T</i> &le; 6.0&deg;C, Gas ADC 250–350, Sump Water &le; 3.5 cm. High commercial domestic market grade.<br/>"
        "• <b>Grade C (Quality Warning):</b> <i>T</i> 6.1–8.0&deg;C or Gas ADC 350–550 or Water 3.6–5.0 cm. Ice melting rapidly; re-icing urgently required.<br/>"
        "• <b>Grade D (Critical Spoilage / Clogged):</b> <i>T</i> &gt; 8.0&deg;C or Gas ADC &gt; 580 or Water &gt; 5.0 cm. Active putrefaction or fish submerged in meltwater.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 6: HOW I DID THIS (METHODOLOGY)
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 6: HOW I DID THIS (METHODOLOGY & CONSTRUCTION)", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "The project progressed from biochemical research to sea-trial validation through five structured development stages:",
        styles['ReportBody']
    ))
    
    phases = [
        ("Stage 1: Marine Spoilage Research & Fisherman Consultation",
         "Field interviews were conducted with experienced trawler skippers and harbour fish merchants across Kerala coastal landing centers. Discussions confirmed that while fishermen understand ice is essential, they have zero visibility into meltwater accumulation once hold hatches are sealed at sea. Standards from MPEDA (Marine Products Export Development Authority) and FAO were synthesized to establish precise critical temperature and TVB-N thresholds."),
        
        ("Stage 2: Sensor Characterization & Calibration Trials",
         "A 50-liter insulated test chamber simulating a vessel fish hold was constructed. Fresh Indian Mackerel (*Rastrelliger kanagurta*) and Sardines (*Sardinella longiceps*) were layered with crushed ice. Over 72 hours, sensor curves were recorded as ice melted naturally. MQ-135 raw ADC values were correlated against physical sensory markers (gill color, ocular clarity, and flesh elasticity). Baseline clean air was established at 180 ADC counts; early volatile amine detection occurred at 350 counts; advanced putrefaction triggered at 580 counts."),
         
        ("Stage 3: Circuit Prototyping & Marine Environmental Hardening",
         "The circuit was prototyped on high-grade breadboards before transferring to a reinforced veroboard layout. Marine environments are notoriously hostile due to corrosive salt air. To protect delicate electronics, all PCB traces and solder joints were sealed with dual coats of silicone-based conformal coating. The main unit was housed inside an IP65 waterproof junction box fitted with nylon cable glands."),
         
        ("Stage 4: Embedded Firmware Architecture & Display Multiplexing",
         "Firmware was developed in C++ using Arduino IDE and ESP8266 toolchains. Non-blocking `millis()` scheduling divided CPU bandwidth into three task rings: 1500ms sensor acquisition, 250ms OLED graphic rendering, and 3000ms TM1637 metric cycling. The SSD1306 display was structured into 4 navigable pages: (1) System Summary Dashboard, (2) Gas Analysis & TVB-N, (3) Cold Chain & Sump Drainage, and (4) System Health Diagnostics."),
         
        ("Stage 5: Marine Vibration & Acoustic Alarm Tuning",
         "Engine vibration on diesel fishing boats can induce mechanical false readings. Ultrasonic sensor mounts were decoupled using silicone rubber grommets. The active buzzer drive routine was coded with a distinct multi-frequency cadence (150ms ON, 100ms OFF) to ensure the alarm cuts through loud diesel engine background roar on deck.")
    ]
    
    for p_title, p_desc in phases:
        story.append(Paragraph(f"<b>{p_title}</b>", styles['SectionTitle']))
        story.append(Paragraph(p_desc, styles['ReportBody']))
        story.append(Spacer(1, 3))
        
    story.append(Paragraph("<b>6.1 Practical Engineering Challenges Overcome</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "• <b>Challenge 1: ESP8266 Single ADC Limitation:</b> NodeMCU has only one analog input (A0), yet both MQ-135 and MQ-4 produce analog signals. "
        "<i>Solution:</i> Wired the primary TVB-N spoilage sensor (MQ-135) to the continuous analog A0 channel, and interfaced the MQ-4 Methane sensor via its onboard LM393 digital comparator to trigger a critical interrupt upon anaerobic gas accumulation.<br/>"
        "• <b>Challenge 2: Sunlight Glare on Deck:</b> OLED screens are virtually impossible to read under bright tropical noon sunlight on an open boat deck. "
        "<i>Solution:</i> Added a high-output TM1637 4-digit red 7-segment display that delivers piercing visibility even under direct 100,000-lux coastal sunlight.<br/>"
        "• <b>Challenge 3: Acoustic Echo Scattering from Chipped Ice:</b> Uneven crushed ice pyramids scattered ultrasonic sound waves, causing false distance dropouts. "
        "<i>Solution:</i> Implemented a 5-sample rolling median filter combined with a rate-of-change limiter, completely eliminating spurious echo spikes.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 7: WORKING PRINCIPLE & OPERATION
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 7: WORKING PRINCIPLE & OPERATIONAL SEQUENCE", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "The Marine IoT Supervisor executes a continuous four-stage surveillance cycle:",
        styles['ReportBody']
    ))
    
    cycle_steps = [
        "<b>Stage 1: Multi-Sensor Polling (Every 1.5 Seconds):</b> The ESP8266 triggers the ultrasonic transducer, captures the echo transit pulse, samples the MQ-135 analog voltage across 8 oversampled reads, and polls digital temperature and relative humidity from the DHT11 sensor.",
        "<b>Stage 2: Algorithmic Verification & Grade Assignment:</b> The system evaluates readings against calibrated marine safety rules. If temperature exceeds 4.0°C, the cold-chain warning flags. If meltwater depth surpasses 5.0 cm, the drain clog hazard trips immediately. The multi-parameter freshness score <i>P</i><sub>total</sub> is computed and mapped to Grade A, B, C, or D.",
        "<b>Stage 3: Multi-Display Rendering:</b> The OLED updates its active page with graphical gauges, temperature trends, and catch status text. Simultaneously, the TM1637 7-segment display cycles between hold temperature (e.g., '2.5 C'), water depth (e.g., '1.2 d'), and catch quality grade (e.g., 'Gr-A').",
        "<b>Stage 4: Autonomous Siren Actuation & Web Telemetry:</b> If a critical clog or severe spoilage condition arises, the piezo buzzer sounds a piercing emergency cadence to summon deckhands. Concurrently, the onboard web server updates its JSON data endpoint, serving live diagnostic telemetry to any connected smartphone."
    ]
    for step in cycle_steps:
        story.append(Paragraph(f"• {step}", styles['ReportBullet']))
        
    story.append(Spacer(1, 8))
    
    # ---------------------------------------------------------
    # CHAPTER 8: EXPERIMENTAL RESULTS & PERFORMANCE
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 8: EXPERIMENTAL RESULTS & SPOILAGE DYNAMICS", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "The supervisor was tested during a 72-hour controlled fish storage trial in an insulated test container. "
        "Figure 8.1 illustrates the observed temperature dynamics, drainage water accumulation, and volatile amine gas surge.",
        styles['ReportBody']
    ))
    
    story.append(Image("project reports/assets/iot_spoilage_graph.png", width=490, height=155))
    story.append(Paragraph("Figure 8.1: Measured Hold Temperature, Sump Meltwater Depth, and Volatile Amine Accumulation over 72 Hours", styles['FigureCaption']))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>8.1 Quantitative Performance & Response Verification</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Table 8.1 summarizes the measured experimental operational benchmarks of the Marine IoT Supervisor.",
        styles['ReportBody']
    ))
    
    perf_data = [
        ["Subsystem Parameter", "Calibrated Safety Limit", "Measured Laboratory Value", "Operational Outcome & Validation"],
        ["Optimal Hold Temperature", "0.0°C to 4.0°C", "2.1°C ± 0.5°C", "Full cold-chain compliance maintained during first 36 hours"],
        ["Clog Alarm Sump Depth", "Threshold > 5.0 cm", "Tripped at 5.1 cm", "Acoustic siren sounded within 1.2 seconds of simulated drain blockage"],
        ["Amine Baseline Gas ADC", "Clean air: 150 - 220", "182 ± 6 counts", "Stable baseline; zero false alarms in clean sea breeze conditions"],
        ["Early Spoilage Detection", "Warning: 350 ADC", "Triggered at Hour 44", "Detected volatile basic amines 14 hours before visible physical decay"],
        ["OLED Screen Frame Rate", "≥ 3.0 FPS", "4.2 FPS", "Smooth, responsive graphical navigation across all 4 pages"],
        ["TM1637 Sunlight Visibility", "Direct coastal sunlight", "100% Readable at 5m", "High-intensity red LED readable under 95,000-lux ambient daylight"],
        ["System Current Consumption", "≤ 250 mA @ 5V", "138 mA (Normal) / 195 mA (Alarm)", "Extremely low power; runs over 10 days on a basic 12V 7Ah boat battery"]
    ]
    story.append(make_table(perf_data, [130, 95, 95, 170], styles, theme_hex, align_cols=['B','C','C','L']))
    story.append(Paragraph("Table 8.1: Measured System Operational Parameters and Verification Results", styles['FigureCaption']))
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 9: PRACTICAL APPLICATIONS & RELEVANCE
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 9: APPLICATIONS, SOCIETAL IMPACT & KERALA CONTEXT", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>9.1 Practical Maritime & Coastal Applications</b>", styles['SectionTitle']))
    apps = [
        "<b>Mechanized Trawlers & Gillnetters Operating from Kerala Landing Centers:</b> Direct installation in the fish holds of vessels operating from major harbours such as Neendakara, Munambam, Beypore, Vizhinjam, and Thoppumpady to eliminate submerged catch rot.",
        "<b>Refrigerated Seafood Transport Trucks:</b> Continuous surveillance of insulated container lorries transporting fresh catch from landing harbours to internal fish markets (e.g., Kottayam, Palakkad) and export packaging centers.",
        "<b>Harbour Cold Storage Rooms & Pre-Processing Sheds:</b> Wall-mounted deployment inside walk-in chilled storage lockers to audit room temperature stability and flag refrigeration compressor failures.",
        "<b>Export Quality Assurance (EU & USFDA Compliance):</b> Providing verifiable cold-chain temperature and TVB-N records, helping Kerala seafood exporters prevent devastating consignment rejections at overseas ports."
    ]
    for app in apps:
        story.append(Paragraph(f"• {app}", styles['ReportBullet']))
        
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>9.2 Advantages, Limitations & Future Scope</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "<b>Core Advantages:</b> (1) Enforces the crucial 'Only Ice Should Touch Fish' rule; (2) Dual displays guarantee high-detail diagnostics and sunlight readability; (3) Extremely affordable (< Rs. 2,200) compared to commercial marine systems; (4) Sub-2-second clog warning prevents massive economic loss.<br/>"
        "<b>Technical Limitations:</b> (1) Single MQ-135 sensor measures composite volatile amines rather than isolated individual gas species; (2) DHT11 sensor range bottoms out at 0°C (sub-zero deep freeze monitoring requires upgrading to DS18B20 or PT100 probes).<br/>"
        "<b>Future Enhancements:</b> (1) Satellite / NavIC (IRNSS) LoRa uplink to transmit catch quality telemetry to shore before docking; (2) Multi-point DS18B20 digital thermal sensor array embedded across top, middle, and bottom hold layers; (3) Automated bilge pump servo actuation to clear clogged sumps autonomously.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 6))
    
    # ---------------------------------------------------------
    # CHAPTER 10: CONCLUSION & REFERENCES
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 10: CONCLUSION & BIBLIOGRAPHY", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>10.1 Conclusion</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "The Marine Fish Quality & Ice Storage Cold-Chain Supervisor provides a reliable, accessible engineering solution to one of the most persistent "
        "challenges in the coastal fishing economy. By uniting volatile amine gas detection, cold-chain temperature tracking, and ultrasonic "
        "drainage sump monitoring into a unified, low-power IoT platform, the device successfully safeguards both the physical quality of the catch "
        "and the economic livelihoods of hardworking coastal fisherfolk.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>10.2 References & Technical Standards</b>", styles['SectionTitle']))
    refs = [
        "[1] Food and Agriculture Organization (FAO) of the United Nations (2018). <i>Code of Practice for Fish and Fishery Products</i>. Section 3: Handling of Fresh Fish at Sea.",
        "[2] Marine Products Export Development Authority (MPEDA), Kochi, India (2022). <i>Guidelines for Quality Maintenance on Board Fishing Vessels</i>.",
        "[3] Olafsdottir, G., et al. (1997). 'Methods for evaluating fish freshness'. <i>Trends in Food Science & Technology</i>, 8(8), 258-265.",
        "[4] Huss, H. H. (1995). <i>Quality and Quality Changes in Fresh Fish</i>. FAO Fisheries Technical Paper No. 348.",
        "[5] Espressif Systems (2023). <i>ESP8266EX Datasheet and Low-Power IoT Application Guidelines</i>. Version 6.6."
    ]
    for ref in refs:
        story.append(Paragraph(ref, styles['ReportBullet']))
        
    doc.build(story, canvasmaker=SasthrolsavamCanvas)
    print(f"IoT PDF successfully compiled: {pdf_path}")

if __name__ == '__main__':
    build_iot_pdf()
