# 环境变量配置补充说明

在 README.md 的 "快速开始" 部分，在 "#### 2. 初始化后端" 和 "#### 3. 配置数据库" 之间添加以下内容：

---

#### 3. 配置环境变量 ⚠️ **必须**

复制环境变量模板并配置：

```bash
cp .envrc.example .envrc
```

编辑 `.envrc` 文件，**必须配置**以下项：

```bash
# 数据库连接
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/mul_in_one"

# JWT 认证密钥（生产环境必须修改！使用下面的命令生成随机密钥）
export JWT_SECRET="your-secret-key-change-in-production"

# 生成安全的随机密钥（推荐）
# export JWT_SECRET="$(openssl rand -hex 32)"

# OAuth 配置（可选，如需第三方登录则取消注释）
# export GITEE_CLIENT_ID="your-gitee-client-id"
# export GITEE_CLIENT_SECRET="your-gitee-client-secret"
# export GITHUB_CLIENT_ID="your-github-client-id"
# export GITHUB_CLIENT_SECRET="your-github-client-secret"

# 其他配置见 .envrc.example 中的详细注释
```

加载环境变量：

```bash
direnv allow  # 如果使用 direnv（推荐）
# 或者手动加载
source .envrc
```

> ⚠️ **重要安全提示**: 
> - `.envrc` 包含敏感信息（API密钥、数据库密码、JWT密钥等）
> - 该文件已自动加入 `.gitignore`，**请勿提交到版本控制系统**
> - 生产环境务必使用强随机密钥，不要使用示例中的默认值

> 📚 **认证系统文档**: 查看 [docs/authentication.md](docs/authentication.md) 了解完整的用户认证和 OAuth 配置指南

---

然后将原来的 "#### 3. 配置数据库" 改为 "#### 4. 配置数据库"，以此类推后续步骤编号都加1。
