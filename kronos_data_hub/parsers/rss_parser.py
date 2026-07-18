"""KRONOS_DATA_HUB - RSS Parser"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET

class RSSParser:
    def __init__(self):
        self.errors = []
        self.feed_data = {}
        self.items = []

    def parse(self, xml_data):
        try:
            root = ET.fromstring(xml_data)
            if root.tag.endswith("rss") or root.tag == "rss":
                return self._parse_rss(root)
            elif root.tag.endswith("feed") or root.tag == "feed":
                return self._parse_atom(root)
            else:
                return self._parse_rss(root)
        except Exception as e:
            self.errors.append(f"RSS parse error: {e}")
            return {"error": str(e), "items": []}

    def _parse_rss(self, root):
        channel = root.find("channel")
        if channel is None:
            return {"error": "No channel found", "items": []}
        self.feed_data = {
            "title": self._get_text(channel, "title"), "link": self._get_text(channel, "link"),
            "description": self._get_text(channel, "description"), "language": self._get_text(channel, "language"),
            "last_build_date": self._get_text(channel, "lastBuildDate"), "type": "rss"
        }
        self.items = []
        for item in channel.findall("item"):
            self.items.append({
                "title": self._get_text(item, "title"), "link": self._get_text(item, "link"),
                "description": self._get_text(item, "description"),
                "pub_date": self._parse_date(self._get_text(item, "pubDate")),
                "guid": self._get_text(item, "guid"),
                "category": [cat.text for cat in item.findall("category") if cat.text],
                "author": self._get_text(item, "author") or self._get_text(item, "{http://purl.org/dc/elements/1.1/}creator"),
                "content": self._get_text(item, "{http://purl.org/rss/1.0/modules/content/}encoded")
            })
        return {"feed": self.feed_data, "items": self.items, "item_count": len(self.items)}

    def _parse_atom(self, root):
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        self.feed_data = {"title": self._get_text(root, "title", ns), "link": self._get_attr(root, "link", "href", ns),
                           "updated": self._get_text(root, "updated", ns), "type": "atom"}
        self.items = []
        for entry in root.findall("atom:entry", ns):
            self.items.append({
                "title": self._get_text(entry, "atom:title", ns), "link": self._get_attr(entry, "atom:link", "href", ns),
                "summary": self._get_text(entry, "atom:summary", ns),
                "pub_date": self._parse_date(self._get_text(entry, "atom:updated", ns)),
                "id": self._get_text(entry, "atom:id", ns), "author": self._get_text(entry, "atom:author/atom:name", ns),
                "content": self._get_text(entry, "atom:content", ns)
            })
        return {"feed": self.feed_data, "items": self.items, "item_count": len(self.items)}

    def _get_text(self, element, tag, ns=None):
        child = element.find(tag, ns) if ns else element.find(tag)
        return child.text.strip() if child is not None and child.text else ""

    def _get_attr(self, element, tag, attr, ns=None):
        child = element.find(tag, ns) if ns else element.find(tag)
        return child.get(attr, "") if child is not None else ""

    def _parse_date(self, date_str):
        if not date_str:
            return None
        formats = ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT", "%Y-%m-%dT%H:%M:%SZ",
                   "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        return date_str

    def filter_items(self, category=None, keyword=None, since=None):
        filtered = self.items
        if category:
            filtered = [item for item in filtered if category in item.get("category", [])]
        if keyword:
            kw = keyword.lower()
            filtered = [item for item in filtered if kw in item.get("title", "").lower() or kw in item.get("description", "").lower()]
        if since:
            filtered = [item for item in filtered if item.get("pub_date") and item["pub_date"] >= since]
        return filtered
