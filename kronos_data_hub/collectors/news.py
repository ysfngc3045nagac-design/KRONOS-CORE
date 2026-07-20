"""KRONOS_DATA_HUB - News API Collector"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from .base_collector import BaseCollector

class NewsCollector(BaseCollector):
    def collect(self, query="football", category=None, days=1, **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            api_key = self._get_api_key()
            if not api_key:
                raise ValueError("News API key not configured")
            url = self._build_url("everything")
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            params = {"q": query, "from": from_date, "sortBy": "publishedAt", "language": "en", "pageSize": 100, "apiKey": api_key}
            if category:
                params["category"] = category
            response = self._make_request(url, params=params)
            response.raise_for_status()
            records = self.parse_response(response)
            saved = self._save_news(records)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"news_{query}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "query": query, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"news_{query}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "query": query}

    def _get_api_key(self):
        import os
        return os.getenv("NEWS_API_KEY") or self.config.get("api_key", "")

    def parse_response(self, response):
        data = self.json_parser.parse(response.content)
        articles = data.get("articles", []) if isinstance(data, dict) else []
        records = []
        for article in articles:
            records.append({"title": article.get("title", ""),
                "content": article.get("content", "") or article.get("description", ""), "url": article.get("url", ""),
                "source_name": article.get("source", {}).get("name", ""), "author": article.get("author", ""),
                "published_at": article.get("publishedAt", ""), "category": self._categorize_news(article.get("title", "")),
                "sentiment": 0.0, "relevance_score": 0.5, "source_id": self.source_id,
                "collected_at": datetime.now().isoformat()})
        return records

    def _categorize_news(self, title):
        title_lower = title.lower()
        keywords = {"injury": ["injury", "injured", "sidelined", "knock", "doubt"],
            "transfer": ["transfer", "sign", "deal", "move to", "join"],
            "match_preview": ["preview", "predicted lineup", "team news"],
            "suspension": ["suspended", "ban", "red card"], "tactical": ["tactics", "formation", "system"]}
        for category, words in keywords.items():
            if any(word in title_lower for word in words):
                return category
        return "general"

    def _save_news(self, records):
        # DUZELTME: category alani "injury"/"transfer" olarak etiketleniyordu
        # ama sadece news tablosuna yaziliyordu; ayri injuries/transfers
        # tablolari (dashboard'da her zaman 0 gorunen) hicbir zaman
        # doldurulmuyordu. Not: haber metninden guvenilir sekilde oyuncu adi
        # cikarmak icin NLP yok; burada sadece baslikta gecen bilinen takim
        # adina gore team_id eslestirilip kabaca kayit aciliyor (player_id
        # bos kalabilir). Daha dogru veri icin API-Football gibi yapisal bir
        # sakatlik/transfer kaynagi eklenmesi onerilir.
        saved = 0
        for record in records:
            team_id = self._match_team_in_text(record["title"])
            self.db.insert("news", {"title": record["title"], "content": record["content"], "url": record["url"],
                "source_id": self.source_id, "source_name": record["source_name"], "category": record["category"],
                "team_id": team_id, "published_at": record["published_at"], "sentiment": record["sentiment"],
                "relevance_score": record["relevance_score"], "is_processed": 0}, conflict_resolution="IGNORE")
            saved += 1
            if record["category"] == "injury":
                self.db.insert("injuries", {
                    "player_id": None, "team_id": team_id, "injury_type": "unspecified",
                    "injury_detail": record["title"], "expected_return": None, "status": "out",
                    "source_id": self.source_id, "reported_at": record["published_at"],
                }, conflict_resolution="IGNORE")
            elif record["category"] == "transfer":
                self.db.insert("transfers", {
                    "player_id": None, "from_team_id": None, "to_team_id": team_id,
                    "transfer_type": "news", "fee": 0.0, "currency": "EUR",
                    "transfer_date": (record["published_at"] or "")[:10], "season": "",
                    "source_id": self.source_id,
                }, conflict_resolution="IGNORE")
        return saved

    def _match_team_in_text(self, text):
        if not text:
            return None
        row = self.db.fetch_one(
            "SELECT id FROM teams WHERE ? LIKE '%' || name || '%' ORDER BY LENGTH(name) DESC LIMIT 1",
            (text,))
        return row["id"] if row else None
