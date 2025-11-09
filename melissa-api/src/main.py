from fastapi import FastAPI

# ▼ ДОБАВЬ ЭТО:
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
# ▲ теперь os.getenv(...) увидит переменные из melissa-api/.env

from src.routes.health import router as health_router
from src.routes.compile import router as compile_router
from src.routes.strategies import router as strategies_router
from src.routes.artifacts import router as artifacts_router
from src.routes.devices import router as devices_router
from src.routes.link import router as link_router     # ← добавить

app = FastAPI(title="Melissa API", version="0.1.0")

app.include_router(health_router,     prefix="/health",        tags=["health"])
app.include_router(compile_router,    prefix="/v1/compile",    tags=["compile"])
app.include_router(strategies_router, prefix="/v1/strategies", tags=["strategies"])
app.include_router(artifacts_router,  prefix="/v1/artifacts",  tags=["artifacts"])
app.include_router(devices_router,    prefix="/v1/devices",    tags=["devices"])
app.include_router(link_router,                               tags=["link"])  # ← добавить