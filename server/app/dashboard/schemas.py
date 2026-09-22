"""Dashboard API response schemas."""

from pydantic import BaseModel

from app.dashboard.models import DashboardSummary


class DashboardSummaryResponse(BaseModel):
    data: DashboardSummary
