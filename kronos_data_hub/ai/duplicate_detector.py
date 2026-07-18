"""KRONOS_DATA_HUB - Duplicate Detector"""
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from difflib import SequenceMatcher

class DuplicateDetector:
    def __init__(self, db_manager):
        self.db = db_manager
        self.similarity_threshold = 0.85

    def find_duplicates(self, table_name, key_fields, check_fields=None):
        fields = key_fields + (check_fields or [])
        field_str = ", ".join(fields)
        query = f"SELECT {field_str}, COUNT(*) as cnt FROM {table_name} GROUP BY {field_str} HAVING cnt > 1"
        return self.db.fetch_all(query)

    def find_similar_teams(self, threshold=0.85):
        teams = self.db.fetch_all("SELECT id, name, country FROM teams WHERE name IS NOT NULL")
        similar_pairs = []
        for i, team1 in enumerate(teams):
            for team2 in teams[i+1:]:
                if team1["country"] != team2["country"]:
                    continue
                similarity = self._string_similarity(team1["name"], team2["name"])
                if similarity >= threshold:
                    similar_pairs.append({"team1_id": team1["id"], "team1_name": team1["name"],
                        "team2_id": team2["id"], "team2_name": team2["name"], "similarity": round(similarity, 3),
                        "country": team1["country"]})
        return sorted(similar_pairs, key=lambda x: x["similarity"], reverse=True)

    def find_similar_matches(self, days_window=1):
        matches = self.db.fetch_all(
            "SELECT id, match_date, home_team_id, away_team_id, source_id FROM matches WHERE match_date > date('now', ?)",
            (f"-{days_window} days",))
        duplicates = []
        for i, m1 in enumerate(matches):
            for m2 in matches[i+1:]:
                if (m1["home_team_id"] == m2["home_team_id"] and m1["away_team_id"] == m2["away_team_id"] and
                    m1["match_date"] == m2["match_date"] and m1["source_id"] != m2["source_id"]):
                    duplicates.append({"match1_id": m1["id"], "match2_id": m2["id"], "match_date": m1["match_date"],
                        "source1": m1["source_id"], "source2": m2["source_id"]})
        return duplicates

    def merge_duplicate_matches(self, match1_id, match2_id, prefer_source=None):
        m1 = self.db.fetch_one("SELECT * FROM matches WHERE id = ?", (match1_id,))
        m2 = self.db.fetch_one("SELECT * FROM matches WHERE id = ?", (match2_id,))
        if not m1 or not m2:
            return {"error": "Match not found"}
        if prefer_source:
            primary = m1 if m1["source_id"] == prefer_source else m2
            secondary = m2 if primary == m1 else m1
        else:
            primary = m1 if m1.get("updated_at", "") >= m2.get("updated_at", "") else m2
            secondary = m2 if primary == m1 else m1
        merged = dict(primary)
        for key in secondary:
            if key not in merged or merged[key] is None:
                merged[key] = secondary[key]
        self.db.execute(
            """UPDATE matches SET home_goals = COALESCE(?, home_goals), away_goals = COALESCE(?, away_goals),
               venue = COALESCE(?, venue), referee = COALESCE(?, referee), status = COALESCE(?, status),
               updated_at = datetime('now') WHERE id = ?""",
            (merged.get("home_goals"), merged.get("away_goals"), merged.get("venue"), merged.get("referee"),
             merged.get("status"), primary["id"]))
        self.db.execute("UPDATE match_statistics SET match_id = ? WHERE match_id = ?", (primary["id"], secondary["id"]))
        self.db.execute("UPDATE odds SET match_id = ? WHERE match_id = ?", (primary["id"], secondary["id"]))
        self.db.execute("DELETE FROM matches WHERE id = ?", (secondary["id"],))
        return {"status": "merged", "kept_id": primary["id"], "removed_id": secondary["id"], "kept_source": primary["source_id"]}

    def _string_similarity(self, s1, s2):
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

    def generate_fingerprint(self, record, fields):
        values = [str(record.get(f, "")).lower().strip() for f in fields]
        fingerprint = "|".join(values)
        return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]

    def get_duplicate_stats(self):
        stats = {}
        for table in ["matches", "teams", "players", "news"]:
            count = self.db.fetch_scalar(f"SELECT COUNT(*) FROM {table}") or 0
            stats[table] = {"total": count}
        similar_teams = self.find_similar_teams()
        stats["similar_teams"] = len(similar_teams)
        similar_matches = self.find_similar_matches(days_window=7)
        stats["duplicate_matches_7d"] = len(similar_matches)
        return stats
