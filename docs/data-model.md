# Panorama Companion 数据模型与状态设计

本文档描述 MVP 当前内存数据模型，以及后续迁移到数据库时推荐的表结构和状态流。

## 1. 当前存储方案

MVP 使用 `MemoryStore` 保存运行时数据，并使用本地文件系统保存素材文件。

```text
MemoryStore
  ├─ trips
  ├─ routes
  ├─ media
  ├─ frames
  ├─ jobs
  ├─ exports
  └─ events

api/data
  ├─ uploads
  ├─ frames
  └─ exports
```

当前实现文件：

```text
api/app/domain/store.py
```

说明：

- `MemoryStore` 适合黑客松演示，不适合生产持久化。
- 服务重启后内存数据会丢失。
- `api/data` 下的文件由 `.gitignore` 忽略，只保留 `.gitkeep`。
- `POST /api/dev/reset` 可重置内存状态。

## 2. 核心实体关系

```text
Trip 1 ── 1 Route
Trip 1 ── N MediaAsset
MediaAsset 1 ── N FrameAsset
Trip 1 ── N Export
Trip 1 ── N TripEvent
Export 1 ── N selected FrameAsset
Export 1 ── N video_draft item
```

## 3. Trip

Trip 表示一次旅行任务，是路线、素材、事件和导出结果的聚合根。

当前字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 旅行 ID，格式 `trip_xxx` |
| `destination` | string | 用户输入目的地 |
| `duration_minutes` | number | 可用旅行时间 |
| `preferences` | string[] | 用户偏好 |
| `use_panorama_camera` | boolean | 是否使用全景相机 |
| `current_location` | object/null | 当前定位，MVP 可为空 |
| `status` | string | 当前旅行状态 |
| `created_at` | ISO datetime | 创建时间 |
| `updated_at` | ISO datetime | 更新时间 |

状态建议：

```text
created
  ↓
route_ready
  ↓
rerouted
  ↓
media_ready
  ↓
frames_ready
  ↓
export_ready
```

当前代码中已使用：

- `created`
- `route_ready`
- `rerouted`

后续可补充更细状态，便于恢复流程和展示进度。

## 4. Route 与 RouteNode

Route 表示某一次路线规划结果。当前 MVP 每个 Trip 只保存最新路线。

Route 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `route_id` | string | 路线 ID |
| `trip_id` | string | 所属旅行 |
| `route_name` | string | 路线名称 |
| `summary` | string | 路线摘要 |
| `change_summary` | string/null | 改路线原因 |
| `total_minutes` | number | 总时长 |
| `nodes` | RouteNode[] | 路线节点 |
| `tips` | string[] | 地图/路线建议 |
| `provider_context` | object | 地图 Provider 上下文 |
| `created_at` | ISO datetime | 创建时间 |

RouteNode 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 节点 ID |
| `name` | string | 节点名称 |
| `type` | string | 节点类型 |
| `lng` | number | 经度 |
| `lat` | number | 纬度 |
| `order_index` | number | 顺序 |
| `stay_minutes` | number | 建议停留时间 |
| `walking_minutes` | number | 到该节点步行时间 |
| `photo_value` | number | 拍摄价值 |
| `rest_value` | number | 休息价值 |
| `ai_reason` | string | AI 推荐理由 |

节点类型示例：

- `start`
- `scenery`
- `photo_spot`
- `rest`
- `food`
- `finish`

后续真实地图接入建议：

- 增加 `poi_id`
- 增加 `address`
- 增加 `provider`
- 增加 `distance_meters`
- 增加 `polyline`

## 5. MediaAsset

MediaAsset 表示用户上传或系统创建的演示素材。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `media_id` | string | 素材 ID |
| `trip_id` | string | 所属旅行 |
| `kind` | string | `image` / `video` / `demo` / `file` |
| `filename` | string | 原始或演示文件名 |
| `path` | string/null | 本地文件路径 |
| `url` | string/null | 静态访问 URL |
| `status` | string | 素材状态 |
| `created_at` | ISO datetime | 创建时间 |

状态建议：

```text
uploaded
ready
frames_ready
failed
```

后续真实相机接入建议增加：

- `source_device`
- `camera_model`
- `capture_started_at`
- `capture_ended_at`
- `gps_track_id`
- `panorama_projection`
- `original_metadata`

## 6. FrameAsset

FrameAsset 是自动出片和 AI 伴游的核心素材单位。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `frame_id` | string | 帧 ID |
| `media_id` | string | 来源素材 |
| `trip_id` | string | 所属旅行 |
| `timestamp_ms` | number | 素材内时间戳 |
| `image_url` | string | 原图 URL |
| `thumbnail_url` | string | 缩略图 URL |
| `path` | string | 本地文件路径 |
| `ai_caption` | string/null | AI 画面描述 |
| `ai_score` | object/null | AI 评分 |
| `selected` | boolean | 是否被自动出片选中 |
| `selected_reason` | string/null | 入选原因 |
| `marked` | boolean | 用户是否标记精彩瞬间 |
| `marked_reason` | string/null | 标记原因 |
| `created_at` | ISO datetime | 创建时间 |

`ai_score` 当前结构：

```json
{
  "lighting": 7,
  "composition": 8,
  "story_value": 9,
  "share_value": 8
}
```

自动选片排序：

```text
sum(ai_score) + marked_boost
```

当前 `marked_boost = 20`。

后续 VLM 接入建议：

- 增加 `detected_objects`
- 增加 `scene_tags`
- 增加 `blur_score`
- 增加 `face_privacy_risk`
- 增加 `safety_risk`
- 增加 `vlm_provider`
- 增加 `vlm_model`

## 7. TripEvent

TripEvent 记录旅程故事线，也是路演中体现“AI 陪伴过程”的关键数据。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `event_id` | string | 事件 ID |
| `trip_id` | string | 所属旅行 |
| `event_type` | string | 事件类型 |
| `title` | string | 展示标题 |
| `detail` | string | 展示说明 |
| `payload` | object | 结构化上下文 |
| `created_at` | ISO datetime | 事件时间 |

当前事件类型：

| 类型 | 触发时机 |
| --- | --- |
| `trip_created` | 创建旅行 |
| `route_generated` | 生成初始路线 |
| `route_updated` | 根据用户状态改路线 |
| `media_uploaded` | 上传素材 |
| `demo_media_created` | 创建演示素材 |
| `frames_extracted` | 抽取候选帧 |
| `frame_marked` | 标记精彩瞬间 |
| `frame_unmarked` | 取消精彩标记 |
| `companion_generated` | 生成 AI 伴游讲解 |
| `export_generated` | 生成自动出片 |
| `export_bundle_created` | 生成 ZIP 素材包 |

事件设计原则：

- 用事件串起“路线、画面、用户状态、出片”的完整故事。
- `detail` 面向用户展示，`payload` 面向后续工程处理。
- 后续可以把事件作为 AI 生成旅行总结的上下文。

## 8. Export

Export 表示一次自动出片结果。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `export_id` | string | 导出 ID |
| `trip_id` | string | 所属旅行 |
| `status` | string | 导出状态 |
| `selected_frames` | FrameAsset[] | 精选帧 |
| `route_recap` | string | 路线回顾 |
| `social_copy` | string | 社交文案 |
| `video_draft` | object[] | 视频镜头表 |
| `story_events` | TripEvent[] | 旅程故事线 |
| `created_at` | ISO datetime | 创建时间 |

Video Draft Item：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `order` | number | 镜头顺序 |
| `frame_id` | string | 对应精选帧 |
| `duration_seconds` | number | 建议时长 |
| `caption` | string | 镜头说明 |
| `shot_type` | string | 镜头类型 |
| `route_node_name` | string/null | 对应路线节点 |
| `transition` | string | 转场建议 |
| `edit_note` | string | 剪辑备注 |

导出产物：

```text
manifest.json
selected_frames/*
```

## 9. Job

Job 表示可查询状态的后台任务。当前抽帧是同步执行，但仍保留 Job 结构。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `job_id` | string | 任务 ID |
| `status` | string | `running` / `succeeded` / `failed` |
| `message` | string/null | 状态说明 |
| `result` | object/null | 任务结果 |
| `created_at` | ISO datetime | 创建时间 |

后续建议：

- 视频抽帧改为异步 Job。
- AI 视觉分析改为异步 Job。
- ZIP 打包和视频渲染改为异步 Job。

## 10. 推荐数据库表设计

生产化建议使用 PostgreSQL。MVP 阶段也可以先用 SQLite。

### `trips`

```sql
CREATE TABLE trips (
  id TEXT PRIMARY KEY,
  destination TEXT NOT NULL,
  duration_minutes INTEGER NOT NULL,
  preferences JSONB NOT NULL,
  use_panorama_camera BOOLEAN NOT NULL,
  current_location JSONB,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

### `routes`

```sql
CREATE TABLE routes (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  route_name TEXT NOT NULL,
  summary TEXT NOT NULL,
  change_summary TEXT,
  total_minutes INTEGER NOT NULL,
  nodes JSONB NOT NULL,
  tips JSONB NOT NULL,
  provider_context JSONB,
  created_at TIMESTAMPTZ NOT NULL
);
```

### `media_assets`

```sql
CREATE TABLE media_assets (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  kind TEXT NOT NULL,
  filename TEXT NOT NULL,
  path TEXT,
  url TEXT,
  status TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL
);
```

### `frames`

```sql
CREATE TABLE frames (
  id TEXT PRIMARY KEY,
  media_id TEXT NOT NULL REFERENCES media_assets(id),
  trip_id TEXT NOT NULL REFERENCES trips(id),
  timestamp_ms INTEGER NOT NULL,
  image_url TEXT NOT NULL,
  thumbnail_url TEXT NOT NULL,
  path TEXT,
  ai_caption TEXT,
  ai_score JSONB,
  selected BOOLEAN NOT NULL DEFAULT FALSE,
  selected_reason TEXT,
  marked BOOLEAN NOT NULL DEFAULT FALSE,
  marked_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL
);
```

### `trip_events`

```sql
CREATE TABLE trip_events (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  event_type TEXT NOT NULL,
  title TEXT NOT NULL,
  detail TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);
```

### `exports`

```sql
CREATE TABLE exports (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  status TEXT NOT NULL,
  selected_frame_ids JSONB NOT NULL,
  route_recap TEXT NOT NULL,
  social_copy TEXT NOT NULL,
  video_draft JSONB NOT NULL,
  story_event_ids JSONB NOT NULL,
  bundle_path TEXT,
  created_at TIMESTAMPTZ NOT NULL
);
```

### `jobs`

```sql
CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  trip_id TEXT REFERENCES trips(id),
  job_type TEXT NOT NULL,
  status TEXT NOT NULL,
  message TEXT,
  result JSONB,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

## 11. 推荐索引

```sql
CREATE INDEX idx_routes_trip_id ON routes(trip_id);
CREATE INDEX idx_media_assets_trip_id ON media_assets(trip_id);
CREATE INDEX idx_frames_trip_id ON frames(trip_id);
CREATE INDEX idx_frames_media_id ON frames(media_id);
CREATE INDEX idx_trip_events_trip_id_created_at ON trip_events(trip_id, created_at);
CREATE INDEX idx_exports_trip_id ON exports(trip_id);
CREATE INDEX idx_jobs_status ON jobs(status);
```

## 12. 数据迁移路线

阶段 1：保持 MemoryStore，但规范 Schema。

- 当前已完成基础字段和 API 契约。
- 继续补充事件类型和 Job 类型。

阶段 2：引入 Repository 层。

```text
domain service
  ↓
repository interface
  ↓
memory repository / sql repository
```

阶段 3：接入 SQLite/PostgreSQL。

- 本地开发使用 SQLite。
- 部署环境使用 PostgreSQL。
- 文件使用本地目录或对象存储。

阶段 4：异步任务化。

- 抽帧、视觉分析、ZIP 打包、视频渲染进入队列。
- Job 表成为前端进度展示来源。

## 13. 隐私与数据保留建议

旅行数据涉及位置、影像和对话，应在生产版本中增加：

- 用户授权记录。
- 素材删除接口。
- 路人/人脸隐私风险标记。
- 旅行轨迹脱敏。
- 数据保留时间配置。
- 本地处理或最小化上传策略。
