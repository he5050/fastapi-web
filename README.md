# FastAPI 用户管理模块交付文档

我已完成基于 FastAPI 分层架构的用户管理模块开发。本项目具备完整的 CRUD 功能、多环境配置支持以及标准化的响应设计。

## 主要特性

1.  **分层架构**: 严格遵循 `Router -> Service -> Repository -> Model` 模式，代码耦合度低。
2.  **多环境配置**: 支持 `.env.dev`, `.env.local`, `.env.pro`，通过 `APP_ENV` 环境变量或启动参数自动切换，优先使用 local 环境。
3.  **标准响应**: 接口返回统一的 JSON 格式，且支持 **驼峰风格 (camelCase)**。
4.  **参数自动转换**: 通过 `BaseSchema` 自动处理请求参数的驼峰化。
5.  **自动化数据库初始化**: 启动时自动检查/创建数据库和表（受 `DB_INIT` 开关控制）。
6.  **异步连接**: 使用 SQLAlchemy (Asyncio) + `aiomysql` 实现高性能数据库操作。
7.  **启动自检**: 启动时自动检查数据库连接并打印当前环境配置信息。

## 项目结构说明

```text
app/
├── api/             # 路由层 (Request Entry)
├── core/            # 核心配置、异常处理、响应封装
├── db/              # 数据库连接与 Session 管理
├── models/          # 数据库 SQL 模型 (*_model.py 风格)
├── repositories/    # 数据访问层 (SQLAlchemy Logic)
├── schemas/         # Pydantic 数据验证模型 (*_schema.py 风格)
├── services/        # 业务逻辑层
└── main.py          # 应用入口
```

## 运行指引

### 1. 安装依赖并创建虚拟环境

本项目使用 modern 的 `uv` 作为包管理工具，请运行以下命令一键完成环境搭建：

```bash
uv sync
```

### 2. 初始化数据库与表

在首次启动或模型变更后，您可以运行初始化脚本自动创建数据库和表结构：

```bash
uv run python -m app.db.init_db
```

_注：该脚本将根据 `.env._`中的配置自动执行`CREATE DATABASE IF NOT EXISTS`。\*

### 3. 配置数据库

请确保本地 MySQL 已启动，并根据 `.env.dev` 中的配置进行微调。
创建数据库（或修改配置以匹配您的环境）。

### 4. 启动应用

您可以使用 `uv` 运行，或者更方便地使用我为您准备的 `start.sh` 脚本（支持多环境启动）：

```bash
# 赋予执行权限 (如果尚未赋予)
chmod +x start.sh

# 默认启动（优先使用 local 环境，不存在则用 dev）
./start.sh

# 指定环境启动
./start.sh local   # 使用 .env.local 配置
./start.sh dev     # 使用 .env.dev 配置
./start.sh pro     # 使用 .env.pro 配置（生产环境）
```

或直接使用 uvicorn：

```bash
# 使用默认配置
uv run uvicorn app.main:app --reload

# 指定环境变量启动
APP_ENV=local uv run uvicorn app.main:app --reload
APP_ENV=dev uv run uvicorn app.main:app --reload
```

## 验证截图/输出示例

启动后您将看到类似如下的中文输出：

```text
📋 已加载环境配置文件: .env.local
🚀 Using uv to start FastAPI in local mode on port 8000...
==================================================
🚀 应用启动中...
🌍 当前环境: local
🛠️  调试模式: 开启
📦 数据库: 127.0.0.1:3306/test
📜 日志级别: INFO
📄 API文档: http://127.0.0.1:8000/docs
==================================================
✅ 数据库连接成功!
```

您可以访问 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 查看交互式 API 文档并进行接口测试。

## 代码质量保证

项目集成了完整的代码质量工具集，确保代码健壮性和规范性：

### 类型检查工具
- **Mypy**: 严格的静态类型检查
- **Pyright (BasedPyright)**: 高性能的异步代码类型推断

### 代码质量工具
- **Black**: 代码自动格式化工具，统一代码风格
- **isort**: Python import 语句自动排序
- **flake8**: 代码风格检查，遵循 PEP 8 规范
- **bandit**: 安全漏洞扫描工具，检测常见安全问题

### 运行代码检查

```bash
# 1. 运行单次检查并直接查看输出
uv run mypy app
uv run basedpyright

# 2. 运行自动化检查并生成时间戳报告 (仅检查)
chmod +x check.sh
./check.sh

# 3. 运行自动化检查并自动修复问题
./check.sh --fix
```

生成的报告将保存在 `docs/` 目录下，文件名为 `类型检查_年月日_时分秒.md`。

### 单独使用各工具

```bash
# 格式化代码（自动修复）
uv run black app/

# 排序导入（自动修复）
uv run isort app/

# 检查代码风格（仅检查）
uv run flake8 app/

# 扫描安全漏洞（仅检查）
uv run bandit -r app/
```

**注意**: 类型检查和安全扫描工具（mypy、basedpyright、bandit）不会自动修复代码，需要手动处理发现的问题。

## 测试指南

### 测试框架和依赖

项目使用 **pytest** 作为测试框架，支持异步测试：

```bash
# 安装测试依赖
uv sync --group dev

# 查看所有安装的依赖
uv pip list
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 按模块运行测试
uv run pytest tests/security/                          # 运行安全测试
uv run pytest tests/unit/                              # 运行所有单元测试
uv run pytest tests/unit/services/                     # 运行服务层测试
uv run pytest tests/unit/schemas/                      # 运行模式验证测试
uv run pytest tests/unit/api/                          # 运行API路由测试
uv run pytest tests/integration/                       # 运行集成测试

# 指定测试类或方法
uv run pytest tests/security/test_password_security.py::TestPasswordSecurity
uv run pytest tests/security/test_password_security.py::TestPasswordSecurity::test_hash_password_bcrypt

# 常用参数
uv run pytest -v                                      # 显示详细信息
uv run pytest --cov=app --cov-report=html            # 生成覆盖率报告
uv run pytest -x --pdb                               # 失败时进入调试模式
uv run pytest -k "password"                          # 只运行包含"password"的测试
```

### 测试用法示例

#### 1. 安全测试 - 密码安全

```bash
# 运行密码安全测试
uv run pytest tests/security/ -v

# 输出示例：
# tests/security/test_password_security.py::TestPasswordSecurity::test_hash_password_bcrypt PASSED [16%]
# tests/security/test_password_security.py::TestPasswordSecurity::test_verify_password PASSED [33%]
# tests/security/test_password_security.py::TestPasswordSecurity::test_password_strength_validation_success PASSED [50%]
```

#### 2. 服务层测试 - 用户服务

```bash
# 运行用户服务测试
uv run pytest tests/unit/services/ -v

# 输出示例：
# tests/unit/services/test_user_service.py::TestUserService::test_create_user_with_password_validation PASSED [25%]
# tests/unit/services/test_user_service.py::TestUserService::test_basic_password_hashing PASSED [50%]
```

#### 3. 模式验证测试 - 数据验证

```bash
# 运行模式验证测试
uv run pytest tests/unit/schemas/ -v

# 输出示例：
# tests/unit/schemas/test_user_schema.py::TestUserSchemaValidation::test_valid_user_creation PASSED [20%]
# tests/unit/schemas/test_user_schema.py::TestUserSchemaValidation::test_valid_password_schema PASSED [40%]
```

#### 4. API 路由测试 - 端点验证

```bash
# 运行API路由测试
uv run pytest tests/unit/api/ -v

# 输出示例：
# tests/unit/api/test_user_router.py::TestUserRouter::test_root_endpoint PASSED [25%]
# tests/unit/api/test_user_router.py::TestUserRouter::test_api_docs_availability PASSED [50%]
```

#### 5. 集成测试 - 完整流程

```bash
# 运行集成测试（测试完整用户工作流）
uv run pytest tests/integration/ -v

# 输出示例：
# tests/integration/test_user_workflow.py::TestUserWorkflow::test_user_creation_workflow PASSED [50%]
# tests/integration/test_user_workflow.py::TestUserWorkflow::test_api_endpoint_structure PASSED [100%]
```

#### 6. 质量保证检查

```bash
# 同时运行所有测试和类型检查
./check.sh && uv run pytest --cov=app --cov-report=term-missing
```

### 测试覆盖率报告

```bash
# 生成详细的HTML覆盖率报告
uv run pytest --cov=app --cov-report=html

# 在终端显示覆盖率
uv run pytest --cov=app --cov-report=term-missing

# 覆盖率报告将显示在 coverage_html/index.html
```

### 测试最佳实践

1. **模块化设计**: 测试按功能和层级划分，便于维护和扩展
2. **环境隔离**: 测试使用模拟对象，不会影响生产数据库
3. **异步支持**: 支持异步代码测试，确保并发安全性
4. **全面覆盖**: 包含单元测试、集成测试和安全测试
5. **持续集成**: 与类型检查工具结合，确保代码质量

### 编写新测试

创建新测试时，请根据功能存放至对应目录：

```python
# 服务层测试 - 存放在 tests/unit/services/
import pytest
from unittest.mock import Mock
from app.services.user_service import UserService

def test_new_feature():
    """测试描述"""
    mock_db = Mock()
    service = UserService(mock_db)

    # 测试逻辑
    result = service.some_method()
    assert result is expected_result
```

每个测试目录都包含 `__init__.py` 文件，支持模块导入和测试发现。
