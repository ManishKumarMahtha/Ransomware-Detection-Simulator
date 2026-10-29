"""
Script to generate the comprehensive Faculty Presentation & Viva Guide PDF
using ReportLab.
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas that adds running header and 'Page X of Y' footer."""
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Ransomware Detection Simulator — Faculty Presentation & Viva Guide")
            self.drawRightString(558, 755, "CSE AI/ML Major Project")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 35, page_text)
        self.drawString(54, 35, "CONFIDENTIAL — Academic Evaluation & Defense Guide")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 47, 558, 47)

        self.restoreState()


def create_presentation_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f172a")    # Slate dark
    accent_blue = colors.HexColor("#0284c7")      # Cyan/Blue
    accent_green = colors.HexColor("#059669")     # Emerald
    accent_red = colors.HexColor("#dc2626")       # Red
    body_text_color = colors.HexColor("#1e293b")  # Dark slate text

    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=accent_blue,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=accent_blue,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=body_text_color,
        spaceAfter=6
    )

    script_speech_style = ParagraphStyle(
        'ScriptSpeech',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e3a8a"),
        backColor=colors.HexColor("#eff6ff"),
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f8fafc"),
        borderPadding=4,
        spaceBefore=3,
        spaceAfter=5
    )

    story = []

    # =========================================================================
    # HEADER / TITLE BLOCK
    # =========================================================================
    story.append(Paragraph("RANSOMWARE DETECTION SIMULATOR", title_style))
    story.append(Paragraph("Faculty Presentation & Viva Defense Master Guide — B.Tech CSE (AI/ML) Major Project", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=accent_blue, spaceBefore=0, spaceAfter=12))

    # Meta Info Card
    meta_data = [
        [
            Paragraph("<b>Candidate Degree:</b> B.Tech CSE (AI/ML)", body_style),
            Paragraph("<b>Academic Track:</b> Defensive Cybersecurity & EDR", body_style)
        ],
        [
            Paragraph("<b>Application:</b> Web-based SOC Simulator", body_style),
            Paragraph("<b>Core Stack:</b> Python, Flask, Watchdog, Scikit-learn, SQLite", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[240, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 1: THE 60-SECOND ELEVATOR PITCH
    # =========================================================================
    story.append(Paragraph("1. The 60-Second Opening Pitch (What to Say First)", h1_style))
    story.append(Paragraph(
        "When your faculty asks <i>'Introduce your project and explain what problem it solves,'</i> deliver this exact pitch with confidence:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Exact Script to Speak:</b><br/>"
        "&ldquo;Respected faculty members, my major project is the <b>Ransomware Detection Simulator</b>. "
        "Traditional antivirus software relies on static file signatures — such as MD5 or SHA-256 hashes. "
        "However, modern cyber adversaries easily defeat signature detection by recompiling their payloads, using polymorphic crypters, "
        "or launching zero-day ransomware where no signature exists.<br/><br/>"
        "To solve this problem, my project implements <b>real-time behavioral anomaly detection</b> — the technology powering modern "
        "Next-Generation Antivirus (NGAV) and Endpoint Detection & Response (EDR) systems. "
        "The system monitors operating system file activity using Python Watchdog, tracks event velocity inside a sliding time window, "
        "detects rapid file-renaming and ransomware extension changes (such as .locked or .crypto), and computes a transparent, explainable "
        "threat score from 0 to 100.<br/><br/>"
        "Furthermore, it couples rule-based heuristics with a <b>Scikit-Learn Random Forest machine learning classifier</b> to evaluate behavioral telemetry, "
        "and demonstrates automated defensive containment in a completely safe, sandbox-isolated environment without endangering host system files.&rdquo;",
        script_speech_style
    ))

    # =========================================================================
    # SECTION 2: SYSTEM ARCHITECTURE & CORE MODULES
    # =========================================================================
    story.append(Paragraph("2. System Architecture & Component Breakdown", h1_style))
    story.append(Paragraph(
        "When your teacher asks how the system is designed under the hood, break it down into these 5 clear modular layers:",
        body_style
    ))

    arch_data = [
        [Paragraph("<b>Component Layer</b>", body_style), Paragraph("<b>Key Technologies</b>", body_style), Paragraph("<b>Engineering Responsibility</b>", body_style)],
        [
            Paragraph("<b>1. Presentation / SOC Dashboard</b>", body_style),
            Paragraph("HTML5, Bootstrap 5, Chart.js 4.4, JavaScript ES6", body_style),
            Paragraph("Renders dark-themed SOC UI, live KPI cards, timeline charts, incident tables, and speed sliders.", body_style)
        ],
        [
            Paragraph("<b>2. Backend Web Server</b>", body_style),
            Paragraph("Python, Flask 3.1, REST APIs", body_style),
            Paragraph("Coordinates session authentication, state machine controls, telemetry polling, and CSV export.", body_style)
        ],
        [
            Paragraph("<b>3. Safe Simulation Engine</b>", body_style),
            Paragraph("Thread state machine, Synthetic payloads", body_style),
            Paragraph("Executes harmless dummy file operations inside isolated <code>demo_data/sandbox/</code> with path traversal guards.", body_style)
        ],
        [
            Paragraph("<b>4. Detection & Scoring Pipeline</b>", body_style),
            Paragraph("Sliding Window, Heuristic Rules, Random Forest", body_style),
            Paragraph("Maintains a sliding deque of events, computes velocity, calculates explainable threat score, triggers alerts.", body_style)
        ],
        [
            Paragraph("<b>5. Persistence & Forensics</b>", body_style),
            Paragraph("SQLite 3 (PRAGMA foreign_keys)", body_style),
            Paragraph("Stores raw security events, persistent security incidents, audit logs, and dynamic detection thresholds.", body_style)
        ]
    ]
    arch_table = Table(arch_data, colWidths=[130, 130, 240])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(arch_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 3: STEP-BY-STEP LIVE DEMO SCRIPT
    # =========================================================================
    story.append(Paragraph("3. Step-by-Step Live Demonstration Walkthrough", h1_style))
    story.append(Paragraph(
        "Follow this exact sequence on your laptop during the faculty demonstration to ensure a smooth, professional presentation:",
        body_style
    ))

    steps_data = [
        ("Step 1: Login & Accessing the SOC",
         "Launch <code>http://127.0.0.1:5000</code> in your browser.<br/>"
         "Click the convenient <b>Admin (Lead SOC)</b> 1-click button on the login screen.<br/>"
         "<b>Say:</b> <i>'We authenticate into the security operations center. The platform supports role-based access for Lead SOC Administrators and Security Analysts.'</i>"),

        ("Step 2: Tour the SOC Dashboard",
         "Point to the 4 KPI cards (Sandbox Files, Safe Operations, Suspicious Events, Threats Detected).<br/>"
         "Show the live <b>Threat Timeline</b> (Chart.js) and <b>Threat Severity Doughnut</b>.<br/>"
         "<b>Say:</b> <i>'This dashboard gives security analysts instant situational awareness. Currently, the environment is at a benign baseline.'</i>"),

        ("Step 3: Run Benign Simulation (Negative Test / Baseline)",
         "Click <b>Simulation Engine</b> in the sidebar. Select <b>Benign User Activity</b> and click <b>Start</b>.<br/>"
         "Watch the live terminal feed and sandbox file list create dummy files (<code>annual_budget.xlsx.txt</code>, <code>research_paper.docx.txt</code>).<br/>"
         "<b>Say:</b> <i>'Here we simulate normal human activity: slow typing, standard edits, and safe renaming. Notice that the threat score remains in the Low tier (under 30), and zero false alerts are generated.'</i>"),

        ("Step 4: Run Ransomware Burst Attack (Positive Test / Anomaly)",
         "On the Simulation page, select <b>Ransomware Burst Attack</b> and click <b>Start</b>.<br/>"
         "Observe the rapid overwriting of dummy files with simulated cipher text, batch renaming to <code>.locked</code>, and the dropping of a simulated ransom note (<code>README_RESTORE_FILES_DEMO.txt</code>).<br/>"
         "Switch to the Dashboard: Point out the red <b>CRITICAL THREAT DETECTED</b> banner that instantly appears.<br/>"
         "<b>Say:</b> <i>'When an automated encryption burst occurs, our sliding window detects high velocity and extension tampering. The threat score spikes to 89/100 (Critical), and our automated defense suspended the process to prevent further spread.'</i>"),

        ("Step 5: Explain the Mathematical Attribution",
         "Click <b>Incident History</b>, then click <b>Details</b> on the top incident.<br/>"
         "Show the faculty the exact mathematical formula string and the Scikit-learn feature vector modal.<br/>"
         "<b>Say:</b> <i>'Our system is completely explainable. Rather than a black-box decision, the modal displays the exact point breakdown: 14 points from rename rate, 40 points from extension tampering, 25 points from modification bursts, and 10 points from event velocity.'</i>"),

        ("Step 6: Show File Monitoring & Safety Bounds",
         "Click <b>File Monitoring</b>. Try entering <code>C:\\Windows</code> and show that the path validator immediately blocks it.<br/>"
         "Click <b>Sandbox</b> and click <b>Start Monitoring</b> to stream live OS Watchdog events.<br/>"
         "<b>Say:</b> <i>'Our watchdog observer captures live operating system I/O events without ever reading private file contents, ensuring zero host overhead and total privacy.'</i>"),

        ("Step 7: Download CSV Forensic Report",
         "Go to <b>Reports & Export</b> and click <b>Download Incidents CSV</b>.<br/>"
         "<b>Say:</b> <i>'Finally, our platform exports comprehensive audit telemetry conforming to NIST SP 800-61 incident response guidelines for forensic analysis.'</i>")
    ]

    for title, desc in steps_data:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(desc, body_style))
        story.append(Spacer(1, 3))

    # =========================================================================
    # SECTION 4: THE MATHEMATICAL THREAT SCORING FORMULA
    # =========================================================================
    story.append(Paragraph("4. The Threat Scoring Mathematical Formulation", h1_style))
    story.append(Paragraph(
        "Faculty love mathematical formulas. Explain this transparent calculation clearly:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Score Formula:</b><br/>"
        "<code>Score = min(100, S_rename + S_extension + S_burst + S_velocity + S_ml)</code>",
        code_style
    ))

    formula_table_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Max Weight</b>", body_style), Paragraph("<b>Mathematical Formulation</b>", body_style), Paragraph("<b>Detection Focus</b>", body_style)],
        [
            Paragraph("<b>Rename Score (S_rename)</b>", body_style),
            Paragraph("35 pts", body_style),
            Paragraph("<code>min(35.0, (N_renames / Threshold_rename) &times; 35.0)</code>", body_style),
            Paragraph("Detects mass automated file renaming within the sliding time window.", body_style)
        ],
        [
            Paragraph("<b>Extension Score (S_ext)</b>", body_style),
            Paragraph("40 pts", body_style),
            Paragraph("<code>0.7 &times; W_ext (1 ext) or 1.0 &times; W_ext (&ge;2 exts)</code>", body_style),
            Paragraph("Detects known ransomware extensions (<code>.locked, .crypto, .enc, .wnry</code>).", body_style)
        ],
        [
            Paragraph("<b>Burst Score (S_burst)</b>", body_style),
            Paragraph("25 pts", body_style),
            Paragraph("<code>min(25.0, (N_mods / Threshold_mod) &times; 25.0)</code>", body_style),
            Paragraph("Detects rapid overwriting of file content (in-place cipher writes).", body_style)
        ],
        [
            Paragraph("<b>Velocity Bonus (S_velocity)</b>", body_style),
            Paragraph("10 pts", body_style),
            Paragraph("<code>min(10.0, (Velocity / Threshold_velocity) &times; 10.0)</code>", body_style),
            Paragraph("Rewards high operations-per-second exceeding human baseline.", body_style)
        ],
        [
            Paragraph("<b>ML Bonus (S_ml)</b>", body_style),
            Paragraph("15 pts", body_style),
            Paragraph("<code>+15 if Random Forest confidence &ge; 75% on borderline cases</code>", body_style),
            Paragraph("AI-driven confirmation for ambiguous behavioral signals.", body_style)
        ]
    ]
    f_table = Table(formula_table_data, colWidths=[110, 60, 180, 150])
    f_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(f_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 5: MACHINE LEARNING MODULE EXPLANATION
    # =========================================================================
    story.append(Paragraph("5. AI/Machine Learning Integration (Scikit-Learn)", h1_style))
    story.append(Paragraph(
        "For your AI/ML major project specialization, highlight these key technical points:",
        body_style
    ))
    story.append(Paragraph(
        "&bull; <b>Model Architecture:</b> Supervised <code>RandomForestClassifier(n_estimators=40, max_depth=6, class_weight='balanced')</code>.<br/>"
        "&bull; <b>Feature Vector:</b> 5 extracted behavioral features:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;1. <code>events_per_sec</code>: Instantaneous I/O velocity.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;2. <code>rename_rate</code>: Renaming operations per second.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;3. <code>ext_change_ratio</code>: Proportion of file operations targeting suspicious extensions.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;4. <code>mod_burst_rate</code>: Rapid write modifications per second.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;5. <code>unique_ext_count</code>: Diversity of file extensions impacted.<br/>"
        "&bull; <b>Explainability & Feature Importance:</b> Feature importance weights are calculated via Gini impurity reduction and rendered in real time on the Settings page.<br/>"
        "&bull; <b>Academic Honesty Note:</b> Clearly state that the model is trained on 1,500 synthetic behavioral vectors for safe educational demonstration, proving the methodology without requiring live malware detonation.",
        body_style
    ))

    # =========================================================================
    # SECTION 6: SAFETY ASSURANCE (WHY IT'S SAFE FOR COLLEGE COMPUTERS)
    # =========================================================================
    story.append(Paragraph("6. Safety Guarantees (Addressing Faculty Safety Concerns)", h1_style))
    story.append(Paragraph(
        "Teachers often ask: <i>'Is this safe to run on university computers? Will it harm my files?'</i> Answer with these 4 safety guarantees:",
        body_style
    ))
    safety_points = [
        ("Strict Sandbox Confinement", "All file operations are programmatically locked to <code>demo_data/sandbox/</code> via <code>is_safe_sandbox_path()</code>. Path traversal (<code>../</code>) is strictly blocked."),
        ("Harmless Dummy Files", "Only harmless synthetic text files (e.g. <code>annual_budget.xlsx.txt</code>) are created. No real encryption ciphers or OS-locking code is executed."),
        ("No Antivirus Interference", "Windows Defender, corporate antivirus, firewall rules, and volume shadow copies (VSS) are never disabled."),
        ("Zero Private Content Inspection", "Python Watchdog inspects only file event metadata (file name and operation type); file contents are never read, preserving privacy and performance.")
    ]
    for sp_title, sp_desc in safety_points:
        story.append(Paragraph(f"<b>&bull; {sp_title}:</b> {sp_desc}", body_style))

    # =========================================================================
    # SECTION 7: TOP 10 TOUGH VIVA QUESTIONS & ANSWERS
    # =========================================================================
    story.append(Paragraph("7. Top 10 Tough Viva Questions & Perfect Model Answers", h1_style))

    viva_qa = [
        ("Q1: What is the fundamental difference between signature detection and behavioral detection?",
         "Signature detection matches known file hashes (like MD5 or SHA-256) against a static database. It fails against polymorphic malware and zero-day threats where no signature exists. Behavioral detection monitors what the software actually *does* at runtime (rapid renaming, high I/O velocity, extension tampering), allowing us to stop brand-new ransomware variants before they complete encryption."),

        ("Q2: How does the sliding time window prevent false positives from everyday user activity?",
         "Everyday user actions (saving a Word document, renaming a spreadsheet) occur at human speeds (1 event every several seconds). Our sliding window evaluates instantaneous velocity over a 5-second window. Unless a process executes multiple renames and modifications per second, the threat score remains strictly in the Low tier (< 30)."),

        ("Q3: What happens if ransomware encrypts files slowly to evade the rate threshold (Stealth Ransomware)?",
         "This is known as a 'low-and-slow' evasion attack. Our simulator includes a dedicated 'Slow Stealth Simulation' profile. Even if the velocity is low, our multi-factor scoring evaluates extension tampering independently. A single file renamed to a known ransomware extension immediately contributes 28 to 40 points, elevating the incident to Medium or High severity regardless of slow velocity."),

        ("Q4: Why did you use Random Forest instead of a Deep Neural Network?",
         "For behavioral telemetry with tabular feature vectors (velocity, rename rate, extension ratios), Random Forest offers superior explainability, requires negligible inference latency (< 5ms), avoids overfitting on small datasets, and provides transparent feature importances via Gini impurity. In cybersecurity EDRs, explainability is essential for SOC analysts to understand why an alert fired."),

        ("Q5: What is the difference between Crypto Ransomware and Locker Ransomware?",
         "Crypto ransomware silently searches for valuable personal or business files (documents, images, databases) and encrypts their contents using strong hybrid ciphers (e.g. AES-256 + RSA-4096), demanding payment for the private key. Locker ransomware locks the user interface or boots into a fake lockscreen without necessarily encrypting files on disk."),

        ("Q6: How does our automated mitigation mechanism respond to an attack?",
         "When an incident reaches a Critical threat score (&ge; 80), our detection coordinator triggers an automated response hook. In this simulation, it automatically suspends the active simulation thread. In an enterprise EDR, this corresponds to terminating the suspicious process tree via API (such as <code>TerminateProcess</code>) and isolating the network interface."),

        ("Q7: How does Watchdog monitor file activity without reading file contents?",
         "Python Watchdog hooks into native operating system APIs — specifically the <code>ReadDirectoryChangesW</code> API on Windows and <code>inotify</code> on Linux. The OS kernel notifies Watchdog of file system events (created, modified, deleted, moved) as lightweight metadata notifications. This ensures zero performance degradation and total user privacy."),

        ("Q8: What is the 3-2-1 backup strategy in ransomware defense?",
         "3 copies of critical organizational data, stored across 2 different storage media types (e.g., local NVMe drive and magnetic tape/NAS), with at least 1 copy stored off-site, air-gapped, or in an immutable cloud bucket (WORM - Write Once, Read Many). Even if ransomware encrypts the entire local network, immutable backups guarantee complete recovery without paying a ransom."),

        ("Q9: Can an attacker bypass this system by keeping the original file extension?",
         "Some advanced ransomware strains encrypt files in-place without altering the file extension to evade extension-based rules. Our system defends against this through our Burst Modification Rate rule ($S_{burst}$), which flags rapid overwrites of multiple files within seconds even if extensions remain unchanged."),

        ("Q10: What are the main limitations and future scope of this project?",
         "Current limitations: As a user-space Python application, it monitors directory events rather than intercepting kernel I/O requests before they hit the disk. Future scope includes developing a Windows File System Minifilter Driver (kernel-level) to block write operations synchronously, integrating Shannon entropy calculation to detect encrypted blocks before renaming, and mapping detection alerts to the MITRE ATT&CK framework.")
    ]

    for q, a in viva_qa:
        story.append(Paragraph(f"<b>{q}</b>", h2_style))
        story.append(Paragraph(f"<b>Model Answer:</b> {a}", body_style))
        story.append(Spacer(1, 4))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {output_path}")


if __name__ == "__main__":
    out = Path("Ransomware_Detection_Simulator_Faculty_Presentation_Guide.pdf").resolve()
    create_presentation_pdf(str(out))
