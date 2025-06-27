import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright

app = FastAPI()

class ParseRequest(BaseModel):
    username: str

@app.on_event("startup")
async def startup():
    app.state.playwright = await async_playwright().start()
    app.state.browser = await app.state.playwright.chromium.launch(headless=True)

@app.on_event("shutdown")
async def shutdown():
    await app.state.browser.close()
    await app.state.playwright.stop()

@app.post("/parse_gifts")
async def parse_gifts(request: ParseRequest):
    username = request.username
    try:
        context = await app.state.browser.new_context()
        page = await context.new_page()

        await page.goto("https://web.telegram.org/k/")
        await page.wait_for_selector("input[placeholder='Search']", timeout=10000)
        await page.fill("input[placeholder='Search']", username)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(3000)

        gifts_elements = await page.query_selector_all("div[data-testid='gift']")
        gifts = [await el.inner_text() for el in gifts_elements]

        await context.close()

        return {"username": username, "gifts": gifts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
