# Panorama Companion 部署与 CI 文档

## 1. 当前部署定位

Panorama Companion 当前是黑客松 MVP，推荐优先使用本地或单机部署：

- 前端：Vite 构建出的静态文件。
- 后端：FastAPI + Uvicorn。
- 存储：本地文件目录 + 内存状态。
- 外部服务：默认不依赖；AI 和地图都可走 mock/demo 模式。

生产化前建议先完成数据库、对象存储和异步任务队列改造。

## 2. 本地开发部署

推荐一键启动：

```powershell
.\scripts\start-dev.ps1
```

默认地址：

```text
Web: http://127.0.0.1:5173
API: http://127.0.0.1:8010
```

停止服务：

```powershell
.\scripts\stop-dev.ps1
```

## 3. 本地生产构建

后端测试：

```powershell
cd api
.\.venv\Scripts\python -m pytest -q
```

前端构建：

```powershell
cd web
npm run build
```

如果 PowerShell 的 `npm` 解析异常，可使用：

```powershell
cd web
node .\node_modules\typescript\bin\tsc -b
node .\node_modules\vite\bin\vite.js build
```

构建产物：

```text
web/dist
```

## 4. GitHub Actions CI

CI 配置：

```text
.github/workflows/ci.yml
```

当前 CI 包含三个 Job：

- `API tests`
  - Python 3.12
  - 安装 `api/requirements-dev.txt`
  - 执行 `python -m pytest -q`
- `Web build`
  - Node 22
  - 执行 `npm ci`
  - 执行 `npm run build`
- `Docker image builds`
  - 构建 `api/Dockerfile`
  - 构建 `web/Dockerfile`
  - 验证容器镜像构建链路没有缺文件或依赖错误

触发条件：

- push 到 `main`
- pull request

## 5. 单机部署建议

### 5.1 后端

安装依赖：

```bash
cd api
python -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

启动：

```bash
./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
```

推荐使用进程管理器：

- systemd
- Supervisor
- PM2
- Docker Compose

### 5.2 前端

构建：

```bash
cd web
npm ci
npm run build
```

部署 `web/dist` 到静态服务器：

- Nginx
- Caddy
- Vercel
- Netlify
- Cloudflare Pages

如果前端和后端分域部署，需要设置：

```env
VITE_API_BASE_URL=https://your-api-domain.com
WEB_ORIGIN=https://your-web-domain.com
APP_BASE_URL=https://your-api-domain.com
```

## 6. Docker Compose 部署

仓库已提供基础容器化配置：

```text
api/Dockerfile
web/Dockerfile
web/nginx.conf
docker-compose.yml
```

本地构建并启动：

```bash
cp .env.example .env
docker compose up --build
```

默认端口：

```text
Web: http://127.0.0.1:5173
API: http://127.0.0.1:8010
```

停止服务：

```bash
docker compose down
```

清理演示数据卷：

```bash
docker compose down -v
```

Compose 当前包含：

- `api`：FastAPI + Uvicorn，镜像内预装 FFmpeg。
- `web`：Vite 静态构建产物 + Nginx。
- `panorama_data`：持久化上传素材、抽帧结果和导出文件。

Compose 可通过根目录 `.env` 覆盖 AI、地图、抽帧和前端构建变量。

## 7. 环境变量清单

后端：

```env
APP_ENV=production
WEB_ORIGIN=https://your-web-domain.com
APP_BASE_URL=https://your-api-domain.com
DATA_DIR=/var/lib/panorama-companion/data
FRAME_EXTRACT_INTERVAL_SECONDS=4
MAX_FRAME_ANALYSIS_COUNT=12
AI_PROVIDER=mock
MAP_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=
OPENAI_VISION_MODEL=
AMAP_WEB_KEY=
AMAP_WEB_SERVICE_KEY=
```

前端：

```env
VITE_API_BASE_URL=https://your-api-domain.com
VITE_AMAP_WEB_KEY=
```

## 8. 文件与持久化

当前本地文件目录：

```text
api/data/uploads
api/data/frames
api/data/exports
```

生产化建议：

- 上传原素材放对象存储。
- 抽帧结果放对象存储。
- ZIP 导出结果放对象存储。
- 数据库只保存 URL、metadata 和处理状态。

推荐对象存储：

- S3
- Cloudflare R2
- 阿里云 OSS
- 腾讯云 COS

Docker Compose 模式下文件持久化到命名卷：

```text
panorama_data
```

## 9. FFmpeg

视频抽帧依赖系统 `ffmpeg` 命令。

MVP 兜底策略：

- FFmpeg 不存在：生成演示 SVG 帧。
- 抽帧失败：生成演示 SVG 帧。
- 视频过大或超时：生成演示 SVG 帧。

生产化建议：

- 容器镜像内预装 FFmpeg。
- 限制上传文件大小。
- 抽帧任务异步化。
- 保存 FFmpeg stderr 便于排查。

## 10. Docker 化后续建议

当前仓库已包含基础 Dockerfile 和 Compose。生产化建议继续拆分：

```text
api/Dockerfile
web/Dockerfile
docker-compose.yml
```

推荐服务：

```text
web
api
postgres
redis
worker
object-storage
```

其中：

- `api` 负责 REST 请求。
- `worker` 负责抽帧、AI 分析、ZIP 打包、视频渲染。
- `postgres` 存业务数据。
- `redis` 存队列和短期缓存。

## 11. 上线前检查清单

- 设置 `APP_ENV=production`。
- 设置正确的 `WEB_ORIGIN`。
- 设置正确的 `APP_BASE_URL`。
- 确认 `/files` 静态文件访问路径可用。
- 配置 CORS 域名。
- 配置上传文件大小限制。
- 配置 HTTPS。
- 配置日志采集。
- 配置数据备份。
- 配置素材删除策略。
- 检查隐私授权文案。
- 检查 AI Key、地图 Key 是否只存在服务端环境变量中。

## 12. 监控建议

后端建议监控：

- `/health` 状态。
- API 5xx 错误率。
- 抽帧失败率。
- 导出失败率。
- 平均抽帧耗时。
- 平均导出耗时。
- 数据目录磁盘占用。

前端建议监控：

- 页面加载失败率。
- API 请求失败率。
- 一键演示完成率。
- ZIP 导出点击率。

## 13. 回滚策略

MVP 阶段：

- 保留最近可运行 commit。
- 保留 `.env.example`。
- 保留本地演示素材 fallback。

生产阶段：

- 前端静态产物按版本发布。
- 后端 API 使用镜像 tag。
- 数据库迁移必须支持回滚或前向兼容。
- 导出 manifest 使用 `schema` 字段标识版本。
