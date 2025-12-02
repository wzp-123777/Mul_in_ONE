"""User manager for handling user-related operations."""

from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin

from mul_in_one_nemo.config import Settings
from mul_in_one_nemo.db.models import User

from .db import get_user_db
from .email import email_service


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """用户管理器，处理注册、验证等逻辑."""
    
    reset_password_token_secret = Settings.from_env().jwt_secret
    verification_token_secret = Settings.from_env().jwt_secret

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """用户注册后的回调."""
        print(f"User {user.id} ({user.username}) has registered.")
        # 如果配置了邮件服务，发送验证邮件
        if email_service.enabled and not user.is_verified:
            try:
                # 生成验证 token
                token = await self.request_verify(user, request)
                email_service.send_verification_email(user.email, token, user.username)
            except Exception as e:
                print(f"Failed to send verification email: {e}")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """忘记密码后的回调."""
        print(f"User {user.id} has forgot their password. Reset token: {token}")
        # 发送密码重置邮件
        if email_service.enabled:
            try:
                email_service.send_password_reset_email(user.email, token, user.username)
            except Exception as e:
                print(f"Failed to send password reset email: {e}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """请求验证邮箱后的回调."""
        print(f"Verification requested for user {user.id}. Verification token: {token}")
        # 发送验证邮件
        if email_service.enabled:
            try:
                email_service.send_verification_email(user.email, token, user.username)
            except Exception as e:
                print(f"Failed to send verification email: {e}")


async def get_user_manager(user_db=Depends(get_user_db)):
    """获取用户管理器（依赖注入）."""
    yield UserManager(user_db)
