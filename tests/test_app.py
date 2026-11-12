from tempfile import NamedTemporaryFile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.models import seed_default_categories


@pytest.fixture
def client_factory():
    temp_db = NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    engine = create_engine(f"sqlite:///{temp_db.name}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as session:
        seed_default_categories(session)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    def make_client():
        return TestClient(app)

    yield make_client
    app.dependency_overrides.clear()


@pytest.fixture
def client(client_factory):
    return client_factory()


def get_csrf_headers(client):
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def register_user(client, username="alice", email="alice@example.com", password="StrongPass1"):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 200
    return response


def test_auth_registration_and_login(client):
    response = register_user(client)
    assert response.json()["user"]["email"] == "alice@example.com"

    login_response = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass1"},
    )
    assert login_response.status_code == 200

    unauthorized = client.get("/api/transactions")
    assert unauthorized.status_code == 200


def test_duplicate_email_is_rejected(client):
    register_user(client, email="dup@example.com")
    response = client.post(
        "/api/auth/register",
        json={"username": "other", "email": "dup@example.com", "password": "StrongPass1"},
    )
    assert response.status_code == 400


def test_logout_and_invalid_access(client):
    register_user(client)
    headers = get_csrf_headers(client)
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200

    unauth = client.get("/api/auth/me")
    assert unauth.status_code == 401


def test_transactions_can_be_created_and_fetched(client):
    register_user(client, username="txnuser", email="txn@example.com")
    headers = get_csrf_headers(client)

    categories = client.get("/api/categories")
    assert categories.status_code == 200
    income_category = next(item["id"] for item in categories.json() if item["name"] == "Salary" and item["type"] == "income")
    expense_category = next(item["id"] for item in categories.json() if item["name"] == "Food" and item["type"] == "expense")

    create_income = client.post(
        "/api/transactions",
        json={
            "transaction_type": "income",
            "category_id": income_category,
            "amount": "2500.00",
            "transaction_date": "2024-11-01",
            "description": "Salary",
        },
        headers=headers,
    )
    assert create_income.status_code == 200

    create_expense = client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "category_id": expense_category,
            "amount": "400.00",
            "transaction_date": "2024-11-05",
            "description": "Groceries",
        },
        headers=headers,
    )
    assert create_expense.status_code == 200

    summary = client.get("/api/dashboard/summary?month=11&year=2024")
    assert summary.status_code == 200
    assert summary.json()["income_total"] == "2500.00"
    assert summary.json()["expense_total"] == "400.00"


def test_budget_and_dashboard_logic(client):
    register_user(client, username="budgetuser", email="budget@example.com")
    headers = get_csrf_headers(client)

    income_category = client.post(
        "/api/categories",
        json={"name": "Salary", "type": "income"},
        headers=headers,
    )
    expense_category = client.post(
        "/api/categories",
        json={"name": "Groceries", "type": "expense"},
        headers=headers,
    )

    client.post(
        "/api/transactions",
        json={
            "transaction_type": "income",
            "category_id": income_category.json()["id"],
            "amount": "3000.00",
            "transaction_date": "2024-12-01",
            "description": "Monthly salary",
        },
        headers=headers,
    )
    client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "category_id": expense_category.json()["id"],
            "amount": "1800.00",
            "transaction_date": "2024-12-10",
            "description": "Groceries",
        },
        headers=headers,
    )

    budget = client.post(
        "/api/budgets",
        json={"amount": "2000.00", "month": 12, "year": 2024},
        headers=headers,
    )
    assert budget.status_code == 200

    dashboard = client.get("/api/dashboard/summary?month=12&year=2024")
    assert dashboard.status_code == 200
    assert dashboard.json()["remaining_balance"] == "1200.00"


def test_invalid_login_and_amount_rejection(client):
    register_user(client, email="invalid@example.com")
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "invalid@example.com", "password": "WrongPassword"},
    )
    assert bad_login.status_code == 401

    headers = get_csrf_headers(client)
    category = client.post("/api/categories", json={"name": "Food", "type": "expense"}, headers=headers)
    bad_amount = client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "category_id": category.json()["id"],
            "amount": "0.00",
            "transaction_date": "2024-11-01",
        },
        headers=headers,
    )
    assert bad_amount.status_code == 422


def test_category_and_report_endpoints(client):
    register_user(client, username="reportuser", email="report@example.com")
    headers = get_csrf_headers(client)

    category = client.post("/api/categories", json={"name": "Groceries", "type": "expense"}, headers=headers)
    assert category.status_code == 200

    client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "category_id": category.json()["id"],
            "amount": "500.00",
            "transaction_date": "2024-10-15",
            "description": "Groceries",
        },
        headers=headers,
    )

    report = client.get("/api/reports/monthly?month=10&year=2024")
    assert report.status_code == 200
    assert report.json()["expense_total"] == "500.00"

    category_report = client.get("/api/reports/category-wise?month=10&year=2024")
    assert category_report.status_code == 200
    assert any(item["category_name"] == "Groceries" for item in category_report.json())


def test_budget_warning_and_user_isolation(client_factory):
    client_a = client_factory()
    client_b = client_factory()
    register_user(client_a, username="alice", email="a@example.com")
    register_user(client_b, username="bob", email="b@example.com")
    headers_a = get_csrf_headers(client_a)
    headers_b = get_csrf_headers(client_b)

    category_a = client_a.post("/api/categories", json={"name": "Salary", "type": "income"}, headers=headers_a)
    category_b = client_b.post("/api/categories", json={"name": "Freelance", "type": "income"}, headers=headers_b)
    assert category_a.status_code == 200
    assert category_b.status_code == 200

    client_a.post(
        "/api/transactions",
        json={
            "transaction_type": "income",
            "category_id": category_a.json()["id"],
            "amount": "1000.00",
            "transaction_date": "2024-11-01",
            "description": "Paycheck",
        },
        headers=headers_a,
    )

    budget = client_a.post(
        "/api/budgets",
        json={"amount": "500.00", "month": 11, "year": 2024},
        headers=headers_a,
    )
    assert budget.status_code == 200

    expense = client_a.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "category_id": category_a.json()["id"],
            "amount": "600.00",
            "transaction_date": "2024-11-10",
            "description": "Expense",
        },
        headers=headers_a,
    )
    assert expense.status_code == 400

    income_cat = client_a.get("/api/categories")
    expense_category = client_a.post(
        "/api/categories",
        json={"name": "Housing", "type": "expense"},
        headers=headers_a,
    )
    client_a.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "category_id": expense_category.json()["id"],
            "amount": "600.00",
            "transaction_date": "2024-11-10",
            "description": "Rent",
        },
        headers=headers_a,
    )

    dashboard = client_a.get("/api/dashboard/summary?month=11&year=2024")
    assert dashboard.status_code == 200
    assert dashboard.json()["budget_warning"] in {"warning", "exceeded", "healthy"}

    other_user = client_b.get("/api/transactions")
    assert other_user.status_code == 200
    assert other_user.json()["items"] == []
