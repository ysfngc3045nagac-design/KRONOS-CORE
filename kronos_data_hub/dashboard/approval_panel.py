"""KRONOS_DATA_HUB - Approval Panel"""
from typing import Dict, List, Any, Optional
from datetime import datetime

class ApprovalPanel:
    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_approval_table()

    def _ensure_approval_table(self):
        self.db.execute("""CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL,
            action TEXT NOT NULL, old_value TEXT, new_value TEXT, confidence_score REAL,
            status TEXT DEFAULT 'pending', reviewed_by TEXT, review_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reviewed_at TIMESTAMP,
            UNIQUE(entity_type, entity_id, action))""")

    def submit_for_approval(self, entity_type, entity_id, action, old_value, new_value, confidence_score=0.0):
        return self.db.insert("approvals", {"entity_type": entity_type, "entity_id": entity_id, "action": action,
            "old_value": str(old_value) if old_value else None, "new_value": str(new_value) if new_value else None,
            "confidence_score": confidence_score, "status": "pending"}, conflict_resolution="REPLACE")

    def approve(self, approval_id, reviewer, notes=""):
        self.db.execute("UPDATE approvals SET status = 'approved', reviewed_by = ?, review_notes = ?, reviewed_at = ? WHERE id = ?",
            (reviewer, notes, datetime.now().isoformat(), approval_id))
        return True

    def reject(self, approval_id, reviewer, notes=""):
        self.db.execute("UPDATE approvals SET status = 'rejected', reviewed_by = ?, review_notes = ?, reviewed_at = ? WHERE id = ?",
            (reviewer, notes, datetime.now().isoformat(), approval_id))
        return True

    def get_pending(self, entity_type=None, limit=50):
        if entity_type:
            return self.db.fetch_all(
                "SELECT * FROM approvals WHERE status = 'pending' AND entity_type = ? ORDER BY confidence_score ASC, created_at DESC LIMIT ?",
                (entity_type, limit))
        return self.db.fetch_all(
            "SELECT * FROM approvals WHERE status = 'pending' ORDER BY confidence_score ASC, created_at DESC LIMIT ?", (limit,))

    def get_stats(self):
        total = self.db.fetch_scalar("SELECT COUNT(*) FROM approvals") or 0
        pending = self.db.fetch_scalar("SELECT COUNT(*) FROM approvals WHERE status = 'pending'") or 0
        approved = self.db.fetch_scalar("SELECT COUNT(*) FROM approvals WHERE status = 'approved'") or 0
        rejected = self.db.fetch_scalar("SELECT COUNT(*) FROM approvals WHERE status = 'rejected'") or 0
        return {"total": total, "pending": pending, "approved": approved, "rejected": rejected,
                "approval_rate": round(approved / max(total, 1) * 100, 2)}
