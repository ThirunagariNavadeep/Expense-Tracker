# ExpenseTrack Specification

## Overview
ExpenseTrack is a personal finance management web application built with Python, FastAPI, SQLAlchemy, SQLite, HTML, CSS and vanilla JavaScript. The app helps a user track income, expenses, monthly budgets and financial summaries while enforcing secure authentication and user-level isolation.

## Goals
- Provide a safe, user-owned budgeting and transaction dashboard.
- Support secure session-based authentication.
- Store data in SQLite with SQLAlchemy models.
- Keep calculations based on actual database records.
- Expose a FastAPI REST API with automatic OpenAPI schema.
- Offer a clean, responsive UI for dashboard, transactions, budgets and reports.
- Deliver test coverage for core auth, transaction and budget behavior.

## Functional Requirements
### Authentication
- Users can register with username, email and password.
- Duplicate emails are rejected.
- Users can log in and receive a secure session cookie.
- Users can log out and clear the session.
- Protected routes require an authenticated user.
- A user cannot access another user’s records.

### Dashboard
- Display total income for the selected month.
- Display total expenses for the selected month.
- Display remaining balance.
- Display monthly budget and utilization.
- Show recent transactions.
- Show category expense totals.
- Show monthly income-vs-expense trends.
- Use real records from the database.

### Transactions
- Users can add, edit, delete and view income and expense records.
- Each transaction includes amount, date, category, description and type.
- Transactions can be filtered by category, date range and search text.
- Income and expense records are stored separately by transaction type.

### Categories
- Default categories must be available for expense tracking.
- Users can create custom categories where needed.
- Categories are associated to a user unless they are shared defaults.

### Budgets
- Users can set an overall monthly budget.
- Users can set category-wise monthly budgets.
- Budgets can be updated or removed.
- Actual spending against the budget is calculated from tracked transactions.
- Budget warnings appear when spending reaches 80% or exceeds 100%.

### Reports
- Show monthly summaries for income and expenses.
- Show category-wise breakdowns.
- Show data by date range.
- Provide a readable visual summary using lightweight frontend charts.

## Non-Functional Requirements
- Use FastAPI for REST endpoints.
- Use SQLAlchemy ORM for all database logic.
- Use Decimal-compatible numeric storage for money.
- Validate all inputs with Pydantic schemas.
- Use secure password hashing and session-based authentication.
- Use environment variables for secrets and configuration.
- Avoid SQL string concatenation and unsafe queries.
- Protect user-owned resources with authorization checks.
- Ensure the app works locally with SQLite and can be adapted to other DB backends.

## Project Structure
- app/
  - __init__.py
  - main.py
  - config.py
  - database.py
  - models/
  - schemas/
  - routes/
  - services/
  - templates/
  - static/
- tests/
- .env.example
- .gitignore
- AGENTS.md
- README.md
- requirements.txt

## Acceptance Criteria
- User can register successfully.
- User can log in and out.
- User can add, update and delete income and expense transactions.
- Dashboard totals are correct.
- Budget warnings work when thresholds are crossed.
- User A cannot access User B’s records.
- Swagger docs are available via FastAPI.
- Automated pytest checks pass.
- App runs locally using documented commands.
- README includes setup instructions and screenshots.

## Workflow to Follow
1. Create project scaffolding and specification files.
2. Define architecture and implementation phases.
3. Implement database models and configuration.
4. Implement authentication and authorization.
5. Implement transaction APIs.
6. Implement budget APIs and calculations.
7. Implement dashboard and reporting APIs.
8. Implement frontend UI pages.
9. Add tests and run them.
10. Fix issues and verify behavior.
11. Review security, maintainability and documentation.
