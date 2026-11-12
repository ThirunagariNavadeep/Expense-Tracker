from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal["income", "expense"]


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: Literal["income", "expense"] | None = None


class CategoryRead(BaseModel):
    id: int
    user_id: int | None = None
    name: str
    type: str
    is_default: bool = False

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    category_id: int
    amount: Decimal = Field(..., gt=0)
    description: str | None = None
    transaction_date: date


class TransactionCreate(TransactionBase):
    transaction_type: Literal["income", "expense"]


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    description: str | None = None
    transaction_date: date | None = None
    transaction_type: Literal["income", "expense"] | None = None


class TransactionRead(BaseModel):
    id: int
    user_id: int
    category_id: int
    transaction_type: str
    amount: Decimal
    description: str | None = None
    transaction_date: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("amount", when_used="json")
    def serialize_amount(self, value: Decimal) -> str:
        return format(value.quantize(Decimal("0.01")), ".2f")


class BudgetBase(BaseModel):
    category_id: int | None = None
    amount: Decimal = Field(..., gt=0)
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    month: int | None = Field(default=None, ge=1, le=12)
    year: int | None = Field(default=None, ge=2000)


class BudgetRead(BaseModel):
    id: int
    user_id: int
    category_id: int | None = None
    amount: Decimal
    month: int
    year: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("amount", when_used="json")
    def serialize_amount(self, value: Decimal) -> str:
        return format(value.quantize(Decimal("0.01")), ".2f")
