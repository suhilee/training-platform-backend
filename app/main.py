from fastapi import FastAPI

from app.auth.router import router as auth_router

from fastapi import Depends
from app.auth.dependencies import get_current_user
from app.models.user import User

app = FastAPI(title="7.77 Training Platform API")

app.include_router(auth_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/auth/me")
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    return {
        "id": str(current_user.id),
        "email": current_user.email,
    }
