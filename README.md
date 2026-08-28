# ai_test_project

基于阿里云百炼（DashScope）OpenAI 兼容接口的多模态视觉识别测试项目，覆盖车辆承保相关的图像理解场景。

## 环境说明

- Python 版本：3.11（由 `.python-version` 锁定，uv 自动使用）
- 包管理器：[uv](https://docs.astral.sh/uv/)
- 虚拟环境：项目根目录 `.venv`，**打开 CodeBuddy 终端后自动激活，无需手动创建**

## 快速开始

### 一、配置 API Key

复制环境变量示例文件并填入真实密钥：

```powershell
Copy-Item .env.example .env
notepad .env
```

填入内容：

```
DASHSCOPE_API_KEY=sk-你的真实密钥
```

`.env` 已被 `.gitignore` 忽略，不会提交到仓库。

### 二、直接运行脚本

打开 CodeBuddy 终端（PowerShell），进入项目目录后虚拟环境自动激活，直接执行即可：

```powershell
python 28-test\open_ai_test1.py
```

无需再执行 `python -m venv .venv` 与 `pip install`。

## 自动激活原理

PowerShell 用户级配置文件
`C:\Users\<用户名>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`
中定义了 `Enable-NearestVenv` 函数：启动终端或执行 `cd` 时，从当前目录逐级向上查找
`.venv\Scripts\Activate.ps1` 并自动激活，切换目录时会先退出旧环境再激活新环境。

## 依赖管理

依赖统一在 `pyproject.toml` 中声明，`uv.lock` 锁定版本。

```powershell
# 安装新依赖
uv add <包名>

# 移除依赖
uv remove <包名>

# 同步环境（换机器或拉取他人改动后）
uv sync

# 不激活环境直接运行（uv 自动处理依赖）
uv run 28-test\open_ai_test1.py
```

## 目录结构

```
ai_test_project/
├── 28-test/                 # 测试脚本目录
│   ├── open_ai_test1.py     # 场景一：单图 —— 车辆里程表读数识别
│   ├── open_ai_test2.py     # 场景二
│   ├── open_ai_test3.py     # 场景三：多图 —— 承保验车（五视角外观审核）
│   ├── open_ai_test4.py     # 场景四
│   └── open_ai_test5.py     # 场景五：单图 —— 危险驾驶行为检测
├── .python-version          # Python 版本锁定（3.11）
├── .env.example             # 环境变量示例
├── pyproject.toml           # 项目与依赖声明
└── uv.lock                  # 依赖版本锁文件
```

## 脚本接口说明

全部脚本遵循统一模式：

| 项 | 值 |
| --- | --- |
| 依赖 | `openai` |
| 鉴权 | 环境变量 `DASHSCOPE_API_KEY` |
| 接口地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 模型 | `qwen-vl-max` |
| 调用方式 | `client.chat.completions.create` |

## 注意事项

- 脚本依赖环境变量 `DASHSCOPE_API_KEY`，未配置时会因 `api_key=None` 而调用失败。
- 统一使用 `uv add` / `uv remove` 管理依赖，避免直接用 `pip install` 导致
  `pyproject.toml` 与实际环境不一致。
- `.venv`、`__pycache__`、`.env` 均已加入 `.gitignore`，不纳入版本控制。
