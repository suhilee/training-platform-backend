from fastapi import FastAPI

app = FastAPI(title="7.77 Training Platform API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}