# 项目名称
enterprise_assistant

# 一、项目介绍
这是一个知识库助手...

# 二、项目结构

```text
app/
├── main.py                                  # FastAPI 应用 + 生命周期（lifespan）装配 + 路由安装
├── __init__.py
├── core/                                    # 横切核心（错误/配置/日志/上下文）
│   ├── __init__.py
│   ├── api_response.py                      # ok()/error 响应负载辅助函数
│   ├── api_schemas.py                       # ApiResponse/Empty/ErrorResponse 数据模型
│   ├── config.py                            # Settings（环境变量/URL/安全开关）
│   ├── enums.py                             # Env/JwtAlg 等枚举
│   ├── error_codes.py                       # 错误码 -> 状态码/消息 映射
│   ├── errors.py                            # AppError + raise_err/resolve_message
│   ├── http_consts.py                       # HTTP 头/状态 常量
│   ├── logging_setup.py                     # JSON 日志 + 上下文过滤器 + 脱敏
│   ├── redaction.py                         # token/密码 脱敏
│   ├── request_context.py                   # ContextVar：request_id/user_id/ip/ua/workspace_id
│   └── security_defaults.py                 # 默认安全响应头取值
├── infra/                                   # 外部系统客户端 + DB 引擎/会话
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                          # SQLAlchemy 声明式基类（DeclarativeBase）
│   │   ├── engine.py                        # create_async_engine()
│   │   ├── session.py                       # async_sessionmaker 工厂
│   │   └── deps.py                          # FastAPI 的 get_db() + 租户 set_config()
│   ├── redis_client.py                      # get_redis(request)
│   ├── elasticsearch_client.py              # create_es_client()
│   ├── qdrant_client.py                     # create_qdrant_client() + 集合（collection）辅助方法
│   ├── blob_storage/
│   │   ├── __init__.py
│   │   ├── interface.py                     # StorageBackend 协议 + StoredObject
│   │   ├── local_fs.py                      # 本地文件系统存储（开发环境）
│   │   └── s3_compat.py                     # S3/MinIO 兼容后端（生产环境）
│   └── celery/
│       ├── __init__.py
│       └── celery_app.py                    # Celery 应用实例 + 配置
├── api/                                     # HTTP 层（路由/中间件/OpenAPI/处理器）
│   ├── __init__.py
│   ├── exception_handlers.py                # AppError/校验/未处理异常 处理器 + 审计记录
│   ├── health.py                            # /healthz /readyz /version
│   ├── openapi.py                           # 注入头部 + 通用错误 schema
│   ├── response.py                          # no_store()、ok_no_store()
│   ├── routes_consts.py                     # NO_STORE_PATHS
│   ├── startup_checks.py                    # 生产安全检查 + 依赖探活（ping）
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── authn.py                         # 挂载认证路由
│   │   ├── admin.py                         # 挂载后台管理路由
│   │   ├── kb_assets.py                     # 资产上传/列表/删除
│   │   ├── kb_search.py                     # 搜索端点（仅检索）
│   │   ├── rag_chat.py                      # 聊天/提问端点（RAG 生成）
│   │   └── agents.py                        # Agent 端点（工具调用/工作流）
│   └── middleware/
│       ├── __init__.py
│       ├── cors.py                          # install_cors()
│       ├── rate_limit.py                    # Redis 固定窗口限流 依赖
│       ├── real_ip.py                       # get_real_ip()
│       ├── request_context.py               # request_id/耗时统计/审计刷盘（flush）
│       ├── security_headers.py              # HSTS/XFO/CSP 等
│       └── tenant.py                        # 工作区（workspace）上下文提取
├── modules/                                 # 业务域（纯服务/模型/依赖）
│   ├── __init__.py
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── context.py                       # ContextVar 缓冲区
│   │   ├── hook.py                          # 懒加载解析 record/init/flush（无硬依赖）
│   │   ├── middleware.py                    # init + flush_audit（写入 DB）
│   │   ├── models.py                        # AuditEvent 表
│   │   └── service.py                       # record() + 元数据归一化/脱敏
│   ├── security/
│   │   ├── __init__.py
│   │   ├── password.py                      # argon2 哈希/校验
│   │   ├── jwt.py                           # 创建/解析访问令牌
│   │   └── jwt_claims.py                    # claim 键名 + 令牌类型
│   ├── auth/
│   │   ├── __init__.py
│   │   └── models.py                        # User/Role/Permission/UserRoleGrant 等
│   ├── resources/
│   │   ├── __init__.py
│   │   └── models.py                        # Workspace/Project/资源目录
│   ├── authn/
│   │   ├── __init__.py
│   │   ├── consts.py                        # refresh token 常量 + 限流名（RL names）
│   │   ├── deps.py                          # get_current_user()
│   │   ├── routes.py                        # /auth 注册/登录/刷新/注销/我是谁（me）
│   │   ├── schemas.py                       # 请求/响应模型
│   │   └── service.py                       # refresh token 签发/校验/消费 + tokenver
│   ├── authz/
│   │   ├── __init__.py
│   │   ├── consts.py                        # SCOPE_GLOBAL
│   │   ├── deps.py                          # permission_required(...)
│   │   ├── scope_keys.py                    # scope 构建/解析 + 含 global 的 scopes
│   │   ├── seed.py                          # 默认 角色/权限 矩阵
│   │   ├── seed_sync.py                     # sync_authz(db)
│   │   └── service.py                       # require_perms(db,user,scope,perm_codes)
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── routes.py                        # /admin 授权（grants）CRUD
│   │   └── schemas.py                       # admin 数据模型
│   ├── kb/                                  # 知识库域（资产/摄取/索引状态）
│   │   ├── __init__.py
│   │   ├── consts.py                        # 允许的 mime/type、流水线状态、限制
│   │   ├── schemas.py                       # API 模型：AssetCreate/AssetResp/SearchReq...
│   │   ├── models.py                        # KBAsset/KBBlob/KBChunk/KBIndexJob/KBTag 表
│   │   ├── storage_keys.py                  # blob/派生物 的确定性 key 布局
│   │   ├── service.py                       # 资产生命周期：创建/上传完成/删除
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py                  # 编排器：步骤 + 状态机 + 幂等性
│   │   │   ├── steps/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sniff.py                 # 检测类型/元数据（pypdf/docx 等）
│   │   │   │   ├── extract_text.py          # PDF/DOCX 文本抽取
│   │   │   │   ├── transcode_media.py       # ffmpeg 媒体规范化转码（音频/视频）
│   │   │   │   ├── asr_whisper.py           # 语音转文本（whisper/faster-whisper）
│   │   │   │   ├── chunk_text.py            # 切块策略（token/语义/结构）
│   │   │   │   ├── embed_chunks.py          # 向量化（fastembed/openai）
│   │   │   │   └── write_indexes.py         # 写入 ES/Qdrant + 更新索引状态
│   │   │   └── utils.py                     # 通用辅助（哈希/临时文件等）
│   │   ├── maintenance/
│   │   │   ├── __init__.py
│   │   │   ├── reindex.py                   # 为 资产/scope 重建索引
│   │   │   └── purge.py                     # 合规删除：DB+ES+Qdrant+存储
│   │   └── deps.py                          # 从 request/workspace/project 构建 scope_key 的辅助
│   ├── search/                              # 检索算法（无 LLM、无 HTTP）
│   │   ├── __init__.py
│   │   ├── types.py                         # RetrievedChunk/QuerySpec/FilterSpec
│   │   ├── query_norm.py                    # 查询归一化 + 语言检测 + 过滤器
│   │   ├── bm25.py                          # BM25 词法检索（rank-bm25）
│   │   ├── dense.py                         # 向量检索（qdrant）
│   │   ├── hybrid.py                        # 混合检索（BM25 + 向量）
│   │   ├── fusion.py                        # RRF/加权融合/分数校准
│   │   ├── rerank.py                        # 重排接口（交叉编码器/LLM 重排）
│   │   ├── parent_child.py                  # 父子结构/章节感知 检索
│   │   ├── filters.py                       # RBAC 感知过滤（scope/resource）
│   │   └── service.py                       # 统一 API：retrieve(query, scope, topk, mode, ...)
│   ├── llm/                                 # 模型路由 + 提示词 + 护栏（不做检索）
│   │   ├── __init__.py
│   │   ├── consts.py                        # 模型名、限制、默认参数
│   │   ├── schemas.py                       # LLMRequest/LLMResponse/Usage
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── rag_answer.md                # 回答提示词模板
│   │   │   ├── query_rewrite.md             # 改写提示词模板
│   │   │   └── tool_agent.md                # 工具型 Agent 系统提示词
│   │   ├── guardrails.py                    # 脱敏 + 注入启发式检测 + 安全输出策略
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── openai_chat.py               # OpenAI Chat Completions 封装
│   │   │   ├── openai_embed.py              # OpenAI Embeddings 封装
│   │   │   └── fastembed_embed.py           # 本地 embeddings（fastembed）
│   │   ├── router.py                        # provider 选择 + fallback
│   │   └── service.py                       # generate/rewrite/embed/rerank 入口
│   ├── rag/                                 # 编排：检索 -> 构建上下文 -> 生成 -> 引用
│   │   ├── __init__.py
│   │   ├── schemas.py                       # AskReq/AskResp/Citation
│   │   ├── context_builder.py               # 将检索 chunks 打包为 prompt 上下文
│   │   ├── citations.py                     # 稳定引用 id + 偏移（offset）
│   │   ├── answer.py                        # RAG 主回答流程
│   │   └── service.py                       # ask(...) 单一门面
│   └── agents/                              # 智能体（工具 + 工作流）
│       ├── __init__.py
│       ├── schemas.py                       # AgentRunReq/AgentRunResp/ToolCall 追踪
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── kb_tools.py                  # 工具：搜索 KB/获取资产/发起上传
│       │   ├── ticket_tools.py              # 工具：创建/审批/关闭工单
│       │   └── admin_tools.py               # 工具：授予/撤销/列出角色（受保护）
│       ├── workflows/
│       │   ├── __init__.py
│       │   ├── chat_agent.py                # 会话型 Agent 的 langgraph 工作流
│       │   └── kb_ingest_agent.py           # 摄取 + 校验 + 总结 的工作流
│       └── service.py                       # run_agent(...) 门面
├── workers/                                 # Celery worker 进程边界（只放任务）
│   ├── __init__.py
│   ├── main.py                              # worker 启动（导入 celery_app + 发现任务）
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── kb_ingest.py                     # Celery 任务：运行 KB 摄取流水线
│   │   ├── kb_reindex.py                    # Celery 任务：重建索引
│   │   └── maintenance.py                   # Celery 任务：清理/合规删除
│   └── utils.py                             # 任务重试/退避（backoff）辅助
├── tests/                                   # 单元/集成测试（pytest）
│   ├── __init__.py
│   ├── conftest.py                          # 测试 app/夹具（db/redis）
│   ├── test_authn.py                        # 注册/登录/刷新/注销
│   ├── test_authz.py                        # require_perms 覆盖
│   ├── test_kb_assets.py                    # 资产生命周期
│   ├── test_kb_ingestion.py                 # 流水线步骤（stub 依赖）
│   ├── test_search.py                       # bm25/dense/hybrid/fusion/rerank
│   └── test_rag.py                          # ask(...)（mock llm）
alembic/
├── env.py                                   # 异步 alembic 环境（导入 models）
├── script.py.mako                           # 模板
└── versions/
    └── <revision>_init.py                   # 迁移文件（自动生成）
requirements.txt                             # 依赖版本锁定（pin）
.env                                         # 本地环境变量（不要提交）
```


# ## 其他
## 一、docker 容器部署
1. Postgres:18.1-bookworm
```bash
sudo docker run -d \
  --name pg18 \
  -e POSTGRES_PASSWORD='123456' \
  -p 5432:5432 \
  postgres:18.1-bookworm
```
2. Redis
```bash
sudo docker run --name some-redis \
      -d -p 6379:6379 \
      redis:7 redis-server\
      --save 60 1 \
      --loglevel warning 
```

3. RabbitMQ
```bash
sudo docker run -d --name rmq \
      -p 5672:5672 \
      -p 15672:15672 \
      -e RABBITMQ_DEFAULT_USER=peter \
      -e RABBITMQ_DEFAULT_PASS=123456 \
      rabbitmq:4.2-management 
```

4. ES
```bash
sudo docker run -d --name es01 \
      -p 9200:9200 \
      -e "discovery.type=single-node" \
      -e "xpack.security.enabled=false" \
      -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
      docker.elastic.co/elasticsearch/elasticsearch:9.2.3 
```



## 二、技术栈
| 分类 | 技术           |
|------|--------------|
| 后端 | Python / FastAPI |
| 数据库 | MySQL / PostgreSQL |
| 向量库 | Qdrant / Chroma |
| 模型 | 待定...        |
| 部署 | Docker       |


## 三、启动的服务
1. Celery
```bash
celery -A app.celery_app:celery_app worker -l info -Q audio -c
```

2. FastAPI
```bash
uvicorn app.main: app --reload --port 8002 
```