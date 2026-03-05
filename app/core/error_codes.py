from __future__ import annotations


ERROR_MESSAGES: dict[str, str] = {
    """
    错误信息，或者叫做异常的说明 
     
    """
    # 异常
    "error.validation_failed": "validation_failed",
    "error.internal": "internal_error",
    "error.http": "http_error",
    "error.rate_limited": "rate_limited",           # 触发限流

    # 鉴权
    "auth.bearer_required": "Missing bearer token",
    "auth.access_token_invalid": "Invalid access token",
    "auth.access_token_expired": "Token expired",
    "auth.user_inactive": "User disabled or not found",
    "auth.email_taken": "Email already exists",
    "auth.credentials_invalid": "Invalid credentials",
    "auth.refresh_token_invalid": "Invalid refresh token",
    "auth.refresh_token_expired": "Refresh expired",

    # 权限
    "rbac.forbidden": "forbidden",
    "rbac.role_required": "no_role",
    "rbac.permission_missing": "missing_perms",

    # 管理
    "admin.role_not_found": "role not found",
    "admin.user_not_found": "user not found",

    # 存储
    "storage.db_error": "db_error",

    # 资源
    "resources.workspace_not_found": "workspace not found",
    "resources.project_not_found": "project not found",
    "resources.workspace_name_taken": "workspace name already exists",
    "resources.project_name_taken": "project name already exists in workspace",

    # 知识库
    "kb.asset_not_found": "kb asset not found",
    "kb.asset_not_uploaded": "kb asset not uploaded",
    "kb.asset_bad_resource_type": "bad resource_type",
    "kb.ingest_unsupported": "unsupported asset type",
    "kb.ingest_failed": "ingest failed",
    "kb.search_failed": "search failed",
}


ERROR_STATUS: dict[str, int] = {
    """
        错误编码/异常编码
    
    """
    # 异常
    "error.validation_failed": 422,
    "error.internal": 500,
    "error.http": 400,
    "error.rate_limited": 429,

    # 鉴权
    "auth.bearer_required": 401,
    "auth.access_token_invalid": 401,
    "auth.access_token_expired": 401,
    "auth.user_inactive": 401,
    "auth.email_taken": 409,
    "auth.credentials_invalid": 401,
    "auth.refresh_token_invalid": 401,
    "auth.refresh_token_expired": 401,

    # 权限
    "rbac.forbidden": 403,
    "rbac.role_required": 403,
    "rbac.permission_missing": 403,

    # 管理
    "admin.role_not_found": 404,
    "admin.user_not_found": 404,

    # 存储
    "storage.db_error": 500,

    # 资源
    "resources.workspace_not_found": 404,
    "resources.project_not_found": 404,
    "resources.workspace_name_taken": 409,
    "resources.project_name_taken": 409,

    # 知识库
    "kb.asset_not_found": 404,
    "kb.asset_not_uploaded": 409,
    "kb.asset_bad_resource_type": 400,
    "kb.ingest_unsupported": 400,
    "kb.ingest_failed": 500,
    "kb.search_failed": 500,
}