#!/bin/bash

# 检查是否传入 --fix 参数
FIX_MODE=false
if [ "$1" == "--fix" ]; then
    FIX_MODE=true
    echo "🔧 自动修复模式已启用"
    echo "----------------------------------------"
else
    echo "🔎 开始执行静态类型检查..."
    echo "----------------------------------------"
fi

# 获取当前时间格式
NOW=$(date "+%Y%m%d_%H%M%S")
REPORT_NAME="类型检查_${NOW}.md"
REPORT_PATH="docs/${REPORT_NAME}"

# 确保 docs 目录存在
mkdir -p docs

# 如果是修复模式，先执行自动修复
if [ "$FIX_MODE" = true ]; then
    echo "🔨 正在执行自动修复..."
    
    echo "  - 格式化代码 (black)..."
    uv run black app
    
    echo "  - 排序导入 (isort)..."
    uv run isort app
    
    echo "✅ 自动修复完成！"
    echo "----------------------------------------"
fi

# 生成报告头部
cat <<EOF > "${REPORT_PATH}"
# 代码类型检查报告
- **生成时间**: $(date "+%Y-%m-%d %H:%M:%S")
- **项目名称**: FastAPI Web
- **检查工具**: Mypy, BasedPyright

---

## 1. Mypy 检查结果
\`\`\`text
EOF

# 运行 Mypy 并记录结果
uv run mypy app >> "${REPORT_PATH}" 2>&1
MYPY_STATUS=$?

cat <<EOF >> "${REPORT_PATH}"
\`\`\`

## 2. BasedPyright 检查结果
\`\`\`text
EOF

# 运行 BasedPyright 并记录结果
uv run basedpyright >> "${REPORT_PATH}" 2>&1
PYRIGHT_STATUS=$?

cat <<EOF >> "${REPORT_PATH}"
\`\`\`

## 3. 代码格式检查 (Black)
\`\`\`text
EOF

# 检查代码格式（不自动修改）
uv run black --check app >> "${REPORT_PATH}" 2>&1
BLACK_STATUS=$?

cat <<EOF >> "${REPORT_PATH}"
\`\`\`

## 4. 导入排序检查 (isort)
\`\`\`text
EOF

# 检查导入排序（不自动修改）
uv run isort --check-only app >> "${REPORT_PATH}" 2>&1
ISORT_STATUS=$?

cat <<EOF >> "${REPORT_PATH}"
\`\`\`

## 5. 代码风格检查 (flake8)
\`\`\`text
EOF

# 运行 flake8 检查
uv run flake8 app >> "${REPORT_PATH}" 2>&1
FLAKE8_STATUS=$?

cat <<EOF >> "${REPORT_PATH}"
\`\`\`

## 6. 安全漏洞检查 (bandit)
\`\`\`text
EOF

# 运行 bandit 安全扫描
uv run bandit -r app >> "${REPORT_PATH}" 2>&1
BANDIT_STATUS=$?

cat <<EOF >> "${REPORT_PATH}"

---
## 总结
- **Mypy 状态**: $([ $MYPY_STATUS -eq 0 ] && echo "✅ 通过" || echo "❌ 发现错误")
- **BasedPyright 状态**: $([ $PYRIGHT_STATUS -eq 0 ] && echo "✅ 通过" || echo "❌ 发现错误")
- **Black 格式检查**: $([ $BLACK_STATUS -eq 0 ] && echo "✅ 通过" || echo "❌ 需要格式化")
- **isort 导入排序**: $([ $ISORT_STATUS -eq 0 ] && echo "✅ 通过" || echo "❌ 需要排序")
- **flake8 代码风格**: $([ $FLAKE8_STATUS -eq 0 ] && echo "✅ 通过" || echo "❌ 发现问题")
- **bandit 安全检查**: $([ $BANDIT_STATUS -eq 0 ] && echo "✅ 通过" || echo "⚠️  发现风险")
EOF

echo "----------------------------------------"
echo "✅ 检查完成！"
if [ $MYPY_STATUS -eq 0 ] && [ $PYRIGHT_STATUS -eq 0 ] && [ $BLACK_STATUS -eq 0 ] && [ $ISORT_STATUS -eq 0 ] && [ $FLAKE8_STATUS -eq 0 ] && [ $BANDIT_STATUS -eq 0 ]; then
    echo "🎉 所有检查均已通过！"
else
    echo "⚠️  发现问题，请查看报告。"
fi
echo "📄 报告已生成至: ${REPORT_PATH}"
