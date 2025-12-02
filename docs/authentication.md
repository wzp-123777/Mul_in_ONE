# FastAPI-Users 认证系统集成文档

## 🎯 已完成的功能

### 后端 (FastAPI)
- ✅ 用户模型 (兼容 FastAPI-Users)
- ✅ JWT 认证后端
- ✅ 邮箱密码登录/注册
- ✅ Gitee OAuth (墙内友好)
- ✅ GitHub OAuth (国际备选)
- ✅ 数据库迁移文件

### 自动生成的 API 端点

#### 认证相关
```
POST   /api/auth/register         # 邮箱密码注册
POST   /api/auth/login            # 登录获取 JWT
POST   /api/auth/logout           # 登出
```

#### OAuth 登录
```
GET    /api/auth/gitee/authorize  # Gitee OAuth 授权跳转
GET    /api/auth/gitee/callback   # Gitee 回调处理
GET    /api/auth/github/authorize # GitHub OAuth 授权跳转  
GET    /api/auth/github/callback  # GitHub 回调处理
```

#### 用户管理
```
GET    /api/users/me              # 获取当前用户信息
PATCH  /api/users/me              # 更新当前用户信息
```

## 🚀 快速开始

### 1. 配置环境变量

复制 `.envrc.example` 为 `.envrc`:

```bash
cp .envrc.example .envrc
```

编辑 `.envrc` 填入：
- `JWT_SECRET`: 生成随机密钥 `openssl rand -hex 32`
- `GITEE_CLIENT_ID` / `GITEE_CLIENT_SECRET`: [Gitee OAuth 申请](https://gitee.com/oauth/applications)
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`: [GitHub OAuth 申请](https://github.com/settings/developers)

加载环境变量：
```bash
direnv allow  # 或者 source .envrc
```

### 2. 运行数据库迁移

```bash
uv run alembic upgrade head
```

### 3. 启动后端

```bash
cd scripts
./start_backend.sh
```

### 4. 测试认证 API

#### 注册新用户
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "strongpassword123",
    "username": "testuser"
  }'
```

#### 登录获取 JWT
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=strongpassword123"
```

返回示例:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 获取当前用户信息
```bash
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🎨 前端集成示例

### Vue 3 + Quasar 登录组件

创建 `LoginPage.vue`:

```vue
<template>
  <q-page class="flex flex-center">
    <q-card style="width: 400px">
      <q-card-section>
        <div class="text-h6">登录 Mul-in-ONE</div>
      </q-card-section>

      <q-card-section>
        <q-input
          v-model="email"
          label="邮箱"
          type="email"
          outlined
        />
        <q-input
          v-model="password"
          label="密码"
          type="password"
          outlined
          class="q-mt-md"
        />
      </q-card-section>

      <q-card-actions align="center">
        <q-btn
          label="登录"
          color="primary"
          @click="login"
          :loading="loading"
        />
      </q-card-actions>

      <q-separator />

      <q-card-section class="text-center">
        <div class="text-subtitle2 q-mb-sm">或使用第三方登录</div>
        <q-btn
          label="Gitee 登录"
          color="red"
          icon="fab fa-git-alt"
          @click="loginWithGitee"
          class="q-mr-sm"
        />
        <q-btn
          label="GitHub 登录"
          color="dark"
          icon="fab fa-github"
          @click="loginWithGitHub"
        />
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from 'src/api'

const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)

async function login() {
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('username', email.value)
    formData.append('password', password.value)
    
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token)
      router.push('/chat')
    }
  } catch (error) {
    console.error('登录失败', error)
  } finally {
    loading.value = false
  }
}

function loginWithGitee() {
  window.location.href = 'http://localhost:8000/api/auth/gitee/authorize'
}

function loginWithGitHub() {
  window.location.href = 'http://localhost:8000/api/auth/github/authorize'
}
</script>
```

### API 请求拦截器 (添加 JWT)

在 `src/api.ts` 中:

```typescript
import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

// 请求拦截器：自动添加 JWT token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理 401 跳转登录
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### OAuth 回调处理页面

创建 `OAuthCallbackPage.vue`:

```vue
<template>
  <q-page class="flex flex-center">
    <q-spinner size="50px" color="primary" />
    <div class="q-mt-md">正在处理登录...</div>
  </q-page>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

onMounted(() => {
  // FastAPI-Users 会在回调时自动设置 cookie 或返回 token
  // 这里处理 URL 中的 token (如果后端配置为返回到前端)
  const token = route.query.token
  if (token) {
    localStorage.setItem('access_token', token)
    router.push('/chat')
  } else {
    // 如果使用 cookie 方式，直接跳转
    router.push('/chat')
  }
})
</script>
```

### 路由配置

在 `router/routes.ts` 中:

```typescript
const routes = [
  {
    path: '/login',
    component: () => import('pages/LoginPage.vue')
  },
  {
    path: '/auth/callback',
    component: () => import('pages/OAuthCallbackPage.vue')
  },
  {
    path: '/chat',
    component: () => import('pages/ChatConversationPage.vue'),
    meta: { requiresAuth: true }
  }
]

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})
```

## 🔐 OAuth 应用配置

### Gitee OAuth 申请

1. 访问 https://gitee.com/oauth/applications
2. 点击"创建应用"
3. 填写信息:
   - **应用名称**: Mul-in-ONE
   - **应用主页**: `http://localhost:3000`
   - **应用回调地址**: `http://localhost:8000/api/auth/gitee/callback`
4. 获取 `Client ID` 和 `Client Secret`

### GitHub OAuth 申请

1. 访问 https://github.com/settings/developers
2. 点击 "New OAuth App"
3. 填写信息:
   - **Application name**: Mul-in-ONE
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:8000/api/auth/github/callback`
4. 获取 `Client ID` 和 `Client Secret`

## 🛡️ 保护现有路由

在需要认证的路由中使用 `current_active_user` 依赖:

```python
from fastapi import Depends
from mul_in_one_nemo.auth import current_active_user
from mul_in_one_nemo.db.models import User

@router.post("/sessions")
async def create_session(
    user: User = Depends(current_active_user),  # 自动验证 JWT
    db: AsyncSession = Depends(get_db)
):
    # 只有已登录用户才能访问
    session = Session(user_id=user.id, ...)
    db.add(session)
    await db.commit()
    return session
```

## 📝 下一步

- [ ] 前端登录页面完整实现
- [ ] 受保护路由迁移 (sessions, personas)
- [ ] 用户头像上传
- [ ] 邮箱验证功能
- [ ] 密码重置流程
- [ ] 多租户权限管理

## 🐛 常见问题

### 1. 迁移失败：主键冲突
确保 `User` 模型不重复定义 `id` 字段，`SQLAlchemyBaseUserTable` 已包含。

### 2. OAuth 回调 404
检查环境变量中的回调 URL 是否与 OAuth 应用配置一致。

### 3. JWT 验证失败
确认 `JWT_SECRET` 已设置且与生成 token 时使用的密钥相同。

## 📚 参考文档

- [FastAPI-Users 官方文档](https://fastapi-users.github.io/fastapi-users/)
- [Gitee OAuth 文档](https://gitee.com/api/v5/oauth_doc)
- [GitHub OAuth 文档](https://docs.github.com/en/developers/apps/building-oauth-apps)
