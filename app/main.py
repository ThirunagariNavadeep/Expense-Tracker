from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models.models import seed_default_categories
from app.routes.auth import router as auth_router
from app.routes.budgets import router as budgets_router
from app.routes.categories import router as categories_router
from app.routes.dashboard import router as dashboard_router
from app.routes.pages import router as pages_router
from app.routes.reports import router as reports_router
from app.routes.transactions import router as transactions_router

app = FastAPI(
    title="ExpenseTrack",
    description="Personal expense and budget management application",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")

app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(budgets_router)
app.include_router(dashboard_router)
app.include_router(reports_router)

Base.metadata.create_all(bind=engine)

from app.database import SessionLocal

with SessionLocal() as session:
    seed_default_categories(session)


@app.get("/health")
def health_check():
    return {"status": "ok"}
