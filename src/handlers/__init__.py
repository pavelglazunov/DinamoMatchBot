from src.handlers.activity import router as activity_router
from src.handlers.start import router as start_router
from src.handlers.matches import router as matches_router

routers = [
    activity_router,
    start_router,
    matches_router,
]
