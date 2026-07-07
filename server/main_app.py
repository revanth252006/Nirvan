from fastapi import FastAPI
from .database import engine
from . import models
from .routers import auth, circles, location, driving, safety, users, agents

# Create all database tables (SQLite for Phase 1)
models.Base.metadata.create_all(bind=engine)

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Nirvan Family Safety App - Backend")

import os
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Include new routers
app.include_router(auth.router)
app.include_router(circles.router)
app.include_router(location.router)
app.include_router(driving.router)
app.include_router(safety.router)
app.include_router(users.router)
app.include_router(agents.router)

@app.get("/")
def root():
    return {"status": "Nirvan Backend is running!", "version": "1.0.0"}

# Note: In Phase 2/3, we will migrate the /predict and /verify_audio endpoints
# from test_api.py into here and connect them to real Users and Circles!
