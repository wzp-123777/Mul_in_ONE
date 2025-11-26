# RAG 技术整合开发计划

为了深化 Persona 的角色设定，我们计划引入 NVIDIA NeMo Agent Toolkit 的 RAG (Retrieval-Augmented Generation) 技术。这使得 Persona 不再仅仅依赖于简短的 System Prompt，而是能够拥有并利用海量的背景知识（例如个人传记、专业领域知识库等），从而在对话中展现出更丰富的个性、记忆和知识水平。

## 第一阶段：技术调研与原型验证

**目标：** 验证 NeMo RAG 功能的核心流程，为后续集成铺平道路。

1. **分析 RAG 示例：**

   * **位置：** `external/NeMo-Agent-Toolkit/examples/RAG/simple_rag`
   * **重点：** 研究 `configs` 目录下的 `milvus_*.yml` 配置文件，理解 RAG Agent 的配置结构、数据源（Vector Store）的连接方式以及工具的定义。
   * **分析：** 明确数据处理、知识库索引和检索的关键组件。
2. **构建独立原型：**

   * 基于 `simple_rag` 示例，编写一个独立的 Python 脚本。
   * 该脚本将模拟完整的 RAG 流程：
     * 连接到一个本地或容器化的 Milvus 实例。
     * 读取一个示例文本文件（例如，一篇人物简介）。
     * 将文本进行切片、编码，并存入 Milvus 集合（Collection）。
     * 初始化一个配置了 RAG 功能的 NeMo Agent。
     * 提出一个与示例文本相关的问题，验证 Agent 能否通过 RAG 检索信息并给出正确答案。

## 第二阶段：后端集成开发

**目标：** 将 RAG 功能无缝整合到现有后端服务中。

1. **扩展数据库模型：**

   * **文件：** `src/mul_in_one_nemo/db/models.py`
   * **变更：**
   * * 创建一个新的数据表 `persona_documents`，用于存储 Persona 关联的知识库文档信息。
     * 字段应包括：`id`, `persona_id` (外键关联 `personas` 表), `document_name`, `document_path`, `status` (例如：'uploaded', 'processing', 'indniexed', 'error')。
2. **开发数据导入服务：**

   * **创建新的 API 端点：**
     * `POST /api/v1/personas/{persona_id}/documents`：用于上传指定 Persona 的知识库文档。
     * `GET /api/v1/personas/{persona_id}/documents`：获取指定 Persona 的所有文档列表。
     * `DELETE /api/v1/documents/{document_id}`：删除指定的知识库文档（并从 Vector Store 中移除相关数据）。
   * **实现后台处理任务：**
     * 文档上传后，API 将文件保存到指定位置，并在 `persona_documents` 表中创建一条记录，状态为 'uploaded'。
     * 触发一个异步后台任务（例如，使用 aio-pika 或 aio-celery）。
     * 该任务负责：
       1. 读取文档内容。
       2. 对文本进行切片（Chunking）。
       3. 调用 embedding 模型生成向量。
       4. 将向量和元数据存入 Milvus 中为该 Persona 单独创建的 Collection。
       5. 更新 `persona_documents` 表中对应记录的状态为 'indexed'。
3. **整合到对话运行时：**

   * **文件：** `src/mul_in_one_nemo/runtime.py`
   * **变更：**
     * 在创建或加载 Agent（`NemoAgent` 实例）时，检查其 Persona 是否在 `persona_documents` 表中有关联且状态为 'indexed' 的文档。
     * 如果存在，动态地为其配置 RAG 工具，并将其指向 Milvus 中对应的 Collection。
     * 这意味着 `get_agent` 或类似的函数需要被改造，以支持动态添加 RAG 功能。

## 第三阶段：前端界面开发

**目标：** 提供用户友好的界面来管理 Persona 的知识库。

1. **设计文档管理 UI：**

   * **位置：** 在 Persona 编辑页面 (`src/mio_frontend/mio-frontend/src/pages/PersonasPage.vue` 或其子组件) 中增加一个新的区域。
   * **功能：**
     * 展示已上传的文档列表及其状态。
     * 提供一个文件上传控件，用于上传新的知识库文档。
     * 提供删除按钮，用于移除不再需要的文档。
     * 显示上传和索引的进度或状态。
2. **实现前端 API 调用：**

   * 在 `src/mio_frontend/mio-frontend/src/api.ts` 或相关模块中，添加与第二阶段创建的后端 API 端点对应的调用函数。
   * 将这些函数与新的 UI 组件进行绑定，完成前后端交互。

## 第四阶段：测试与优化

**目标：** 确保新功能的稳定性、可靠性和性能。

1. **编写单元与集成测试：**

   * **后端：** 为文档上传/删除 API、数据处理流程编写 `pytest` 测试用例。
   * **运行时：** 编写测试用例，验证 Agent 在有无 RAG 文档的情况下，其行为符合预期。
2. **进行端到端测试：**

   * 模拟完整用户流程：
     1. 创建一个 Persona。
     2. 为其上传一篇包含特定信息的知识文档。
     3. 等待文档索引完成。
     4. 开启一个包含该 Persona 的新会话。
     5. 向其提问，问题需要依赖于上传文档中的知识。
     6. 验证 Persona 是否能正确回答。
3. **性能与资源评估：**

   * 评估文档索引过程对系统资源的消耗。
   * 评估 RAG 检索在对话过程中的延迟影响。
   * 根据评估结果进行必要的优化。
