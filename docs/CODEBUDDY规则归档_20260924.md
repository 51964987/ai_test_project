# CODEBUDDY 规则归档（2026-09-24 精简前完整快照）

> 说明：本文件是 `CODEBUDDY.md`「通用工程约束」精简前的完整快照（原 1-13 条逐字保留，含触发场景、强制动作细节、项目实例与实测证据）。
> 增补约定：新教训先写入本文件对应条目（沿用原编号续号，即 14 起续），再在 `CODEBUDDY.md` 加/改一行规则并标注「原 N」；禁止把案例叙述直接写进 `CODEBUDDY.md`。
> 注：原文件中条目「原 13」排在「原 12」之前（历史编号错位），本快照按原文顺序保留，未做改动。

---

## 原 1　不重复造轮子

**不重复造轮子**：若之前实现过类似功能，先理解已有的实现逻辑与曾思考过的细节，再在其基础上修改完善；不要绕开旧实现重新发明轮子。

## 原 2　中文注释 + UTF-8

**中文注释 + UTF-8**：生成的代码注释一律用中文，文件以 UTF-8 编码保存。

## 原 3　运行环境为 Windows

**运行环境为 Windows**：命令、路径分隔、脚本均按 Windows 环境处理（如 `cd d:\path`、反斜杠路径），不要假设 Linux/macOS。

## 原 4　不主动写测试与说明文档

**不主动写测试与说明文档**：用户未明确要求时，不编写测试脚本，也不生成专门的项目说明 `.md` 文件。

## 原 5　代码禁止 emoji

**代码禁止 emoji**：源码、注释、字符串中不得出现 emoji 字符。

## 原 6　迁移先 copy 再改写

**迁移先 copy 再改写**：做代码迁移/重构时，先复制原文件再在其上修改，不要从头重复写一遍（避免遗漏或引入错误）。

## 原 7　不考虑 fallback 与旧兼容

**不考虑 fallback 与旧兼容**：本项目没有老用户，不做向后兼容与兼容层；处理思路是「消除 fallback 触发场景」，而非「加更多兜底分支」。

## 原 8　不盲目折中

**不盲目折中**：方案清晰合理即可，不必为了稳妥而给折中方案（折中往往意味着还没想清楚）；不过度优化、不预支复杂度。

## 原 9　新建/变更文件必须可运行且无警告/问题

**新建/变更文件必须可运行且无警告/问题**：任何新建或改动的代码文件，交付前必须保证能正常运行且**不残留任何语法错误、类型错误、Lint 警告或明显问题**（如未使用的导入、未定义变量、空异常处理、明显逻辑死分支等）。措施：改动后用项目既有自检手段核验——后端 `python -m py_compile <文件>` + 启动不报错；前端 `npx vue-tsc --noEmit` 与 `read_lints` 均 0 错误；对受影响接口/功能发起真实验证。发现问题必须当场修复，不要以「应该没问题」带病交付。

## 原 10　密钥一律从环境变量读取，禁止硬编码

**密钥一律从环境变量读取，禁止硬编码**：任何 API Key / Token / 密码都不得写死在源码里（含 `sk-xxx` 占位串），统一用 `os.getenv` 读取并校验：

```python
KEY: str | None = os.getenv("XXX_API_KEY")
if not KEY:
    raise ValueError("请先设置环境变量 XXX_API_KEY")
```

如需从 `.env` 读取，仍先 `sys.path.insert(0, str(Path(__file__).resolve().parents[N]))` 再 `from env_loader import load_dotenv; load_dotenv()` 把 `.env` 注入 `os.environ`，随后走 `os.getenv`（**不要**用裸 `os.environ["XXX"]`，缺 key 会抛裸 `KeyError`；也不要用 `require_env`，与新标准不一致）。新增/改动脚本时**举一反三**：检查同目录其它脚本是否仍硬编码密钥或仍是旧取法，一并改为本模式。

- 实例：2026-09-16 `openai-test/*.py` 全部统一为 `os.getenv` + `raise ValueError` 模式。
- 例外（坑）：以 `_test.py` / `test_*` 结尾的文件会被 basedpyright 归入「测试执行环境」，其静态导入根**不含项目根**，无法解析根目录的 `env_loader` 模块（`reportMissingImports`）。这类文件不要 `import env_loader`，改用标准库就地加载 `.env`（参考 `openai-test/dashscope_agicto_test.py` 的 `_load_dotenv()`），其余文件仍走 `env_loader.load_dotenv()`。实例：2026-09-16 `dashscope_agicto_test.py` 因文件名含 `_test` 触发此坑。

## 原 11　第三方 SDK 类型声明窄于网关/私有协议时，用原始请求而不是类型欺骗

**第三方 SDK 类型声明窄于网关/私有协议时，用原始请求而不是类型欺骗**：当 SDK 参数类型覆盖不到实际要传的结构（如 OpenAI SDK `embeddings.create` 的 `input` 只声明文本/token，而 AGICTO 网关透传百炼多模态向量需传 `{"contents":[{"image":url}]}`），改用 `client.post(path, cast_to=..., body={...})` 发原始请求，禁止用 `cast("错误类型", payload)` 或 `list[Any]` 骗过类型检查。

- 实例：2026-09-16 `openai-test/dashscope_agicto_test.py`（basedpyright `reportArgumentType` 报错）。

## 原 13　网关「OpenAI 兼容接口」实际透传上游原生协议时，请求体形状必须实测枚举，不能照抄 OpenAI 文档

**网关「OpenAI 兼容接口」实际透传上游原生协议时，请求体形状必须实测枚举，不能照抄 OpenAI 文档**：

- 触发场景：通过 AGICTO 之类的中转网关调用上游模型（尤其是上游明说「不支持 OpenAI 兼容接口」的能力，如百炼多模态向量），报错来自上游（如 `BadRequest.IllegalInput: The input parameter requires json format.`）而不是网关。
- 强制动作：先查**上游原生 HTTP 协议**确定真实结构，再写一个临时探针脚本一次性枚举 3-5 种候选形状（object/list/string/OpenAI 风格）打同一接口，用实测结果定案，探针脚本用完即删；不要凭猜测反复改一版跑一次。
- 关键认知：SDK 的参数与 HTTP 的字段常**不一一对应**（DashScope 的 `input=[...]` 对应 HTTP 的 `input.contents`），按 SDK 写法拼 HTTP body 必错。
- 实例：2026-09-16 `openai-test/dashscope_agicto_test.py`，正确 body 为 `{"model":..., "input": {"contents": [{"image": url}]}, "parameters": {...}}`；传 `[{"image":url}]`、`[{"type":"image",...}]`、纯字符串均报上述错误，实测相似度 1.000000 通过。

## 原 12　资源文件路径一律基于脚本位置解析，且要举一反三

**资源文件路径一律基于脚本位置解析，且要举一反三**：读取同目录或子目录的资源文件（CSV、图片、模型权重、配置等）时，必须用 `Path(__file__).resolve().parent` 定位，**严禁使用裸相对路径**（如 `open("data.csv")`、`pd.read_csv("x.csv")`）。根因：相对路径按**运行目录（cwd）**解析，cwd 由调用方决定，从其它目录运行即 `FileNotFoundError`。

更进一步的——排查/修复任一类问题时必须**举一反三**：用 `search_content`/`search_file` 等手段确认同项目其它文件是否存在同类隐患（例如多个脚本都用了相对路径、同一套错误调用方式），一并修复或明确列出提醒，**不要只解决当前报错的这一个文件**。
