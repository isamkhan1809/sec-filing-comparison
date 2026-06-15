"""
Claude AI-powered comparative analysis of 10-K filings.
"""

import json
import re
import anthropic


class FilingAnalyser:
    MODEL = "claude-3-5-sonnet-20241022"

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def compare_filings(
        self,
        company_a_name: str,
        filing_a: dict,
        company_b_name: str,
        filing_b: dict,
    ) -> dict:
        """
        Compare two 10-K filings using Claude.
        Returns a structured analysis dict.
        """
        prompt = f"""You are a senior financial analyst. Compare these two companies' 10-K filings and provide a structured, insightful analysis.

## Company A: {company_a_name}

### Business Description:
{filing_a.get('business_description', 'Not available')[:1500]}

### Risk Factors:
{filing_a.get('risk_factors', 'Not available')[:1500]}

### Management Discussion & Analysis:
{filing_a.get('mda', 'Not available')[:1500]}

### Financial Highlights:
{filing_a.get('financial_highlights', 'Not available')[:500]}

---

## Company B: {company_b_name}

### Business Description:
{filing_b.get('business_description', 'Not available')[:1500]}

### Risk Factors:
{filing_b.get('risk_factors', 'Not available')[:1500]}

### Management Discussion & Analysis:
{filing_b.get('mda', 'Not available')[:1500]}

### Financial Highlights:
{filing_b.get('financial_highlights', 'Not available')[:500]}

---

Provide your analysis as a valid JSON object with exactly these keys:
{{
  "risk_comparison": "Detailed side-by-side analysis of risk factors (3-4 paragraphs)",
  "revenue_narrative": "Comparison of revenue growth trajectories and financial performance (2-3 paragraphs)",
  "language_tone": {{
    "{company_a_name}": "confident|cautious|neutral",
    "{company_b_name}": "confident|cautious|neutral",
    "differences": "Explanation of tone differences and what they signal (1-2 paragraphs)"
  }},
  "key_differentiators": ["differentiator 1", "differentiator 2", "differentiator 3", "differentiator 4", "differentiator 5"],
  "investment_signals": ["signal 1", "signal 2", "signal 3", "signal 4", "signal 5"],
  "overall_summary": "Executive summary comparing both companies (2-3 paragraphs)"
}}

Return ONLY the JSON object, no other text."""

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()

        # Parse JSON — strip markdown fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON object from the response
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            # Return structured fallback
            return {
                "risk_comparison": raw[:500],
                "revenue_narrative": "Analysis parsing error — see raw output.",
                "language_tone": {
                    company_a_name: "neutral",
                    company_b_name: "neutral",
                    "differences": "Could not parse structured response.",
                },
                "key_differentiators": ["See raw analysis above"],
                "investment_signals": ["See raw analysis above"],
                "overall_summary": raw[:1000],
            }

    def extract_financials(self, filing_text: str) -> dict:
        """
        Use Claude to extract structured financial data from filing text.
        Returns {revenue, net_income, eps, yoy_growth}.
        """
        prompt = f"""Extract key financial metrics from this 10-K filing excerpt.
Return ONLY a JSON object with these keys: revenue, net_income, eps, yoy_growth.
Use "N/A" if a value cannot be found.

Filing text:
{filing_text[:3000]}

Return ONLY the JSON object."""

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
            return {"revenue": "N/A", "net_income": "N/A", "eps": "N/A", "yoy_growth": "N/A"}
