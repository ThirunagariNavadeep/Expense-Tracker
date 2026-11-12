from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.models import Budget, Category, Transaction


DEFAULT_DECIMAL_ZERO = Decimal("0.00")


def money_to_string(value) -> str:
    decimal_value = Decimal(str(value))
    return format(decimal_value.quantize(Decimal("0.01")), ".2f")


def month_boundaries(month: int, year: int):
    start_date = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    end_date = next_month - timedelta(days=1)
    return start_date, end_date


def normalize_decimal(value) -> Decimal:
    return Decimal(str(value)) if not isinstance(value, Decimal) else value


def get_month_totals(db: Session, user_id: int, month: int, year: int, transaction_type: str) -> Decimal:
    start_date, end_date = month_boundaries(month, year)
    total = (
        db.query(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )
    return normalize_decimal(total or Decimal("0.00"))


def get_category_totals(db: Session, user_id: int, month: int, year: int, transaction_type: str):
    start_date, end_date = month_boundaries(month, year)
    rows = (
        db.query(
            Category.id,
            Category.name,
            func.coalesce(func.sum(
                Transaction.amount
            ), Decimal("0.00")).label("total"),
        )
        .outerjoin(
            Transaction,
            (Transaction.category_id == Category.id)
            & (Transaction.transaction_type == transaction_type)
            & (Transaction.user_id == user_id)
            & (Transaction.transaction_date >= start_date)
            & (Transaction.transaction_date <= end_date),
        )
        .filter(Category.type == transaction_type)
        .filter(or_(Category.user_id == user_id, Category.is_default.is_(True)))
        .group_by(Category.id, Category.name)
        .all()
    )
    result = []
    for category_id, name, total in rows:
        result.append({"category_id": category_id, "category_name": name, "total": money_to_string(total)})
    return result


def get_overall_budget(db: Session, user_id: int, month: int, year: int) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(Budget.amount), Decimal("0.00")))
        .filter(Budget.user_id == user_id, Budget.month == month, Budget.year == year, Budget.category_id.is_(None))
        .scalar()
    )
    return normalize_decimal(total or Decimal("0.00"))


def get_budget_utilization(db: Session, user_id: int, month: int, year: int) -> Decimal:
    monthly_budget = get_overall_budget(db, user_id, month, year)
    expense_total = get_month_totals(db, user_id, month, year, "expense")
    if monthly_budget <= 0:
        return Decimal("0.00")
    return (expense_total / monthly_budget) * Decimal("100")


def get_recent_transactions(db: Session, user_id: int, limit: int = 5):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


def get_monthly_trend(db: Session, user_id: int, months: int = 6):
    result = []
    from datetime import datetime

    today = datetime.utcnow()
    for offset in range(months):
        month_date = (today.month - 1 + offset) % 12 + 1 if False else None

    # Generate from current month backward.
    current_year = today.year
    current_month = today.month
    for index in range(months):
        target_month = current_month - index
        target_year = current_year
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1
        start_date, end_date = month_boundaries(target_month, target_year)
        income_total = (
            db.query(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
            .filter(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "income",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .scalar()
        )
        expense_total = (
            db.query(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
            .filter(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "expense",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .scalar()
        )
        result.append(
            {
                "month": f"{target_year}-{target_month:02d}",
                "income": money_to_string(income_total or Decimal("0.00")),
                "expenses": money_to_string(expense_total or Decimal("0.00")),
            }
        )
    result.reverse()
    return result


def get_budget_warning_for_month(db: Session, user_id: int, month: int, year: int) -> str:
    monthly_budget = get_overall_budget(db, user_id, month, year)
    if monthly_budget <= 0:
        return "no_budget"

    expense_total = get_month_totals(db, user_id, month, year, "expense")
    utilization = (expense_total / monthly_budget) * Decimal("100")
    if utilization >= Decimal("100"):
        return "exceeded"
    if utilization >= Decimal("80"):
        return "warning"
    return "healthy"


def get_dashboard_summary(db: Session, user_id: int, month: int, year: int):
    income_total = get_month_totals(db, user_id, month, year, "income")
    expense_total = get_month_totals(db, user_id, month, year, "expense")
    monthly_budget = get_overall_budget(db, user_id, month, year)
    remaining_balance = income_total - expense_total
    remaining_budget = monthly_budget - expense_total
    utilization = Decimal("0.00")
    if monthly_budget > 0:
        utilization = (expense_total / monthly_budget) * Decimal("100")

    recent_transactions = get_recent_transactions(db, user_id, 5)
    recent_list = []
    for item in recent_transactions:
        recent_list.append(
            {
                "id": item.id,
                "type": item.transaction_type,
                "amount": item.amount,
                "description": item.description,
                "category_id": item.category_id,
                "transaction_date": item.transaction_date.isoformat(),
            }
        )

    return {
        "income_total": money_to_string(income_total),
        "expense_total": money_to_string(expense_total),
        "remaining_balance": money_to_string(remaining_balance),
        "monthly_budget": money_to_string(monthly_budget),
        "remaining_budget": money_to_string(remaining_budget),
        "budget_utilization": money_to_string(utilization),
        "budget_warning": get_budget_warning_for_month(db, user_id, month, year),
        "recent_transactions": [
            {
                **item,
                "amount": money_to_string(item["amount"]),
            }
            for item in recent_list
        ],
    }
