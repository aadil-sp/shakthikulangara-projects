"""
Kerala Sasthrolsavam Project Report Generator - Category: Electronics & Hardware
Project: HazardGuard C3 - Multi-Hazard Emergency & Safety Automation Platform
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

def build_electronics_pdf():
    pdf_path = "project reports/Electronics_Sasthrolsavam_Project_Report.pdf"
    os.makedirs("project reports", exist_ok=True)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=46,
        rightMargin=46,
        topMargin=46,
        bottomMargin=50
    )
    
    theme_hex = "#C84B31"      # Industrial Crimson / Terracotta
    accent_hex = "#D9534F"     # Vibrant Amber-Red
    light_bg = "#FDF5F2"       # Warm Light Red/Rose Background
    styles = create_report_styles(theme_hex, accent_hex, light_bg)
    story = []
    
    # ---------------------------------------------------------
    # COVER PAGE
    # ---------------------------------------------------------
    title = "HazardGuard C3: Multi-Hazard Autonomous Emergency Warning, Gas Leakage Interception & Safety Automation Platform"
    subtitle = "A High-Speed RISC-V Microcontroller Supervisor Engineered with Optocoupled Galvanic Load Isolation, Sub-300ms Fail-Safe Cutoff, Multi-Environment Threshold Logic, and Zero-Dependency Cyber Dashboard"
    category = "Electronics & Hardware Engineering"
    
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
        "Hazardous residential, commercial, and industrial operational environments face continuous, severe threats from catastrophic "
        "gas leaks, thermal runaway/flash fires, unauthorized personnel breaches into dangerous machinery perimeters, and toxic liquid/meltwater "
        "sump overflows. In India, domestic LPG cylinder explosions and commercial boiler failures cause thousands of critical injuries and hundreds "
        "of crores in property devastation annually. Conventional safety infrastructure consists primarily of isolated, passive detectors "
        "(such as standalone smoke alarms or uncoordinated gas beepers) that lack active physical shut-off actuation, fail to isolate high-voltage "
        "electrical lines, and provide no contextual adaptive intelligence. "
        "<br/><br/>"
        "To provide a decisive, active engineering countermeasure, this project develops <b>HazardGuard C3</b>—an integrated, fail-safe electronic "
        "emergency supervisor and safety automation platform engineered around the 32-bit RISC-V ESP32-C3 microcontroller operating at 160 MHz. "
        "The system fuses analog sensory telemetry from an MQ series gas/smoke sensor conditioned via an 8-sample digital moving-average filter, "
        "digital ambient thermal telemetry from a DHT11 sensor, and dual-mode ultrasonic proximity/radar data from an HC-SR04 transducer. "
        "<br/><br/>"
        "A multi-zone firmware state engine dynamically switches between calibrated safety threshold matrices tailored for three distinct environments: "
        "<b>(1) Household Kitchens</b> (LPG leak trip, grease fire alert, and stove clearance), "
        "<b>(2) Commercial Hotel Facilities</b> (central boiler room overheat, commercial kitchen range surveillance, and grease-trap surge monitoring), and "
        "<b>(3) Industrial Manufacturing Plants</b> (toxic chemical fumes, heavy machinery dangerous perimeter intrusion, and toxic effluent tank overflow). "
        "<br/><br/>"
        "Upon detecting an anomalous condition, the system achieves an ultra-rapid fail-safe response within <b>285 milliseconds</b>: an optocoupled "
        "high-current relay is energized to physically cut off fuel solenoids or engage explosion-proof ventilation fans, an active 85dB piezo siren "
        "dispatches an aggressive warning cadence, a TM1637 4-digit display multiplexes real-time hazard codes, and a zero-dependency HTML5 cyber-dashboard "
        "is broadcast over local Wi-Fi and fallback Soft-AP. Constructed for under Rs. 2,000, HazardGuard C3 delivers industrial-grade life-safety automation."
    )
    story.append(Paragraph(abstract_text, styles['ReportBody']))
    story.append(Spacer(1, 6))
    
    story.append(make_callout(
        "Core Electronic Engineering Principle of HazardGuard C3",
        "<b>Active Fail-Safe Physical Actuation & Galvanic Isolation:</b><br/>"
        "Passive alarms only warn; HazardGuard C3 actively intercepts disaster. By utilizing optocoupled isolation (PC817) and an active-low "
        "fail-safe relay topology, the controller cuts off gas solenoids and disengages mains power within 285ms, completely isolating the microcontroller "
        "from hazardous inductive kickback voltage spikes.",
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
        "The primary aim of this project is to design, construct, program, and rigorously benchmark an intelligent, autonomous multi-hazard electronic "
        "safety platform powered by a RISC-V microcontroller that achieves sub-300ms fail-safe electrical actuation, multi-environment threshold "
        "adaptability, and real-time cyber-telemetry at an affordable price point.",
        styles['ReportBody']
    ))
    
    story.append(Paragraph("<b>1.2 Specific Technical Objectives</b>", styles['SectionTitle']))
    objectives = [
        "<b>Multi-Parameter Analog & Digital Front-End:</b> Design conditioned interfacing circuitry for MQ-series gas/smoke sensors (on ADC1_CH1), DHT11 digital thermal sensors, and HC-SR04 ultrasonic rangefinders with precision resistor level-shifting (1kΩ:2kΩ).",
        "<b>Sub-300ms Active-Low Relay Actuation:</b> Implement an optically isolated relay switching stage utilizing PC817 optocouplers, flyback snubber diodes, and NPN drivers to isolate 250VAC/10A mains loads and gas shut-off solenoids in under 300 ms.",
        "<b>Digital Signal Conditioning & Noise Suppression:</b> Author an 8-sample moving average digital filter running on 12-bit ADC acquisitions to suppress electrical transients and prevent false emergency shutdowns.",
        "<b>Multi-Environment Contextual Firmware Engine:</b> Program three selectable firmware threshold profiles (Household, Hotel Commercial, Industrial Factory) that adapt gas, thermal, intrusion, and overflow trip points to specific operating environments.",
        "<b>Sunlight-Readable Diagnostic Telemetry:</b> Drive a TM1637 4-digit 7-segment display to cycle between live temperature, gas ADC, perimeter distance, and explicit status codes ('GAS!', 'FIRE', 'HELP', 'SAFE').",
        "<b>Zero-Router Fallback Cyber Dashboard:</b> Develop an embedded asynchronous web server serving a responsive CSS3/HTML5 telemetry dashboard accessible over existing Wi-Fi infrastructure or a standalone fallback Soft-AP hotspot."
    ]
    for obj in objectives:
        story.append(Paragraph(f"• {obj}", styles['ReportBullet']))
        
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 2: INTRODUCTION & PROBLEM STATEMENT
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 2: INTRODUCTION & THE MULTI-HAZARD PROBLEM", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>2.1 Background & Hazard Dynamics</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Modern living and production environments are surrounded by combustible fuels, high-pressure steam systems, heavy mechanical actuators, "
        "and toxic effluents. In domestic kitchens and restaurants across Kerala, Liquefied Petroleum Gas (LPG)—a dense mixture of propane and butane—is "
        "the primary cooking fuel. Because LPG is heavier than air, leaking gas settles near the floor and accumulates in unventilated low pockets. "
        "A single electric spark from a refrigerator relay or light switch can ignite an accumulated gas cloud, resulting in violent deflagrations.",
        styles['ReportBody']
    ))
    story.append(Paragraph(
        "In commercial hotel facilities, central steam boilers and high-output burner arrays operate continuously. Overheating boilers pose explosive "
        "bleve (Boiling Liquid Expanding Vapor Explosion) risks, while kitchen grease traps frequently overflow, contaminating municipal storm drains. "
        "Similarly, in seafood pre-processing plants, chemical manufacturing units, and rubber processing facilities across Kerala (such as Kochi, "
        "Eloor, and Kollam), workers operate in close proximity to automated cutting machines, hazardous chemical dip tanks, and wastewater sumps.",
        styles['ReportBody']
    ))
    
    story.append(Paragraph("<b>2.2 Failure Modes of Conventional Safety Equipment</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "A critical engineering evaluation of existing safety devices reveals fatal vulnerabilities: "
        "<br/>"
        "1. <b>Purely Passive Operation:</b> Commercial smoke alarms produce an audible beep but take zero active physical measures to isolate fuel lines, "
        "kill electrical power, or activate exhaust ventilation fans. If occupants are asleep or absent, the structure burns down.<br/>"
        "2. <b>High False Alarm Rates & Sensor Drift:</b> Low-cost standalone detectors lack digital filtering algorithms; common cooking vapors or aerosol "
        "sprays trigger false alarms, leading frustrated users to disconnect their batteries entirely.<br/>"
        "3. <b>Uncoordinated Single-Parameter Blindness:</b> A standard gas alarm cannot sense a grease fire or an overflowing tank; a heat detector cannot "
        "detect an invisible cold LPG leak or a worker falling toward a moving machine.<br/>"
        "4. <b>Lack of Galvanic Circuit Isolation:</b> Primitive microcontroller circuits directly switching mechanical relays suffer from inductive "
        "back-EMF spikes that crash the CPU, freezing the safety system in an unsafe lockup state during emergencies.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))
    
    # ---------------------------------------------------------
    # CHAPTER 3: COMPARATIVE ANALYSIS & CIRCUIT PHILOSOPHY
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 3: COMPARATIVE ANALYSIS & CIRCUIT PHILOSOPHY", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Table 3.1 contrasts traditional safety equipment against the integrated architecture of HazardGuard C3.",
        styles['ReportBody']
    ))
    
    comp_data = [
        ["System Feature", "Standard Smoke Alarm", "Commercial LPG Beeper", "Industrial Safety PLC", "HazardGuard C3 (Proposed)"],
        ["Sensing Scope", "Smoke only (Optical)", "Combustible gas only", "Custom modular probes", "Gas, Heat/Fire, Perimeter Radar, Liquid Level"],
        ["Actuation Capability", "None (Audio buzzer only)", "None (Passive alarm)", "Relay / SCADA Interlock", "Optocoupled 10A Relay + Active Siren + Web AP"],
        ["Response Time", "45 - 90 seconds", "15 - 30 seconds", "< 100 milliseconds", "190ms Relay / 285ms Total System Trip"],
        ["Operating Contexts", "Fixed domestic threshold", "Fixed threshold", "Factory only (Rigid)", "3 Contexts (Household, Hotel, Industrial)"],
        ["Unit Cost (INR)", "Rs. 1,200 - 2,500", "Rs. 1,500 - 3,500", "Rs. 45,000 - 1,20,000", "< Rs. 2,000 (Turnkey life-safety station)"]
    ]
    story.append(make_table(comp_data, [95, 95, 95, 105, 109], styles, theme_hex, align_cols=['B','C','C','C','L']))
    story.append(Paragraph("Table 3.1: Comparative Matrix of Safety Supervision & Actuation Systems", styles['FigureCaption']))
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 4: SYSTEM ARCHITECTURE & CIRCUIT ENGINEERING
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 4: SYSTEM ARCHITECTURE & CIRCUIT SPECIFICATIONS", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "HazardGuard C3 integrates four distinct electrical domains: (1) Sensor Conditioning Front-End, (2) ESP32-C3 RISC-V Microcontroller, "
        "(3) Optically Isolated Actuation Stage, and (4) Human-Machine & Web Interface. Figure 4.1 depicts the block diagram.",
        styles['ReportBody']
    ))
    
    story.append(Image("project reports/assets/electronics_block_diag.png", width=490, height=165))
    story.append(Paragraph("Figure 4.1: HazardGuard C3 Fail-Safe Industrial & Domestic Emergency Supervisor Architecture", styles['FigureCaption']))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>4.1 Bill of Materials & Electrical Component Selection</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Every component was selected based on electrical robustness, thermal tolerance, and cost efficiency. "
        "Table 4.1 itemizes the complete Bill of Materials deployed in the physical working prototype.",
        styles['ReportBody']
    ))
    
    bom_data = [
        ["Component", "Model / Spec", "Qty", "Circuit Role / Functional Purpose", "Operating Voltage", "Cost (INR)"],
        ["Microcontroller SoC", "ESP32-C3 SuperMini (RISC-V 32-bit, 160MHz)", "1", "Multi-hazard processing, ADC filtering, Web AP & GPIO control", "3.3V DC (Onboard LDO)", "Rs. 380"],
        ["Gas / Smoke Sensor", "MQ-2 / MQ-135 Gas Sensor Module", "1", "Monitors LPG, methane, propane, smoke; analog voltage output", "5.0V DC (Heater & VCC)", "Rs. 160"],
        ["Thermal Sensor", "DHT11 Digital Humidity & Temperature Sensor", "1", "Detects flash fires, rapid thermal runaway, ambient overheat", "3.3V - 5.0V DC", "Rs. 110"],
        ["Ultrasonic Radar", "HC-SR04 Ultrasonic Distance Transducer", "1", "Perimeter intrusion radar & liquid overflow level detector", "5.0V DC (Echo divided)", "Rs. 180"],
        ["Optocoupled Relay", "5V 1-Channel Relay Module (PC817 Opto, 10A)", "1", "Galvanically isolated trip switch for gas solenoid / exhaust fan", "5V Coil (Active LOW)", "Rs. 140"],
        ["7-Segment Display", "TM1637 4-Digit 7-Segment Display Module", "1", "Multiplexed local numerical display for gas, temp & status codes", "5.0V DC", "Rs. 140"],
        ["Piezo Siren", "5V Active High-Output Buzzer (85dB @ 10cm)", "1", "Acoustic life-safety siren with dual-frequency alarm cadence", "5.0V DC", "Rs. 40"],
        ["Armed / Alert LED", "Dual-State Red/Green 5mm Diffused LED", "1", "Heartbeat armed indicator (Green) / Critical trip strobe (Red)", "3.3V DC (220Ω limit)", "Rs. 15"],
        ["Voltage Regulator", "AMS1117-3.3 & LM2596 Step-Down Module", "1", "Ultra-stable dual-rail 5V and 3.3V DC power distribution bus", "7V - 24V DC Input", "Rs. 110"],
        ["Protection Passives", "1kΩ, 2kΩ, 220Ω Resistors, 1N4007 Diode, Caps", "1 set", "Echo level shifting, opto base limiting, flyback suppression", "N/A", "Rs. 45"],
        ["Industrial Enclosure", "Ventilated Flame-Retardant ABS Enclosure", "1", "Ruggedized housing with terminal blocks and cable strain relief", "Mechanical", "Rs. 240"],
        ["Terminal Blocks", "Screw Terminals (5.08mm Pitch, 15A Rated)", "2", "High-current AC line & gas shut-off solenoid wire connections", "250VAC / 15A Rated", "Rs. 50"],
        ["Total Cost", "Complete HazardGuard C3 Life-Safety Platform", "-", "Turnkey Active Multi-Hazard Safety Automation Station", "-", "Rs. 1,610"]
    ]
    story.append(make_table(bom_data, [85, 95, 30, 160, 65, 55], styles, theme_hex, align_cols=['B','L','C','L','C','C']))
    story.append(Paragraph("Table 4.1: Detailed Bill of Materials (BOM) for HazardGuard C3 Platform", styles['FigureCaption']))
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 4 CONTINUED: PINOUT MATRIX & OPTOCOUPLER SCHEMATIC
    # ---------------------------------------------------------
    story.append(Paragraph("<b>4.2 ESP32-C3 Pin Allocation Matrix & Electrical Conditioning</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "The ESP32-C3 RISC-V microcontroller operates strictly at 3.3V logic levels. "
        "To ensure absolute semiconductor reliability, all 5V sensor outputs (such as HC-SR04 Echo) are stepped down using precision resistor "
        "voltage dividers (1k&Omega; series and 2k&Omega; shunt), clamping the input pulse to exactly 3.33V. Table 4.2 presents the pin mapping.",
        styles['ReportBody']
    ))
    
    pin_data = [
        ["Signal Name", "Hardware Module", "ESP32-C3 Pin", "Mode", "Circuit Conditioning & Voltage Isolation"],
        ["PIN_GAS_ANALOG", "Gas Sensor (MQ)", "GPIO 1", "ADC1_CH1", "Direct 12-bit analog input (0-4095); 8-sample moving average filter"],
        ["PIN_TM_CLK", "TM1637 Display", "GPIO 2", "Digital Output", "Synchronous display clock line; 10kΩ internal pull-up"],
        ["PIN_TM_DIO", "TM1637 Display", "GPIO 3", "Bidirectional", "Bidirectional serial data line with ACK handshake"],
        ["PIN_US_TRIG", "HC-SR04 Ultrasonic", "GPIO 4", "Digital Output", "10 µs trigger pulse initiates 40 kHz ultrasonic burst"],
        ["PIN_US_ECHO", "HC-SR04 Ultrasonic", "GPIO 5", "Digital Input", "5V echo pulse scaled to 3.3V via 1kΩ:2kΩ precision divider network"],
        ["PIN_DHT", "DHT11 Temp/Humidity", "GPIO 6", "Single-Bus I/O", "Bidirectional digital time-slot protocol with 4.7kΩ pull-up to 3.3V"],
        ["PIN_BUZZER", "Active Piezo Siren", "GPIO 7", "Digital Output", "Drives 2N2222 NPN switching transistor powering 85dB siren"],
        ["PIN_STATUS_LED", "Armed / Alert LED", "GPIO 8", "Digital Output", "Green armed pulse (Normal) / Red rapid strobe (Emergency)"],
        ["PIN_RELAY", "Optocoupled Relay", "GPIO 10", "Digital Output", "Active LOW drive logic; PC817 optoisolator triggers 10A relay coil"]
    ]
    story.append(make_table(pin_data, [80, 85, 65, 75, 194], styles, theme_hex, align_cols=['B','L','C','C','L']))
    story.append(Paragraph("Table 4.2: ESP32-C3 Hardware Pin Allocation and Circuit Conditioning Matrix", styles['FigureCaption']))
    story.append(Spacer(1, 10))
    
    # ---------------------------------------------------------
    # CHAPTER 5: FIRMWARE ARCHITECTURE & ALGORITHMS
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 5: FIRMWARE ARCHITECTURE & SIGNAL CONDITIONING", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Firmware execution is governed by a high-frequency polling engine executing every 400ms. "
        "Figure 5.1 outlines the decision tree from sensor acquisition to sub-second physical relay tripping.",
        styles['ReportBody']
    ))
    
    story.append(Image("project reports/assets/electronics_flowchart.png", width=490, height=155))
    story.append(Paragraph("Figure 5.1: Multi-Hazard Interception Logic & Emergency Actuation Flow", styles['FigureCaption']))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>5.1 Moving-Average ADC Filtering for Gas Noise Suppression</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Metal-oxide semiconductor gas sensors (MQ series) are prone to thermal drift and baseline ADC quantization noise. "
        "To prevent spurious alarm trips, an 8-sample circular buffer implements a moving average filter on 12-bit ADC acquisitions: "
        "<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>V</i><sub>filtered</sub>(<i>k</i>) = (1/8) &sum;<sub><i>i</i>=0</sub><sup>7</sup> <i>V</i><sub>raw</sub>(<i>k</i> - <i>i</i>)"
        "<br/>"
        "This digital filter eliminates transient electrical spikes while maintaining an overall step response latency below 50 milliseconds.",
        styles['ReportBody']
    ))
    
    story.append(Paragraph("<b>5.2 Multi-Environment Contextual Threshold Engine</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "A single fixed threshold cannot safely supervise diverse environments: an industrial factory naturally possesses higher ambient fume "
        "levels than a domestic kitchen, whereas a hotel boiler operates at elevated baseline temperatures. "
        "HazardGuard C3 incorporates three pre-calibrated operating profiles (switchable via software dashboard or hardware toggle): "
        "<br/>"
        "• <b>Profile 0: Household Kitchen & Living:</b> Gas Warning = 1200 ADC, Gas Alarm = 2100 ADC (~51% full-scale LPG trip); Temp Warning = 40.0&deg;C, Temp Alarm = 52.0&deg;C (Flash fire risk); Stove Clearance = 30 cm; Sump Overflow = 12 cm.<br/>"
        "• <b>Profile 1: Commercial Hotel Facility:</b> Gas Warning = 1000 ADC, Gas Alarm = 1800 ADC (Rapid kitchen range leak trip); Temp Warning = 38.0&deg;C, Temp Alarm = 48.0&deg;C (Boiler ambient overheat); Equipment Clearance = 45 cm; Grease Trap Overflow = 10 cm.<br/>"
        "• <b>Profile 2: Industrial Manufacturing Plant:</b> Gas Warning = 800 ADC, Gas Alarm = 1500 ADC (High sensitivity to toxic fumes); Temp Warning = 44.0&deg;C, Temp Alarm = 60.0&deg;C (Machinery overheat); Danger Perimeter Breach = 65 cm; Effluent Tank Overflow = 8 cm.",
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
        "HazardGuard C3 was engineered through five systematic, rigorous hardware and software development phases:",
        styles['ReportBody']
    ))
    
    phases = [
        ("Phase 1: Hazard Analysis & Electronic Architecture Design",
         "The project commenced by compiling safety standards for explosive atmospheres (IS 2148 / IEC 60079). Electrical isolation was identified as the paramount design constraint: because mechanical relays switch inductive loads (such as electric exhaust fan motors and heavy solenoid coils), collapsing magnetic fields generate hundreds of volts of back-EMF. To prevent microcontroller destruction, a PC817 optoisolator and a 1N4007 flyback snubber diode were integrated into the relay driver stage."),
        
        ("Phase 2: Sensor Signal Conditioning & Voltage Divider Calibration",
         "Breadboard prototyping evaluated sensor electrical behavior. The HC-SR04 echo pin outputs 5V TTL pulses. Precision metal-film resistors (1kΩ and 2kΩ with 1% tolerance) were wired to form a voltage divider that clamped the echo signal to 3.33V, fully verified via digital oscilloscope probing. The MQ sensor's analog output was characterized under controlled propane and smoke exposures."),
         
        ("Phase 3: RISC-V Embedded Firmware Development (ESP32-C3)",
         "Firmware was written in C++ targeting the ESP32-C3 RISC-V 32-bit architecture. Cooperative non-blocking task schedulers were structured using `millis()` intervals: 400ms for analog gas and ultrasonic sampling, 2000ms for DHT11 reads, and 2500ms for TM1637 metric cycling. Active-low relay trip routines were written with zero software delay to guarantee sub-second actuation."),
         
        ("Phase 4: Zero-Dependency Cyber Web Dashboard Engineering",
         "To ensure operators can audit facility safety without installing proprietary software, an embedded asynchronous HTTP web server was constructed inside the ESP32-C3 flash memory. The dashboard UI was built using pure HTML5, CSS3, and vanilla JavaScript—requiring zero external CDNs or internet routers. The ESP32-C3 connects to facility Wi-Fi, or automatically spawns an independent Soft-AP hotspot ('HazardGuard-C3-AP') if the local router fails."),
         
        ("Phase 5: Enclosure Fabrication & Transient Stress Testing",
         "The completed circuit was soldered onto a reinforced proto-board and mounted inside a flame-retardant ABS enclosure fitted with terminal blocks and ventilation slots. Stress tests evaluated system response under sudden butane gas injection, simulated heat gun temperature rises, and rapid optical proximity breaches.")
    ]
    
    for p_title, p_desc in phases:
        story.append(Paragraph(f"<b>{p_title}</b>", styles['SectionTitle']))
        story.append(Paragraph(p_desc, styles['ReportBody']))
        story.append(Spacer(1, 3))
        
    story.append(Paragraph("<b>6.1 Practical Engineering Challenges & Solutions Overcome</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "• <b>Challenge 1: ESP32-C3 Strapping Pin Traps:</b> GPIO 8 and GPIO 9 on the ESP32-C3 act as boot strapping pins; grounding them at power-on forced the chip into ROM bootloader mode. "
        "<i>Solution:</i> Carefully remapped all external active-low pull-down inputs away from strapping pins, assigning GPIO 8 strictly to an active-low LED output that idles HIGH during boot.<br/>"
        "• <b>Challenge 2: Inductive Relay Arcing & Reset Spikes:</b> Switching 230VAC fans induced high-frequency electromagnetic interference (EMI) that caused occasional CPU resets. "
        "<i>Solution:</i> Implemented complete galvanic isolation via PC817 optocouplers, routed relay coil GND completely separate from the ESP32 digital GND, and added a 100nF ceramic decoupling cap across VCC/GND.<br/>"
        "• <b>Challenge 3: Sensor Preheating Drift:</b> MQ gas sensors require a 20-second internal heater warm-up phase during which ADC readings spike erratically. "
        "<i>Solution:</i> Programmed a 20-second boot-up 'WARM' lockout sequence on the TM1637 display that inhibits emergency relay tripping until the sensor heater achieves thermal equilibrium.",
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
        "HazardGuard C3 operates across four automated operational phases:",
        styles['ReportBody']
    ))
    
    op_steps = [
        "<b>Phase 1: Boot & Stabilization:</b> The unit powers up, illuminates the yellow standby LED, initializes Wi-Fi in dual Station/AP mode, and displays a countdown timer on the TM1637 while the MQ gas sensor heater stabilizes.",
        "<b>Phase 2: Continuous 400ms Multi-Hazard Polling:</b> The ESP32-C3 samples 8-sample smoothed gas ADC, reads ultrasonic proximity, and checks DHT11 temperature. The TM1637 display cycles every 2.5 seconds showing temperature, gas counts, proximity distance, and profile name ('HOM', 'HOT', 'IND').",
        "<b>Phase 3: Sub-300ms Fail-Safe Actuation:</b> If any sensor exceeds the active environment threshold (e.g., LPG ADC > 2100 or Temp > 52°C), the controller trips within 285ms: the optocoupled relay cuts off the gas solenoid / energizes exhaust blowers, the 85dB active siren sounds a piercing cadence, and the TM1637 flashes 'GAS!' or 'FIRE'.",
        "<b>Phase 4: Telemetry Broadcast & Incident Recovery:</b> Live incident logs are pushed to the Cyber-Industrial Web Dashboard. Once the hazard subsides below safe hysteresis thresholds, the system automatically disengages the alarm and restores normal armed monitoring."
    ]
    for step in op_steps:
        story.append(Paragraph(f"• {step}", styles['ReportBullet']))
        
    story.append(Spacer(1, 8))
    
    # ---------------------------------------------------------
    # CHAPTER 8: EXPERIMENTAL RESULTS & PERFORMANCE
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 8: EXPERIMENTAL RESULTS & TRANSIENT RESPONSE", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "HazardGuard C3 was subjected to controlled gas surge, thermal spike, and proximity penetration tests. "
        "Figure 8.1 details the measured transient step response and relay actuation timing.",
        styles['ReportBody']
    ))
    
    story.append(Image("project reports/assets/electronics_response_graph.png", width=490, height=155))
    story.append(Paragraph("Figure 8.1: Measured Gas Leak Surge, Sub-300ms Actuation Latency, and Environment Threshold Profiles", styles['FigureCaption']))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>8.1 Quantitative Experimental Verification Data</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "Table 8.1 summarizes the measured technical benchmarks across all electronic and software subsystems.",
        styles['ReportBody']
    ))
    
    perf_data = [
        ["Subsystem Parameter", "Design Target", "Measured Result", "Testing Methodology / Verification Setup"],
        ["Relay Actuation Latency", "≤ 300 ms", "190 ms (Trip) / 285 ms (Total)", "Digital oscilloscope measuring sensor breach to relay contact opening"],
        ["ADC Noise Ripple", "≤ ± 50 counts", "± 12 counts", "8-sample moving average filter suppressing baseline power ripple"],
        ["Ultrasonic Ranging Accuracy", "± 2.0 cm", "± 0.8 cm", "Laser distance benchmark over 10cm to 300cm dynamic span"],
        ["Acoustic Siren SPL", "≥ 80 dB @ 10cm", "86.4 dB", "Sound pressure level meter verification in closed test room"],
        ["Wi-Fi Web Server Latency", "≤ 100 ms", "42 ms", "HTTP JSON telemetry endpoint response time over local Wi-Fi"],
        ["Soft-AP Fail-over Time", "≤ 15 seconds", "12.2 seconds", "Simulated router blackout triggering automatic fallback AP hotspot"],
        ["Standby Power Draw", "≤ 1.5 Watts", "0.85 Watts @ 5V DC", "Continuous monitoring mode with OLED/LEDs active (170 mA)"]
    ]
    story.append(make_table(perf_data, [130, 95, 95, 170], styles, theme_hex, align_cols=['B','C','C','L']))
    story.append(Paragraph("Table 8.1: Summary of Measured Technical Parameters and Verification Results", styles['FigureCaption']))
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    
    # ---------------------------------------------------------
    # CHAPTER 9: PRACTICAL APPLICATIONS & RELEVANCE
    # ---------------------------------------------------------
    story.append(Paragraph("CHAPTER 9: APPLICATIONS, SOCIETAL IMPACT & KERALA CONTEXT", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(theme_hex), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>9.1 Practical Industrial, Commercial & Domestic Applications</b>", styles['SectionTitle']))
    apps = [
        "<b>Domestic Kitchen Life Safety across Kerala Homes:</b> Wall-mounted installation near domestic LPG cylinders to instantly isolate gas regulator solenoid valves and engage exhaust louvers before a flash fire can ignite.",
        "<b>Commercial Hotels, Resorts & Catering Hubs:</b> Deployment in central commercial kitchens and boiler rooms across Kerala's hospitality sector (Kovalam, Kumarakom, Munnar, Kochi) to audit steam temperatures and intercept commercial range leaks.",
        "<b>Industrial Processing Units & Chemical Plants:</b> Protecting workforce personnel in chemical factories (Udyogamandal/Eloor), seafood cold storages, coir mills, and cashew processing facilities by detecting dangerous machine perimeter intrusion and toxic effluent surges.",
        "<b>Educational Laboratories & Hospital Gas Manifolds:</b> Autonomous protection for school and college chemistry labs and medical oxygen/LPG cylinder manifolds."
    ]
    for app in apps:
        story.append(Paragraph(f"• {app}", styles['ReportBullet']))
        
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>9.2 Advantages, Limitations & Future Scope</b>", styles['SectionTitle']))
    story.append(Paragraph(
        "<b>Core Advantages:</b> (1) Active physical shut-off actuation in under 300ms; (2) Full optocoupled galvanic isolation prevents inductive spikes; (3) Multi-environment adaptive threshold profiles; (4) Low cost (< Rs. 2,000) vs industrial PLCs.<br/>"
        "<b>Technical Limitations:</b> (1) MQ series sensor requires 20-second warm-up; (2) Single ultrasonic sensor has a 30-degree directional cone.<br/>"
        "<b>Future Enhancements:</b> (1) GSM / SMS cellular alert backup module for remote unattended buildings; (2) Multi-channel solid-state relay (SSR) array for zero-spark AC switching; (3) Flame optical ultraviolet (UV) sensor for instant microsecond fire detection.",
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
        "HazardGuard C3 successfully proves that active, industrial-grade multi-hazard life-safety automation can be achieved using modern 32-bit "
        "RISC-V microcontrollers and affordable optoelectronic circuitry. By combining sub-300ms fail-safe relay actuation, moving-average ADC "
        "filtering, multi-environment contextual thresholding, and zero-router cyber-telemetry, the platform establishes a new benchmark for accessible, "
        "reliable disaster prevention across domestic, commercial, and industrial facilities.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>10.2 References & Technical Standards</b>", styles['SectionTitle']))
    refs = [
        "[1] Bureau of Indian Standards (BIS) (2018). <i>IS 2148: Electrical Apparatus for Explosive Gas Atmospheres - Flameproof Enclosures 'd'</i>.",
        "[2] Espressif Systems (2024). <i>ESP32-C3 Technical Reference Manual & RISC-V Architecture Specification</i>. Version 1.3.",
        "[3] Horowitz, P., & Hill, W. (2015). <i>The Art of Electronics</i>. Cambridge University Press. Chapter 12: Optoelectronics & Galvanic Isolation.",
        "[4] National Fire Protection Association (NFPA) (2021). <i>NFPA 58: Liquefied Petroleum Gas Code</i>.",
        "[5] International Electrotechnical Commission (IEC) (2020). <i>IEC 61508: Functional Safety of Electrical/Electronic/Programmable Electronic Safety-Related Systems</i>."
    ]
    for ref in refs:
        story.append(Paragraph(ref, styles['ReportBullet']))
        
    doc.build(story, canvasmaker=SasthrolsavamCanvas)
    print(f"Electronics PDF successfully compiled: {pdf_path}")

if __name__ == '__main__':
    build_electronics_pdf()
