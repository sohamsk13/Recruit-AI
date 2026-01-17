from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import jobs, applicants, admin, health
from .middleware.error_handler import error_handler

app = FastAPI(title="AI Hiring Platform")

# Add error handling middleware
app.middleware("http")(error_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
routers = [jobs.router, applicants.router, admin.router, health.router]
for router in routers:
    app.include_router(router)
