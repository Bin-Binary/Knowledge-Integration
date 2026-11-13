import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from dotenv import load_dotenv
from config.system_config import AgentSystemConfig


def start_server() -> None:
    """生产级程序总启动入口：从统一配置中心读取网络参数并拉起服务"""
    load_dotenv()

    cfg_path = os.getenv("AGENT_CONFIG_PATH", "config/agent_settings.json")
    sys_cfg = AgentSystemConfig.load_from_json(cfg_path)
    srv = sys_cfg.server

    uvicorn.run(
        "api.server:app",
        host=srv.host,
        port=srv.port,
        workers=1 if srv.reload else srv.workers,
        reload=srv.reload,
        log_level=srv.log_level,
        access_log=True
    )

if __name__ == "__main__":
    start_server()
