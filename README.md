<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=SEC%20Filing%20Comparison%20Tool&fontSize=40&fontColor=fff&animation=twinkling&desc=10-K%20Analysis%20%7C%20Risk%20Factors%20%7C%20Claude%20AI%20Insights&descAlignY=62&descSize=18" width="100%"/>

<br/>

<a href="https://github.com/isamkhan1809/sec-filing-comparison">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=7C83FD&center=true&vCenter=true&multiline=true&repeat=true&width=700&height=120&lines=SEC+10-K+Filing+Comparison+Tool;SEC+EDGAR+API+%7C+Claude+AI+Analysis;Risk+Factors+%7C+Revenue+Trends+%7C+Tone+Analysis;Free+%E2%80%94+No+API+Keys+for+EDGAR" alt="Typing SVG" />
</a>

<br/><br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude_3.5-191919?style=for-the-badge&logo=anthropic&logoColor=white)
![SEC EDGAR](https://img.shields.io/badge/SEC_EDGAR-Free_API-003087?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAySURBVDhPY2AYBfQHAABBAAGhiKEWAAAAAElFTkSuQmCC&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)

</div>

---

## 🚀 What is this?

A **Streamlit web app** that fetches two companies' 10-K annual filings directly from SEC EDGAR, parses the key sections, and uses **Claude claude-3-5-sonnet-20241022** to produce a deep side-by-side comparative analysis — risk factors, revenue narrative, executive tone, and investment signals — all in a rich, interactive UI.

---

## ✨ Features

- 📄 **Live 10-K Retrieval** — pulls filings directly from SEC EDGAR (free, no key required)
- ⚠️ **Risk Factor Comparison** — Claude synthesises both companies' risk landscapes
- 💰 **Revenue & Financial Narrative** — AI-powered growth trajectory analysis
- 🗣️ **Executive Language Tone** — confident / cautious / neutral scoring with sentiment gauges
- 🔑 **Key Differentiators** — what sets each company apart strategically
- 📡 **Investment Signals** — actionable insights distilled from filings
- 📊 **Interactive Charts** — radar charts, tone bar charts, and sentiment gauges (Plotly)
- 📝 **Top Risk Keywords** — frequency analysis of risk factor language
- 🗂️ **Raw Section Viewer** — inspect parsed Item 1, 1A, 7, and financial highlights

---

## 🖥️ Usage

### 1. Clone & install

```bash
git clone https://github.com/isamkhan1809/sec-filing-comparison.git
cd sec-filing-comparison
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 3. Run the app

```bash
streamlit run streamlit_app.py
```

### 4. Compare companies

1. Enter two company names or tickers (e.g. `Apple` and `Microsoft`)
2. Select a filing year (2022 – 2024)
3. Paste your Anthropic API key in the sidebar
4. Click **Compare Filings**

---

## 🗂️ Project Structure

```
sec-filing-comparison/
├── app/
│   ├── __init__.py
│   ├── edgar_client.py    # SEC EDGAR API (search, fetch 10-Ks)
│   ├── filing_parser.py   # BeautifulSoup HTML → section extraction
│   ├── analyser.py        # Claude API comparative analysis
│   └── visualiser.py      # Plotly radar, bar, gauge charts
├── streamlit_app.py       # Streamlit UI entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key ([get one here](https://console.anthropic.com)) |

> **SEC EDGAR** requires no API key — just a valid User-Agent email header (already configured).

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit 1.39 |
| AI Analysis | Anthropic Claude claude-3-5-sonnet-20241022 |
| Data Source | SEC EDGAR REST API |
| HTML Parsing | BeautifulSoup4 + lxml |
| Charts | Plotly 5.24 |
| HTTP | Requests |

---

## ⚖️ License

MIT — free to use, fork, and build on.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer&animation=twinkling" width="100%"/>

<sub>Built with ❤️ using Claude AI · SEC EDGAR data is public domain · Not financial advice</sub>

</div>
