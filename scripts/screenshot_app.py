import json
import random
import string
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


def register_user():
    username = "ux_demo_" + "".join(random.choices(string.ascii_lowercase, k=6))
    email = f"{username}@example.com"
    payload = json.dumps({"username": username, "email": email, "password": "Password123"}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/register",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        return response.status, username, email


def main():
    Path("screenshots").mkdir(exist_ok=True)
    status, username, email = register_user()
    if status != 200:
        raise RuntimeError(f"User registration failed with status {status}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:8000/login", wait_until="networkidle")
        page.screenshot(path="screenshots/login.png", full_page=True)
        page.fill('input[name="email"]', email)
        page.fill('input[name="password"]', "Password123")
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard")
        page.screenshot(path="screenshots/dashboard.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
