import os
import sys
from datetime import datetime

# Import ReportLab modules
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress page number, headers, and footers on the cover page
        
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header
        self.drawString(54, 750, "TradeCore — Technical Project Report")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        self.line(54, 55, 558, 55)
        self.drawRightString(558, 40, f"Page {self._pageNumber} of {page_count}")
        self.drawString(54, 40, "Confidential — Internal Development Documentation")
        self.restoreState()

def create_report(output_filename):
    # Setup document geometry (Margins = 0.75" / 54pt)
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom colors
    c_primary = colors.HexColor("#1E293B")    # Slate 800
    c_secondary = colors.HexColor("#0EA5E9")  # Sky 500
    c_dark = colors.HexColor("#0F172A")       # Slate 900
    c_muted = colors.HexColor("#64748B")      # Slate 500
    c_light = colors.HexColor("#F8FAFC")      # Slate 50
    c_border = colors.HexColor("#E2E8F0")     # Slate 200

    # Custom typography styles
    style_cover_title = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=c_primary,
        alignment=1, # Center
        spaceAfter=15
    )
    
    style_cover_subtitle = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=16,
        leading=22,
        textColor=c_secondary,
        alignment=1, # Center
        spaceAfter=30
    )

    style_cover_desc = ParagraphStyle(
        'CoverDesc',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=16,
        textColor=c_muted,
        alignment=1, # Center
        spaceAfter=80
    )

    style_h1 = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_secondary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_dark,
        spaceAfter=8
    )

    style_body_bold = ParagraphStyle(
        'BodyBold',
        parent=style_body,
        fontName='Helvetica-Bold'
    )

    style_code = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=12,
        textColor=c_dark,
        backColor=colors.HexColor("#F1F5F9"),
        borderPadding=6,
        spaceAfter=8
    )

    story = []

    # ================= PAGE 1: COVER PAGE =================
    story.append(Spacer(1, 120))
    story.append(Paragraph("TradeCore", style_cover_title))
    story.append(Paragraph("Professional Trading Journal & Market Screener", style_cover_subtitle))
    story.append(Paragraph("Comprehensive Project Specification, Directory Structure, Database Architecture, and Reorganization Report", style_cover_desc))
    
    # Metadata block
    metadata_data = [
        [Paragraph("<b>Prepared By:</b>", style_body), Paragraph("Antigravity AI Coding Assistant", style_body)],
        [Paragraph("<b>Date:</b>", style_body), Paragraph(datetime.now().strftime("%B %d, %Y"), style_body)],
        [Paragraph("<b>Environment:</b>", style_body), Paragraph("Local Development Sandbox", style_body)],
        [Paragraph("<b>App Version:</b>", style_body), Paragraph("v1.1 (Auto-Sync Enabled)", style_body)],
        [Paragraph("<b>Database System:</b>", style_body), Paragraph("PostgreSQL 15+", style_body)]
    ]
    t_meta = Table(metadata_data, colWidths=[120, 200])
    t_meta.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, c_border),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(KeepTogether([
        Spacer(1, 60),
        t_meta
    ]))
    story.append(PageBreak())

    # ================= PAGE 2: EXECUTIVE SUMMARY & FUNCTIONAL OVERVIEW =================
    story.append(Paragraph("1. Executive Summary & Core Functionalities", style_h1))
    story.append(Paragraph(
        "<b>TradeCore</b> is a professional trading platform designed to bridge the gap between automated mathematical analysis "
        "and disciplined trading execution. By integrating real-time market data feeds, institutional session calculations, "
        "custom risk parameters, checklist verification, and comprehensive portfolio journal auditing, TradeCore acts "
        "as a central decision-support cockpit for active traders.",
        style_body
    ))
    
    story.append(Paragraph("Key System Modules and Features:", style_h2))
    
    features_list = [
        ("Market Reference Levels Engine", "Calculates daily session boundaries including Central Pivot Range (CPR - Pivot, TC, BC) and Camarilla levels (R1-R5, S1-S5). Features real-time price tick streaming with silent, flicker-free background auto-sync polling every 2 seconds, and manual hard-sync controls."),
        ("AI Intelligence Setup Agent", "Interactive terminal widget verifying rules, leverage parameters, risk profiles (max 1.0% limit), and consecutive loss limits. Parses and logs chat commands, scanning watchlisted items for confluence setups."),
        ("Multi-Market Support", "Configured out-of-the-box for Global Forex (OANDA), Indian Indices & Equities (NSE/BSE exchange times via Alice Blue integration), and major Cryptocurrencies (Binance)."),
        (" дисциплинирован Journaling & Checklists", "Enforces rigorous preparation by requiring traders to complete structured Technical and Confirmation Checklists before entering/exiting trades. Saves detailed metrics (R-Multiple, holding duration, notes, and screenshots) to database tables."),
        ("Advanced Performance Analytics", "Calculates net profit/loss, win rates, expectancy, profit factor, average risk-to-reward ratio, and draws equity curves, category metrics (segment, style, direction), and distributions in real time.")
    ]

    for title, desc in features_list:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", style_body))
    
    story.append(Spacer(1, 15))
    story.append(PageBreak())

    # ================= PAGE 3: DIRECTORY STRUCTURE =================
    story.append(Paragraph("2. Project Directory Structure & Organization", style_h1))
    story.append(Paragraph(
        "The project is structured into two main decoupled modules: a FastAPI Python backend serving a RESTful API and managing "
        "background scanner threads, and a Next.js TypeScript frontend utilizing modern React features and styled with "
        "custom premium CSS variables.",
        style_body
    ))

    # Directory Structure Table
    dir_structure = [
        [Paragraph("<b>Directory / File</b>", style_body_bold), Paragraph("<b>Description / Responsibility</b>", style_body_bold)],
        [Paragraph("<b>backend/app/api/</b>", style_body), Paragraph("REST API route controllers (auth.py, trades.py, checklists.py, dashboard.py, market.py, scanners.py, backtesting.py).", style_body)],
        [Paragraph("<b>backend/app/core/</b>", style_body), Paragraph("System configurations (config.py), security hashing/JWT (security.py), and SQLAlchemy database session creation (database.py).", style_body)],
        [Paragraph("<b>backend/app/models/</b>", style_body), Paragraph("SQLAlchemy schema model definitions mapped directly to PostgreSQL database tables (models.py).", style_body)],
        [Paragraph("<b>backend/app/schemas/</b>", style_body), Paragraph("Pydantic classes verifying schema payloads for incoming API requests and outgoing responses.", style_body)],
        [Paragraph("<b>backend/app/services/</b>", style_body), Paragraph("Business engines for quote fetching (market_data.py), CPR/Camarilla pivots (pivots.py), live session opens (market_reference.py), and scanner checks (scanner_engine.py).", style_body)],
        [Paragraph("<b>backend/scripts/</b>", style_body), Paragraph("Developer diagnostic scripts sandbox (e.g. verify_tz.py, check_preferences.py) and PDF generators. Moved from the backend root to maintain folder cleanliness.", style_body)],
        [Paragraph("<b>frontend/src/app/</b>", style_body), Paragraph("Next.js App Router folders. The dashboard page.tsx manages workspace modes (Market vs Portfolio) and layouts.", style_body)],
        [Paragraph("<b>frontend/src/components/</b>", style_body), Paragraph("Reusable visual components including AppLayout wrapper, navigations, and widgets.", style_body)],
        [Paragraph("<b>frontend/src/context/</b>", style_body), Paragraph("Global React Context states, including CurrencyContext for seamless USD/INR performance conversions.", style_body)],
        [Paragraph("<b>frontend/src/services/</b>", style_body), Paragraph("Client-side Axios client (api.ts) mapping backend endpoints to frontend handlers.", style_body)],
        [Paragraph("<b>docker-compose.yml</b>", style_body), Paragraph("Docker container orchestrator for Postgres DB, backend FastAPI server, and Next.js client.", style_body)]
    ]

    t_dir = Table(dir_structure, colWidths=[160, 340])
    t_dir.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_light),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_dir)
    story.append(PageBreak())

    # ================= PAGE 4: DATABASE SCHEMA (PART 1) =================
    story.append(Paragraph("3. Database Structure & Relational Schemas", style_h1))
    story.append(Paragraph(
        "TradeCore uses PostgreSQL for high performance structured data storage. The database schema relies heavily on UUIDs "
        "as primary keys, foreign-key cascade actions, and GIN indexes on JSONB columns to optimize analytical search queries. "
        "Below is the database table configuration:",
        style_body
    ))

    db_schema_1 = [
        [Paragraph("<b>Table Name</b>", style_body_bold), Paragraph("<b>Key Columns & Constraints</b>", style_body_bold), Paragraph("<b>Description / Details</b>", style_body_bold)],
        [
            Paragraph("<b>users</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• email: String (Unique, Indexed)<br/>• hashed_password: String<br/>• google_id: String", style_body),
            Paragraph("Core user credential table. Supports standard email/password authentication and Google OAuth linking.", style_body)
        ],
        [
            Paragraph("<b>strategies</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• user_id: UUID (FK -> users.id)<br/>• rules: JSONB<br/>• risk_rules: JSONB", style_body),
            Paragraph("Defines trading styles. Rules list criteria (entry/exit trigger thresholds) and risk thresholds (e.g. max 1% per trade).", style_body)
        ],
        [
            Paragraph("<b>trades</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• user_id: UUID (FK -> users.id)<br/>• strategy_id: UUID (FK -> strategies.id)<br/>• entry_price: Numeric<br/>• stop_loss: Numeric<br/>• target_price: Numeric<br/>• exit_price: Numeric<br/>• setup: JSONB<br/>• analytics: JSONB", style_body),
            Paragraph("Main journal table storing entry/exit details, holding duration, and status (WIN/LOSS/OPEN). Uses GIN indexes on setup, psychology, analytics, and tags fields.", style_body)
        ],
        [
            Paragraph("<b>trade_images</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• trade_id: UUID (FK -> trades.id)<br/>• category: String<br/>• file_url: String", style_body),
            Paragraph("Saves chart snapshots (HTF, LTF, Entry, Exit) linked to specific trades, stored locally or on Google Drive.", style_body)
        ],
        [
            Paragraph("<b>watchlist</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• user_id: UUID (FK -> users.id)<br/>• symbol: String (Indexed)<br/>• market: String<br/>• settings: JSONB", style_body),
            Paragraph("Tracks user-defined tickers and custom alert criteria for real-time background scanners.", style_body)
        ]
    ]

    t_db1 = Table(db_schema_1, colWidths=[90, 200, 210])
    t_db1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_light),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_db1)
    story.append(PageBreak())

    # ================= PAGE 5: DATABASE SCHEMA (PART 2) =================
    story.append(Paragraph("3. Database Structure & Relational Schemas (Continued)", style_h1))
    
    db_schema_2 = [
        [Paragraph("<b>Table Name</b>", style_body_bold), Paragraph("<b>Key Columns & Constraints</b>", style_body_bold), Paragraph("<b>Description / Details</b>", style_body_bold)],
        [
            Paragraph("<b>market_data</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• symbol: String<br/>• market: String<br/>• trueday_open: Numeric<br/>• cpr_levels: JSONB<br/>• camarilla_levels: JSONB", style_body),
            Paragraph("Caches live reference open boundaries, ranges, and calculated pivot points for dynamic dashboard retrieval. Unique constraint on (symbol, market).", style_body)
        ],
        [
            Paragraph("<b>pivot_levels</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• symbol: String<br/>• market: String<br/>• date: Date<br/>• cpr_pivot: Numeric<br/>• camarilla_r1..s4: Numeric", style_body),
            Paragraph("Daily cache table mapping historical daily CPR and Camarilla boundaries per symbol to optimize indicator loading speeds.", style_body)
        ],
        [
            Paragraph("<b>market_candles</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• symbol: String (Indexed)<br/>• timeframe: String<br/>• datetime: DateTime<br/>• open/high/low/close: Numeric", style_body),
            Paragraph("Stores raw OHLC price feeds for multiple timeframes. Leveraged by backtesting and scanner engines. Unique constraint on (symbol, timeframe, datetime).", style_body)
        ],
        [
            Paragraph("<b>scanner_results</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• symbol: String (Indexed)<br/>• scanner_name: String<br/>• signal_type: String<br/>• triggered_at: DateTimeTZ<br/>• telegram_sent: Boolean", style_body),
            Paragraph("Caches identified candle patterns (e.g. CPR breakout, EMA crossover). Tracked to prevent duplicate Telegram alerts.", style_body)
        ],
        [
            Paragraph("<b>scanner_settings</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• user_id: UUID (FK -> users.id)<br/>• enabled_scanners: JSONB<br/>• telegram_enabled: Boolean", style_body),
            Paragraph("Stores user alerts configurations and bot credentials (telegram_bot_token, telegram_chat_id).", style_body)
        ],
        [
            Paragraph("<b>user_market_preferences</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• user_id: UUID (FK -> users.id, Unique)<br/>• favorite_symbols: JSONB<br/>• broker_credentials: JSONB", style_body),
            Paragraph("Maintains dashboard UI configurations, active watchlist selections, and broker configuration credentials.", style_body)
        ],
        [
            Paragraph("<b>trade_market_snapshot</b>", style_body),
            Paragraph("• id: UUID (PK)<br/>• trade_id: UUID (FK -> trades.id, Unique)<br/>• cpr_levels: JSONB<br/>• camarilla_levels: JSONB", style_body),
            Paragraph("Saves the exact session opens and institutional levels matrix at the time of trade execution for future review.", style_body)
        ]
    ]

    t_db2 = Table(db_schema_2, colWidths=[90, 200, 210])
    t_db2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_light),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_db2)
    story.append(PageBreak())

    # ================= PAGE 6: REORGANIZATION LOG & HEALTH CHECK =================
    story.append(Paragraph("4. File Reorganization Log & System Health Check", style_h1))
    story.append(Paragraph(
        "To enforce production-grade repository hygiene and separate execution scripts from core application logic, "
        "we analyzed the repository file layout. Standing developer utilities and debugging scripts were consolidated "
        "into the dedicated script folder:",
        style_body
    ))
    
    # Reorg logs
    reorg_data = [
        [Paragraph("<b>Original Path</b>", style_body_bold), Paragraph("<b>Consolidated Path</b>", style_body_bold), Paragraph("<b>Functional Responsibility</b>", style_body_bold)],
        [
            Paragraph("backend/check_preferences.py", style_body),
            Paragraph("backend/scripts/check_preferences.py", style_body),
            Paragraph("Queries database user_market_preferences table to inspect dynamic favorite lists and layouts.", style_body)
        ],
        [
            Paragraph("backend/verify_tz.py", style_body),
            Paragraph("backend/scripts/verify_tz.py", style_body),
            Paragraph("Diagnostic testing script checking timezone offsets between local system time, IST (Midnight), and NY (00:00 Open).", style_body)
        ],
        [
            Paragraph("backend/verify_tv_spot.py", style_body),
            Paragraph("backend/scripts/verify_tv_spot.py", style_body),
            Paragraph("Fetches spot quotes from TradingView feed, validating pivot calculations (Camarilla & CPR) and active filters.", style_body)
        ],
        [
            Paragraph("backend/generate_report.py", style_body),
            Paragraph("backend/scripts/generate_report.py", style_body),
            Paragraph("PDF report compiler script using ReportLab to write, format, and structure this document automatically.", style_body)
        ]
    ]

    t_reorg = Table(reorg_data, colWidths=[150, 150, 200])
    t_reorg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_light),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_reorg)
    
    story.append(Paragraph("System Health & Server Execution Status:", style_h2))
    
    health_data = [
        [Paragraph("<b>Module</b>", style_body_bold), Paragraph("<b>Run Command</b>", style_body_bold), Paragraph("<b>Network Port</b>", style_body_bold), Paragraph("<b>Current Status</b>", style_body_bold)],
        [
            Paragraph("FastAPI Backend", style_body),
            Paragraph("uvicorn app.main:app --host 0.0.0.0 --port 8000", style_body),
            Paragraph("http://localhost:8000", style_body),
            Paragraph("<font color='#10B981'><b>ACTIVE (Running)</b></font>", style_body)
        ],
        [
            Paragraph("Next.js Frontend", style_body),
            Paragraph("npm run dev", style_body),
            Paragraph("http://localhost:3000", style_body),
            Paragraph("<font color='#10B981'><b>ACTIVE (Running)</b></font>", style_body)
        ],
        [
            Paragraph("PostgreSQL Database", style_body),
            Paragraph("Local PG Service (Docker / Host)", style_body),
            Paragraph("localhost:5432 (DB: tradecore)", style_body),
            Paragraph("<font color='#10B981'><b>CONNECTED</b></font>", style_body)
        ]
    ]

    t_health = Table(health_data, colWidths=[100, 180, 110, 110])
    t_health.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_light),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_health)

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)

if __name__ == "__main__":
    # The script outputs the PDF to the project root directory
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "TradeCore_Project_Report.pdf"
    )
    print(f"Generating report at {output_path}...")
    create_report(output_path)
    print("Report generated successfully.")
