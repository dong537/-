# Panorama Companion 技术栈文档

## 1. 技术选型目标

Panorama Companion 的 MVP 目标是先证明完整产品闭环，而不是一开始追求重型工程化。技术栈围绕四个原则选择：

- 演示稳定：没有外部 Key 时也能完整跑通。
- 迭代快速：前后端都使用轻量框架，便于黑客松现场修改。
- 可真实接入：AI、地图、相机、媒体处理都预留 Provider/接口边界。
- 可交付：自动出片结果能导出 manifest 和精选帧 ZIP，方便后续剪辑工具接入。

## 2. 总体架构

```text
React Web
  ├─ 旅行目标输入
  ├─ 路线地图与状态按钮
  ├─ 素材上传/演示素材
  ├─ AI 伴游讲解与语音播报
  ├─ 精彩瞬间标记
  ├─ 自动出片结果
  └─ 旅程故事线

FastAPI API
  ├─ Trip / Route Service
  ├─ Media Service
  ├─ Agent Orchestrator
  ├─ Provider Layer
  ├─ Export Service
  └─ Dev / Smoke Endpoints

Local MVP Storage
  ├─ MemoryStore
  ├─ data/uploads
  ├─ data/frames
  └─ data/exports
```

## 3. 前端技术栈

| 模块 | 技术 | 当前用途 |
| --- | --- | --- |
| UI 框架 | React 19 | 单页 MVP 应用 |
| 语言 | TypeScript | 类型化 API、组件和状态 |
| 构建工具 | Vite 7 | 本地开发、生产构建 |
| 状态管理 | Zustand | 旅行、路线、素材、导出结果、故事事件 |
| 图标 | Lucide React | 按钮、状态、时间线图标 |
| 地图 | 高德 JS API / Demo Map | 有 `VITE_AMAP_WEB_KEY` 时加载高德，否则使用演示地图 |
| 语音 | Web Speech API | 浏览器端播报 AI 伴游讲解 |
| 样式 | CSS | 轻量响应式布局，无外部 UI 框架 |

前端关键文件：

- `web/src/App.tsx`：主流程编排，一键演示、路线、素材、出片、导出。
- `web/src/store/useTripStore.ts`：Zustand 全局状态。
- `web/src/api/client.ts`：API 客户端封装。
- `web/src/components/MapView.tsx`：地图展示和高德加载兜底。
- `web/src/components/MediaPanel.tsx`：素材预览、抽帧、标记、语音播报。
- `web/src/components/OutputPanel.tsx`：自动出片、文案复制、ZIP 导出。
- `web/src/components/StoryTimeline.tsx`：旅程事件故事线。

## 4. 后端技术栈

核心数据模型与未来数据库设计见：

- [data-model.md](data-model.md)

| 模块 | 技术 | 当前用途 |
| --- | --- | --- |
| Web 框架 | FastAPI | REST API、CORS、静态文件服务 |
| 数据校验 | Pydantic | 请求/响应 Schema |
| 运行服务 | Uvicorn | 本地 API 服务 |
| 环境变量 | python-dotenv | `.env` 配置加载 |
| 测试 | Pytest + FastAPI TestClient | MVP 闭环测试 |
| HTTP 测试依赖 | HTTPX | TestClient 底层依赖 |
| 媒体处理 | FFmpeg | 视频抽帧，失败时 fallback 到演示帧 |
| 导出 | Python zipfile | 生成 ZIP 素材包 |
| 存储 | 内存 + 本地文件 | 黑客松 MVP 数据和素材管理 |
| 容器化 | Docker + Docker Compose | 单机部署、CI 镜像构建验证 |

后端关键文件：

- `api/app/main.py`：FastAPI 应用入口，注册路由和静态文件。
- `api/app/core/config.py`：环境变量和目录配置。
- `api/app/domain/store.py`：内存数据、事件记录、重置逻辑。
- `api/app/domain/route_service.py`：路线生成与状态改路线。
- `api/app/domain/media_service.py`：上传、演示素材、抽帧、精彩标记。
- `api/app/domain/agent_orchestrator.py`：伴游讲解、自动出片、manifest、ZIP 导出。
- `api/app/domain/providers.py`：AI/地图 Provider 抽象。
- `api/tests/test_mvp_flow.py`：端到端闭环测试。

## 5. API 能力边界

详细接口契约见：

- [api-contract.md](api-contract.md)

| 能力 | Endpoint |
| --- | --- |
| 健康检查 | `GET /health` |
| 运行配置 | `GET /api/dev/config` |
| 重置演示数据 | `POST /api/dev/reset` |
| 创建旅行 | `POST /api/trips` |
| 查询旅行详情 | `GET /api/trips/{trip_id}` |
| 生成路线 | `POST /api/trips/{trip_id}/route` |
| 状态改路线 | `POST /api/trips/{trip_id}/reroute` |
| 上传素材 | `POST /api/trips/{trip_id}/media` |
| 创建演示素材 | `POST /api/trips/{trip_id}/media/demo` |
| 抽取候选帧 | `POST /api/media/{media_id}/extract-frames` |
| 标记精彩瞬间 | `POST /api/frames/{frame_id}/mark` |
| 生成伴游讲解 | `POST /api/trips/{trip_id}/companion/analyze` |
| 自动出片 | `POST /api/trips/{trip_id}/exports` |
| 导出 manifest | `GET /api/exports/{export_id}/manifest` |
| 导出 ZIP 素材包 | `GET /api/exports/{export_id}/bundle` |

## 6. AI 与地图策略

MVP 默认使用 mock/provider fallback，保证没有外部服务时也能路演。

AI 层：

- 当前实现：`AIProvider` 返回确定性伴游提示和社交文案。
- 预留实现：`OpenAIProvider`，可接入 `OPENAI_API_KEY`、`OPENAI_TEXT_MODEL`、`OPENAI_VISION_MODEL`。
- 推荐扩展：路线规划用文本模型，画面理解用视觉模型，文案和镜头表用文本模型。

地图层：

- 当前实现：内置西湖演示路线。
- 前端可选：`VITE_AMAP_WEB_KEY` 加载高德 JS API。
- 后端预留：`AMAP_WEB_SERVICE_KEY` 给路线搜索、POI、地理编码使用。
- 推荐扩展：把 `route_service.py` 的固定路线替换为 Provider 返回的 POI 和步行路线。

## 7. 媒体与出片链路

```text
Upload / Demo Media
  ↓
Frame Extraction
  ├─ 图片：直接作为帧
  ├─ 视频：FFmpeg 按间隔抽帧
  └─ 失败兜底：生成 SVG 演示帧
  ↓
Frame Scoring
  ├─ lighting
  ├─ composition
  ├─ story_value
  └─ share_value
  ↓
Manual Mark Boost
  ↓
Auto Export
  ├─ selected_frames
  ├─ route_recap
  ├─ social_copy
  ├─ video_draft
  ├─ story_events
  └─ ZIP bundle
```

ZIP 素材包包含：

- `manifest.json`
- `selected_frames/*`

manifest 包含：

- 旅行目标
- 路线节点
- 媒体素材
- 精选帧
- 视频镜头表
- 旅程故事线
- 文案
- 剪辑交接说明

## 8. 运行与验证

部署、CI 和上线检查详见：

- [deployment.md](deployment.md)

本地启动：

```powershell
.\scripts\start-dev.ps1
```

Docker 启动：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

后端测试：

```powershell
cd api
.\.venv\Scripts\python -m pytest -q
```

前端类型检查：

```powershell
cd web
node .\node_modules\typescript\bin\tsc -b
```

前端构建：

```powershell
cd web
node .\node_modules\vite\bin\vite.js build
```

烟测：

```powershell
.\scripts\smoke-test.ps1
```

## 9. 环境变量

后端：

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `APP_ENV` | `development` | 运行环境 |
| `WEB_ORIGIN` | `http://127.0.0.1:5173` | CORS 来源 |
| `APP_BASE_URL` | `http://127.0.0.1:8010` | 静态文件 URL 前缀 |
| `DATA_DIR` | `./data` | 本地素材目录 |
| `FRAME_EXTRACT_INTERVAL_SECONDS` | `4` | 视频抽帧间隔 |
| `MAX_FRAME_ANALYSIS_COUNT` | `12` | 最大抽帧数量 |
| `AI_PROVIDER` | `mock` | AI Provider |
| `MAP_PROVIDER` | `mock` | 地图 Provider |
| `OPENAI_API_KEY` | 空 | OpenAI 接入 |
| `OPENAI_TEXT_MODEL` | 空 | 文本模型 |
| `OPENAI_VISION_MODEL` | 空 | 视觉模型 |
| `AMAP_WEB_KEY` | 空 | 高德前端 Key |
| `AMAP_WEB_SERVICE_KEY` | 空 | 高德 Web Service Key |

前端：

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8010` | API 地址 |
| `VITE_AMAP_WEB_KEY` | 空 | 高德 JS API Key |

## 10. 后续工程化方向

短期：

- 使用 SQLite/PostgreSQL 替代 MemoryStore。
- 把导出任务改为异步 Job。
- 增加真实地图路线搜索和 POI 推荐。
- 增加 OpenAI Vision 画面理解。
- 增加 ZIP 包内视频草稿说明文件或 EDL。
- 为 Docker Compose 增加 postgres、redis、worker 和对象存储服务。

中期：

- 接入对象存储保存原素材和抽帧。
- 加队列处理视频抽帧和 AI 分析。
- 支持用户账号和旅行历史。
- 对接影石相机 SDK 或文件导入流程。
- 加前端 E2E 测试。

长期：

- 多模态实时伴游。
- 旅行记忆库和个性化 Agent。
- 小红书/抖音模板化导出。
- 离线城市包。
- 多人旅行协同。
