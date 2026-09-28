from fastapi import FastAPI

from app.auth.router import router as auth_router

app = FastAPI(title="7.77 Training Platform API")

app.include_router(auth_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
