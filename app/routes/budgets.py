from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_csrf
from app.database import get_db
from app.models.models import Budget, Category, User
from app.schemas.schemas import BudgetCreate, BudgetRead, BudgetUpdate

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.get("")
def list_budgets(
    month: int | None = Query(default=None),
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Budget).filter(Budget.user_id == current_user.id)
    if month is not None:
        query = query.filter(Budget.month == month)
    if year is not None:
        query = query.filter(Budget.year == year)

    budgets = query.order_by(Budget.year.desc(), Budget.month.desc(), Budget.id.desc()).all()
    return [BudgetRead.model_validate(item).model_dump(mode="json") for item in budgets]


@router.post("")
def create_budget(
    payload: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: User = Depends(require_csrf),
):
    if payload.category_id is not None:
        category = db.query(Category).filter(Category.id == payload.category_id).first()
        if not category or category.user_id not in {current_user.id, None}:
            raise HTTPException(status_code=404, detail="Category not found.")
        if category.type != "expense":
            raise HTTPException(status_code=400, detail="Category budgets are only supported for expense categories.")

    existing = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.category_id == payload.category_id,
            Budget.month == payload.month,
            Budget.year == payload.year,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="A budget already exists for this category and month.")

    budget = Budget(
        user_id=current_user.id,
        category_id=payload.category_id,
        amount=Decimal(str(payload.amount)),
        month=payload.month,
        year=payload.year,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return BudgetRead.model_validate(budget).model_dump(mode="json")


@router.put("/{budget_id}")
def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: User = Depends(require_csrf),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found.")
    if budget.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this budget.")

    if payload.category_id is not None:
        category = db.query(Category).filter(Category.id == payload.category_id).first()
        if not category or category.user_id not in {current_user.id, None}:
            raise HTTPException(status_code=404, detail="Category not found.")
        if category.type != "expense":
            raise HTTPException(status_code=400, detail="Category budgets are only supported for expense categories.")
        budget.category_id = payload.category_id

    if payload.amount is not None:
        budget.amount = Decimal(str(payload.amount))
    if payload.month is not None:
        budget.month = payload.month
    if payload.year is not None:
        budget.year = payload.year

    db.commit()
    db.refresh(budget)
    return BudgetRead.model_validate(budget).model_dump(mode="json")


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: User = Depends(require_csrf),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found.")
    if budget.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this budget.")

    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully."}
