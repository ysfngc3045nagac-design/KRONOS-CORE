"""KRONOS_DATA_HUB - Source Discovery"""
import requests
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse

class SourceDiscovery:
    def __init__(self):
        self.known_patterns = {
            "api": [r"/api/", r"/v\d+/", r"/rest/"],
            "data": [r"/data/", r"/download/", r"/export/"],
            "feed": [r"/feed/", r"/rss/", r"/xml/"]
        }
        self.discovered = []

    def discover_from_github(self, query="football data api", max_results=10):
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "sort": "updated", "order": "desc", "per_page": max_results}
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            sources = []
            for item in data.get("items", []):
                sources.append({
                    "name": item.get("name"), "description": item.get("description", ""),
                    "url": item.get("html_url"), "api_url": item.get("url"),
                    "stars": item.get("stargazers_count", 0), "language": item.get("language", ""),
                    "updated": item.get("updated_at"), "source_type": "github",
                    "relevance_score": self._score_relevance(item, query)
                })
            return sorted(sources, key=lambda x: x["relevance_score"], reverse=True)
        except Exception as e:
            return [{"error": str(e)}]

    def discover_from_page(self, page_url, depth=1):
        try:
            response = requests.get(page_url, timeout=30, headers={"User-Agent": "KRONOS_DATA_HUB/1.0"})
            from parsers.html_parser import HTMLParser
            parser = HTMLParser()
            parser.parse(response.text)
            sources = []
            links = parser.extract_links(base_url=page_url)
            for link in links:
                href = link["href"]
                text = link["text"]
                for category, patterns in self.known_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, href, re.IGNORECASE):
                            sources.append({"url": href, "text": text, "category": category,
                                             "source_type": "web", "discovered_from": page_url})
                            break
            return sources
        except Exception as e:
            return [{"error": str(e)}]

    def test_source(self, url, method="GET", timeout=10):
        try:
            start = __import__('time').time()
            response = requests.request(method, url, timeout=timeout,
                                         headers={"User-Agent": "KRONOS_DATA_HUB/1.0", "Accept": "application/json"})
            elapsed = (__import__('time').time() - start) * 1000
            content_type = response.headers.get("Content-Type", "")
            return {
                "url": url, "status": "accessible" if response.status_code < 400 else "error",
                "status_code": response.status_code, "response_time_ms": round(elapsed, 2),
                "content_type": content_type, "content_length": len(response.content),
                "is_json": "json" in content_type.lower(), "is_xml": "xml" in content_type.lower(),
                "is_csv": "csv" in content_type.lower() or "text/csv" in content_type,
                "has_cors": "access-control" in str(response.headers).lower()
            }
        except requests.exceptions.Timeout:
            return {"url": url, "status": "timeout", "error": "Request timed out"}
        except Exception as e:
            return {"url": url, "status": "error", "error": str(e)}

    def _score_relevance(self, repo, query):
        score = 0
        score += min(repo.get("stargazers_count", 0) / 1000, 5)
        updated = repo.get("updated_at", "")
        if updated:
            from datetime import datetime
            try:
                last_update = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                days_ago = (datetime.now() - last_update).days
                score += max(0, 3 - days_ago / 60)
            except:
                pass
        desc = repo.get("description", "").lower()
        query_terms = query.lower().split()
        for term in query_terms:
            if term in desc:
                score += 1
        return score

    def get_discovered_sources(self):
        return self.discovered
