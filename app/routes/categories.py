from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.models import Category, User
from app.schemas.schemas import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    categories = (
        db.query(Category)
        .filter(or_(Category.user_id == current_user.id, Category.is_default.is_(True)))
        .order_by(Category.is_default.desc(), Category.name.asc())
        .all()
    )
    return [CategoryRead.model_validate(item).model_dump(mode="json") for item in categories]


@router.post("")
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Category name is required.")

    category = (
        db.query(Category)
        .filter(Category.user_id == current_user.id, Category.name == payload.name.strip(), Category.type == payload.type)
        .first()
    )
    if category:
        raise HTTPException(status_code=400, detail="A category with that name already exists for this user.")

    new_category = Category(name=payload.name.strip(), type=payload.type, is_default=False, user_id=current_user.id)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return CategoryRead.model_validate(new_category).model_dump(mode="json")


@router.put("/{category_id}")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    if category.user_id != current_user.id or category.is_default:
        raise HTTPException(status_code=403, detail="You do not have permission to modify this category.")

    if payload.name is not None:
        category.name = payload.name.strip()
    if payload.type is not None:
        category.type = payload.type

    db.commit()
    db.refresh(category)
    return CategoryRead.model_validate(category).model_dump(mode="json")


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    if category.user_id != current_user.id or category.is_default:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this category.")

    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully."}
