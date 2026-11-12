from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/")
def root_redirect():
    return RedirectResponse(url="/login")


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/transactions")
def transactions_page(request: Request):
    return templates.TemplateResponse("transactions.html", {"request": request})


@router.get("/budgets")
def budgets_page(request: Request):
    return templates.TemplateResponse("budgets.html", {"request": request})


@router.get("/reports")
def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


@router.get("/profile")
def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})
