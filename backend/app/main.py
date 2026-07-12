import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import setup_database
from .routers import auth, listings, messages

setup_database()

app = FastAPI(title="Workplace Market API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(messages.router)


@app.get("/health")
def health():
    return {"status": "ok"}
