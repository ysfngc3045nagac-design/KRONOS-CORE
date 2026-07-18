"""KRONOS_DATA_HUB - Anomaly Detector"""
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime

class AnomalyDetector:
    def __init__(self, db_manager):
        self.db = db_manager
        self.thresholds = {"z_score": 3.0, "iqr_multiplier": 1.5, "min_records": 10,
                            "max_null_ratio": 0.3, "max_duplicate_ratio": 0.1}

    def detect_numeric_outliers(self, values, method="z_score"):
        if len(values) < self.thresholds["min_records"]:
            return []
        outliers = []
        if method == "z_score":
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0
            if std == 0:
                return []
            for i, value in enumerate(values):
                z_score = abs((value - mean) / std)
                if z_score > self.thresholds["z_score"]:
                    outliers.append({"index": i, "value": value, "z_score": round(z_score, 2),
                        "mean": round(mean, 2), "std": round(std, 2), "method": "z_score",
                        "severity": "high" if z_score > 4 else "medium"})
        elif method == "iqr":
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            q1 = sorted_vals[n // 4]
            q3 = sorted_vals[3 * n // 4]
            iqr = q3 - q1
            lower = q1 - self.thresholds["iqr_multiplier"] * iqr
            upper = q3 + self.thresholds["iqr_multiplier"] * iqr
            for i, value in enumerate(values):
                if value < lower or value > upper:
                    outliers.append({"index": i, "value": value, "q1": q1, "q3": q3, "iqr": iqr,
                        "bounds": (lower, upper), "method": "iqr",
                        "severity": "high" if value < lower - iqr or value > upper + iqr else "medium"})
        return outliers

    def detect_odds_anomalies(self, match_id):
        odds = self.db.fetch_all("SELECT * FROM odds WHERE match_id = ? ORDER BY timestamp DESC", (match_id,))
        if len(odds) < 2:
            return []
        anomalies = []
        for i in range(1, len(odds)):
            current = odds[i]
            previous = odds[i - 1]
            for field in ["home_odds", "draw_odds", "away_odds"]:
                curr_val = current.get(field, 0) or 0
                prev_val = previous.get(field, 0) or 0
                if prev_val > 0:
                    change = abs(curr_val - prev_val) / prev_val
                    if change > 0.2:
                        anomalies.append({"type": "odds_drift", "field": field, "previous": prev_val,
                            "current": curr_val, "change_percent": round(change * 100, 2),
                            "bookmaker": current.get("bookmaker", ""), "timestamp": current.get("timestamp", ""),
                            "severity": "high" if change > 0.5 else "medium"})
        return anomalies

    def detect_score_anomalies(self, match_id):
        match = self.db.fetch_one(
            """SELECT m.*, ht.name as home_team_name, at.name as away_team_name
               FROM matches m LEFT JOIN teams ht ON m.home_team_id = ht.id
               LEFT JOIN teams at ON m.away_team_id = at.id WHERE m.id = ?""", (match_id,))
        if not match or match.get("home_goals") is None:
            return []
        anomalies = []
        total_goals = (match.get("home_goals") or 0) + (match.get("away_goals") or 0)
        if total_goals > 7:
            anomalies.append({"type": "high_score", "total_goals": total_goals,
                "home_goals": match["home_goals"], "away_goals": match["away_goals"], "severity": "medium"})
        goal_diff = abs((match.get("home_goals") or 0) - (match.get("away_goals") or 0))
        if goal_diff > 5:
            anomalies.append({"type": "lopsided_score", "goal_difference": goal_diff, "severity": "medium"})
        return anomalies

    def detect_data_quality_issues(self, table_name, source_id=None):
        issues = []
        columns = self.db.fetch_all(f"PRAGMA table_info({table_name})")
        for col in columns:
            col_name = col["name"]
            where_clause = f"WHERE source_id = '{source_id}'" if source_id else ""
            total = self.db.fetch_scalar(f"SELECT COUNT(*) FROM {table_name} {where_clause}") or 0
            null_count = self.db.fetch_scalar(
                f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL {where_clause.replace('WHERE', 'AND') if where_clause else ''}") or 0
            if total > 0:
                null_ratio = null_count / total
                if null_ratio > self.thresholds["max_null_ratio"]:
                    issues.append({"type": "high_null_ratio", "table": table_name, "column": col_name,
                        "null_count": null_count, "total_count": total, "null_ratio": round(null_ratio, 3),
                        "severity": "high" if null_ratio > 0.5 else "medium"})
        if table_name == "matches":
            dupes = self.db.fetch_all("SELECT source_match_id, COUNT(*) as cnt FROM matches GROUP BY source_match_id HAVING cnt > 1")
            for dupe in dupes:
                issues.append({"type": "duplicate_records", "table": table_name,
                    "source_match_id": dupe["source_match_id"], "count": dupe["cnt"], "severity": "medium"})
        return issues

    def run_full_scan(self):
        all_issues = []
        tables = ["matches", "odds", "teams", "players", "news"]
        for table in tables:
            issues = self.detect_data_quality_issues(table)
            all_issues.extend(issues)
        recent_matches = self.db.fetch_all(
            "SELECT id FROM matches WHERE status = 'finished' AND match_date > date('now', '-7 days')")
        for match in recent_matches:
            anomalies = self.detect_score_anomalies(match["id"])
            all_issues.extend(anomalies)
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for issue in all_issues:
            severity_counts[issue.get("severity", "low")] += 1
        return {"total_issues": len(all_issues), "severity_breakdown": severity_counts, "issues": all_issues,
                "scan_time": datetime.now().isoformat(), "status": "clean" if len(all_issues) == 0 else "issues_found"}
