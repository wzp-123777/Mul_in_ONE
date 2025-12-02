"""Authentication routes for FastAPI backend."""

from fastapi import APIRouter

from mul_in_one_nemo.auth import UserCreate, UserRead, UserUpdate, auth_backend, fastapi_users
from mul_in_one_nemo.auth.oauth import get_gitee_oauth_client, get_github_oauth_client

router = APIRouter()

# 基础认证路由
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)

# 注册路由
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# 用户管理路由
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Gitee OAuth 路由（可选）
gitee_client = get_gitee_oauth_client()
if gitee_client:
    router.include_router(
        fastapi_users.get_oauth_router(
            gitee_client,
            auth_backend,
            "changeme-in-production",  # OAuth state secret
            associate_by_email=True,  # 通过邮箱关联已有账户
        ),
        prefix="/auth/gitee",
        tags=["auth"],
    )

# GitHub OAuth 路由（可选）
github_client = get_github_oauth_client()
if github_client:
    router.include_router(
        fastapi_users.get_oauth_router(
            github_client,
            auth_backend,
            "changeme-in-production",
            associate_by_email=True,
        ),
        prefix="/auth/github",
        tags=["auth"],
    )
