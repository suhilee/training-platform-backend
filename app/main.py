from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import uuid
import logging
from app.core.request_context import (
    create_request_id,
    reset_request_context,
    set_request_context,
)

from app.auth.router import router as auth_router
from app.registrations.router import router as registrations_router
from app.sessions.router import router as sessions_router
from app.training_types.router import router as training_types_router
from app.certificates.router import router as certificates_router
from app.instructors.router import (
    public_router as public_instructors_router,
    router as instructors_router,
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="7.77 Training Platform API")

UPLOADS_DIRECTORY = Path(__file__).resolve().parent.parent / "uploads"
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOADS_DIRECTORY, check_dir=False),
    name="uploads",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:4173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

logger = logging.getLogger("uvicorn.error")


@app.middleware("http")
async def add_request_context(request, call_next):
    request_id = create_request_id()
    endpoint = f"{request.method} {request.url.path}"

    request_id_token, endpoint_token = set_request_context(
        request_id,
        endpoint,
    )

    try:
        response = await call_next(request)

    except Exception:
        logger.exception(
            "Unhandled exception | request_id=%s | endpoint=%s",
            request_id,
            endpoint,
        )
        raise

    finally:
        reset_request_context(
            request_id_token,
            endpoint_token,
        )

    return response

app.include_router(auth_router)
app.include_router(training_types_router)
app.include_router(instructors_router)
app.include_router(public_instructors_router)
app.include_router(registrations_router)
app.include_router(sessions_router)
app.include_router(certificates_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
