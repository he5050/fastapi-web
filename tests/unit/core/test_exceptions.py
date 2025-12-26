import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppError, global_exception_handler
from app.core.response import BaseResponse


class TestAppError:
    """应用异常类测试"""

    def test_app_error_creation_with_message_only(self):
        """测试只提供消息创建应用异常"""
        error = AppError("Test error message")
        
        assert error.message == "Test error message"
        assert error.code == 400  # 默认错误码

    def test_app_error_creation_with_message_and_code(self):
        """测试提供消息和错误码创建应用异常"""
        error = AppError("Test error message", 500)
        
        assert error.message == "Test error message"
        assert error.code == 500

    def test_app_error_inheritance(self):
        """测试应用异常继承关系"""
        error = AppError("Test message")
        
        assert isinstance(error, Exception)
        assert hasattr(error, 'message')
        assert hasattr(error, 'code')

    def test_app_error_string_representation(self):
        """测试应用异常字符串表示"""
        error = AppError("Test message", 500)
        
        str_repr = str(error)
        assert "Test message" in str_repr

    def test_app_error_attributes(self):
        """测试应用异常属性"""
        error = AppError("Test message", 404)
        
        assert error.message == "Test message"
        assert error.code == 404
        assert hasattr(error, '__dict__')

    def test_app_error_edge_cases(self):
        """测试应用异常边界情况"""
        # 空消息
        error1 = AppError("")
        assert error1.message == ""
        assert error1.code == 400
        
        # 零错误码
        error2 = AppError("message", 0)
        assert error2.code == 0
        
        # 负错误码
        error3 = AppError("message", -1)
        assert error3.code == -1
        
        # 大错误码
        error4 = AppError("message", 999)
        assert error4.code == 999


class TestGlobalExceptionHandler:
    """全局异常处理器测试"""

    @pytest.fixture
    def mock_request(self):
        """创建模拟请求"""
        mock_request = Mock(spec=Request)
        mock_request.url = "http://test.com"
        mock_request.method = "GET"
        return mock_request

    @pytest.mark.asyncio
    async def test_handle_app_error(self, mock_request):
        """测试处理应用异常"""
        app_error = AppError("Business logic error", 400)
        
        response = await global_exception_handler(mock_request, app_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200  # AppError总是返回200
        
        # 验证响应内容
        content = response.body.decode()
        response_data = eval(content)  # 简单解析JSON（实际应该用json.loads）
        
        assert response_data['success'] is False
        assert response_data['message'] == "Business logic error"
        assert response_data['data'] is None

    @pytest.mark.asyncio
    async def test_handle_app_error_with_custom_code(self, mock_request):
        """测试处理带自定义错误码的应用异常"""
        app_error = AppError("Custom error", 500)
        
        response = await global_exception_handler(mock_request, app_error)
        
        assert response.status_code == 200  # 仍然返回200
        
        content = response.body.decode()
        response_data = eval(content)
        
        assert response_data['success'] is False
        assert response_data['message'] == "Custom error"

    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_request):
        """测试处理HTTP异常"""
        http_error = HTTPException(status_code=404, detail="Not found")
        
        response = await global_exception_handler(mock_request, http_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        content = response.body.decode()
        response_data = eval(content)
        
        assert response_data['success'] is False
        assert response_data['message'] == "Not found"

    @pytest.mark.asyncio
    async def test_handle_http_exception_with_status_422(self, mock_request):
        """测试处理422状态码的HTTP异常"""
        http_error = HTTPException(status_code=422, detail="Validation error")
        
        response = await global_exception_handler(mock_request, http_error)
        
        assert response.status_code == 422
        
        content = response.body.decode()
        response_data = eval(content)
        
        assert response_data['success'] is False
        assert response_data['message'] == "Validation error"

    @pytest.mark.asyncio
    async def test_handle_pydantic_validation_error(self, mock_request):
        """测试处理Pydantic验证异常"""
        # 模拟Pydantic验证异常
        pydantic_error = Mock()
        pydantic_error.errors.return_value = [
            {
                "loc": ["body", "username"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
        
        response = await global_exception_handler(mock_request, pydantic_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        
        content = response.body.decode()
        response_data = eval(content)
        
        assert response_data['success'] is False
        assert "body.username参数错误" in response_data['message']
        assert "field required" in response_data['message']

    @pytest.mark.asyncio
    async def test_handle_pydantic_validation_error_value_error_prefix(self, mock_request):
        """测试处理带Value error前缀的Pydantic验证异常"""
        pydantic_error = Mock()
        pydantic_error.errors.return_value = [
            {
                "loc": ["body", "password"],
                "msg": "Value error, Password too short",
                "type": "value_error.any_str.min_length"
            }
        ]
        
        response = await global_exception_handler(mock_request, pydantic_error)
        
        content = response.body.decode()
        response_data = eval(content)
        
        assert response_data['success'] is False
        assert "body.password参数错误: Password too short" in response_data['message']
        assert "Value error," not in response_data['message']  # 前缀应该被移除

    @pytest.mark.asyncio
    async def test_handle_pydantic_validation_error_no_errors(self, mock_request):
        """测试处理没有错误的Pydantic验证异常"""
        pydantic_error = Mock()
        pydantic_error.errors.return_value = []
        
        response = await global_exception_handler(mock_request, pydantic_error)
        
        assert response.status_code == 422
        
        content = response.body.decode()
        response_data = eval(content)
        
        assert response_data['success'] is False
        assert response_data['message'] == "参数验证失败"

    @pytest.mark.asyncio
    async def test_handle_pydantic_validation_error_no_loc(self, mock_request):
        """测试处理没有loc字段的Pydantic验证异常"""
        pydantic_error = Mock()
        pydantic_error.errors.return_value = [
            {
                "msg": "Validation failed",
                "type": "validation_error"
            }
        ]
        
        response = await global_exception_handler(mock_request, pydantic_error)
        
        content = response.body.decode()
        response_data = eval(content)
        
        assert response_data['success'] is False
        assert "参数错误: Validation failed" in response_data['message']

    @pytest.mark.asyncio
    async def test_handle_unknown_exception(self, mock_request):
        """测试处理未知异常"""
        unknown_error = Exception("Something went wrong")
        
        with patch('builtins.print') as mock_print:
            response = await global_exception_handler(mock_request, unknown_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        content = response.body.decode()
        response_data = eval(content)
        
        assert response_data['success'] is False
        assert response_data['message'] == "服务器内部错误"
        
        # 验证异常被打印
        mock_print.assert_called_once()
        assert "系统异常: Something went wrong" in str(mock_print.call_args)

    @pytest.mark.asyncio
    async def test_handle_unknown_exception_with_traceback(self, mock_request):
        """测试处理带追踪信息的未知异常"""
        try:
            raise ValueError("Test error with traceback")
        except Exception as unknown_error:
            with patch('builtins.print') as mock_print:
                response = await global_exception_handler(mock_request, unknown_error)
            
            assert response.status_code == 500
            mock_print.assert_called_once()
            
            # 验证异常信息被正确捕获和打印
            call_args = str(mock_print.call_args)
            assert "系统异常" in call_args
            assert "Test error with traceback" in call_args

    @pytest.mark.asyncio
    async def test_response_format_consistency(self, mock_request):
        """测试响应格式一致性"""
        test_errors = [
            AppError("App error"),
            HTTPException(status_code=404, detail="HTTP error"),
        ]
        
        for error in test_errors:
            response = await global_exception_handler(mock_request, error)
            content = response.body.decode()
            response_data = eval(content)
            
            # 验证响应格式一致性
            assert 'success' in response_data
            assert 'message' in response_data
            assert 'data' in response_data
            assert response_data['success'] is False

    @pytest.mark.asyncio
    async def test_error_handler_with_none_request(self):
        """测试请求为None时的错误处理"""
        app_error = AppError("Test error")
        
        response = await global_exception_handler(None, app_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_error_handler_with_complex_pydantic_error(self, mock_request):
        """测试处理复杂Pydantic验证异常"""
        pydantic_error = Mock()
        pydantic_error.errors.return_value = [
            {
                "loc": ["body", "user", "address", "street"],
                "msg": "Value error, Street name too long",
                "type": "value_error.any_str.max_length"
            },
            {
                "loc": ["body", "user", "email"],
                "msg": "Invalid email format",
                "type": "value_error.email"
            }
        ]
        
        response = await global_exception_handler(mock_request, pydantic_error)
        
        content = response.body.decode()
        response_data = eval(content)
        
        # 应该只处理第一个错误
        assert "body.user.address.street参数错误" in response_data['message']
        assert "Street name too long" in response_data['message']

    @pytest.mark.asyncio
    async def test_error_handler_with_nested_loc(self, mock_request):
        """测试处理嵌套loc字段的Pydantic验证异常"""
        pydantic_error = Mock()
        pydantic_error.errors.return_value = [
            {
                "loc": ["body", "nested", 0, "field"],
                "msg": "Invalid value",
                "type": "value_error"
            }
        ]
        
        response = await global_exception_handler(mock_request, pydantic_error)
        
        content = response.body.decode()
        response_data = eval(content)
        
        # 数字应该被转换为字符串并包含在路径中
        assert "body.nested.0.field参数错误" in response_data['message']
