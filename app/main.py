from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.registrations.router import router as registrations_router
from app.sessions.router import router as sessions_router
from app.training_types.router import router as training_types_router
from app.certificates.router import router as certificates_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="7.77 Training Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router)
app.include_router(training_types_router)
app.include_router(registrations_router)
app.include_router(sessions_router)
app.include_router(certificates_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
