from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import devices, notifications, stats
from .services.arp_service import is_arp_available
from .services.cleanup_service import CleanupService
from .services.monitor_service import MonitorService


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    monitor = MonitorService()
    cleanup = CleanupService()
    app.state.monitor_service = monitor
    await monitor.start()
    cleanup.start()
    yield
    cleanup.stop()
    await monitor.stop()


app = FastAPI(title="BadPing", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/status")
async def status():
    return {
        "arp_available": is_arp_available(),
    }
