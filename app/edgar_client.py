"""
SEC EDGAR API client for fetching 10-K filings.
"""

import re
import time
import requests
from typing import Optional


class EDGARClient:
    BASE_URL = "https://data.sec.gov/"
    SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
    COMPANY_SEARCH_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "isamkhan1809@gmail.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        })

    def _get(self, url: str, params: dict = None, headers: dict = None) -> requests.Response:
        """Make a GET request with rate limiting."""
        time.sleep(0.1)  # SEC EDGAR rate limit courtesy
        hdrs = {"User-Agent": "isamkhan1809@gmail.com"}
        if headers:
            hdrs.update(headers)
        resp = requests.get(url, params=params, headers=hdrs, timeout=30)
        resp.raise_for_status()
        return resp

    def search_company(self, company_name: str) -> list[dict]:
        """
        Search for companies by name or ticker.
        Returns list of {cik, name, ticker}.
        """
        results = []

        # Try EDGAR full-text search first
        try:
            url = "https://efts.sec.gov/LATEST/search-index"
            params = {
                "q": f'"{company_name}"',
                "dateRange": "custom",
                "startdt": "2020-01-01",
                "forms": "10-K",
            }
            resp = self._get(url, params=params, headers={"Host": "efts.sec.gov"})
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            seen_ciks = set()
            for hit in hits[:10]:
                src = hit.get("_source", {})
                cik = str(src.get("entity_id", "")).lstrip("0") or str(src.get("ciks", [""])[0]).lstrip("0")
                name = src.get("display_names", [src.get("entity_name", "")])[0]
                ticker = src.get("file_num", "")
                if cik and cik not in seen_ciks:
                    seen_ciks.add(cik)
                    results.append({"cik": cik, "name": name, "ticker": ticker})
        except Exception:
            pass

        # Fall back to company search endpoint
        if not results:
            try:
                url = "https://www.sec.gov/cgi-bin/browse-edgar"
                params = {
                    "company": company_name,
                    "CIK": "",
                    "type": "10-K",
                    "dateb": "",
                    "owner": "include",
                    "count": "10",
                    "search_text": "",
                    "action": "getcompany",
                    "output": "atom",
                }
                resp = self._get(url, params=params, headers={"Host": "www.sec.gov"})
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                for entry in soup.find_all("entry")[:10]:
                    cik_tag = entry.find("cik")
                    name_tag = entry.find("company-name")
                    if cik_tag and name_tag:
                        cik = cik_tag.text.strip().lstrip("0")
                        name = name_tag.text.strip()
                        results.append({"cik": cik, "name": name, "ticker": ""})
            except Exception:
                pass

        # Try the company_tickers.json as a last resort
        if not results:
            try:
                resp = self._get(
                    "https://www.sec.gov/files/company_tickers.json",
                    headers={"Host": "www.sec.gov"},
                )
                tickers_data = resp.json()
                query = company_name.lower()
                for _idx, info in tickers_data.items():
                    if (
                        query in info.get("title", "").lower()
                        or query.upper() == info.get("ticker", "").upper()
                    ):
                        results.append({
                            "cik": str(info["cik_str"]),
                            "name": info["title"],
                            "ticker": info["ticker"],
                        })
                        if len(results) >= 10:
                            break
            except Exception:
                pass

        return results

    def get_10k_filings(self, cik: str, count: int = 3) -> list[dict]:
        """
        Get list of 10-K filings for a company.
        Returns list of {accession_number, filing_date, report_date, primary_document}.
        """
        cik_padded = str(cik).zfill(10)
        url = f"{self.SUBMISSIONS_URL}CIK{cik_padded}.json"
        resp = self._get(url, headers={"Host": "data.sec.gov"})
        data = resp.json()

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        accessions = filings.get("accessionNumber", [])
        filing_dates = filings.get("filingDate", [])
        report_dates = filings.get("reportDate", [])
        primary_docs = filings.get("primaryDocument", [])

        results = []
        for i, form in enumerate(forms):
            if form in ("10-K", "10-K/A") and len(results) < count:
                results.append({
                    "accession_number": accessions[i],
                    "filing_date": filing_dates[i] if i < len(filing_dates) else "",
                    "report_date": report_dates[i] if i < len(report_dates) else "",
                    "primary_document": primary_docs[i] if i < len(primary_docs) else "",
                })

        return results

    def get_filing_document(self, cik: str, accession_number: str, primary_document: str = "") -> str:
        """
        Fetch the full HTML/text content of a 10-K filing.
        """
        accession_no_dashes = accession_number.replace("-", "")
        cik_str = str(cik).lstrip("0")

        # If we have the primary document name, use it directly
        if primary_document:
            url = f"{self.ARCHIVES_URL}{cik_str}/{accession_no_dashes}/{primary_document}"
            try:
                resp = self._get(url, headers={"Host": "www.sec.gov"})
                return resp.text
            except Exception:
                pass

        # Otherwise, fetch the filing index to find the primary document
        index_url = f"{self.ARCHIVES_URL}{cik_str}/{accession_no_dashes}/{accession_number}-index.htm"
        try:
            resp = self._get(index_url, headers={"Host": "www.sec.gov"})
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            # Look for the main 10-K document (not exhibits)
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 4:
                    doc_type = cells[3].text.strip() if len(cells) > 3 else ""
                    if doc_type in ("10-K", "10-K/A"):
                        link = cells[2].find("a")
                        if link and link.get("href"):
                            doc_url = "https://www.sec.gov" + link["href"]
                            doc_resp = self._get(doc_url, headers={"Host": "www.sec.gov"})
                            return doc_resp.text
        except Exception:
            pass

        # Try the filing viewer JSON
        try:
            json_url = f"{self.ARCHIVES_URL}{cik_str}/{accession_no_dashes}/index.json"
            resp = self._get(json_url, headers={"Host": "www.sec.gov"})
            index_data = resp.json()
            for item in index_data.get("directory", {}).get("item", []):
                name = item.get("name", "")
                if name.lower().endswith((".htm", ".html")) and "10k" in name.lower():
                    doc_url = f"{self.ARCHIVES_URL}{cik_str}/{accession_no_dashes}/{name}"
                    doc_resp = self._get(doc_url, headers={"Host": "www.sec.gov"})
                    return doc_resp.text
            # Fall back to any .htm file that's not an exhibit
            for item in index_data.get("directory", {}).get("item", []):
                name = item.get("name", "")
                if name.lower().endswith((".htm", ".html")) and not name.lower().startswith("ex"):
                    doc_url = f"{self.ARCHIVES_URL}{cik_str}/{accession_no_dashes}/{name}"
                    doc_resp = self._get(doc_url, headers={"Host": "www.sec.gov"})
                    return doc_resp.text
        except Exception:
            pass

        raise ValueError(f"Could not retrieve 10-K document for CIK {cik}, accession {accession_number}")
