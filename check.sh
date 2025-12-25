#!/bin/bash

# 获取当前时间格式
NOW=$(date "+%Y%m%d_%H%M%S")
REPORT_NAME="类型检查_${NOW}.md"
REPORT_PATH="docs/${REPORT_NAME}"

echo "🔎 开始执行静态类型检查..."
echo "----------------------------------------"

# 确保 docs 目录存在
mkdir -p docs

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

---
## 总结
- **Mypy 状态**: $([ $MYPY_STATUS -eq 0 ] && echo "✅ 通过" || echo "❌ 发现错误")
- **BasedPyright 状态**: $([ $PYRIGHT_STATUS -eq 0 ] && echo "✅ 通过" || echo "❌ 发现错误")
EOF

echo "----------------------------------------"
echo "✅ 检查完成！"
if [ $MYPY_STATUS -eq 0 ] && [ $PYRIGHT_STATUS -eq 0 ]; then
    echo "🎉 所有类型检查均已通过！"
else
    echo "⚠️  发现类型错误，请查看报告。"
fi
echo "📄 报告已生成至: ${REPORT_PATH}"
