# 1. 安装依赖（DashScope Python SDK）
pip install dashscope

# 2. 配置 Key
#   Linux / macOS
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
#   Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"

# 3. 单张图
python local_image_vlm.py 1-Chinese-document-extraction.jpg

# 4. 整目录逐个识别
python local_image_vlm.py . --question "这是哪类保险单证？列出关键字段"

# 5. 多图合并成一次请求（如身份证正反面）
python local_image_vlm.py ./ids --merge --model qwen-vl-max

# 6. 容器 / 网络盘等 file:// 不可用的环境，切 Base64
python local_image_vlm.py ./images --mode base64
