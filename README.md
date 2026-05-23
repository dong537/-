# 智能影像健康监测系统 MVP

基于新 PRD 实现的健康监测演示系统：通过 Insta360 影像采集、基础体征录入、AI 行为识别、日度日志和周度报告，形成可演示的健康管理闭环。

## 已实现能力

- 用户基础健康数据录入：BMI、血压、心率、血氧、血糖等。
- 异常体征提示：血压、血糖、BMI 等超出范围时进入风险提示。
- Insta360 设备绑定：当前使用 `insta360_android_sdk_v1_9_11_bridge` provider contract，保留真实 SDK 接入边界。
- 影像采集模拟：支持手动抓拍、自动采集、场景标签选择。
- AI 行为分析：识别饮食、运动、睡眠、久坐、户外放松等行为。
- 身心健康评分：输出身体分、心理分、风险标签和个性化建议。
- 日度健康日志：汇总今日行为、异常行为和风险提示。
- 周度健康报告：生成趋势、身体评估、心理评估、饮食/运动/睡眠/心态建议和下周目标。

## 启动方式

推荐一键启动：

```powershell
.\scripts\start-dev.ps1
```

默认地址：

- Web: http://127.0.0.1:5173
- API: http://127.0.0.1:8010

也可以分开启动：

```powershell
.\scripts\start-api.ps1
.\scripts\start-web.ps1
```

停止开发服务：

```powershell
.\scripts\stop-dev.ps1
```

## Docker 启动

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## 验证

后端静态检查和测试：

```powershell
.\scripts\test-api.ps1
```

前端构建：

```powershell
cd web
npm run build
```

前端 E2E：

```powershell
cd web
npx playwright install chromium
npm run test:e2e
```

## 核心接口

```text
GET  /api/health/dashboard
POST /api/health/profiles
POST /api/health/devices/bind
POST /api/health/captures
POST /api/health/daily/{user_id}
POST /api/health/weekly/{user_id}
POST /api/health/demo
```

## 文档

- [健康监测实现说明](docs/health-monitoring-implementation.md)
- [影石 SDK 接入说明](docs/insta360-sdk-integration.md)
- [技术栈文档](docs/technical-stack.md)
- [API 契约](docs/api-contract.md)
- [部署说明](docs/deployment.md)
