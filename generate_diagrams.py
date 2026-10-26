import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

os.makedirs('project reports/assets', exist_ok=True)

# -------------------------------------------------------------
# 1. ROBOTICS DIAGRAMS
# -------------------------------------------------------------
def make_robotics_block_diag():
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # Color palette
    c_blue = '#1A4B82'
    c_light_blue = '#EBF3FB'
    c_teal = '#0D6E6E'
    c_light_teal = '#E6F7F7'
    c_dark = '#0F2537'
    c_accent = '#D9534F'

    # Box 1: Overhead Vision
    ax.add_patch(patches.FancyBboxPatch((0.4, 2.7), 2.5, 1.8, boxstyle="round,pad=0.1", fc=c_light_blue, ec=c_blue, lw=1.8))
    ax.text(1.65, 4.0, "OVERHEAD VISION", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(1.65, 3.5, "• 1080p 60FPS Camera\n• ArUco DICT_4X4_50\n• Sub-pixel Refinement\n• Pose (X, Y, θ)", ha='center', va='center', fontsize=7.5, color='#333333')

    # Box 2: Host Processing Station
    ax.add_patch(patches.FancyBboxPatch((3.7, 2.7), 2.6, 1.8, boxstyle="round,pad=0.1", fc=c_light_teal, ec=c_teal, lw=1.8))
    ax.text(5.0, 4.0, "HOST CONTROL STATION", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(5.0, 3.5, "• PyQt6 Interactive HUD\n• Waypoint Sequencer\n• Angular PID Controller\n• Obstacle Bias Engine", ha='center', va='center', fontsize=7.5, color='#333333')

    # Box 3: AGV Mobile Robot
    ax.add_patch(patches.FancyBboxPatch((7.1, 1.0), 2.5, 3.5, boxstyle="round,pad=0.1", fc='#FFF9E6', ec='#D48806', lw=1.8))
    ax.text(8.35, 4.0, "ESP32 AGV CHASSIS", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(8.35, 2.5, "• ESP32 240MHz SoC\n• Dual HC-SR04 Sensors\n  (Left & Right Cones)\n• L298N Motor Driver\n• Twin DC Geared Motors\n• 7.4V Li-Po & Buck Reg.\n• Fail-safe Killswitch", ha='center', va='center', fontsize=7.5, color='#333333')

    # Arrows
    # Vision -> Host
    ax.annotate("", xy=(3.7, 3.6), xytext=(2.9, 3.6),
                arrowprops=dict(arrowstyle="->", color=c_blue, lw=2.0))
    ax.text(3.3, 3.8, "Video", ha='center', va='bottom', fontsize=7.5, fontweight='bold', color=c_blue)

    # Host -> Robot (Control Packets)
    ax.annotate("", xy=(7.1, 3.6), xytext=(6.3, 3.6),
                arrowprops=dict(arrowstyle="->", color=c_teal, lw=2.0))
    ax.text(6.7, 3.85, "WiFi / ESP-NOW\nPWM Commands", ha='center', va='bottom', fontsize=7, fontweight='bold', color=c_teal)

    # Robot -> Host (Telemetry)
    ax.annotate("", xy=(6.3, 2.0), xytext=(7.1, 2.0),
                arrowprops=dict(arrowstyle="->", color=c_accent, lw=2.0))
    ax.text(6.7, 1.6, "Ultrasonic & Battery\nTelemetry (20Hz)", ha='center', va='top', fontsize=7, fontweight='bold', color=c_accent)

    # Bottom Callout / Title
    ax.text(5.0, 0.4, "Figure 1: ArUcoNav Closed-Loop Overhead Vision & Autonomous AGV Architecture", 
            ha='center', va='center', fontsize=8.5, style='italic', color='#444444')

    plt.tight_layout()
    plt.savefig('project reports/assets/robotics_block_diag.png', bbox_inches='tight')
    plt.close()

def make_robotics_flowchart():
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    c_box = '#F0F4F8'
    c_border = '#1A4B82'

    nodes = [
        (0.8, 2.5, "Acquire Camera\nFrame (60 FPS)"),
        (2.6, 2.5, "Detect ArUco & Corner\nSubpixel Refinement"),
        (4.4, 2.5, "Compute Center (X,Y)\n& Heading Angle (θ)"),
        (6.3, 2.5, "Calculate Error to Target\n& Check Ultrasonic Cones"),
        (8.2, 2.5, "PID Motor Control &\nPWM Drive via WiFi")
    ]

    for i, (x, y, text) in enumerate(nodes):
        ax.add_patch(patches.FancyBboxPatch((x-0.75, y-0.8), 1.5, 1.6, boxstyle="round,pad=0.1", fc=c_box, ec=c_border, lw=1.5))
        ax.text(x, y, text, ha='center', va='center', fontsize=7.2, fontweight='bold', color='#111111')
        if i < len(nodes) - 1:
            ax.annotate("", xy=(nodes[i+1][0]-0.75, y), xytext=(x+0.75, y),
                        arrowprops=dict(arrowstyle="->", color='#1A4B82', lw=1.8))

    # Feedback loop arrow from end back to start
    ax.annotate("", xy=(0.8, 3.4), xytext=(8.2, 3.4),
                arrowprops=dict(arrowstyle="->", color='#2A75D3', lw=1.5, connectionstyle="bar,fraction=-0.25"))
    ax.text(4.5, 4.4, "Real-Time 30Hz Closed-Loop Navigation Cycle", ha='center', va='center', fontsize=8, fontweight='bold', color='#2A75D3')

    ax.text(5.0, 0.4, "Figure 2: Computational Vision Pipeline & Closed-Loop Motion Planning Flow",
            ha='center', va='center', fontsize=8.5, style='italic', color='#444444')

    plt.tight_layout()
    plt.savefig('project reports/assets/robotics_flowchart.png', bbox_inches='tight')
    plt.close()

def make_robotics_perf_graph():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), dpi=220)

    # Plot 1: Heading Error vs Time
    t = np.linspace(0, 4, 200)
    # Step response with PID settling
    error = 65 * np.exp(-1.8 * t) * np.cos(3.2 * t)
    ax1.plot(t, error, color='#1A4B82', lw=2, label='Heading Error (deg)')
    ax1.axhline(0, color='gray', linestyle='--', lw=0.8)
    ax1.axhspan(-5, 5, color='#EBF3FB', alpha=0.8, label='Target Tolerance (±5°)')
    ax1.set_title('PID Orientation Convergence', fontsize=8.5, fontweight='bold', color='#0F2537')
    ax1.set_xlabel('Time (seconds)', fontsize=7.5)
    ax1.set_ylabel('Angular Error (°)', fontsize=7.5)
    ax1.legend(fontsize=6.5, loc='upper right')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.tick_params(labelsize=7)

    # Plot 2: Trajectory Tracking with Obstacle Avoidance
    x_nominal = np.linspace(0, 100, 100)
    y_nominal = np.zeros_like(x_nominal)
    # Deflection around obstacle at x=50, y=0
    y_actual = 25 * np.exp(-((x_nominal - 50) / 12)**2)
    ax2.plot(x_nominal, y_nominal, 'k--', lw=1.2, label='Nominal Waypoint Path')
    ax2.plot(x_nominal, y_actual, color='#0D6E6E', lw=2, label='AGV Avoidance Path')
    # Obstacle marker
    circle = plt.Circle((50, 0), 6, color='#D9534F', alpha=0.8, label='Dynamic Obstacle')
    ax2.add_patch(circle)
    ax2.set_xlim(-5, 105)
    ax2.set_ylim(-15, 35)
    ax2.set_title('Reactive Ultrasonic Deflection Trajectory', fontsize=8.5, fontweight='bold', color='#0F2537')
    ax2.set_xlabel('X Coordinate (cm)', fontsize=7.5)
    ax2.set_ylabel('Y Coordinate (cm)', fontsize=7.5)
    ax2.legend(fontsize=6.5, loc='upper right')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.tick_params(labelsize=7)

    plt.tight_layout()
    plt.savefig('project reports/assets/robotics_perf_graph.png', bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------
# 2. IOT DIAGRAMS
# -------------------------------------------------------------
def make_iot_block_diag():
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    c_teal = '#0D6E6E'
    c_light_teal = '#E6F7F7'
    c_orange = '#D48806'
    c_dark = '#0A3641'

    # SENSORS
    ax.add_patch(patches.FancyBboxPatch((0.4, 0.8), 2.5, 3.6, boxstyle="round,pad=0.1", fc=c_light_teal, ec=c_teal, lw=1.8))
    ax.text(1.65, 4.0, "FISH HOLD SENSORS", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(1.65, 2.4, "• MQ-135 Gas Sensor\n  (Ammonia, TMA, TVB-N)\n• MQ-4 Gas Sensor\n  (Methane Anaerobic Gas)\n• DHT11 Probe\n  (Hold Temp & Humidity)\n• Waterproof Ultrasonic\n  (Meltwater Level in Sump)", ha='center', va='center', fontsize=7.2, color='#222222')

    # NODEMCU CONTROLLER
    ax.add_patch(patches.FancyBboxPatch((3.7, 1.2), 2.6, 3.0, boxstyle="round,pad=0.1", fc='#F3F9FF', ec='#1A4B82', lw=1.8))
    ax.text(5.0, 3.8, "NODEMCU ESP8266 SoC", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(5.0, 2.5, "• 80MHz Tensilica L106\n• 10-bit ADC Processing\n• Rolling Median Filter\n• Freshness Scoring Engine\n• Drain Clog Classifier\n• Wi-Fi AP & Web Server", ha='center', va='center', fontsize=7.2, color='#222222')

    # OUTPUTS & INDICATORS
    ax.add_patch(patches.FancyBboxPatch((7.1, 0.8), 2.5, 3.6, boxstyle="round,pad=0.1", fc='#FFF9E6', ec=c_orange, lw=1.8))
    ax.text(8.35, 4.0, "OUTPUT & TELEMETRY", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(8.35, 2.4, "• SSD1306 128x64 OLED\n  (4-Screen GUI Dashboard)\n• TM1637 4-Digit 7-Seg\n  (High-Visibility Sunlight)\n• High-Pitch Audio Siren\n  (Deck Spoilage Warning)\n• Local Web Dashboard\n  (Live Real-Time Telemetry)", ha='center', va='center', fontsize=7.2, color='#222222')

    # Connectors
    ax.annotate("", xy=(3.7, 2.7), xytext=(2.9, 2.7),
                arrowprops=dict(arrowstyle="->", color=c_teal, lw=2.0))
    ax.text(3.3, 2.9, "Raw ADC &\nDigital Data", ha='center', va='bottom', fontsize=7, fontweight='bold', color=c_teal)

    ax.annotate("", xy=(7.1, 2.7), xytext=(6.3, 2.7),
                arrowprops=dict(arrowstyle="->", color=c_orange, lw=2.0))
    ax.text(6.7, 2.9, "I2C, GPIO &\nHTTP Stream", ha='center', va='bottom', fontsize=7, fontweight='bold', color=c_orange)

    ax.text(5.0, 0.4, "Figure 1: Marine Catch Quality, Cold Chain & Drainage Sump IoT Supervisor Architecture",
            ha='center', va='center', fontsize=8.5, style='italic', color='#444444')

    plt.tight_layout()
    plt.savefig('project reports/assets/iot_block_diag.png', bbox_inches='tight')
    plt.close()

def make_iot_flowchart():
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    c_box = '#EBF7F7'
    c_border = '#0D6E6E'

    steps = [
        (0.8, 2.5, "Sensor Acquisition:\nGas, Temp, Depth"),
        (2.6, 2.5, "Rolling Median Filter\n& Signal Validation"),
        (4.4, 2.5, "Threshold Evaluation:\nTemp > 4°C? Gas Spike?\nWater > 2.0 cm?"),
        (6.3, 2.5, "Freshness Index Calc:\nGrade A (Fresh) ->\nGrade D (Spoiled)"),
        (8.2, 2.5, "Actuate Siren, Update\nOLED, 7-Seg & Web")
    ]

    for i, (x, y, text) in enumerate(steps):
        ax.add_patch(patches.FancyBboxPatch((x-0.75, y-0.8), 1.5, 1.6, boxstyle="round,pad=0.1", fc=c_box, ec=c_border, lw=1.5))
        ax.text(x, y, text, ha='center', va='center', fontsize=7.0, fontweight='bold', color='#111111')
        if i < len(steps) - 1:
            ax.annotate("", xy=(steps[i+1][0]-0.75, y), xytext=(x+0.75, y),
                        arrowprops=dict(arrowstyle="->", color=c_border, lw=1.8))

    ax.annotate("", xy=(0.8, 3.4), xytext=(8.2, 3.4),
                arrowprops=dict(arrowstyle="->", color='#149B9B', lw=1.5, connectionstyle="bar,fraction=-0.25"))
    ax.text(4.5, 4.4, "Continuous 1.5-Second Marine Surveillance Loop", ha='center', va='center', fontsize=8, fontweight='bold', color='#0D6E6E')

    ax.text(5.0, 0.4, "Figure 2: Cold-Chain Verification and Multi-Parameter Freshness Logic Flow",
            ha='center', va='center', fontsize=8.5, style='italic', color='#444444')

    plt.tight_layout()
    plt.savefig('project reports/assets/iot_flowchart.png', bbox_inches='tight')
    plt.close()

def make_iot_spoilage_graph():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), dpi=220)

    hours = np.linspace(0, 72, 150)
    # Simulated fish storage: Good ice until hr 36, then melting and spoilage
    temp = 1.5 + 0.05 * hours + 3.0 / (1 + np.exp(-(hours - 40) / 6))
    gas_adc = 180 + 30 * np.exp(hours / 35) + np.random.normal(0, 4, len(hours))
    water_level = np.clip(0.8 + 0.03 * hours + 4.5 / (1 + np.exp(-(hours - 48) / 4)), 0, 8)

    ax1.plot(hours, temp, color='#1A4B82', lw=2, label='Hold Temp (°C)')
    ax1.axhline(4.0, color='red', linestyle='--', lw=1, label='Max Chilled Limit (4°C)')
    ax1.plot(hours, water_level, color='#0D6E6E', lw=2, label='Meltwater Depth (cm)')
    ax1.axhline(5.0, color='orange', linestyle=':', lw=1, label='Clog Hazard (5cm)')
    ax1.set_title('Storage Temp & Drainage Dynamics', fontsize=8.5, fontweight='bold', color='#0A3641')
    ax1.set_xlabel('Storage Duration (Hours)', fontsize=7.5)
    ax1.set_ylabel('Temp (°C) / Depth (cm)', fontsize=7.5)
    ax1.legend(fontsize=6.5, loc='upper left')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.tick_params(labelsize=7)

    # Plot 2: Volatile Amine / Spoilage Gas ADC
    ax2.plot(hours, gas_adc, color='#C84B31', lw=2, label='MQ-135 Spoilage Gas ADC')
    ax2.axhline(350, color='goldenrod', linestyle='--', lw=1, label='Early Warning (350 ADC)')
    ax2.axhline(580, color='darkred', linestyle='--', lw=1, label='Spoiled Threshold (580 ADC)')
    ax2.set_title('Volatile Amine (TMA/NH3) Accumulation', fontsize=8.5, fontweight='bold', color='#0A3641')
    ax2.set_xlabel('Storage Duration (Hours)', fontsize=7.5)
    ax2.set_ylabel('Raw Sensor ADC (0-1023)', fontsize=7.5)
    ax2.legend(fontsize=6.5, loc='upper left')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.tick_params(labelsize=7)

    plt.tight_layout()
    plt.savefig('project reports/assets/iot_spoilage_graph.png', bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------
# 3. ELECTRONICS DIAGRAMS
# -------------------------------------------------------------
def make_electronics_block_diag():
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    c_dark = '#212529'
    c_red = '#C84B31'
    c_light_red = '#FDF5F2'
    c_blue = '#1A4B82'

    # SENSING FRONT END
    ax.add_patch(patches.FancyBboxPatch((0.4, 0.8), 2.5, 3.6, boxstyle="round,pad=0.1", fc=c_light_red, ec=c_red, lw=1.8))
    ax.text(1.65, 4.0, "MULTI-HAZARD SENSORS", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(1.65, 2.4, "• Gas/Smoke Sensor\n  (Analog ADC1_CH1 / G1)\n• DHT11 Thermal Sensor\n  (Digital Fire Mon. / G6)\n• HC-SR04 Proximity Radar\n  (Intrusion & Overflow / G4,5)\n• 1k:2k Echo Voltage Divider\n  (5V to 3.3V GPIO Protect)", ha='center', va='center', fontsize=7.2, color='#222222')

    # ESP32-C3 CONTROLLER
    ax.add_patch(patches.FancyBboxPatch((3.7, 1.2), 2.6, 3.0, boxstyle="round,pad=0.1", fc='#F3F9FF', ec=c_blue, lw=1.8))
    ax.text(5.0, 3.8, "ESP32-C3 RISC-V SoC", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(5.0, 2.5, "• 160MHz 32-bit RISC-V\n• Moving-Average ADC Filter\n• Multi-Zone Threshold Logic\n  (Home / Hotel / Factory)\n• <300ms Fail-Safe Cutoff\n• Built-in Wi-Fi & AP Server", ha='center', va='center', fontsize=7.2, color='#222222')

    # ACTIVE ACTUATION & UI
    ax.add_patch(patches.FancyBboxPatch((7.1, 0.8), 2.5, 3.6, boxstyle="round,pad=0.1", fc='#F5F5F5', ec='#333333', lw=1.8))
    ax.text(8.35, 4.0, "ACTUATION & SAFETY", ha='center', va='center', fontsize=9, fontweight='bold', color=c_dark)
    ax.text(8.35, 2.4, "• Optocoupled 10A Relay\n  (Isolates Solenoid/Exhaust)\n• High-Output Piezo Siren\n  (Multi-Frequency Warning)\n• TM1637 4-Digit Display\n  (Metric Multiplexing)\n• Cyber Web Dashboard\n  (Zero-router Control)", ha='center', va='center', fontsize=7.2, color='#222222')

    # Connectors
    ax.annotate("", xy=(3.7, 2.7), xytext=(2.9, 2.7),
                arrowprops=dict(arrowstyle="->", color=c_red, lw=2.0))
    ax.text(3.3, 2.9, "Analog &\nDigital Signals", ha='center', va='bottom', fontsize=7, fontweight='bold', color=c_red)

    ax.annotate("", xy=(7.1, 2.7), xytext=(6.3, 2.7),
                arrowprops=dict(arrowstyle="->", color=c_dark, lw=2.0))
    ax.text(6.7, 2.9, "Opto-Tripped\nControl Pulse", ha='center', va='bottom', fontsize=7, fontweight='bold', color=c_dark)

    ax.text(5.0, 0.4, "Figure 1: HazardGuard C3 Fail-Safe Industrial & Domestic Emergency Supervisor",
            ha='center', va='center', fontsize=8.5, style='italic', color='#444444')

    plt.tight_layout()
    plt.savefig('project reports/assets/electronics_block_diag.png', bbox_inches='tight')
    plt.close()

def make_electronics_flowchart():
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=220)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    c_box = '#FDF5F2'
    c_border = '#C84B31'

    steps = [
        (0.8, 2.5, "Acquire 8-Sample\nADC & Echo Distance"),
        (2.6, 2.5, "Compare with Active\nProfile Thresholds"),
        (4.4, 2.5, "Evaluate Fault Hazard:\nGas? Heat? Intrusion?\nOverflow?"),
        (6.3, 2.5, "Sub-300ms Safety Trip:\nEnergize Relay &\nSound 85dB Siren"),
        (8.2, 2.5, "Serve Incident Log to\nWeb & Display TM Code")
    ]

    for i, (x, y, text) in enumerate(steps):
        ax.add_patch(patches.FancyBboxPatch((x-0.75, y-0.8), 1.5, 1.6, boxstyle="round,pad=0.1", fc=c_box, ec=c_border, lw=1.5))
        ax.text(x, y, text, ha='center', va='center', fontsize=7.0, fontweight='bold', color='#111111')
        if i < len(steps) - 1:
            ax.annotate("", xy=(steps[i+1][0]-0.75, y), xytext=(x+0.75, y),
                        arrowprops=dict(arrowstyle="->", color=c_border, lw=1.8))

    ax.annotate("", xy=(0.8, 3.4), xytext=(8.2, 3.4),
                arrowprops=dict(arrowstyle="->", color='#D9534F', lw=1.5, connectionstyle="bar,fraction=-0.25"))
    ax.text(4.5, 4.4, "Rapid 400ms Autonomous Safety Polling Engine", ha='center', va='center', fontsize=8, fontweight='bold', color='#C84B31')

    ax.text(5.0, 0.4, "Figure 2: Multi-Hazard Interception Logic & Emergency Actuation Flow",
            ha='center', va='center', fontsize=8.5, style='italic', color='#444444')

    plt.tight_layout()
    plt.savefig('project reports/assets/electronics_flowchart.png', bbox_inches='tight')
    plt.close()

def make_electronics_response_graph():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), dpi=220)

    # Plot 1: Gas concentration step response & Relay Trip Time
    t_ms = np.linspace(0, 1000, 250)
    # Gas leak step at t=200ms
    gas_val = 600 + 2600 / (1 + np.exp(-(t_ms - 320) / 40))
    relay_state = np.where(t_ms >= 510, 0, 1) # Active LOW relay trips at 510ms (190ms after threshold breach)

    ax1.plot(t_ms, gas_val, color='#C84B31', lw=2, label='Filtered Gas ADC')
    ax1.axhline(2100, color='darkorange', linestyle='--', lw=1.2, label='Alarm Threshold (2100 ADC)')
    ax1.axvline(320, color='gray', linestyle=':', lw=1)
    ax1.axvline(510, color='red', linestyle=':', lw=1)
    ax1.annotate('Threshold\nBreach', xy=(320, 2100), xytext=(220, 2700),
                 arrowprops=dict(arrowstyle='->', color='black', lw=1), fontsize=6.5, fontweight='bold')
    ax1.annotate('Relay Cutoff\n(Δt=190ms)', xy=(510, 2100), xytext=(540, 2700),
                 arrowprops=dict(arrowstyle='->', color='red', lw=1), fontsize=6.5, fontweight='bold')
    ax1.set_title('Gas Leak Surge & Actuation Latency', fontsize=8.5, fontweight='bold', color='#212529')
    ax1.set_xlabel('Time (milliseconds)', fontsize=7.5)
    ax1.set_ylabel('12-bit ADC Value (0-4095)', fontsize=7.5)
    ax1.legend(fontsize=6.5, loc='lower right')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.tick_params(labelsize=7)

    # Plot 2: Multi-Zone Sensitivity Thresholds
    categories = ['Household', 'Hotel Commercial', 'Industrial Plant']
    gas_thresholds = [2100, 1800, 1500]
    temp_thresholds = [52.0, 48.0, 60.0]
    x = np.arange(len(categories))
    width = 0.35

    ax2.bar(x - width/2, gas_thresholds, width, label='Gas Alarm ADC', color='#D9534F')
    ax2_twin = ax2.twinx()
    ax2_twin.bar(x + width/2, temp_thresholds, width, label='Temp Alarm (°C)', color='#1A4B82')

    ax2.set_ylabel('Gas ADC Limit', fontsize=7.5, color='#D9534F')
    ax2_twin.set_ylabel('Temp Limit (°C)', fontsize=7.5, color='#1A4B82')
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, fontsize=7)
    ax2.set_title('Environment Calibration Profiles', fontsize=8.5, fontweight='bold', color='#212529')
    ax2.grid(True, linestyle=':', alpha=0.4, axis='y')
    ax2.tick_params(labelsize=7)
    ax2_twin.tick_params(labelsize=7)

    plt.tight_layout()
    plt.savefig('project reports/assets/electronics_response_graph.png', bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    print("Generating technical diagrams...")
    make_robotics_block_diag()
    make_robotics_flowchart()
    make_robotics_perf_graph()
    make_iot_block_diag()
    make_iot_flowchart()
    make_iot_spoilage_graph()
    make_electronics_block_diag()
    make_electronics_flowchart()
    make_electronics_response_graph()
    print("All 9 diagrams generated successfully in project reports/assets/")
