# 测试
# 1. 数据库修正
# 在项目根目录下的终端中执行：
# alembic revision --autogenerate -m "kb_assets_chunks_jobs"
# alembic upgrade head
# ✅db里出现表kb_assets, kb_chunks, kb_index_jobs
#
#
# 2. 启动FastAPI
# uvicorn app.main:app --reload
#
# 3. 健康检查
# curl http://127.0.0.1:8000/healthz
# ✅返回结果得到{"data":{"ok":true},"meta":null}
#
# curl http://127.0.0.1:8000/readyz
# ✅返回结果得到{"data":{"ok":true,"deps":{"db":true,"redis":true,"es":true,"qdrant":true}},"meta":null}
# 如果有false则某个组件木有启动正确，去看下docker
#
#
# 4. 启动Celery worker
# 打开一个后来不要关闭的终端
# celery -A app.infra.celery.celery_app.celery_app worker -l INFO
# ✅看到worker启动成功。日志里能看到已注册任务kb.ingest_asset。
# 我这边蓝色log出现后得到：
# [tasks]
#   . kb.ingest_asset   # 这里就是28号文件中，我们项目中目前唯一的消息队列的任务
#
# [2026-02-23 17:57:41,849: INFO/MainProcess] Connected to amqp://peter:**@127.0.0.1:5672//
# [2026-02-23 17:57:41,853: INFO/MainProcess] mingle: searching for neighbors
# [2026-02-23 17:57:42,901: INFO/MainProcess] mingle: all alone
# [2026-02-23 17:57:42,943: INFO/MainProcess] celery@airm2 ready.
#
#
# 5. 获取token/workspace_id
# ‼️之前我们所有用户的密码应该都是Password123! （包含叹号）
#
# 5.1 注册新用户，过年前注册的我忘了，注册一个新的，⚠️密码至少8位
# 如果没有忘记密码，或者尝试一下Password123!。用之前的用户直接登录即可。
# curl -i -X POST http://127.0.0.1:8000/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"user2@example.com","password":"12345678"}'
#
#
# 5.2 登录拿token
# TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"user2@example.com","password":"12345678"}' | jq -r '.data.access_token // .access_token')
#
#
# 5.3 拿到workspace id
# WS_JSON=$(curl -s http://127.0.0.1:8000/workspaces \
#   -H "Authorization: Bearer $TOKEN")
#
# WORKSPACE_ID=$(echo "$WS_JSON" | jq -r '.data[0].id')
# echo "$WORKSPACE_ID"
# ✅我这里是2，你那边反正应该是一个int数字。
#
#
# 5.4 管理员登录拿token，⚠️之前测试脚本密码是Password123!
# ADMIN_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"admin@example.com","password":"Password123!"}' | jq -r '.data.access_token // .access_token')
#
# 这里记得打印一下echo $ADMIN_TOKEN一定要有结果
#
# 5.5 取普通用户id
# USER_ID=$(curl -s http://127.0.0.1:8000/auth/me \
#   -H "Authorization: Bearer $TOKEN" | jq -r '.data.id')
#
#
# 5.6 管理员给普通用户在该workspace授权admin角色
# ⚠️为了得到这个结果，我改了一下他们哪个代码app/modules/admin/routes.py，事务问题没有很好解决
# res = await db.execute(stmt)
# if not db.in_transaction():
#     await db.commit()
#
# rc = int(getattr(res, "rowcount", 0) or 0)
# idempotent = (rc == 0)
#
#
# curl -i -X POST "http://127.0.0.1:8000/admin/grants?workspace_id=$WORKSPACE_ID" \
#   -H "Authorization: Bearer $ADMIN_TOKEN" \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"user_id\": $USER_ID,
#     \"role_name\": \"admin\",
#     \"scope_key\": \"workspace:$WORKSPACE_ID\"
#   }"
# ✅
# HTTP/1.1 201 Created
# date: Mon, 23 Feb 2026 10:30:58 GMT
# server: uvicorn
# content-length: 56
# content-type: application/json
# x-request-id: 0a9aa227a5634c34afec824542318312
# x-response-time-ms: 41
# x-content-type-options: nosniff
# x-frame-options: DENY
# referrer-policy: no-referrer
# permissions-policy: geolocation=(), microphone=(), camera=()
#
# {"data":{"granted":true,"idempotent":false},"meta":null}
#
#
#
# 5.7 用普通用户测试创建资产
# cat >> hello.txt
# The quick brown fox jumps over the lazy dog.
# This document is used for KB ingestion testing.
# Apple banana orange.
#
#
# curl -i -X POST http://127.0.0.1:8000/kb/assets \
#   -H "Authorization: Bearer $TOKEN" \
#   -H "Content-Type: application/json" \
#   -H "X-Workspace-Id: $WORKSPACE_ID" \
#   -d '{
#     "filename":"hello.txt",
#     "title":"Hello Doc",
#     "mime_type":"text/plain",
#     "project_id": null,
#     "resource_type":"doc",
#     "meta":{"source":"manual_test"}
#   }'
#
#
#
#
# 6. KB测试用例
# 6.1 创建asset
# curl -X POST http://127.0.0.1:8000/kb/assets \
#   -H "Authorization: Bearer $TOKEN" \
#   -H "Content-Type: application/json" \
#   -H "X-Workspace-Id: $WORKSPACE_ID" \
#   -d '{
#     "filename":"hello.txt",
#     "title":"Hello Doc",
#     "mime_type":"text/plain",
#     "project_id": null,
#     "resource_type":"doc",
#     "meta":{"source":"manual_test"}
#   }'
# ✅HTTP 201，返回里有asset_id，status通常是pending
#
# 6.2 上传文件内容
# 上传：
# curl -X POST "http://127.0.0.1:8000/kb/assets/$ASSET_ID/upload" \
#   -H "Authorization: Bearer $ACCESS_TOKEN" \
#   -H "X-Workspace-Id: $WID" \
#   -F "file=@hello.txt;type=text/plain"
#
# ✅返回 storage_key、size_bytes、sha256
# ✅DB里这个asset的status变为uploaded
# ✅本地目录 ./data/blob/ws/<wid>/assets/<asset_id>/original/hello.txt出现
#
# 6.3 触发ingest
# curl -X POST "http://127.0.0.1:8000/kb/assets/$ASSET_ID/ingest" \
#   -H "Authorization: Bearer $ACCESS_TOKEN" \
#   -H "X-Workspace-Id: $WID"
#
# ✅HTTP 202，返回 { task_name: "kb.ingest_asset", asset_id: ... }
# 然后看 worker 日志，应该能看到任务开始/结束。
#
# 6.4 验证ingest结果
# 看数据库对不对
# kb_assets.status应该从indexing变成ready
# kb_chunks 应该有多行（至少 1 行）
# kb_index_jobs 对应 asset 的 status 应为 done
# Qdrant验证collection kb_chunks存在
# points数量增加大致=chunks数
# kb_chunks 表里能看到切出来的chunk内容
# Qdrant payload 包含 workspace_id/project_id/asset_id/chunk_id/resource_type
#
#
# 7. 检索测试
# 7.1 BM25
#
# curl -X POST http://127.0.0.1:8000/kb/search \
#   -H "Authorization: Bearer $ACCESS_TOKEN" \
#   -H "X-Workspace-Id: $WID" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "q":"quick brown fox",
#     "mode":"bm25",
#     "top_k": 5,
#     "project_id": null
#   }'
#
# ✅items非空，sources包含bm25，ontent里能看到含quick brown fox的chunk
#
# 7.2 Dense
#
# curl -X POST http://127.0.0.1:8000/kb/search \
#   -H "Authorization: Bearer $ACCESS_TOKEN" \
#   -H "X-Workspace-Id: $WID" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "q":"animals jumping",
#     "mode":"dense",
#     "top_k": 5
#   }'
#
# ✅items可能也非空（dense取决于embedding模型与语义相似）
# ✅sources包含dense
#
# 7.3 Hybrid=
#
# curl -X POST http://127.0.0.1:8000/kb/search \
#   -H "Authorization: Bearer $ACCESS_TOKEN" \
#   -H "X-Workspace-Id: $WID" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "q":"banana orange",
#     "mode":"hybrid",
#     "top_k": 5
#   }'
#
# ✅items非空
# sources常见是["bm25","dense"]或其中之一
# score是RRF分数，不是原始bm25/dense分