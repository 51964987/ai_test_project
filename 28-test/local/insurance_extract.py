# 本文件是脚本而非包内模块，同目录导入属正常用法，关闭隐式相对导入告警
# pyright: reportImplicitRelativeImport=false
import json
import os
import sys

from local_image_vlm import ask, ask_multi

if not os.getenv("DASHSCOPE_API_KEY"):
    sys.exit("请先设置环境变量 DASHSCOPE_API_KEY")

# 场景一：多语言单证抽取（对应仓库中的中/日/法/德/韩样张）
LANGS = {
    "1-Chinese-document-extraction.jpg":  "中文",
    "2-Japanese-document-extraction.jpg": "日文",
    "3-French-document-extraction.jpg":   "法文",
    "4-German-document-extraction.jpg":   "德文",
    "5-Korean-document-extraction.jpg":   "韩文",
}
for name, lang in LANGS.items():
    q = (f"这是一张{lang}保险单证。请先用原文列出关键字段（键名），再给出中文对照翻译。"
         "输出格式为 JSON，键为原文字段名，值为原文值；另加一个 _zh 对象给出中文键值对。")
    print(name, "->", ask(name, q, model="qwen-vl-max"))


# 场景二：保单首页字段抽取（强约束，防幻觉）
FIELDS = ["保单号", "投保人姓名", "被保险人姓名", "险种名称",
          "保险金额", "保险期间", "签发日期"]
prompt = (
    "你是寿险保单信息抽取助手。请从图中提取以下字段：" + str(FIELDS) +
    "。要求：1) 只输出 JSON，不要任何解释；" +
    "2) 图中没有的字段值为空字符串，严禁编造；" +
    "3) 金额保留两位小数，日期统一 YYYY-MM-DD。"
)
raw = ask("policy_001.jpg", prompt, model="qwen-vl-max", mode="base64")
raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
data = json.loads(raw)
print(data)


# 场景三：身份证正反面一致性校验（多图一次请求）
q = ("对比这两张身份证的正反面，判断是否属于同一人，"
     "并提取姓名、性别、民族、出生日期、身份证号、签发机关、有效期。"
     "以 JSON 输出，包含 fields 与 is_same_person 两个键。")
print(ask_multi(["id_front.jpg", "id_back.jpg"], q, model="qwen-vl-max"))
