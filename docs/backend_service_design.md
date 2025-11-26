# Backend Service Design

## 1. 设计目标
覆盖多 Persona 会话、可扩展 RAG、低延迟消息生成、可靠调度。

## 2. 服务分层
API 层 -> 应用协调层 -> RuntimeSession 管理 -> Scheduler/队列层 -> 数据与向量存储层。

## 3. 请求生命周期
客户端发起 `POST /api/sessions/{id}/messages` 或 WebSocket 带 `ws_token` -> 路由验证 -> Persona & Session 绑定 -> 入队 -> RuntimeSession 消费 -> 调用 LLM 或检索 -> 生成消息 -> 推送给客户端。

## 4. API 概要
- POST /api/sessions/{id}/messages 发送消息
- GET /api/sessions/{id} 获取会话
- WebSocket /ws/sessions/{id}?ws_token=...

## 5. 数据模型
包含 Session, Message, Persona, RuntimeSession, 向量检索集合，消息与 Persona 多对一关联。

## 6. Runtime & Scheduler 策略
RuntimeSession 保持 sticky session 行为，对同一会话消息使用同一执行上下文；使用 asyncio.Queue 作为内部调度结构，支持优先级扩展。

## 7. 配置与依赖
api_configuration.yaml 管理模型与 persona 绑定；依赖 OpenAI 兼容接口、Milvus、SQLAlchemy、FastAPI。

## 8. 可观测性
计划添加 tracing (OpenTelemetry)、metrics (处理耗时、队列长度)、structured logging。

## 9. 迭代里程碑
里程碑1：基础会话与消息流转。里程碑2：RAG 集成。里程碑3：多 Persona 调度优化。里程碑4：可观测性与治理。

## 10. 进度记录
使用 docs/ 目录下进度文件每日记录，含完成项与问题。

## 11. 开放问题
- 调度优先级策略细化
- RAG 缓存刷新策略
- 失败重试次数与死信队列

## 12. 模块接口速览
Scheduler: push(message), pop(); RuntimeSession: run(message); Persona: build_prompt(); RAGService: ingest_url(), generate_response();

## 13. 测试策略
单元测试：模型/调度/配置解析；集成测试：消息生命周期；文档测试：设计文档关键段落与关键字；性能测试：高并发消息吞吐。

### 关键词引用
RuntimeSession / asyncio.Queue / sticky session / POST /api/sessions/{id}/messages / ws_token
