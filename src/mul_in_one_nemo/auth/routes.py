"""Authentication routes for FastAPI backend."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from mul_in_one_nemo.auth import UserCreate, UserRead, UserUpdate, auth_backend, fastapi_users
from mul_in_one_nemo.auth.oauth import get_gitee_oauth_client, get_github_oauth_client
from mul_in_one_nemo.auth.turnstile import turnstile_service
from mul_in_one_nemo.auth.manager import get_user_manager

router = APIRouter()


class RegisterWithCaptcha(BaseModel):
    """注册请求（含人机验证）."""
    email: str
    password: str
    username: str
    display_name: str | None = None
    turnstile_token: str | None = None


@router.post("/auth/register-with-captcha", response_model=UserRead, tags=["auth"])
async def register_with_captcha(
    data: RegisterWithCaptcha,
    request: Request,
    user_manager = Depends(get_user_manager)
):
    """带 Turnstile 验证的注册端点."""
    # 验证 Turnstile token
    if turnstile_service.enabled:
        if not data.turnstile_token:
            raise HTTPException(status_code=400, detail="Missing captcha token")
        
        client_ip = request.client.host if request.client else None
        success, error = await turnstile_service.verify_token(data.turnstile_token, client_ip)
        
        if not success:
            raise HTTPException(status_code=400, detail=error or "Captcha verification failed")
    
    # 创建用户
    user_create = UserCreate(
        email=data.email,
        password=data.password,
        username=data.username,
        display_name=data.display_name
    )
    
    try:
        user = await user_manager.create(user_create, request=request)
        return UserRead.from_orm(user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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

# 邮箱验证路由
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

# 密码重置路由
router.include_router(
    fastapi_users.get_reset_password_router(),
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
