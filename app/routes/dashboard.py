from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.models import Category, Transaction, User
from app.services.finance_service import get_dashboard_summary, get_month_totals, get_overall_budget, get_category_totals

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_summary(
    month: int | None = Query(default=None),
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    target_month = month or now.month
    target_year = year or now.year
    summary = get_dashboard_summary(db, current_user.id, target_month, target_year)
    summary["selected_month"] = target_month
    summary["selected_year"] = target_year
    return summary


@router.get("/category-breakdown")
def get_category_breakdown(
    month: int | None = Query(default=None),
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    target_month = month or now.month
    target_year = year or now.year
    return get_category_totals(db, current_user.id, target_month, target_year, "expense")


@router.get("/monthly-trends")
def get_monthly_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.finance_service import get_monthly_trend

    return get_monthly_trend(db, current_user.id, months=6)
