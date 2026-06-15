"""
Parse 10-K filings to extract key sections.
"""

import re
from bs4 import BeautifulSoup


class FilingParser:
    MAX_SECTION_CHARS = 3000

    # Patterns for section headings in 10-K filings
    SECTION_PATTERNS = {
        "business_description": [
            r"item\s*1[\.\s]*(?:business|description of business)",
            r"(?:^|\n)\s*item\s+1\b(?!\s*[aAbB])",
        ],
        "risk_factors": [
            r"item\s*1a[\.\s]*risk factors",
            r"item\s*1\.?a\.?\s+risk\s+factors",
            r"risk\s+factors",
        ],
        "mda": [
            r"item\s*7[\.\s]*management.?s?\s+discussion\s+and\s+analysis",
            r"management.?s\s+discussion\s+and\s+analysis\s+of\s+financial\s+condition",
            r"item\s*7\b",
        ],
        "quantitative_disclosures": [
            r"item\s*7a[\.\s]*quantitative",
            r"item\s*7\.?a",
        ],
        "financial_statements": [
            r"item\s*8[\.\s]*financial\s+statements",
            r"item\s*8\b",
        ],
    }

    def parse_10k(self, html_content: str) -> dict:
        """
        Parse HTML content of a 10-K filing and extract key sections.
        Returns dict with business_description, risk_factors, financial_highlights,
        mda, and executive_language.
        """
        soup = BeautifulSoup(html_content, "lxml")

        # Remove scripts and styles
        for tag in soup(["script", "style", "meta", "link"]):
            tag.decompose()

        # Get plain text
        full_text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        full_text = re.sub(r"\n{3,}", "\n\n", full_text)
        full_text = re.sub(r"[ \t]{2,}", " ", full_text)

        sections = {
            "business_description": self._extract_section(
                full_text, "business_description", "risk_factors"
            ),
            "risk_factors": self._extract_section(
                full_text, "risk_factors", "mda"
            ),
            "mda": self._extract_section(
                full_text, "mda", "quantitative_disclosures"
            ),
        }

        # Extract financial highlights from MDA and financial statements
        financial_text = self._extract_section(
            full_text, "mda", "financial_statements"
        )
        sections["financial_highlights"] = self._extract_financial_numbers(financial_text or full_text[:5000])

        # Executive language: first 2000 chars of MDA
        mda = sections.get("mda", "")
        sections["executive_language"] = mda[:2000] if mda else full_text[:2000]

        return sections

    def _extract_section(self, text: str, start_section: str, end_section: str) -> str:
        """Extract text between two section markers."""
        start_patterns = self.SECTION_PATTERNS.get(start_section, [])
        end_patterns = self.SECTION_PATTERNS.get(end_section, [])

        start_idx = self._find_section_start(text, start_patterns)
        if start_idx == -1:
            return ""

        end_idx = self._find_section_start(text, end_patterns, after=start_idx + 100)
        if end_idx == -1:
            end_idx = start_idx + self.MAX_SECTION_CHARS * 2  # fallback

        section_text = text[start_idx:end_idx].strip()
        return section_text[: self.MAX_SECTION_CHARS]

    def _find_section_start(self, text: str, patterns: list, after: int = 0) -> int:
        """Find the start index of a section matching any of the given patterns."""
        search_text = text[after:].lower()
        best_idx = -1
        for pattern in patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                idx = match.start() + after
                if best_idx == -1 or idx < best_idx:
                    best_idx = idx
        return best_idx

    def _extract_financial_numbers(self, text: str) -> str:
        """Extract revenue, income, and other financial numbers from text."""
        financial_patterns = [
            r"(?:net\s+)?revenue[s]?\s*[:\$]?\s*[\$]?\s*[\d,\.]+\s*(?:million|billion|M|B)?",
            r"(?:net\s+)?income\s*[:\$]?\s*[\$]?\s*[\d,\.]+\s*(?:million|billion|M|B)?",
            r"(?:diluted\s+)?(?:earnings|loss)\s+per\s+share\s*[:\$]?\s*[\$]?\s*[\d,\.]+",
            r"gross\s+(?:profit|margin)\s*[:\$]?\s*[\$]?\s*[\d,\.]+\s*(?:million|billion|M|B)?",
            r"operating\s+(?:income|loss)\s*[:\$]?\s*[\$]?\s*[\d,\.]+\s*(?:million|billion|M|B)?",
            r"total\s+assets\s*[:\$]?\s*[\$]?\s*[\d,\.]+\s*(?:million|billion|M|B)?",
            r"cash\s+and\s+cash\s+equivalents\s*[:\$]?\s*[\$]?\s*[\d,\.]+\s*(?:million|billion|M|B)?",
        ]

        found = []
        text_lower = text.lower()
        for pattern in financial_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            found.extend(matches[:2])  # limit per pattern

        if found:
            return "\n".join(found[: 20])
        return text[:500]  # fallback: return beginning of text
