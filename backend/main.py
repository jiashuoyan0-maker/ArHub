"""ArHub Web Backend - FastAPI entry point."""
from __future__ import annotations
import asyncio
import logging
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Windows 上必须使用 ProactorEventLoop 才能支持 asyncio.create_subprocess_exec
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import API_PORT, APPDATA_DIR, FRONTEND_DIST, IS_DESKTOP
from services.state_store import init_db
from services.workflow_engine import set_broadcast
from routers import workflows, artifacts, checkpoints, ws, settings, editor, extensions
from routers import docx_export as docx_export_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
LOG_DIR = APPDATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
APP_LOG_PATH = LOG_DIR / "backend-app.log"
ERROR_LOG_PATH = LOG_DIR / "backend-error.log"


def write_error_log(message: str) -> None:
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        pass


try:
    _fh = logging.FileHandler(APP_LOG_PATH, encoding="utf-8", mode="a")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(_fh)
except Exception:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    orig_handler = loop.get_exception_handler()
    def _log_exc(loop, context):
        write_error_log(f"ASYNCIO: {context.get('exception', 'no exception')}\n{context.get('message', '')}\n\n")
        if orig_handler:
            orig_handler(loop, context)
    loop.set_exception_handler(_log_exc)
    await init_db()
    # 注入 WebSocket 广播函数到 workflow_engine
    set_broadcast(ws.manager.broadcast)

    # 自动恢复被后端重启中断的工作流
    from services.state_store import get_workflows_to_resume
    from services.workflow_engine import run_workflow
    from routers.workflows import _tasks
    resume_ids = get_workflows_to_resume()
    for wf_id in resume_ids:
        logging.getLogger(__name__).info("Auto-resuming workflow %s after restart", wf_id)
        task = asyncio.create_task(run_workflow(wf_id))
        _tasks[wf_id] = task  # 注册到 _tasks 防止心跳检测重复触发

    # 启动心跳检测（每 60 秒检查僵尸工作流并自动恢复）
    from routers.workflows import start_heartbeat
    start_heartbeat()

    yield


app = FastAPI(title="ArHub", version="1.0.9", lifespan=lifespan)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    tb = traceback.format_exc()
    write_error_log(f"=== {request.method} {request.url.path} ===\n{type(exc).__name__}: {exc}\n{tb}\n\n")
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {str(exc)[:200]}"})



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://127.0.0.1:{API_PORT}",
        f"http://localhost:{API_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflows.router)
app.include_router(artifacts.router)
app.include_router(checkpoints.router)
app.include_router(settings.router)
app.include_router(editor.router)
app.include_router(ws.router)
app.include_router(docx_export_router.router)


# ============================================================
# Open-source compatibility endpoints. ArHub does not require activation.
# ============================================================
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class LicenseVerifyRequest(BaseModel):
    license_key: str
    machine_id: str


@app.post("/api/license/verify")
async def license_verify(req: LicenseVerifyRequest):
    """Keep legacy clients working without contacting a license server."""
    return {"valid": True, "message": "ArHub open-source edition does not require activation."}


@app.get("/api/license/status")
async def license_status():
    """产品版不再要求输入激活码；保留接口兼容旧前端。"""
    return {"licensed": True}


@app.middleware("http")
async def license_middleware(request: Request, call_next):
    """Compatibility no-op retained for installations using the old middleware stack."""
    return await call_next(request)


@app.get("/api/health")
async def health():
    return {"status": "ok", "desktop": IS_DESKTOP}


# Open, manifest-only extension registry. Schema v1 never imports or executes
# third-party extension code.
from extension_registry import ExtensionRegistry

_APP_ROOT = Path(__file__).resolve().parent.parent
_extension_registry = ExtensionRegistry(
    builtin_dir=_APP_ROOT / "extensions",
    user_dir=APPDATA_DIR / "extensions",
    schema_path=_APP_ROOT / "extension.schema.json",
)
extensions.configure(_extension_registry)
app.include_router(extensions.router)


@app.get("/api/extensions/registry")
async def extension_registry():
    return _extension_registry.snapshot()


@app.get("/api/extensions/schema")
async def extension_schema():
    return _extension_registry.schema()


@app.get("/api/templates")
async def get_templates():
    """返回可用的工作流模板"""
    from services.workflow_engine import TEMPLATES
    result = {}
    for key, tmpl in TEMPLATES.items():
        result[key] = {
            "name": tmpl.display_name,
            "pipeline_skill": tmpl.pipeline_skill,
            "steps": [
                {"skill_name": s.skill_name, "display_name": s.display_name,
                 "has_checkpoint": s.has_checkpoint, "checkpoint_type": s.checkpoint_type}
                for s in tmpl.sub_steps
            ],
        }
    return result


# --- 桌面模式：托管前端静态文件 ---
_IMMUTABLE_ASSET = re.compile(r"^(?:index-[\w-]+\.(?:js|css)|KaTeX_[\w.-]+\.(?:woff2|woff|ttf))$")


class FrontendStaticFiles(StaticFiles):
    """内容哈希资源长缓存；无哈希的 overlay 资源走 ETag 协商（304 可复用缓存体和 V8 code cache）。"""

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = (
            "public, max-age=31536000, immutable" if _IMMUTABLE_ASSET.match(path) else "no-cache"
        )
        return response


if IS_DESKTOP and FRONTEND_DIST.is_dir():
    # 静态资源（js/css/images）
    app.mount("/assets", FrontendStaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static-assets")

    # logo 等 public 文件
    @app.get("/logo.svg")
    async def serve_logo():
        logo = FRONTEND_DIST / "logo.svg"
        if logo.exists():
            return FileResponse(str(logo), media_type="image/svg+xml", headers={"Cache-Control": "no-cache"})

    # SPA fallback：所有非 /api /ws 路径返回 index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 先检查是否是静态文件
        static_file = FRONTEND_DIST / full_path
        if static_file.is_file() and not full_path.startswith("api") and not full_path.startswith("ws"):
            return FileResponse(str(static_file), headers={"Cache-Control": "no-cache"})
        # 否则返回 index.html（SPA 路由）
        return FileResponse(str(FRONTEND_DIST / "index.html"), headers={"Cache-Control": "no-cache"})
