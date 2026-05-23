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
  "counts": {
    "trips": 1,
    "media": 1,
    "frames": 5,
    "exports": 1,
    "events": 8
  }
}
```

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
