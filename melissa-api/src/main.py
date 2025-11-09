from fastapi import FastAPI

# ▼ ДОБАВЬ ЭТО:
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
# ▲ теперь os.getenv(...) увидит переменные из melissa-api/.env

from src.routes import health, compile as compile_rt, strategies, artifacts, devices
app = FastAPI(title="Melissa API", version="0.1.0")

app.include_router(health.router,     prefix="/health",       tags=["health"])
app.include_router(compile_rt.router, prefix="/v1/compile",   tags=["compile"])
app.include_router(strategies.router, prefix="/v1/strategies",tags=["strategies"])
app.include_router(artifacts.router,  prefix="/v1/artifacts", tags=["artifacts"])
app.include_router(devices.router,    prefix="/v1/devices",   tags=["devices"])