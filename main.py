from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.customers.router import router as customer_router
from app.modules.projects.router import router as project_router
from api.auth import router as auth_router
from api.task import router as task_router
from api.admin_rbac import router as admin_rbac_router
from api.note import router as note_router
from contextlib import asynccontextmanager
from core.config import settings
from core.database import SessionLocal
from core.exception_handler import global_exception_handler, rate_limit_handler
from seeders.rbac_seed import seed_roles, seed_permissions, assign_admin_permissions
from seeders.admin_seed import create_admin

from core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = SessionLocal()

    try:
        seed_roles(db)
        seed_permissions(db)
        assign_admin_permissions(db)
        create_admin(db)

    finally:
        db.close()

    yield


app = FastAPI(title="Mini CRM", lifespan=lifespan)

cors_origins = settings.get_cors_origins_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=len(cors_origins) > 0 and "*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(customer_router)
app.include_router(project_router)
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(admin_rbac_router)
app.include_router(note_router)


app.add_middleware(SlowAPIMiddleware)

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.add_exception_handler(Exception, global_exception_handler)
