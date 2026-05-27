#!/bin/bash

set -e

echo "=========================================="
echo "Voice Text Enhancer - 安装脚本"
echo "=========================================="
echo ""

cd "$(dirname "$0")/.."

echo "[1/6] 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  ✓ Python 版本: $python_version"
echo ""

echo "[2/6] 创建虚拟环境（可选，推荐）..."
read -p "是否创建虚拟环境？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "  ✓ 虚拟环境已创建"
    else
        echo "  ✓ 虚拟环境已存在"
    fi

    echo "  激活虚拟环境..."
    source venv/bin/activate
else
    echo "  跳过虚拟环境创建"
fi
echo ""

echo "[3/6] 升级 pip..."
python3 -m pip install --upgrade pip --quiet
echo "  ✓ pip 已升级"
echo ""

echo "[4/6] 安装依赖..."
python3 -m pip install -r requirements.txt --quiet
echo "  ✓ 依赖安装完成"
echo ""

echo "[5/6] 创建配置文件..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✓ 已创建 .env 文件"
    echo "  ⚠️  请编辑 .env 文件，添加你的 DEEPSEEK_API_KEY"
else
    echo "  ✓ .env 文件已存在"
fi

if [ ! -f "config.yaml" ]; then
    cp config.example.yaml config.yaml
    echo "  ✓ 已创建 config.yaml 文件"
else
    echo "  ✓ config.yaml 文件已存在"
fi
echo ""

echo "[6/6] 检查配置..."
api_key=$(grep DEEPSEEK_API_KEY .env | cut -d '=' -f2)
if [ "$api_key" == "sk-your-api-key-here" ] || [ -z "$api_key" ]; then
    echo "  ⚠️  DEEPSEEK_API_KEY 未配置"
    echo "  请访问 https://platform.deepseek.com/api_keys 获取 API Key"
    echo "  然后编辑 .env 文件进行配置"
else
    echo "  ✓ DEEPSEEK_API_KEY 已配置"
fi
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 配置 API Key（如果还没配置）："
echo "   编辑 .env 文件，设置 DEEPSEEK_API_KEY"
echo ""
echo "2. 授予系统权限："
echo "   运行程序后，系统会提示授予以下权限："
echo "   - 辅助功能（Accessibility）"
echo "   - 输入监控（Input Monitoring）"
echo "   在 '系统设置 > 隐私与安全性' 中授予"
echo ""
echo "3. 启动程序："
echo "   python3 main.py"
echo ""
echo "4. 使用方法："
echo "   - 选中要处理的文本"
echo "   - 按快捷键 Cmd+Shift+P"
echo "   - 等待处理完成"
echo ""
echo "=========================================="
