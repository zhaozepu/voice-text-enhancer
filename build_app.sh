#!/bin/bash

set -e

echo "================================"
echo "Voice Text Enhancer - 打包脚本"
echo "================================"
echo ""

cd "$(dirname "$0")"

echo "[1/5] 激活虚拟环境..."
source venv/bin/activate

echo "[2/5] 清理旧的构建文件..."
rm -rf build dist VoiceTextEnhancer.app
echo "✓ 清理完成"

echo ""
echo "[3/5] 开始打包应用..."
pyinstaller VoiceTextEnhancer.spec --clean

if [ $? -ne 0 ]; then
    echo "✗ 打包失败"
    exit 1
fi

echo "✓ 打包完成"

echo ""
echo "[4/5] 复制配置文件到应用内..."
# 创建配置目录
mkdir -p "dist/VoiceTextEnhancer.app/Contents/Resources/config"

# 复制配置文件
cp config.example.yaml "dist/VoiceTextEnhancer.app/Contents/Resources/config/"
cp .env.example "dist/VoiceTextEnhancer.app/Contents/Resources/config/"

echo "✓ 配置文件已复制"

echo ""
echo "[5/5] 创建用户配置目录..."
USER_CONFIG_DIR="$HOME/.voice-text-enhancer"
if [ ! -d "$USER_CONFIG_DIR" ]; then
    mkdir -p "$USER_CONFIG_DIR"
    echo "✓ 已创建用户配置目录: $USER_CONFIG_DIR"
else
    echo "✓ 用户配置目录已存在: $USER_CONFIG_DIR"
fi

echo ""
echo "================================"
echo "打包完成！"
echo "================================"
echo ""
echo "应用位置: dist/VoiceTextEnhancer.app"
echo ""
echo "下一步："
echo "1. 移动应用到 /Applications："
echo "   cp -r dist/VoiceTextEnhancer.app /Applications/"
echo ""
echo "2. 首次运行前配置："
echo "   - 复制配置文件："
echo "     cp config.example.yaml ~/.voice-text-enhancer/config.yaml"
echo "     cp .env.example ~/.voice-text-enhancer/.env"
echo "   - 编辑 ~/.voice-text-enhancer/.env 添加 API Key"
echo ""
echo "3. 授予权限："
echo "   系统设置 > 隐私与安全性 > 辅助功能"
echo "   系统设置 > 隐私与安全性 > 输入监控"
echo "   添加 VoiceTextEnhancer.app"
echo ""
echo "4. 双击启动应用"
echo ""
