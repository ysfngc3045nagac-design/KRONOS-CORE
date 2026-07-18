"""KRONOS_DATA_HUB - HTML Parser"""
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

class HTMLParser:
    def __init__(self):
        self.errors = []
        self.soup = None

    def parse(self, html, parser="html.parser"):
        try:
            self.soup = BeautifulSoup(html, parser)
            return self
        except Exception as e:
            self.errors.append(f"HTML parse error: {e}")
            return self

    def select(self, css_selector):
        if not self.soup:
            return []
        return self.soup.select(css_selector)

    def select_one(self, css_selector):
        elements = self.select(css_selector)
        return elements[0] if elements else None

    def get_text(self, css_selector, default=""):
        element = self.select_one(css_selector)
        return element.get_text(strip=True) if element else default

    def get_attr(self, css_selector, attr, default=""):
        element = self.select_one(css_selector)
        return element.get(attr, default) if element else default

    def extract_table(self, css_selector="table", headers=None):
        if not self.soup:
            return []
        table = self.soup.select_one(css_selector)
        if not table:
            return []
        rows = table.find_all("tr")
        if not rows:
            return []
        if headers is None:
            header_row = rows[0]
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
            data_rows = rows[1:]
        else:
            data_rows = rows
        result = []
        for row in data_rows:
            cells = row.find_all(["td", "th"])
            if len(cells) == len(headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    key = headers[i].strip().lower().replace(" ", "_") if i < len(headers) else f"col_{i}"
                    row_data[key] = self._clean_text(cell.get_text())
                result.append(row_data)
        return result

    def extract_links(self, css_selector="a", base_url=""):
        if not self.soup:
            return []
        links = []
        for a in self.soup.select(css_selector):
            href = a.get("href", "")
            if href and not href.startswith(("#", "javascript:")):
                if base_url and not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href.lstrip("/")
                links.append({"text": a.get_text(strip=True), "href": href, "title": a.get("title", "")})
        return links

    def extract_json_ld(self):
        if not self.soup:
            return []
        scripts = self.soup.find_all("script", type="application/ld+json")
        results = []
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                results.append(data)
            except:
                pass
        return results

    def find_scripts_with_data(self, pattern=""):
        if not self.soup:
            return []
        scripts = []
        for script in self.soup.find_all("script"):
            text = script.string or ""
            if pattern and pattern in text:
                scripts.append(text)
            elif not pattern and len(text) > 100:
                scripts.append(text)
        return scripts

    def _clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def remove_elements(self, css_selectors):
        if self.soup:
            for selector in css_selectors:
                for element in self.soup.select(selector):
                    element.decompose()
        return self
