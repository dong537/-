# Panorama Companion API 契约

本文档描述当前 MVP 的后端接口、请求响应结构、错误约定和演示调用顺序。API Base URL 默认为：

```text
http://127.0.0.1:8010
```

## 1. 通用约定

- 请求体默认使用 `application/json`。
- 上传素材使用 `multipart/form-data`。
- 成功响应默认返回 JSON，ZIP 素材包返回 `application/zip`。
- 未找到资源时返回 `404`。
- 上传文件超过 `MAX_UPLOAD_BYTES` 时返回 `413`。
- 所有响应会带有 `X-Request-ID`，便于日志排查。
- MVP 使用内存状态，重启服务后业务数据会丢失。
- `/files/*` 暴露本地 `api/data` 下的上传素材、抽帧和导出文件。

## 2. 健康检查

### `GET /health`

用于确认 API 服务、AI Provider 和地图 Provider 状态。

响应示例：

```json
{
  "status": "ok",
  "app_env": "development",
  "ai_provider": "mock",
  "ai_mode": "mock",
  "map_provider": "mock",
  "map_mode": "mock"
}
```

### `GET /ready`

用于部署健康检查，确认数据目录可写、素材目录存在、FFmpeg 可用。

响应示例：

```json
{
  "status": "ready",
  "checks": {
    "data_dir_writable": true,
    "uploads_dir_exists": true,
    "frames_dir_exists": true,
    "exports_dir_exists": true,
    "ffmpeg_available": true
  }
}
```

当任一检查失败时返回 `503`，`status` 为 `degraded`，响应体仍包含 `checks` 详情，前端系统状态面板会直接展示这些检查项。

## 3. 开发辅助

### `GET /api/dev/config`

返回当前运行配置和内存对象数量。

响应关键字段：

```json
{
  "app_env": "development",
  "ai_provider": "mock",
  "ai_mode": "mock",
  "map_provider": "mock",
  "map_mode": "mock",
  "app_base_url": "http://127.0.0.1:8010",
  "frame_extract_interval_seconds": 4,
  "max_frame_analysis_count": 12,
  "max_upload_bytes": 262144000,
  "request_log_enabled": true,
  "store_persistence_enabled": true,
  "state_file": "C:\\path\\to\\api\\data\\state.json",
  "store_loaded_at": null,
  "store_saved_at": "2026-05-23T00:00:00+00:00",
  "store_persistence_error": null,
  "insta360_sdk_demo_path": "",
  "insta360_native_bridge_enabled": false,
  "counts": {
    "trips": 1,
    "media": 1,
    "frames": 5,
    "exports": 1,
    "events": 8
  }
}
```

### `GET /api/health/insta360/sdk/status`

返回影石 SDK v1.9.11 bridge contract 状态、本地 demo 引用状态和已映射能力。

响应关键字段：

```json
{
  "provider": "insta360_android_sdk_v1_9_11_bridge",
  "sdk_version": "1.9.11",
  "bridge_mode": "contract_only",
  "native_bridge_available": false,
  "demo_reference": {
    "path": "C:\\Users\\Lenovo\\Desktop\\黑客松prd\\sdk_demo_1.9.11",
    "exists": true,
    "committed": false,
    "note": "Local SDK demo is used as a reference only and is ignored by git."
  },
  "workflows": ["bind", "capture", "sync", "export", "status"]
}
```

### `GET /api/health/insta360/sdk/command-plan?operation=capture`

返回指定 SDK 操作的指令计划。`operation` 支持：

- `bind`
- `capture`
- `sync`
- `export`
- `status`

响应关键字段：

```json
{
  "operation": "capture",
  "provider": "insta360_android_sdk_v1_9_11_bridge",
  "sdk_version": "1.9.11",
  "title": "自动/手动采集",
  "recommended_connection": "Wi-Fi 或 USB",
  "backend_handoff": "POST /api/health/captures",
  "steps": [
    {
      "order": 1,
      "name": "读取相机能力",
      "sdk_calls": ["fetchCameraOptions(callback)", "initCameraSupportConfig(callback)", "getSupportCaptureMode()"],
      "demo_files": ["ui/capture/CaptureViewModel.kt"],
      "backend_event": "校验设备在线和采集配置",
      "notes": "旧控制流需要把 offline capture setting 批量下发到相机。"
    }
  ]
}
```

### `POST /api/health/insta360/bridge/devices`

Android bridge 注册或更新真实影石设备。

请求关键字段：

```json
{
  "user_id": "demo_user",
  "device_name": "Insta360 X4 Living Room",
  "device_model": "Insta360 X4",
  "camera_serial": "X4REAL001",
  "camera_version": "v1.2.3",
  "connection_type": "usb",
  "status": "online",
  "battery_percent": 73,
  "storage_free_gb": 44.2,
  "auto_capture_enabled": true,
  "capture_interval_minutes": 10,
  "capture_window": "08:00-22:00"
}
```

响应为 `DeviceResponse`，包含 `device_id`，Android bridge 后续状态和采集上报使用该 ID。

### `POST /api/health/insta360/bridge/devices/{device_id}/status`

Android bridge 上报真实设备状态。

```json
{
  "connection_type": "wifi",
  "status": "online",
  "battery_percent": 68,
  "storage_free_gb": 43.6,
  "camera_version": "v1.2.3"
}
```

### `POST /api/health/insta360/bridge/captures`

Android bridge 上报抓拍元数据。适用于 SDK 返回相机文件 URL 或本地路径，但不直接上传文件的场景。

```json
{
  "user_id": "demo_user",
  "device_id": "device_xxx",
  "camera_serial": "X4REAL001",
  "capture_mode": "auto",
  "scene_hint": "breakfast",
  "local_path": "/storage/emulated/0/DCIM/Camera01/IMG_001.jpg",
  "camera_file_urls": ["http://camera.local/DCIM/Camera01/VID_001.insv"]
}
```

### `POST /api/health/insta360/bridge/captures/upload`

Android bridge 直接上传真实图片文件。请求为 `multipart/form-data`：

```text
file=<image file>
user_id=demo_user
device_id=device_xxx
camera_serial=X4REAL001
capture_mode=auto
scene_hint=workout
captured_at=2026-05-23T14:30:00+08:00
```

后端会保存到 `api/data/uploads/insta360-health/`，并立即进入健康影像分析流程。

### `POST /api/dev/reset?clear_files=false`

重置内存演示状态。`clear_files=true` 时会清理本地上传、抽帧和导出文件。

响应：

```json
{
  "status": "reset"
}
```

## 4. 旅行与路线

### `POST /api/trips`

创建一次旅行目标。

请求：

```json
{
  "destination": "杭州西湖附近",
  "duration_minutes": 120,
  "preferences": ["风景", "拍视频", "轻松"],
  "use_panorama_camera": true,
  "current_location": {
    "lng": 120.148,
    "lat": 30.245
  }
}
```

响应：

```json
{
  "trip_id": "trip_xxx",
  "status": "created"
}
```

说明：

- `destination` 必填。
- `duration_minutes` 取值范围为 `15-720`。
- 创建成功后会记录 `trip_created` 故事事件。

### `GET /api/trips?limit=10`

返回最近更新的旅行摘要，用于前端恢复上一次演示。

响应示例：

```json
[
  {
    "trip_id": "trip_xxx",
    "destination": "杭州西湖附近",
    "duration_minutes": 120,
    "status": "route_ready",
    "created_at": "2026-05-23T00:00:00+00:00",
    "updated_at": "2026-05-23T00:05:00+00:00",
    "route_ready": true,
    "media_count": 1,
    "frame_count": 5,
    "export_count": 1,
    "event_count": 8
  }
]
```

### `GET /api/trips/{trip_id}`

查询旅行详情，包含旅行、路线、素材、帧、导出结果和故事事件。

响应结构：

```json
{
  "trip": {},
  "route": {},
  "media": [],
  "frames": [],
  "exports": [],
  "events": []
}
```

### `POST /api/trips/{trip_id}/route`

生成初始路线。

响应关键字段：

```json
{
  "route_id": "route_xxx",
  "route_name": "西湖轻松 City Walk",
  "summary": "以湖边风景、轻松步行和短视频拍摄为主，保留一个明确休息点。",
  "change_summary": null,
  "total_minutes": 120,
  "nodes": [
    {
      "id": "node_xxx",
      "name": "湖边步道",
      "type": "scenery",
      "lng": 120.1514,
      "lat": 30.2444,
      "order_index": 2,
      "stay_minutes": 20,
      "walking_minutes": 8,
      "photo_value": 9,
      "rest_value": 4,
      "ai_reason": "水面、树影和行人节奏都适合全景视频开头。"
    }
  ],
  "tips": []
}
```

成功后会记录 `route_generated` 事件。

### `POST /api/trips/{trip_id}/reroute`

根据用户当前状态调整路线。

请求：

```json
{
  "status_action": "tired",
  "remaining_minutes": 80,
  "current_location": {
    "lng": 120.148,
    "lat": 30.245
  }
}
```

`status_action` 当前支持：

- `normal`
- `tired`
- `photo`
- `food`
- `short_time`
- `quiet`

响应同 `RoutePlan`。成功后会记录 `route_updated` 事件。

## 5. 素材与抽帧

### `POST /api/trips/{trip_id}/media`

上传图片或视频素材。

请求：

```text
multipart/form-data
file=<image/video file>
```

响应：

```json
{
  "media_id": "media_xxx",
  "trip_id": "trip_xxx",
  "kind": "image",
  "filename": "demo.jpg",
  "url": "http://127.0.0.1:8010/files/uploads/xxx.jpg",
  "status": "uploaded"
}
```

成功后会记录 `media_uploaded` 事件。

说明：
- 单文件大小受 `MAX_UPLOAD_BYTES` 限制，默认 `262144000` 字节。
- 超过限制时返回 `413`，并删除已写入的临时文件。

### `POST /api/trips/{trip_id}/media/demo`

创建内置演示素材，适合没有真实视频时路演。

响应：

```json
{
  "media_id": "media_xxx",
  "trip_id": "trip_xxx",
  "kind": "demo",
  "filename": "demo-panorama-west-lake",
  "url": null,
  "status": "ready"
}
```

成功后会记录 `demo_media_created` 事件。

### `POST /api/media/{media_id}/extract-frames`

从素材中抽取候选帧。

响应：

```json
{
  "job_id": "job_xxx",
  "status": "succeeded",
  "frames": [
    {
      "frame_id": "frame_xxx",
      "media_id": "media_xxx",
      "trip_id": "trip_xxx",
      "timestamp_ms": 0,
      "image_url": "http://127.0.0.1:8010/files/frames/media_xxx/frame_000.svg",
      "thumbnail_url": "http://127.0.0.1:8010/files/frames/media_xxx/frame_000.svg",
      "ai_caption": "湖边视野开阔，水面和天空形成稳定的横向层次。",
      "ai_score": {
        "lighting": 7,
        "composition": 6,
        "story_value": 8,
        "share_value": 7
      },
      "selected": false,
      "selected_reason": null,
      "marked": false,
      "marked_reason": null
    }
  ]
}
```

成功后会记录 `frames_extracted` 事件。

## 6. 精彩瞬间

### `POST /api/frames/{frame_id}/mark`

标记或取消标记一个候选帧。

请求：

```json
{
  "marked": true,
  "reason": "用户标记的精彩瞬间"
}
```

响应为更新后的 `FrameAsset`。

说明：

- 标记后自动出片会给该帧加权。
- 标记成功记录 `frame_marked`。
- 取消标记记录 `frame_unmarked`。

## 7. AI 伴游

### `POST /api/trips/{trip_id}/companion/analyze`

根据当前帧、路线节点和用户状态生成伴游讲解。

请求：

```json
{
  "frame_id": "frame_xxx",
  "route_node_id": "node_xxx",
  "user_status": "tired"
}
```

响应：

```json
{
  "message": "湖边步道这一段可以慢一点。湖边视野开阔，水面和天空形成稳定的横向层次。你现在有点累，可以把拍摄动作做得更轻，不需要追求太多角度。",
  "shooting_tips": ["相机略微抬高", "保持慢速移动", "让天空和地面各留出一点空间"],
  "scene_tags": ["City Walk", "湖边", "全景素材"],
  "safety_tips": [],
  "share_value": 8,
  "frame": {}
}
```

成功后会记录 `companion_generated` 事件。

## 8. 自动出片

### `POST /api/trips/{trip_id}/exports`

生成自动出片结果。

响应关键字段：

```json
{
  "export_id": "export_xxx",
  "status": "succeeded",
  "selected_frames": [],
  "route_recap": "今日路线：西湖天地入口 -> 湖边步道 -> 湖畔咖啡休息点",
  "social_copy": "今天的杭州西湖附近不是攻略里的打卡路线...",
  "video_draft": [
    {
      "order": 1,
      "frame_id": "frame_xxx",
      "duration_seconds": 5,
      "caption": "湖边视野开阔，水面和天空形成稳定的横向层次。",
      "shot_type": "开场环境",
      "route_node_name": "西湖天地入口",
      "transition": "淡入开场",
      "edit_note": "关联路线节点：西湖天地入口。可作为路线叙事中的稳定镜头。"
    }
  ],
  "story_events": []
}
```

成功后会记录 `export_generated` 事件。

### `GET /api/exports/{export_id}/manifest`

下载或查看导出 manifest JSON。

manifest 包含：

- `schema`
- `generated_at`
- `trip`
- `route`
- `media_assets`
- `selected_frames`
- `video_draft`
- `story_events`
- `copy`
- `handoff`

### `GET /api/exports/{export_id}/bundle`

下载 ZIP 素材包。

响应：

```text
Content-Type: application/zip
Content-Disposition: attachment; filename="{export_id}-bundle.zip"
```

ZIP 内容：

```text
manifest.json
selected_frames/01-frame_xxx.svg
selected_frames/02-frame_xxx.svg
...
```

下载成功生成 ZIP 时会记录 `export_bundle_created` 事件。

## 9. Job 查询

### `GET /api/jobs/{job_id}`

查询任务状态。当前主要用于抽帧任务。

响应：

```json
{
  "job_id": "job_xxx",
  "status": "succeeded",
  "message": "已生成 5 张候选帧",
  "result": {
    "frame_count": 5
  }
}
```

## 10. 推荐演示调用顺序

```text
POST /api/trips
POST /api/trips/{trip_id}/route
POST /api/trips/{trip_id}/reroute
POST /api/trips/{trip_id}/media/demo
POST /api/media/{media_id}/extract-frames
POST /api/frames/{frame_id}/mark
POST /api/trips/{trip_id}/companion/analyze
POST /api/trips/{trip_id}/exports
GET  /api/exports/{export_id}/bundle
```

## 11. 前后端字段对齐

前端类型位于：

```text
web/src/types/index.ts
```

后端 Schema 位于：

```text
api/app/schemas/trip.py
api/app/schemas/media.py
```

如果后端响应字段变化，需要同步更新前端类型和 `web/src/api/client.ts`。

## 12. 后续扩展契约

建议后续新增接口时保持以下方向：

- 长任务统一返回 `job_id`，通过 `/api/jobs/{job_id}` 查询。
- AI/VLM 分析结果保留 `provider`、`model`、`confidence` 字段。
- 路线节点增加真实地图 `poi_id` 和 `address`。
- 素材增加 `source_device`、`camera_model`、`gps_track`。
- 导出增加 `render_status` 和最终视频 `video_url`。
