# 1. 安装依赖
pip install openai pandas openpyxl

# 2. 配置 Key
#   Linux / macOS
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
#   Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"

# 3. 运行（本地图片放在 ./images，Excel 的 image 列填文件名）
python batch_insurance_vlm.py --image-dir ./images --model qwen-vl-max --save-every

#    若沿用教程的 OSS 图片名（不含扩展名）
python batch_insurance_vlm.py --oss
