"""
统一异常定义
"""

from __future__ import annotations


class AppException(Exception):
    """应用基础异常"""

    def __init__(self, message: str, code: str = "UNKNOWN", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(message=message, code="NOT_FOUND", status_code=404)


class UnauthorizedError(AppException):
    """未授权"""

    def __init__(self, message: str = "请先登录"):
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401)


class ForbiddenError(AppException):
    """无权限"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


class BusinessError(AppException):
    """业务逻辑错误"""

    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        super().__init__(message=message, code=code, status_code=400)


class ConflictError(AppException):
    """资源冲突（如重复、状态冲突）"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(message=message, code="CONFLICT", status_code=409)


class ValidationError(AppException):
    """参数校验错误"""

    def __init__(self, message: str = "参数校验失败"):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422)
