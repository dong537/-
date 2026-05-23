# 智能影像健康监测系统实现说明

## PRD 覆盖范围

当前代码已把新 PRD 落成可演示 MVP，覆盖以下闭环：

- 用户基础体征录入：BMI 自动计算、血压、心率、血氧、血糖等数据保存和异常提示。
- Insta360 设备接入边界：提供 mock SDK provider，支持绑定、状态、电量、存储、自动采集间隔和采集时段。
- 影像采集：支持手动抓拍、自动定时采集模拟、离线缓存模式字段预留。
- AI 行为分析：根据影像场景识别饮食、运动、睡眠、久坐、户外放松等行为。
- 身心健康评分：生成身体健康分、心理健康分、风险标签和建议。
- 日度日志：汇总当日行为频次、异常行为、风险提示和综合分。
- 周度报告：汇总近 7 日趋势、身体评估、心理评估、四类建议和下周目标。
- 异常容错：支持设备离线状态、低电量/故障字段、离线采集缓存、恢复联网后批量同步分析。
- 识别失败处理：支持 AI 识别失败状态、人工补充场景备注、重新生成行为分析。
- 历史回溯：支持日报历史、周报历史、体征趋势回溯。
- 趋势查询：支持近 N 天分数、体征、行为和风险标签趋势。
- 隐私删除：支持按用户删除健康档案、体征、采集、行为、设备、日报和周报数据。
- 报告导出：支持周度报告 PDF 下载入口，MVP 阶段输出可交接的 PDF-like 文件。
- 可视化工作台：前端首页展示设备、体征、采集、分析、日报、周报和趋势。

## 后端新增模块

| 文件 | 作用 |
| --- | --- |
| `api/app/api/health.py` | 健康监测 REST API |
| `api/app/domain/health_service.py` | 体征、设备、采集、行为分析、日报、周报业务逻辑 |
| `api/app/schemas/health.py` | 健康监测请求/响应 Schema |
| `api/tests/test_health_flow.py` | 新 PRD 核心闭环测试 |

核心接口：

```text
GET  /api/health/dashboard
POST /api/health/profiles
POST /api/health/devices/bind
PATCH /api/health/devices/{device_id}
POST /api/health/captures
POST /api/health/captures/{capture_id}/review
POST /api/health/devices/{device_id}/sync
POST /api/health/daily/{user_id}
GET  /api/health/daily/{user_id}
GET  /api/health/trends/{user_id}
POST /api/health/weekly/{user_id}
GET  /api/health/weekly/{user_id}
GET  /api/health/weekly/reports/{report_id}/pdf
POST /api/health/demo
DELETE /api/health/users/{user_id}
```

## 前端新增能力

主页面已改为健康监测工作台：

- 顶部健康评分卡：综合、身体、心理、采集数。
- 左侧：系统状态、体征表单、Insta360 设备绑定状态。
- 右侧：场景采集按钮、AI 行为分析列表、日度日志、周度报告、采集历史。
- 一键演示：自动生成体征、设备、6 条采集、日报和周报。

关键文件：

```text
web/src/App.tsx
web/src/api/client.ts
web/src/types/index.ts
web/src/styles.css
web/tests/e2e/mvp-flow.spec.ts
```

## Insta360 SDK 接入边界

当前 `health_service.py` 使用 `insta360_mock_sdk` 作为 provider 名称，模拟绑定和采集结果。后续接真实 SDK 时建议替换为独立 provider：

```text
api/app/domain/insta360_provider.py
```

建议 provider 方法：

- `discover_devices()`
- `bind_device(device_id)`
- `get_device_status(device_id)`
- `configure_auto_capture(device_id, interval_minutes, capture_window)`
- `trigger_capture(device_id)`
- `sync_offline_cache(device_id)`

业务层只依赖 provider 返回的设备状态和图片元数据，不直接耦合 SDK 细节。

## 验证命令

```powershell
.\scripts\test-api.ps1
cd web
npm run build
```

E2E 需要先启动 API，且本机需安装 Playwright Chromium：

```powershell
cd web
npx playwright install chromium
npm run test:e2e
```
