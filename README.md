# FastAPI 用户管理模块交付文档

我已完成基于 FastAPI 分层架构的用户管理模块开发。本项目具备完整的 CRUD 功能、多环境配置支持以及标准化的响应设计。

## 主要特性

1.  **分层架构**: 严格遵循 `Router -> Service -> Repository -> Model` 模式，代码耦合度低。
2.  **多环境配置**: 支持 `.env.dev`, `.env.local`, `.env.pro`，通过 `APP_ENV` 环境变量自动切换。
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

您可以使用 `uv` 运行，或者更方便地使用我为您准备的 `start.sh` 脚本（它会自动识别环境并开启 --reload）：

```bash
# 赋予执行权限 (如果尚未赋予)
chmod +x start.sh

# 启动项目
./start.sh
```

或直接使用 uvicorn：

```bash
uv run uvicorn app.main:app --reload
```

## 验证截图/输出示例

启动后您将看到类似如下的中文输出：

```text
==================================================
🚀 应用启动中...
🌍 当前环境: dev
🛠️  调试模式: 开启
📦 数据库: 127.0.0.1:3306/fastapi_web
📜 日志级别: DEBUG
📄 API文档: http://127.0.0.1:8000/docs
==================================================
✅ 数据库连接成功!
```

您可以访问 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 查看交互式 API 文档并进行接口测试。

## 代码质量保证

项目集成了以下静态代码分析工具，确保代码健壮性：

- **Mypy**: 严格的静态类型检查。
- **Pyright (BasedPyright)**: 高性能的异步代码类型推断。
- **SonarQube**: 预设了 `sonar-project.properties` 配置文件。

运行类型检查：

```bash
# 1. 运行单次检查并直接查看输出
uv run mypy app
uv run basedpyright

# 2. 运行自动化检查并生成时间戳报告 (推荐)
chmod +x check.sh
./check.sh
```

生成的报告将保存在 `docs/` 目录下，文件名为 `类型检查_年月日_时分秒.md`。

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

# 运行指定测试文件
uv run pytest tests/test_basic_functionality.py

# 运行指定测试类
uv run pytest tests/test_password_security.py::TestPasswordSecurity

# 运行指定测试方法
uv run pytest tests/test_password_security.py::TestPasswordSecurity::test_hash_password_bcrypt

# 运行测试并显示详细信息
uv run pytest -v

# 运行测试并显示覆盖率报告
uv run pytest --cov=app --cov-report=html --cov-report=term-missing

# 在失败时进入PDB调试模式
uv run pytest -x --pdb
```

### 测试用法示例

#### 1. 基础功能测试

```bash
# 运行基础功能测试
uv run pytest tests/test_basic_functionality.py -v

# 输出示例：
# test_basic_functionality.py::test_basic_password_hashing PASSED [ 25%]
# test_basic_functionality.py::test_basic_password_verification PASSED [ 50%]
# test_basic_functionality.py::test_password_strength_basic PASSED [ 75%]
# test_basic_functionality.py::test_user_schema_basic PASSED [100%]
```

#### 2. 密码安全测试

```bash
# 运行完整的密码安全测试套件
uv run pytest tests/test_password_security.py -v
uv run pytest tests/test_password_security_fixed.py -v

# 输出示例：
# test_password_security.py::TestPasswordSecurity::test_hash_password_bcrypt PASSED
# test_password_security.py::TestPasswordSecurity::test_verify_password PASSED
# test_password_security.py::TestPasswordSecurity::test_password_strength_validation_success PASSED
# ...
```

#### 3. 异步功能测试

```bash
# 运行异步测试（包含数据库模拟）
uv run pytest tests/test_password_security.py::TestPasswordSecurity::test_create_user_with_password_validation -v
```

#### 4. 持续集成检查

```bash
# 同时运行所有测试和类型检查
./check.sh && uv run pytest --cov=app --cov-report=term-missing
```

### 测试文件说明

- **`test_basic_functionality.py`**: 基础功能测试（密码哈希、验证、模式验证）
- **`test_password_security.py`**: 完整的密码安全测试套件
- **`test_password_security_fixed.py`**: 修复版本的密码安全测试

### 测试最佳实践

1. **环境隔离**: 测试会自动使用独立的测试环境，不会影响生产数据库
2. **模拟对象**: 使用 `unittest.mock` 模拟数据库连接
3. **异步支持**: 使用 `pytest-asyncio` 支持异步测试
4. **覆盖率**: 支持生成详细的覆盖率报告

### 编写新测试

创建新测试时参考现有测试结构：

```python
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
