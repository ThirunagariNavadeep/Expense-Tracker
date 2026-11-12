from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.models import Category, Transaction, User
from app.services.finance_service import get_category_totals, get_month_totals, money_to_string

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/monthly")
def monthly_summary(
    month: int | None = Query(default=None),
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    target_month = month or now.month
    target_year = year or now.year
    income_total = get_month_totals(db, current_user.id, target_month, target_year, "income")
    expense_total = get_month_totals(db, current_user.id, target_month, target_year, "expense")
    return {
        "month": target_month,
        "year": target_year,
        "income_total": money_to_string(income_total),
        "expense_total": money_to_string(expense_total),
        "remaining_balance": money_to_string(income_total - expense_total),
    }


@router.get("/category-wise")
def category_wise_report(
    month: int | None = Query(default=None),
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    target_month = month or now.month
    target_year = year or now.year
    return get_category_totals(db, current_user.id, target_month, target_year, "expense")
