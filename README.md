# 项目名称
enterprise_assistant

# 一、项目介绍
这是一个知识库助手...

# 二、项目结构
```text
app/
├── core/                           # common，公共的
│   ├── http_consts.py  	            # HTTP头与状态字段常量
│   ├── enums.py  		                # 枚举：环境、JWT 算法等
│   ├── api_schemas.py  		        # 统一API响应/错误的Pydantic Schema
│   ├── api_response.py  	            # ok/no-store等响应构造工具
│   ├── error_codes.py  	            # 错误码 -> message/status映射表
│   ├── errors.py  		                # AppError + raise_err/resolve_message
│   ├── request_context.py  	        # ContextVar：request_id/user_id/ip/ua
│   ├── redaction.py  		            # 脱敏，主要是一些token字段等，比如密码，不要记录到日志或者审计中
│   ├── logging_setup.py  	            # JSON日志格式化和全局的日志配置
│   ├── security_defaults.py  	        # 安全头默认值，比如HSTS/XFO/Referrer等
│   └── config.py
├── infra/  			            # 基础设施层，主要是外部依赖客户端连接
│   ├── db.py 	
│   ├── redis_client.py	
│   └── elasticsearch_client.py	
├── celery_app.py		            # Celery应用入口
├── tasks/  			            # Celery任务集合
│   └── example.py
├── models/  			            # ORM基础与统一导出
│   ├── base.py  		                # Declarative Base（所有模型的基类）
│   └── __init__.py  		            # 聚合导入模型
├── audit/ 
│   ├── models.py 
│   ├── context.py  		            # 审计事件缓冲区ContextVar
│   ├── middleware.py  		            # init/flush请求结束批量写入audit_events
│   └── service.py  		            # record()写入审计事件到缓冲区并脱敏meta
├── web/  	
│   ├── routes_consts.py  	        # 路由相关常量
│   ├── exception_handlers.py  	    # 全局异常，然后统一错误
│   ├── openapi.py  		        # OpenAPI增强，主要是统一错误响应与响应头
│   ├── health.py  		            # 健康检查
│   ├── startup_checks.py  	        # 启动自检
│   └── middleware/  		        # Web中间件集合
│       ├── real_ip.py  	            # 解析真实客户端IP
│       ├── middleware.py  	            # RequestContext：rid/耗时/ctx + audit flush
│       ├── cors.py  		            # CORS安装封装
│       ├── security_headers.py         # 安全响应头中间件
│       └── rate_limit.py  	            # 基于Redis的固定窗口IP限流依赖
├── auth/	
│   └── models.py  		                # User/Role/Permission/UserRoleGrant等ORM，这里为后面的authz和n使用
└── resources/
    └── models.py  		                # 资源域模型，主要是权限部分用的资源，写好这里workspace/project/resource目录）
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