# Panorama Companion MVP

基于 PRD 和技术栈文档生成的黑客松 MVP 工程。

## 功能闭环

- 输入旅行目标，生成 City Walk 路线。
- 点击状态按钮，让 AI 重新规划路线。
- 上传视频/图片，或使用演示素材。
- 抽帧并生成 AI 伴游讲解。
- 支持浏览器语音播报 AI 伴游讲解。
- 支持用户手动标记精彩瞬间，自动出片时提高权重。
- 自动精选图片并生成旅行总结和社交文案。
- 生成带镜头类型、路线节点、转场和剪辑备注的视频草稿。
- 一键复制发布文案，导出包含 manifest 和精选帧的 ZIP 素材包。
- 一键演示完整闭环，适合路演兜底。

## 技术栈

- Web：React + TypeScript + Vite + Zustand + Lucide Icons
- API：Python + FastAPI + Pydantic
- 媒体处理：FFmpeg，不可用时自动使用演示帧兜底
- 存储：MVP 使用本地文件和内存数据
- 地图：无 Key 时使用演示地图，有 `VITE_AMAP_WEB_KEY` 时前端可加载高德地图
- 部署：Docker Compose 可启动 Web + API + 持久化数据卷

完整技术栈、架构边界和后续扩展见：

- [docs/technical-stack.md](docs/technical-stack.md)
- [docs/api-contract.md](docs/api-contract.md)
- [docs/data-model.md](docs/data-model.md)
- [docs/deployment.md](docs/deployment.md)

## 启动方式

推荐一键启动：

```powershell
.\scripts\start-dev.ps1
```

也可以分开启动：

```powershell
.\scripts\start-api.ps1
.\scripts\start-web.ps1
```

停止后台开发服务：

```powershell
.\scripts\stop-dev.ps1
```

默认地址：

- Web: http://127.0.0.1:5173
- API: http://127.0.0.1:8010

说明：本项目默认使用 `8010` 作为 API 端口，避开本机可能已占用的 `8000`。

## Docker 启动

仓库已提供 API/Web 镜像和 Compose 编排：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

默认地址：

- Web: http://127.0.0.1:5173
- API: http://127.0.0.1:8010

停止并保留数据卷：

```powershell
docker compose down
```

清理本地演示数据卷：

```powershell
docker compose down -v
```

## 手动启动

后端：

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

后端测试依赖：

```powershell
cd api
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest
```

前端：

```powershell
cd web
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

如果 PowerShell 把 `npm` 解析到异常路径，可显式使用 Node 官方 npm：

```powershell
& 'C:\Program Files\nodejs\npm.cmd' install
& 'C:\Program Files\nodejs\npm.cmd' run dev -- --host 127.0.0.1 --port 5173
```

## 环境变量

后端可选：

```env
APP_ENV=development
WEB_ORIGIN=http://127.0.0.1:5173
APP_BASE_URL=http://127.0.0.1:8010
FRAME_EXTRACT_INTERVAL_SECONDS=4
MAX_FRAME_ANALYSIS_COUNT=12
AI_PROVIDER=mock
MAP_PROVIDER=mock
OPENAI_API_KEY=
AMAP_WEB_SERVICE_KEY=
```

前端可选：

```env
VITE_API_BASE_URL=http://127.0.0.1:8010
VITE_AMAP_WEB_KEY=
```

复制模板：

```powershell
Copy-Item api\.env.example api\.env
Copy-Item web\.env.example web\.env
```

没有地图 Key、AI Key 或真实视频素材时，项目会自动走 mock/demo 模式。

## 验证

烟测：

```powershell
.\scripts\smoke-test.ps1
```

后端测试：

```powershell
.\scripts\test-api.ps1
```

前端构建：

```powershell
cd web
& 'C:\Program Files\nodejs\npm.cmd' run build
```

前端 E2E：

```powershell
cd web
npm run test:e2e
```

## 演示辅助

重置演示状态：

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8010/api/dev/reset
```

查看运行模式：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8010/api/dev/config
```
