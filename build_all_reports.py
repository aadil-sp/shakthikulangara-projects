#!/usr/bin/env python3
"""
Master Builder: Regenerates all diagrams and compiles all three Kerala Sasthrolsavam
Project Reports (Robotics, IoT, Electronics) into high-resolution, anonymous PDFs.
"""

import sys
import subprocess

def main():
    print("=" * 70)
    print("KERALA SASTHROLSAVAM PROJECT REPORT BUILDER")
    print("=" * 70)
    
    print("\n[1/4] Generating High-Resolution Technical Diagrams...")
    import generate_diagrams
    generate_diagrams.make_robotics_block_diag()
    generate_diagrams.make_robotics_flowchart()
    generate_diagrams.make_robotics_perf_graph()
    generate_diagrams.make_iot_block_diag()
    generate_diagrams.make_iot_flowchart()
    generate_diagrams.make_iot_spoilage_graph()
    generate_diagrams.make_electronics_block_diag()
    generate_diagrams.make_electronics_flowchart()
    generate_diagrams.make_electronics_response_graph()
    print("Diagrams successfully generated in 'project reports/assets/'.")

    print("\n[2/4] Compiling Category: Robotics...")
    import generate_robotics_report
    generate_robotics_report.build_robotics_pdf()

    print("\n[3/4] Compiling Category: Internet of Things (IoT)...")
    import generate_iot_report
    generate_iot_report.build_iot_pdf()

    print("\n[4/4] Compiling Category: Electronics & Hardware...")
    import generate_electronics_report
    generate_electronics_report.build_electronics_pdf()

    print("\n" + "=" * 70)
    print("ALL 3 PROJECT REPORTS COMPILED SUCCESSFULLY!")
    print("Outputs located in './project reports/':")
    print("  1. Robotics_Sasthrolsavam_Project_Report.pdf")
    print("  2. IoT_Sasthrolsavam_Project_Report.pdf")
    print("  3. Electronics_Sasthrolsavam_Project_Report.pdf")
    print("=" * 70)

if __name__ == '__main__':
    main()
