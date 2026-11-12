from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_csrf
from app.database import get_db
from app.models.models import Category, Transaction, User
from app.schemas.schemas import TransactionCreate, TransactionRead, TransactionUpdate

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def list_transactions(
    transaction_type: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if search:
        like_term = f"%{search}%"
        query = query.join(Category, Category.id == Transaction.category_id, isouter=True)
        query = query.filter(
            or_(
                Transaction.description.ilike(like_term),
                Transaction.transaction_type.ilike(like_term),
                Category.name.ilike(like_term),
            )
        )

    total = query.count()
    items = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [TransactionRead.model_validate(item).model_dump(mode="json") for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("")
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: User = Depends(require_csrf),
):
    category = db.query(Category).filter(Category.id == payload.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    if category.user_id not in {current_user.id, None}:
        raise HTTPException(status_code=403, detail="This category does not belong to you.")
    if category.type != payload.transaction_type:
        raise HTTPException(status_code=400, detail="Selected category does not match the transaction type.")

    transaction = Transaction(
        user_id=current_user.id,
        category_id=payload.category_id,
        transaction_type=payload.transaction_type,
        amount=Decimal(str(payload.amount)),
        description=payload.description.strip() if payload.description else None,
        transaction_date=payload.transaction_date,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return TransactionRead.model_validate(transaction).model_dump(mode="json")


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this transaction.")
    return TransactionRead.model_validate(transaction).model_dump(mode="json")


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: User = Depends(require_csrf),
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this transaction.")

    if payload.category_id is not None:
        category = db.query(Category).filter(Category.id == payload.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        if category.user_id not in {current_user.id, None}:
            raise HTTPException(status_code=403, detail="This category does not belong to you.")
        new_type = payload.transaction_type or transaction.transaction_type
        if category.type != new_type:
            raise HTTPException(status_code=400, detail="Selected category does not match the transaction type.")
        transaction.category_id = payload.category_id

    if payload.amount is not None:
        transaction.amount = Decimal(str(payload.amount))
    if payload.description is not None:
        transaction.description = payload.description.strip() if payload.description else None
    if payload.transaction_date is not None:
        transaction.transaction_date = payload.transaction_date
    if payload.transaction_type is not None:
        transaction.transaction_type = payload.transaction_type

    db.commit()
    db.refresh(transaction)
    return TransactionRead.model_validate(transaction).model_dump(mode="json")


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: User = Depends(require_csrf),
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this transaction.")

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully."}
