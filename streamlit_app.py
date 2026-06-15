"""
SEC 10-K Filing Comparison Tool — Streamlit entry point.
"""

import os
import traceback

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.edgar_client import EDGARClient
from app.filing_parser import FilingParser
from app.analyser import FilingAnalyser
from app.visualiser import FilingVisualiser

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SEC 10-K Filing Comparison",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 { color: #e94560; margin: 0; font-size: 2.2rem; }
    .main-header p  { color: #a8b2d8; margin: 0.5rem 0 0; font-size: 1rem; }

    .company-card {
        background: linear-gradient(135deg, #1e1e3a, #252550);
        border: 1px solid #3a3a6e;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .company-card h3 { color: #7c83fd; margin: 0 0 0.5rem; }

    .metric-badge {
        display: inline-block;
        background: rgba(124, 131, 253, 0.15);
        border: 1px solid #7c83fd;
        color: #7c83fd;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        margin: 0.15rem;
    }

    .insight-box {
        background: rgba(30, 40, 80, 0.6);
        border-left: 4px solid #e94560;
        border-radius: 4px;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
    }

    .signal-item {
        background: rgba(0, 204, 150, 0.1);
        border: 1px solid rgba(0, 204, 150, 0.3);
        border-radius: 6px;
        padding: 0.5rem 0.8rem;
        margin: 0.3rem 0;
        color: #00cc96;
    }

    .diff-item {
        background: rgba(99, 110, 250, 0.1);
        border: 1px solid rgba(99, 110, 250, 0.3);
        border-radius: 6px;
        padding: 0.5rem 0.8rem;
        margin: 0.3rem 0;
        color: #636efa;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 40, 80, 0.5);
        border-radius: 8px 8px 0 0;
        border: 1px solid #3a3a6e;
        color: #a8b2d8;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(124, 131, 253, 0.2);
        border-color: #7c83fd;
        color: #7c83fd;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="main-header">
        <h1>📊 SEC 10-K Filing Comparison</h1>
        <p>Compare two companies' annual filings side-by-side using SEC EDGAR + Claude AI</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        help="Get your key at https://console.anthropic.com",
    )

    st.markdown("---")
    st.markdown("## 🏢 Companies to Compare")

    company_a = st.text_input(
        "Company A (name or ticker)",
        placeholder="e.g. Apple or AAPL",
        value="Apple",
    )
    company_b = st.text_input(
        "Company B (name or ticker)",
        placeholder="e.g. Microsoft or MSFT",
        value="Microsoft",
    )

    year = st.selectbox(
        "Filing Year",
        options=[2024, 2023, 2022],
        index=0,
    )

    st.markdown("---")
    compare_btn = st.button("🔍 Compare Filings", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown(
        """
        <small style='color:#6b7db3'>
        📌 <b>Data source:</b> SEC EDGAR (free)<br>
        🤖 <b>AI analysis:</b> Claude claude-3-5-sonnet-20241022<br>
        ⚡ <b>No EDGAR key needed</b>
        </small>
        """,
        unsafe_allow_html=True,
    )

# ── Helpers ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_parse(company_name: str, target_year: int) -> tuple[dict, str, str]:
    """
    Fetch latest 10-K for company and parse it.
    Returns (parsed_sections, resolved_company_name, filing_date).
    """
    client = EDGARClient()
    parser = FilingParser()

    companies = client.search_company(company_name)
    if not companies:
        raise ValueError(f"No company found for '{company_name}'")

    company_info = companies[0]
    cik = company_info["cik"]
    resolved_name = company_info["name"]

    filings = client.get_10k_filings(cik, count=5)
    if not filings:
        raise ValueError(f"No 10-K filings found for {resolved_name}")

    # Pick the filing closest to the target year
    chosen = None
    for f in filings:
        date_str = f.get("filing_date", "") or f.get("report_date", "")
        if str(target_year) in date_str or str(target_year - 1) in date_str:
            chosen = f
            break
    if not chosen:
        chosen = filings[0]  # most recent

    html = client.get_filing_document(cik, chosen["accession_number"], chosen.get("primary_document", ""))
    sections = parser.parse_10k(html)

    return sections, resolved_name, chosen.get("filing_date", "unknown")


def run_comparison(co_a: str, co_b: str, yr: int, api_key: str):
    """Full pipeline: fetch, parse, analyse, display."""

    progress = st.progress(0, text="Starting…")

    # ── Fetch Company A ──────────────────────────────────────────────
    progress.progress(10, text=f"Fetching {co_a} 10-K from SEC EDGAR…")
    try:
        sections_a, name_a, date_a = fetch_and_parse(co_a, yr)
    except Exception as e:
        st.error(f"❌ Failed to fetch {co_a}: {e}")
        st.code(traceback.format_exc())
        return

    # ── Fetch Company B ──────────────────────────────────────────────
    progress.progress(35, text=f"Fetching {co_b} 10-K from SEC EDGAR…")
    try:
        sections_b, name_b, date_b = fetch_and_parse(co_b, yr)
    except Exception as e:
        st.error(f"❌ Failed to fetch {co_b}: {e}")
        st.code(traceback.format_exc())
        return

    # ── Claude Analysis ──────────────────────────────────────────────
    progress.progress(60, text="Running Claude AI comparative analysis…")
    analyser = FilingAnalyser(api_key=api_key)
    try:
        analysis = analyser.compare_filings(name_a, sections_a, name_b, sections_b)
    except Exception as e:
        st.error(f"❌ Claude analysis failed: {e}")
        st.code(traceback.format_exc())
        return

    # ── Extract financials ───────────────────────────────────────────
    progress.progress(80, text="Extracting financial metrics…")
    fin_a = analyser.extract_financials(
        sections_a.get("financial_highlights", "") + "\n" + sections_a.get("mda", "")
    )
    fin_b = analyser.extract_financials(
        sections_b.get("financial_highlights", "") + "\n" + sections_b.get("mda", "")
    )

    progress.progress(100, text="Done!")
    progress.empty()

    # ── Company header cards ─────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""<div class="company-card">
                <h3>🅰 {name_a}</h3>
                <p style='color:#a8b2d8'>Filing date: <b>{date_a}</b></p>
                <span class="metric-badge">Revenue: {fin_a.get('revenue','N/A')}</span>
                <span class="metric-badge">Net Income: {fin_a.get('net_income','N/A')}</span>
                <span class="metric-badge">EPS: {fin_a.get('eps','N/A')}</span>
                <span class="metric-badge">YoY Growth: {fin_a.get('yoy_growth','N/A')}</span>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="company-card">
                <h3>🅱 {name_b}</h3>
                <p style='color:#a8b2d8'>Filing date: <b>{date_b}</b></p>
                <span class="metric-badge">Revenue: {fin_b.get('revenue','N/A')}</span>
                <span class="metric-badge">Net Income: {fin_b.get('net_income','N/A')}</span>
                <span class="metric-badge">EPS: {fin_b.get('eps','N/A')}</span>
                <span class="metric-badge">YoY Growth: {fin_b.get('yoy_growth','N/A')}</span>
            </div>""",
            unsafe_allow_html=True,
        )

    vis = FilingVisualiser()

    # ── Tabs ─────────────────────────────────────────────────────────
    tab_overview, tab_risk, tab_fin, tab_lang, tab_raw = st.tabs([
        "🌐 Overview",
        "⚠️ Risk Factors",
        "💰 Financial Analysis",
        "🗣️ Executive Language",
        "📄 Raw Sections",
    ])

    # ── Overview tab ─────────────────────────────────────────────────
    with tab_overview:
        st.markdown("### 📋 Overall Summary")
        st.markdown(
            f'<div class="insight-box">{analysis.get("overall_summary","")}</div>',
            unsafe_allow_html=True,
        )

        col_r, col_l = st.columns(2)
        with col_r:
            st.plotly_chart(
                vis.comparison_radar(analysis, name_a, name_b),
                use_container_width=True,
            )
        with col_l:
            st.markdown("### 🔑 Key Differentiators")
            for item in analysis.get("key_differentiators", []):
                st.markdown(f'<div class="diff-item">◆ {item}</div>', unsafe_allow_html=True)

            st.markdown("### 📡 Investment Signals")
            for item in analysis.get("investment_signals", []):
                st.markdown(f'<div class="signal-item">▶ {item}</div>', unsafe_allow_html=True)

    # ── Risk Factors tab ─────────────────────────────────────────────
    with tab_risk:
        st.markdown("### ⚠️ Risk Factor Comparison")
        st.markdown(
            f'<div class="insight-box">{analysis.get("risk_comparison","")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### 📝 Top Risk Keywords")

        top_a, top_b = vis.risk_factor_wordcloud_text(
            sections_a.get("risk_factors", ""),
            sections_b.get("risk_factors", ""),
            name_a,
            name_b,
        )

        col_wa, col_wb = st.columns(2)
        with col_wa:
            st.markdown(f"**{name_a} — Top Risk Keywords**")
            for word, count in top_a:
                pct = min(100, int(count / (top_a[0][1] or 1) * 100))
                st.markdown(
                    f"`{word}` &nbsp; {'█' * (pct // 10)}{'░' * (10 - pct // 10)} {count}x",
                    unsafe_allow_html=True,
                )
        with col_wb:
            st.markdown(f"**{name_b} — Top Risk Keywords**")
            for word, count in top_b:
                pct = min(100, int(count / (top_b[0][1] or 1) * 100))
                st.markdown(
                    f"`{word}` &nbsp; {'█' * (pct // 10)}{'░' * (10 - pct // 10)} {count}x",
                    unsafe_allow_html=True,
                )

    # ── Financial Analysis tab ────────────────────────────────────────
    with tab_fin:
        st.markdown("### 💰 Revenue & Financial Narrative")
        st.markdown(
            f'<div class="insight-box">{analysis.get("revenue_narrative","")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### 📊 Extracted Financial Metrics")
        col_fa, col_fb = st.columns(2)
        with col_fa:
            st.markdown(f"**{name_a}**")
            st.metric("Revenue", fin_a.get("revenue", "N/A"))
            st.metric("Net Income", fin_a.get("net_income", "N/A"))
            st.metric("EPS", fin_a.get("eps", "N/A"))
            st.metric("YoY Growth", fin_a.get("yoy_growth", "N/A"))
        with col_fb:
            st.markdown(f"**{name_b}**")
            st.metric("Revenue", fin_b.get("revenue", "N/A"))
            st.metric("Net Income", fin_b.get("net_income", "N/A"))
            st.metric("EPS", fin_b.get("eps", "N/A"))
            st.metric("YoY Growth", fin_b.get("yoy_growth", "N/A"))

    # ── Executive Language tab ────────────────────────────────────────
    with tab_lang:
        st.markdown("### 🗣️ Executive Tone Analysis")

        tone_data = analysis.get("language_tone", {})

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(
                vis.sentiment_gauge(tone_data.get(name_a, "neutral"), name_a),
                use_container_width=True,
            )
            tone_a = tone_data.get(name_a, "neutral")
            emoji = "🟢" if "confident" in str(tone_a).lower() else ("🔴" if "cautious" in str(tone_a).lower() else "🟡")
            st.markdown(f"**Tone: {emoji} {tone_a.capitalize() if isinstance(tone_a, str) else tone_a}**")

        with col_g2:
            st.plotly_chart(
                vis.sentiment_gauge(tone_data.get(name_b, "neutral"), name_b),
                use_container_width=True,
            )
            tone_b = tone_data.get(name_b, "neutral")
            emoji_b = "🟢" if "confident" in str(tone_b).lower() else ("🔴" if "cautious" in str(tone_b).lower() else "🟡")
            st.markdown(f"**Tone: {emoji_b} {tone_b.capitalize() if isinstance(tone_b, str) else tone_b}**")

        st.markdown("---")
        st.plotly_chart(
            vis.language_tone_bar(analysis, name_a, name_b),
            use_container_width=True,
        )

        st.markdown("### 📝 Tone Differences")
        st.markdown(
            f'<div class="insight-box">{tone_data.get("differences","")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.markdown(f"**{name_a} — Executive Language (MDA excerpt)**")
            st.text_area(
                "",
                value=sections_a.get("executive_language", "")[:2000],
                height=250,
                key="exec_a",
                label_visibility="collapsed",
            )
        with col_ex2:
            st.markdown(f"**{name_b} — Executive Language (MDA excerpt)**")
            st.text_area(
                "",
                value=sections_b.get("executive_language", "")[:2000],
                height=250,
                key="exec_b",
                label_visibility="collapsed",
            )

    # ── Raw Sections tab ──────────────────────────────────────────────
    with tab_raw:
        st.markdown("### 📄 Raw Parsed Sections")

        section_labels = {
            "business_description": "Item 1 — Business Description",
            "risk_factors": "Item 1A — Risk Factors",
            "mda": "Item 7 — MD&A",
            "financial_highlights": "Financial Highlights (extracted)",
        }

        for key, label in section_labels.items():
            with st.expander(label):
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.markdown(f"**{name_a}**")
                    st.text_area(
                        "",
                        value=sections_a.get(key, "Not found"),
                        height=200,
                        key=f"raw_{key}_a",
                        label_visibility="collapsed",
                    )
                with col_r2:
                    st.markdown(f"**{name_b}**")
                    st.text_area(
                        "",
                        value=sections_b.get(key, "Not found"),
                        height=200,
                        key=f"raw_{key}_b",
                        label_visibility="collapsed",
                    )


# ── Main logic ─────────────────────────────────────────────────────────────────
if compare_btn:
    if not anthropic_key:
        st.error("Please enter your Anthropic API key in the sidebar.")
    elif not company_a or not company_b:
        st.error("Please enter both company names.")
    else:
        run_comparison(company_a, company_b, year, anthropic_key)
else:
    # Landing state
    st.markdown(
        """
        <div style='text-align:center; padding:3rem; color:#a8b2d8'>
            <h2 style='color:#7c83fd'>How it works</h2>
            <p>1️⃣ Enter two company names or tickers in the sidebar</p>
            <p>2️⃣ Select the filing year (2022 – 2024)</p>
            <p>3️⃣ Add your Anthropic API key</p>
            <p>4️⃣ Click <b>Compare Filings</b></p>
            <br>
            <p style='color:#6b7db3; font-size:0.9rem'>
                10-K filings are fetched live from <b>SEC EDGAR</b> (free, no key required).<br>
                Claude AI analyses risk factors, revenue trends, and executive tone.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
