"""环境变量加载工具（项目级公共模块，位于项目根目录）。

统一提供 .env 加载与必填环境变量读取能力，避免各脚本重复实现。

用法::

    from env_loader import load_dotenv, require_env

    load_dotenv()                            # 自动查找并加载 .env
    api_key = require_env("AGICTO_API_KEY")  # 读取不到时给出明确的中文修复指引

子目录脚本引用本模块前，需先把项目根目录加入模块搜索路径::

    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[N]))  # N 视脚本层级而定
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# .env 文件名
ENV_FILE_NAME = ".env"

# 本模块所在目录，即项目根目录（作为兜底查找位置）
PROJECT_ROOT = Path(__file__).resolve().parent


def _main_script_dir() -> Path:
    """推断入口脚本所在目录；交互式或模块方式运行时退回当前工作目录。"""
    argv0 = sys.argv[0] if sys.argv and sys.argv[0] else ""
    if argv0:
        script_path = Path(argv0).resolve()
        if script_path.is_file():
            return script_path.parent
    return Path.cwd()


def _candidate_env_files() -> list[Path]:
    """按优先级返回待加载的 .env 候选路径（已去重并保持顺序）。"""
    candidates = [
        _main_script_dir() / ENV_FILE_NAME,
        Path.cwd() / ENV_FILE_NAME,
        PROJECT_ROOT / ENV_FILE_NAME,
    ]
    result: list[Path] = []
    for item in candidates:
        resolved = item.resolve()
        if resolved not in result:
            result.append(resolved)
    return result


def load_dotenv(env_path: str | Path | None = None) -> list[Path]:
    """把 .env 中的 KEY=VALUE 写入 os.environ，不覆盖已存在的系统环境变量。

    :param env_path: 指定 .env 路径；为 None 时按「入口脚本目录 -> 当前工作目录 -> 项目根目录」顺序加载。
    :return: 实际成功加载的 .env 路径列表。
    """
    targets = [Path(env_path)] if env_path else _candidate_env_files()
    loaded: list[Path] = []

    for path in targets:
        if not path.is_file():
            continue
        # 用 utf-8-sig 读取，兼容带 BOM 的 .env（记事本另存后常见）
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
        loaded.append(path)

    return loaded


def require_env(name: str) -> str:
    """读取必填环境变量；缺失时抛出带修复指引的 SystemExit。

    :param name: 环境变量名。
    :return: 变量值（已去除首尾空白）。
    """
    value = os.environ.get(name, "").strip()
    if value:
        return value

    env_hint = "\n".join(f"  - {path}" for path in _candidate_env_files())
    raise SystemExit(
        f"未配置环境变量 {name}。请在下列任一 .env 文件中写入：\n"
        f"{env_hint}\n\n    {name}=你的取值\n\n"
        f"或在 PowerShell 会话中执行：$env:{name}='你的取值'"
    )
