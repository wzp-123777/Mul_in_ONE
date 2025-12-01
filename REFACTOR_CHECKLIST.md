# User-Tenant 合并重构清单

## 概述

将 Tenant 和 User 概念合并为单一的 User，使用 username 作为主要标识符。

永远不要忘记要用uv操作

=

## ✅ 已完成

### 1. 数据库 Schema

- [X] `alembic/versions/20240722_0001_initial_schema.py` - 合并 tenants 和 users 表
- [X] `alembic/versions/e23b22c205c4_add_tenant_embedding_api_profile.py` - 更新外键引用
- [X] `src/mul_in_one_nemo/db/models.py` - 更新 SQLAlchemy 模型
- [X] `src/mul_in_one_nemo/service/models.py` - 更新数据传输对象

### 新的 users 表结构

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    display_name VARCHAR(128),
    role VARCHAR(32) DEFAULT 'member',
    created_at TIMESTAMP,
    embedding_api_profile_id INTEGER REFERENCES api_profiles(id)
);
```

## 🔧 待修改文件清单

### A. Repository 层 (`src/mul_in_one_nemo/service/repositories.py`)

#### 修改要点：

1. 移除所有 `TenantRow` 相关导入和引用
2. 将 `UserRow` 重命名理解为新的 User（原 Tenant+User）
3. 所有方法签名：`tenant_id: str, user_id: str` → `username: str`
4. 数据库查询：移除 tenant join，通过 `users.username` 过滤

#### 具体修改位置：

**导入部分** (第1-30行)

```python
# 删除
from ..db.models import Tenant as TenantRow, User as UserRow

# 改为
from ..db.models import User as UserRow
```

**PersonaRepository 类**

- `get_tenant_embedding_config(tenant_id)` → `get_user_embedding_config(username)`
- `get_embedding_api_config_for_tenant(tenant_id)` → `get_embedding_api_config_for_user(username)`
- `load_persona_settings(tenant_id)` → `load_persona_settings(username)`

查询示例修改：

```python
# 原来 (约 line 80-90)
stmt = (
    select(PersonaRow, TenantRow.name, APIProfileRow)
    .join(TenantRow, PersonaRow.tenant_id == TenantRow.id)
    .where(TenantRow.name == tenant_id)
)

# 改为
stmt = (
    select(PersonaRow, UserRow.username, APIProfileRow)
    .join(UserRow, PersonaRow.user_id == UserRow.id)
    .where(UserRow.username == username)
)
```

**SessionRepository 类**

- `create(tenant_id, user_id, ...)` → `create(username, ...)`
- `list_sessions(tenant_id, user_id)` → `list_sessions(username)`
- `get_session(session_id)` 保持不变，但内部实现简化

session_id 生成：

```python
# 原来 (约 line 133)
session_id = f"sess_{tenant_id}_{uuid.uuid4().hex[:8]}"

# 改为
session_id = f"sess_{username}_{uuid.uuid4().hex[:8]}"
```

查询修改示例 (约 line 450-460)：

```python
# 原来
stmt = (
    select(SessionRow, TenantRow.name, UserRow.email)
    .join(TenantRow, SessionRow.tenant_id == TenantRow.id)
    .join(UserRow, SessionRow.user_id == UserRow.id)
    .where(TenantRow.name == tenant_id, UserRow.email == user_id)
)

# 改为
stmt = (
    select(SessionRow, UserRow.username)
    .join(UserRow, SessionRow.user_id == UserRow.id)
    .where(UserRow.username == username)
)
```

**_get_or_create_user 方法** (约 line 400-430)

```python
# 删除整个方法，因为不再需要 tenant/user 两级查找
# 改为简单的 username 查询：

async def _get_user_by_username(self, db, username: str) -> UserRow:
    stmt = select(UserRow).where(UserRow.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User '{username}' not found")
    return user
```

**_to_session_record** (约 line 180-210)

```python
# 原来
def _to_session_record(
    self, 
    session_row: SessionRow, 
    tenant_name: str, 
    user_email: str,
    participants
) -> SessionRecord:
    return SessionRecord(
        id=session_row.id,
        tenant_id=tenant_name,
        user_id=user_email,
        ...
    )

# 改为
def _to_session_record(
    self, 
    session_row: SessionRow, 
    username: str,
    participants
) -> SessionRecord:
    return SessionRecord(
        id=session_row.id,
        username=username,
        ...
    )
```

### B. Service 层 (`src/mul_in_one_nemo/service/session_service.py`)

#### 修改要点：

- `create_session(tenant_id, user_id, ...)` → `create_session(username, ...)`
- 所有调用 repository 的地方更新参数

**SessionService 类** (约 line 190-210)

```python
# 原来
async def create_session(
    self,
    tenant_id: str,
    user_id: str,
    user_persona: str | None = None,
    initial_persona_ids: list[int] | None = None,
) -> SessionRecord:
    async with self._repo as repo:
        return await repo.create(
            tenant_id, user_id, 
            user_persona=user_persona, 
            initial_persona_ids=initial_persona_ids or []
        )

# 改为
async def create_session(
    self,
    username: str,
    user_persona: str | None = None,
    initial_persona_ids: list[int] | None = None,
) -> SessionRecord:
    async with self._repo as repo:
        return await repo.create(
            username,
            user_persona=user_persona, 
            initial_persona_ids=initial_persona_ids or []
        )
```

### C. API 路由层

#### C.1 Sessions 路由 (`src/mul_in_one_nemo/service/routers/sessions.py`)

**查询参数修改** (所有端点)

```python
# 原来
@router.post("")
async def create_session(
    tenant_id: str = Query(...),
    user_id: str = Query(...),
    ...
):

# 改为
@router.post("")
async def create_session(
    username: str = Query(...),
    ...
):
```

**调用更新**

```python
# 原来
session = await session_service.create_session(tenant_id, user_id, ...)

# 改为
session = await session_service.create_session(username, ...)
```

需要修改的端点：

- `POST /api/sessions` - 创建会话
- `GET /api/sessions` - 列出会话
- `POST /api/sessions/{session_id}/messages` - 发送消息
- `GET /api/sessions/{session_id}` - 获取会话详情（可能不需要改）

#### C.2 Personas 路由 (`src/mul_in_one_nemo/service/routers/personas.py`)

**查询参数修改**

```python
# 原来
@router.get("")
async def list_personas(
    tenant_id: str = Query("default_tenant"),
    ...
):

# 改为
@router.get("")
async def list_personas(
    username: str = Query(...),
    ...
):
```

**调用更新**

```python
# 原来
personas = await persona_repo.load_persona_settings(tenant_id)

# 改为
personas = await persona_repo.load_persona_settings(username)
```

需要修改的端点：

- `GET /api/personas` - 列出角色
- `POST /api/personas` - 创建角色
- `PUT /api/personas/{persona_id}` - 更新角色
- `DELETE /api/personas/{persona_id}` - 删除角色

#### C.3 API Profiles 路由 (`src/mul_in_one_nemo/service/routers/api_profiles.py`)

同样的模式：`tenant_id` → `username`

### D. RAG 服务层 (`src/mul_in_one_nemo/service/rag_service.py`)

#### 修改要点：

- Collection 命名：`{tenant_id}_persona_{id}_rag` → `{username}_persona_{id}_rag`
- 方法签名更新

**ingest_text 方法** (约 line 380-420)

```python
# 原来
async def ingest_text(
    self,
    text: str,
    persona_id: int,
    tenant_id: str,
    source: str = "background",
) -> int:
    collection_name = f"{tenant_id}_persona_{persona_id}_rag"
    ...

# 改为
async def ingest_text(
    self,
    text: str,
    persona_id: int,
    username: str,
    source: str = "background",
) -> int:
    collection_name = f"{username}_persona_{persona_id}_rag"
    ...
```

**delete_documents_by_source** (约 line 440-470)

```python
# tenant_id → username
```

**query 方法** (约 line 280-320)

```python
# tenant_id → username
```

### E. Runtime 和 Tools

#### E.1 RAG Context (`src/mul_in_one_nemo/service/rag_context.py`)

如果存在 tenant_id 的 context 变量，改为 username：

```python
# 原来
_rag_context_tenant: ContextVar[str | None] = ContextVar("rag_tenant", default=None)

# 改为
_rag_context_username: ContextVar[str | None] = ContextVar("rag_username", default=None)
```

#### E.2 RAG Query Tool (`src/mul_in_one_nemo/tools/rag_query_tool.py`)

**Config 类** (约 line 46)

```python
# 原来
class RagQueryToolConfig(BaseModel):
    tenant_id: Optional[str] = Field(default=None, ...)
    persona_id: Optional[int] = Field(default=None, ...)

# 改为
class RagQueryToolConfig(BaseModel):
    username: Optional[str] = Field(default=None, ...)
    persona_id: Optional[int] = Field(default=None, ...)
```

**_single 方法** (约 line 66-90)

```python
# 原来
ctx_tenant, ctx_persona = get_rag_context()
tenant_id = ctx_tenant or config.tenant_id
persona_id = ctx_persona or config.persona_id
collection_name = f"{tenant_id}_persona_{persona_id}_rag"

# 改为
ctx_username, ctx_persona = get_rag_context()
username = ctx_username or config.username
persona_id = ctx_persona or config.persona_id
collection_name = f"{username}_persona_{persona_id}_rag"
```

#### E.3 Runtime Adapter (`src/mul_in_one_nemo/service/runtime_adapter.py`)

**invoke_stream 方法** (约 line 160-170, 250-260)

```python
# 原来
set_rag_context(tenant_id=session.tenant_id, persona_id=persona_id)

# 改为
set_rag_context(username=session.username, persona_id=persona_id)
```

#### E.4 Dependencies (`src/mul_in_one_nemo/service/dependencies.py`)

**get_rag_service** (约 line 75-95)

```python
# 原来
persona_record.tenant_id
embedding_config = await repo.get_tenant_embedding_config(persona_record.tenant_id)
embedding_api_config = await repo.get_embedding_api_config_for_tenant(persona_record.tenant_id)

# 改为
persona_record.username
embedding_config = await repo.get_user_embedding_config(persona_record.username)
embedding_api_config = await repo.get_embedding_api_config_for_user(persona_record.username)
```

### F. 前端 API 调用 (`src/mio_frontend/`)

#### 搜索并替换：

```bash
# 在前端代码中搜索
tenant_id=
tenantId:
tenant_id:

# 全部替换为
username=
username:
username:
```

#### 主要文件（可能）：

- API 客户端代码
- 状态管理（如 Redux/Zustand stores）
- 组件中的 API 调用

示例：

```typescript
// 原来
const response = await fetch(`/api/sessions?tenant_id=default_tenant&user_id=test`);

// 改为
const response = await fetch(`/api/sessions?username=test`);
```

### G. 配置和工具

#### G.1 测试文件 (`tests/`)

- 更新所有测试用例中的 `tenant_id` → `username`
- 更新 mock 数据

#### G.2 文档

- `README.md` - 更新 API 示例
- `docs/` - 更新架构文档

## 🔍 搜索替换辅助命令

```bash
# 1. 查找所有 tenant_id 引用
rg "tenant_id" src/ --type py

# 2. 查找所有 TenantRow 引用
rg "TenantRow" src/ --type py

# 3. 查找所有 get_tenant 开头的方法
rg "get_tenant" src/ --type py

# 4. 查找所有 collection 命名
rg "f\"{.*}_persona_" src/ --type py
```

## ⚠️ 注意事项

### 1. Milvus Collections

旧的 collections 不会自动迁移，需要：

- 方案 A：重建所有 collections（删除旧数据）
- 方案 B：手动重命名 collections（保留旧数据）

```python
# 如果需要迁移 Milvus 数据
from pymilvus import connections, utility

connections.connect(host="localhost", port="19530")

# 列出所有 collections
collections = utility.list_collections()
for coll in collections:
    if coll.startswith("default_tenant_"):
        new_name = coll.replace("default_tenant_", "test_")
        # Milvus 不支持重命名，需要复制数据
        print(f"需要手动迁移: {coll} -> {new_name}")
```

### 2. Session ID 格式变化

```python
# 旧格式: sess_default_tenant_abc123
# 新格式: sess_test_abc123
```

现有 sessions 的 ID 不会改变，但新创建的会用新格式。

### 3. 向后兼容性

如果需要支持旧 API：

```python
# 在路由中添加兼容层
@router.get("")
async def list_sessions(
    username: str = Query(None),
    # 兼容旧参数
    tenant_id: str = Query(None),
    user_id: str = Query(None),
):
    # 优先使用新参数
    if username:
        actual_username = username
    elif tenant_id and user_id:
        # 旧方式：假设 user_id 就是 username
        actual_username = user_id
    else:
        raise HTTPException(400, "Missing username parameter")
  
    return await session_service.list_sessions(actual_username)
```

## ✅ 验证步骤

### 1. 数据库验证

```bash
# 运行迁移
uv run alembic upgrade head

# 创建测试用户
psql -h .postgresql/run -U postgres mul_in_one -c "
INSERT INTO users (username, email, display_name, role)
VALUES ('test', 'test@example.com', 'Test User', 'admin');
"

# 验证表结构
psql -h .postgresql/run -U postgres mul_in_one -c "\d users"
```

### 2. 代码验证

```bash
# 检查导入错误
uv run python -c "from src.mul_in_one_nemo.db import models; print('OK')"

# 检查类型错误
uv run mypy src/mul_in_one_nemo/service/ --ignore-missing-imports
```

### 3. 功能测试

```bash
# 启动后端
./scripts/start_backend.sh

# 测试 API
curl "http://localhost:8000/api/sessions?username=test"
curl -X POST "http://localhost:8000/api/sessions?username=test"
```

## 📊 预估工作量

- **Repository 层**: 2-3 小时（最复杂）
- **Service 层**: 1 小时
- **API 路由**: 1-2 小时
- **RAG 相关**: 1 小时
- **前端**: 1-2 小时
- **测试验证**: 1 小时
- **总计**: 7-10 小时

## 🎯 建议执行顺序

1. ✅ 数据库 Schema（已完成）
2. ✅ 数据模型（已完成）
3. Repository 层（最核心）
4. Service 层
5. API 路由层
6. RAG 和 Tools
7. 前端调用
8. 测试验证

## 🔄 回滚计划

如果出现问题，可以回滚：

```bash
# 1. 回滚代码
git reset --hard HEAD

# 2. 回滚数据库
uv run alembic downgrade -1

# 3. 恢复旧数据（如果有备份）
pg_restore -d mul_in_one backup.sql
```
