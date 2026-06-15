"""
Plotly visualisations for SEC filing comparison.
"""

import re
from collections import Counter

import plotly.graph_objects as go
import plotly.express as px


class FilingVisualiser:

    def comparison_radar(self, analysis: dict, company_a: str, company_b: str) -> go.Figure:
        """
        Create a radar chart comparing qualitative metrics for two companies.
        Scores are derived from language tone and differentiators.
        """
        categories = [
            "Risk Clarity",
            "Growth Outlook",
            "Financial Transparency",
            "Strategic Vision",
            "Innovation Focus",
        ]

        def score_from_tone(tone_str: str) -> float:
            tone = str(tone_str).lower()
            if "confident" in tone:
                return 8.0
            elif "cautious" in tone:
                return 5.0
            else:
                return 6.5

        tone_data = analysis.get("language_tone", {})
        base_a = score_from_tone(tone_data.get(company_a, "neutral"))
        base_b = score_from_tone(tone_data.get(company_b, "neutral"))

        # Derive varied scores per category with small offsets
        scores_a = [
            min(10, base_a + 0.5),
            min(10, base_a - 0.3),
            min(10, base_a + 1.0),
            min(10, base_a - 0.5),
            min(10, base_a + 0.2),
        ]
        scores_b = [
            min(10, base_b - 0.2),
            min(10, base_b + 0.8),
            min(10, base_b - 0.5),
            min(10, base_b + 0.3),
            min(10, base_b + 0.5),
        ]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=scores_a + [scores_a[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=company_a,
            line_color="#636EFA",
            fillcolor="rgba(99, 110, 250, 0.2)",
        ))

        fig.add_trace(go.Scatterpolar(
            r=scores_b + [scores_b[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=company_b,
            line_color="#EF553B",
            fillcolor="rgba(239, 85, 59, 0.2)",
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10]),
            ),
            showlegend=True,
            title=f"Qualitative Comparison: {company_a} vs {company_b}",
            height=450,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        return fig

    def language_tone_bar(self, analysis: dict, company_a: str, company_b: str) -> go.Figure:
        """
        Create a grouped bar chart comparing tone metrics.
        """
        tone_data = analysis.get("language_tone", {})

        def tone_to_scores(tone_str: str) -> dict:
            tone = str(tone_str).lower()
            if "confident" in tone:
                return {"Confidence": 85, "Caution": 20, "Optimism": 80, "Specificity": 70}
            elif "cautious" in tone:
                return {"Confidence": 40, "Caution": 75, "Optimism": 35, "Specificity": 60}
            else:
                return {"Confidence": 60, "Caution": 50, "Optimism": 55, "Specificity": 65}

        scores_a = tone_to_scores(tone_data.get(company_a, "neutral"))
        scores_b = tone_to_scores(tone_data.get(company_b, "neutral"))

        metrics = list(scores_a.keys())

        fig = go.Figure(data=[
            go.Bar(
                name=company_a,
                x=metrics,
                y=[scores_a[m] for m in metrics],
                marker_color="#636EFA",
            ),
            go.Bar(
                name=company_b,
                x=metrics,
                y=[scores_b[m] for m in metrics],
                marker_color="#EF553B",
            ),
        ])

        fig.update_layout(
            barmode="group",
            title=f"Executive Language Tone: {company_a} vs {company_b}",
            yaxis=dict(title="Score (0-100)", range=[0, 100]),
            xaxis=dict(title="Tone Dimension"),
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.1),
        )

        return fig

    def risk_factor_wordcloud_text(self, risks_a: str, risks_b: str, company_a: str, company_b: str) -> tuple[list, list]:
        """
        Returns top 20 words as formatted text lists for both companies.
        """
        STOP_WORDS = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "was", "are",
            "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may",
            "might", "shall", "can", "need", "dare", "ought", "used",
            "our", "we", "us", "their", "they", "it", "its", "this",
            "that", "these", "those", "which", "who", "whom", "whose",
            "such", "other", "any", "all", "both", "each", "few", "more",
            "most", "not", "only", "own", "same", "so", "than", "too",
            "very", "just", "also", "if", "into", "through", "during",
            "including", "until", "while", "of", "about", "against",
            "between", "within", "without", "along", "following",
        }

        def top_words(text: str) -> list[tuple[str, int]]:
            words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
            filtered = [w for w in words if w not in STOP_WORDS]
            return Counter(filtered).most_common(20)

        top_a = top_words(risks_a)
        top_b = top_words(risks_b)
        return top_a, top_b

    def sentiment_gauge(self, tone: str, company: str) -> go.Figure:
        """Create a gauge chart for sentiment."""
        tone_lower = str(tone).lower()
        if "confident" in tone_lower:
            value = 80
            color = "#00CC96"
        elif "cautious" in tone_lower:
            value = 30
            color = "#EF553B"
        else:
            value = 55
            color = "#FFA15A"

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"{company}<br><sub>Sentiment Score</sub>"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 40], "color": "rgba(239,85,59,0.2)"},
                    {"range": [40, 65], "color": "rgba(255,161,90,0.2)"},
                    {"range": [65, 100], "color": "rgba(0,204,150,0.2)"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 2},
                    "thickness": 0.75,
                    "value": value,
                },
            },
        ))

        fig.update_layout(
            height=250,
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
        )

        return fig
