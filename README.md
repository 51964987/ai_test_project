# ai_test_project

基于阿里云百炼（DashScope）OpenAI 兼容接口的多模态视觉识别测试项目，覆盖车辆承保相关的图像理解场景。

## 环境说明

- Python 版本：3.11（由 `.python-version` 锁定，uv 自动使用）
- 包管理器：[uv](https://docs.astral.sh/uv/)
- 虚拟环境：项目根目录 `.venv`，**打开 CodeBuddy 终端后自动激活，无需手动创建**

### 已知环境问题：uv 托管解释器不可用

本机 uv 的托管 Python 目录（默认 `%APPDATA%\uv\python`，迁移到 `D:\uv-python` 同样如此）
被 Windows 判定为**不受信任的装入点**，uv 查询解释器时报：

```text
error: Failed to query Python interpreter
  Caused by: 无法遍历该路径，因为它包含不受信任的装入点。 (os error 448)
```

后果：`uv sync` / `uv run` / `uv python find` / `uv python install` 全部失败；
`.venv\Scripts\python.exe` 是失效的 uv trampoline，IDE 类型检查器因此解析不到任何第三方包，
会把 `pandas`、`openai` 等全部报成 `reportMissingImports`，并级联产生上百条误报。

**当前的处理方式**：`.venv` 改用系统 Python 重建，并在 `pyproject.toml` 的
`[tool.basedpyright]` 中显式指定 `venvPath` / `venv`，绕开自动发现。

`.venv` 再次损坏或换机器时，用下面的命令重建：

```powershell
uv venv --python 'D:\biancheng\python\python3.11.4\python.exe' --clear
uv sync --python 'D:\biancheng\python\python3.11.4\python.exe'
```

## 快速开始

### 一、配置环境变量

复制示例文件并填入真实密钥：

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` 已被 `.gitignore` 忽略，不会提交到仓库。文件里除 `DASHSCOPE_API_KEY` 外，
还包含 `PYTHONIOENCODING=utf-8` 与 `PYTHONUTF8=1`，`uv run` 会自动加载项目根的 `.env`。

### 二、直接运行脚本

打开 CodeBuddy 终端（PowerShell），进入项目目录后虚拟环境自动激活，直接执行即可：

```powershell
python 28-test\车险\car_test1.py
```

无需再执行 `python -m venv .venv` 与 `pip install`。

若终端里中文路径出现乱码，先执行 `chcp 65001` 切到 UTF-8 代码页，或用 Tab 补全路径。

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

# 重新生成锁文件（改动 pyproject 依赖后必须执行）
uv lock

# 不激活环境直接运行（uv 自动处理依赖）
uv run 28-test\车险\car_test1.py
```

当前声明的运行时依赖：

| 包 | 用途 |
| --- | --- |
| `openai` | OpenAI 兼容模式调用（`vlm/`、`车险/`） |
| `dashscope` | DashScope 原生 SDK（`local/`） |
| `pandas` | 读写 Excel 批量任务表 |
| `openpyxl` | `to_excel` / `read_excel` 的 Excel 引擎 |
| `pillow` | 视觉定位结果绘制检测框 |
| `requests` | 下载远端图片 |

开发依赖 `pandas-stubs`：pandas 不自带 `py.typed`，装上官方类型存根后类型检查器
才能校验 DataFrame 相关调用。

`28-test\车险\2-car-test5.py` 依赖的 `torch` / `transformers` / `qwen-vl-utils` 体积过大
（数 GB），**未列入**项目依赖，需要本地 GPU 部署时自行安装。

## 目录结构

```text
ai_test_project/
├── main.py                            # 项目入口占位
├── 28-test/
│   ├── vlm/                           # OpenAI 兼容模式 · 寿险单证批量抽取
│   │   ├── batch_insurance_vlm.py     # 生产版：重试 + 断点续跑 + 本地图/OSS + CLI
│   │   ├── minimal_vlm.py             # 最小可运行版：Excel 逐行调用
│   │   └── make_template.py           # 生成 prompt_template_cn.xlsx 模板
│   ├── local/                         # DashScope 原生 SDK · 本地图片识别
│   │   ├── local_image_vlm.py         # 单图/多图/目录批量问答，支持 file:// 与 Base64
│   │   ├── insurance_extract.py       # 寿险单证抽取场景集（复用 local_image_vlm）
│   │   └── minimal_local.py           # 最小示例：本地图片单图问答
│   └── 车险/                          # OpenAI 兼容模式 · 车险场景集
│       ├── car_test1.py               # 单图：里程表读数识别（高清模式 OCR）
│       ├── car_test2.py               # 多图：承保验车（五视角外观审核）
│       ├── car_test3.py               # 视频帧序列：危险驾驶行为检测
│       ├── car_test4.py               # 单图：事故要素 JSON 抽取（response_format）
│       ├── car_test5.py               # 多图：事故前后同车核验（反欺诈）
│       ├── car_test6.py               # 生产版：批量 Excel 流水线（重试 + 并发 + 断点续跑）
│       ├── 2-car_test1.py             # 单轮图文问答 + 完整响应对象解析
│       ├── 2-car_test2.py             # 视觉定位：框出轮毂位置并绘制到原图
│       ├── 2-car_test3.py             # 多轮对话：定损追问（图片随轮重传）
│       ├── 2-car_test4.py             # 视频理解：video_url 与帧序列两种方式
│       ├── 2-car-test5.py             # 本地部署：Transformers 直跑 Qwen2.5-VL（可选）
│       └── 2-car-test6.py             # 流式输出 + 思考模式（qwen3-vl-plus）
├── .python-version                    # Python 版本锁定（3.11）
├── .env.example                       # 环境变量示例
├── pyproject.toml                     # 项目、依赖与类型检查配置
└── uv.lock                            # 依赖版本锁文件
```

## 脚本接口说明

全部脚本遵循统一模式：

| 项 | 值 |
| --- | --- |
| 鉴权 | 环境变量 `DASHSCOPE_API_KEY` |
| 接口地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 模型 | `qwen-vl-max` / `qwen-vl-max-latest` / `qwen-vl-plus` / `qwen3-vl-plus` |
| OpenAI 兼容模式 | `client.chat.completions.create` |
| DashScope 原生 SDK | `MultiModalConversation.call` |

## 类型检查

类型检查器为 **basedpyright**（IDE 内置），配置集中在 `pyproject.toml` 的
`[tool.basedpyright]`：

| 配置项 | 说明 |
| --- | --- |
| `venvPath` / `venv` | 显式指向 `.venv`，绕开失效的 uv 托管解释器 |
| `include` | 分析范围限定为 `main.py` 与 `28-test` |
| `reportUnknownMemberType = false` | pandas-stubs 自身含 Unknown（`read_excel` / `to_excel` 有数十个重载） |
| `reportAny = false` | pandas `Series` 取值一律返回 `Any` |

这两条规则只针对第三方存根的固有噪音关闭，代码层面的真实类型错误仍会完整上报。

**已知限制**：IDE 不会收集 `28-test\车险\` 目录（中文路径）的诊断，该目录的问题需靠
`ruff check` 与 LSP 手动核查发现。

### 编写新脚本时的约定

- `messages` 统一标注为 `list[ChatCompletionMessageParam]`（SDK 官方类型）。
- 构造 `content` 时**逐条 `append`，不要用列表推导**：推导式会退化成
  `dict[str, object]`，无法通过 SDK 的 `TypedDict` 校验。
- DashScope 扩展字段（`type="video"` / `type="video_url"` / `fps`）在 openai SDK 中没有
  对应类型，用 `cast(list[ChatCompletionMessageParam], [...])` 声明。
- `completion.usage` 与 `message.content` 在 SDK 中均为可选字段，用海象运算符
  （`if usage := completion.usage:`）或 `or ""` 取值兼做类型收窄。
- `df.iterrows()` 的索引静态类型是 `Hashable`，不能直接做 `+1`；需要行号时用
  `enumerate(df.iterrows(), 1)`。
- 用 `argparse.Namespace` 子类给 `parse_args` 补静态类型时，**只声明属性、不要赋默认值**。
  argparse 只在属性不存在时才注入 `default`，一旦类里预置了值（哪怕是 `""`），
  `add_argument(default=...)` 会被整个跳过，命令行默认值静默失效。
  此时用文件级 `# pyright: reportUninitializedInstanceVariable=false` 消除未初始化告警，
  不要靠"类默认值填成和 default 一样"来绕——两处同步迟早会漂。
- 读回 Excel 的结果列后必须 `df["response"] = df["response"].fillna("").astype(str)`：
  一是全空列会被推断成 `float64`，而 **pandas 3.x 不允许往 float 列写字符串**
  （2.x 会静默 upcast），写入时直接抛 `TypeError`；
  二是 `str(NaN) == "nan"` 是 truthy，会让"该行是否已有结果"的判断全部失真，
  表现为整张表被静默跳过、脚本却报告成功。

## 注意事项

- 脚本依赖环境变量 `DASHSCOPE_API_KEY`，未配置时会因 `api_key=None` 而调用失败。
- 统一使用 `uv add` / `uv remove` 管理依赖，避免直接用 `pip install` 导致
  `pyproject.toml` 与实际环境不一致。改动依赖后记得执行 `uv lock`。
- `.venv`、`__pycache__`、`.env` 均已加入 `.gitignore`，不纳入版本控制。
- Windows 控制台默认 GBK，若模型回复含 ⚠️ 等 GBK 无法表示的字符，`print` 会抛
  `UnicodeEncodeError`。UTF-8 输出由 PowerShell 配置文件与项目根 `.env` 共同保证。
  uv 不支持 `[tool.uv] env` 字段，该配置已迁移到 `.env.example`。
- 模型统一使用 `qwen-vl-max` 系列。DashScope 的带日期版本模型（如
  `qwen-vl-max-2024-08-09`）会随时间下线，出现 404 `model_not_found` 时改用最新版。
- **教程示例的 OSS 图源 `vl-image.oss-cn-shanghai.aliyuncs.com` 已停用**
  （返回 `403 UserDisable`），所有引用该前缀的脚本调用时都会得到
  `400 InternalError.Algo.InvalidParameter: Failed to download multimodal content`。
  请改用本地图片（项目自带的车险示例图在 `28-test\vlm\images\`），
  或把 `OSS_PREFIX` 换成自己可访问的图源。
- 服务端返回 4xx（429 限流除外）属于参数/权限类永久错误，脚本不会重试，直接带行号报错；
  只有网络错误、429、5xx 才会指数退避重试。
- Excel 的 `image` 列按以下顺序判定单个名字的来源：

  1. `http://` / `https://` / `data:` 开头 —— 完整 URL，原样使用
  2. 加了 `--oss` —— 一律按 OSS 图片名，拼前缀并补 `.jpg`
  3. 本地能找到 —— 读本地图转 Base64，**名字省略扩展名时会自动补全**再查找
     （按 `.jpg/.jpeg/.png/.webp/.bmp/.gif/.tiff` 顺序）
  4. 本地找不到且名字没有扩展名 —— 按 OSS 图片名处理
  5. 有扩展名但本地找不到 —— 直接报错，不猜

  `--image-dir` 默认是脚本同级的 `images` 目录，可以不加参数直接跑。
  OSS 图片名带不带扩展名都行，脚本统一补 `.jpg`，不要自己再拼一次后缀。
  OpenAI 兼容模式不支持 `file://` 路径，本地图片一律走 Base64。
