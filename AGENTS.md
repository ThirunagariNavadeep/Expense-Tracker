# ExpenseTrack Agent Instructions

## Purpose
This project is a personal expense and budget tracking application built with FastAPI, SQLAlchemy, SQLite and vanilla JavaScript. Follow the specification in `SPEC.md` and prioritize correctness, security and maintainability.

## Core Rules
- Keep the code modular and easy to understand.
- Use SQLAlchemy ORM queries, not raw SQL string concatenation.
- Validate all request data with Pydantic schemas.
- Enforce user ownership checks for every protected resource.
- Use secure password hashing and session cookies.
- Keep financial calculations based on Decimal values.
- Make UI pages functional, not just mockups.
- Write tests for auth, transactions, budgets and dashboard logic.

## Development Phases
1. Setup project scaffolding and dependencies.
2. Implement data models, DB configuration and seed categories.
3. Implement secure authentication and CSRF protection.
4. Implement transaction and category APIs.
5. Implement budget logic and budget APIs.
6. Implement dashboard and reporting APIs.
7. Implement the frontend UI.
8. Run pytest and fix failing cases.
9. Review security and documentation.

## Required Practices
- Work in small, testable steps.
- Prefer clear CRUD flows over large abstracted modules.
- Avoid adding unnecessary dependencies.
- Keep secrets in environment variables.
- Avoid destructive database actions during development/testing.
- Use a temporary SQLite database for tests.

## Deliverables
- Clear file structure under `app/`.
- Functional FastAPI API with Swagger docs.
- Responsive frontend pages.
- Passing automated tests.
- Documentation in `README.md`.
- Screenshots of the actual app in the final repo.
