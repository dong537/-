# Panorama Companion Demo Runbook

## 1. 启动

在项目根目录运行：

```powershell
.\scripts\start-dev.ps1
```

或分别启动：

```powershell
.\scripts\start-api.ps1
.\scripts\start-web.ps1
```

演示结束后可停止后台服务：

```powershell
.\scripts\stop-dev.ps1
```

默认地址：

- Web: http://127.0.0.1:5173
- API: http://127.0.0.1:8010

## 2. 验证

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

预期结果：

- `Health = ok`
- `AiMode = mock`
- `MapMode = mock`
- `RouteNodes = 5`
- `Frames = 5`
- `MarkedFrame = True`
- `SelectedFrames = 5`
- `DraftShots = 5`
- `FirstShotType` 有值

## 3. 路演操作顺序

最快演示：

1. 打开 Web 页面。
2. 点击“一键演示”，等待完整闭环生成。
3. 展示路线、状态改路线、演示素材、精彩标记、伴游讲解、自动出片和 manifest 导出。

手动演示：

1. 打开 Web 页面。
2. 保留默认目标“杭州西湖附近”，点击“生成路线”。
3. 点击“我累了”或“想拍照”，展示 AI 实时改路线。
4. 点击“使用演示素材”。
5. 在候选帧条里点击星标，标记一个精彩瞬间。
6. 点击“生成伴游讲解”。
7. 点击伴游卡片上的声音按钮，演示语音播报。
8. 点击“生成结果”，展示精选图片、路线回顾、社交文案和视频镜头表。
9. 点击“导出素材包”，下载包含 `manifest.json` 和精选帧的 ZIP。
10. 如需重来，点击右上角“重置”。

## 4. 兜底策略

- 无 AI Key：使用 mock AI 文案。
- 无地图 Key：使用演示地图和西湖演示路线。
- 无真实素材：使用后端生成的 SVG 演示帧。
- FFmpeg 抽帧失败：自动 fallback 到演示帧。
- 端口 8000 冲突：项目默认使用 8010。

## 5. 可选配置

复制环境变量模板：

```powershell
Copy-Item api\.env.example api\.env
Copy-Item web\.env.example web\.env
```

当前代码已经预留：

- `AI_PROVIDER`
- `OPENAI_API_KEY`
- `OPENAI_TEXT_MODEL`
- `OPENAI_VISION_MODEL`
- `MAP_PROVIDER`
- `AMAP_WEB_KEY`
- `AMAP_WEB_SERVICE_KEY`

MVP 默认不依赖外部服务，方便黑客松现场稳定演示。
