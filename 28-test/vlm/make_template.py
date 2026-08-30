import pandas as pd

rows = [
    {"prompt": "你是寿险单证抽取助手。提取：保单号、投保人姓名、被保险人姓名、险种名称、保险金额、保险期间、签发日期。以 JSON 输出，缺失字段值为空字符串，禁止编造。只输出 JSON。",
     "image": "policy_001.jpg", "response": ""},

    {"prompt": "识别这张住院发票，提取：发票代码、发票号码、姓名、金额合计、开票日期、医院名称。以 JSON 输出，金额保留两位小数。",
     "image": "invoice_002.jpg", "response": ""},

    {"prompt": "对比这两张身份证正反面，判断是否为同一人，并提取姓名、性别、身份证号、有效期。以 JSON 输出。",
     "image": "[id_front.jpg,id_back.jpg]", "response": ""},

    {"prompt": "这是一份体检报告。列出所有异常项（项目名、结果值、参考范围、是否异常），并说明是否涉及寿险核保常见风险（高血压、糖尿病、结节、肝功能异常）。以 JSON 输出。",
     "image": "medical_003.jpg", "response": ""},

    {"prompt": "qwenvl markdown",          # 官方推荐：文档解析为 Markdown
     "image": "claim_form_004.jpg", "response": ""},
]
pd.DataFrame(rows).to_excel("prompt_template_cn.xlsx", index=False)
print("模板已生成：prompt_template_cn-tmp.xlsx")
