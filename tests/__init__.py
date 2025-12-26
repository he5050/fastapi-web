"""
FastAPI Web Application 测试包

测试层级结构：
- unit/        - 单元测试
  - api/       - API路由测试
  - core/      - 核心组件测试
  - services/  - 服务层测试
  - schemas/   - 模式验证测试
  - repositories/ - 数据访问层测试
  - models/    - 模型测试
- integration/ - 集成测试
- security/    - 安全测试

测试运行命令：
uv run pytest                    # 运行所有测试
uv run pytest tests/unit/        # 运行所有单元测试
uv run pytest tests/integration/ # 运行集成测试
uv run pytest tests/security/    # 运行安全测试
"""
