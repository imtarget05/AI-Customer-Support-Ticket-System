from pydantic import BaseModel


class DashboardStats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_category: dict[str, int]
    # HIGH or URGENT tickets not yet RESOLVED/CLOSED.
    high_priority_open: int
