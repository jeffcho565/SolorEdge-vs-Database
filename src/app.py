"""FastAPI application — serves the SPA and exposes the evaluation API."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.evaluator import evaluate_address

app = FastAPI(
    title="Edge Data Center Feasibility Analyzer",
    description=(
        "Given a commercial address, scores it across six data-driven criteria "
        "to determine whether it is a stronger candidate for an edge data center "
        "or for rooftop solar."
    ),
    version="1.0.0",
)

_STATIC = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


class AddressRequest(BaseModel):
    address: str


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_homepage():
    return HTMLResponse((_STATIC / "homepage.html").read_text(encoding="utf-8"))


@app.get("/analyze", response_class=HTMLResponse, include_in_schema=False)
async def serve_spa():
    return HTMLResponse((_STATIC / "index.html").read_text(encoding="utf-8"))


@app.post("/api/evaluate")
async def evaluate(request: AddressRequest):
    if not request.address.strip():
        raise HTTPException(status_code=400, detail="Address cannot be empty")
    try:
        return await evaluate_address(request.address.strip())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation error: {exc}")


@app.get("/health")
async def health():
    return {"status": "ok"}
