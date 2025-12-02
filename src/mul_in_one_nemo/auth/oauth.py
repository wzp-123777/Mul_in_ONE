"""OAuth clients configuration (Gitee, GitHub, etc.)."""

import os

from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.oauth2 import BaseOAuth2


class GiteeOAuth2(BaseOAuth2):
    """Gitee OAuth2 客户端."""
    
    display_name = "Gitee"
    
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint="https://gitee.com/oauth/authorize",
            access_token_endpoint="https://gitee.com/oauth/token",
            refresh_token_endpoint="https://gitee.com/oauth/token",
            base_scopes=["user_info"],
        )
    
    async def get_id_email(self, token: str) -> tuple[str, str | None]:
        """获取用户唯一标识和邮箱."""
        async with self.get_httpx_client() as client:
            response = await client.get(
                "https://gitee.com/api/v5/user",
                params={"access_token": token},
            )
            response.raise_for_status()
            data = response.json()
            return str(data["id"]), data.get("email")


def get_gitee_oauth_client() -> GiteeOAuth2 | None:
    """获取 Gitee OAuth 客户端（如果配置了）."""
    client_id = os.getenv("GITEE_CLIENT_ID")
    client_secret = os.getenv("GITEE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return None
    
    return GiteeOAuth2(client_id=client_id, client_secret=client_secret)


def get_github_oauth_client() -> GitHubOAuth2 | None:
    """获取 GitHub OAuth 客户端（备选，国际用户）."""
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return None
    
    return GitHubOAuth2(client_id=client_id, client_secret=client_secret)
