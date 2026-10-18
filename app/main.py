from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.registrations.router import router as registrations_router
from app.sessions.router import router as sessions_router

app = FastAPI(title="7.77 Training Platform API")

app.include_router(auth_router)
app.include_router(registrations_router)
app.include_router(sessions_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
