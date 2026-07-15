"""Mac takvimi analizi"""

from datetime import datetime


class ScheduleEngine:

    def days_between(self, first: datetime, second: datetime) -> int:
        return abs((second - first).days)

    def rest_score(self, days: int) -> float:
        if days >= 7:
            return 100
        if days >= 5:
            return 90
        if days >= 4:
            return 80
        if days >= 3:
            return 70
        if days >= 2:
            return 55
        return 35
