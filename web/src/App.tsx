import {
  Activity,
  AlertTriangle,
  BatteryMedium,
  Camera,
  CheckCircle2,
  Clock3,
  Dumbbell,
  FastForward,
  FileText,
  HeartPulse,
  Loader2,
  Moon,
  RefreshCcw,
  Salad,
  ShieldCheck,
  Smartphone,
  Sparkles,
  TrendingUp,
  Wifi
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  bindHealthDevice,
  createHealthCapture,
  deleteHealthUserData,
  downloadWeeklyReportPdf,
  generateDailyLog,
  generateWeeklyReport,
  getHealthDashboard,
  getInsta360CommandPlan,
  getInsta360SdkStatus,
  getRuntimeConfig,
  getHealthTrends,
  resetDemo,
  reviewHealthCapture,
  runHealthDemo,
  saveHealthProfile,
  syncHealthDevice,
  updateHealthDevice
} from "./api/client";
import { SystemStatusPanel } from "./components/SystemStatusPanel";
import type { RuntimeConfig } from "./api/client";
import type {
  CaptureCreatePayload,
  HealthDashboard,
  HealthProfilePayload,
  Insta360CommandPlan,
  Insta360SdkOperation,
  Insta360SdkStatus,
  TrendResponse
} from "./types";

const userId = "demo_user";

const sceneOptions = [
  { value: "breakfast", label: "规律早餐", icon: Salad },
  { value: "late snack", label: "夜间加餐", icon: AlertTriangle },
  { value: "workout", label: "运动健身", icon: Dumbbell },
  { value: "sitting", label: "久坐办公", icon: Clock3 },
  { value: "sleep", label: "规律睡眠", icon: Moon },
  { value: "outdoor walk", label: "户外放松", icon: Activity }
];

const sdkOperations: Array<{ value: Insta360SdkOperation; label: string }> = [
  { value: "bind", label: "绑定" },
  { value: "capture", label: "采集" },
  { value: "sync", label: "同步" },
  { value: "export", label: "导出" }
];

const defaultProfile: HealthProfilePayload = {
  user_id: userId,
  name: "Demo User",
  age: 32,
  gender: "unspecified",
  vital_signs: {
    height_cm: 172,
    weight_kg: 76,
    bmi: null,
    systolic_bp: 132,
    diastolic_bp: 86,
    heart_rate: 82,
    blood_oxygen: 98,
    blood_glucose: 7.2,
    blood_lipid: 5.4,
    uric_acid: 398,
    notes: "亚健康作息，关注血糖、体重和久坐压力。"
  }
};

function scoreTone(score?: number | null) {
  if (!score) return "muted";
  if (score >= 85) return "good";
  if (score >= 70) return "warn";
  return "risk";
}

function formatTime(value?: string | null) {
  if (!value) return "--";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function categoryName(category: string) {
  const names: Record<string, string> = {
    diet: "饮食",
    exercise: "运动",
    sleep: "睡眠",
    daily: "日常"
  };
  return names[category] ?? category;
}

export function App() {
  const [dashboard, setDashboard] = useState<HealthDashboard | null>(null);
  const [runtime, setRuntime] = useState<RuntimeConfig | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("录入体征并绑定 Insta360 相机后，即可开始健康影像采集。");
  const [profile, setProfile] = useState<HealthProfilePayload>(defaultProfile);
  const [sceneHint, setSceneHint] = useState("breakfast");
  const [trend, setTrend] = useState<TrendResponse | null>(null);
  const [sdkStatus, setSdkStatus] = useState<Insta360SdkStatus | null>(null);
  const [sdkPlan, setSdkPlan] = useState<Insta360CommandPlan | null>(null);
  const [sdkOperation, setSdkOperation] = useState<Insta360SdkOperation>("capture");

  const latestMetric = dashboard?.profile?.latest_metric;
  const todayLog = dashboard?.today_log;
  const weeklyReport = dashboard?.weekly_report;
  const device = dashboard?.device;

  const scoreCards = useMemo(
    () => [
      { label: "综合健康分", value: todayLog?.overall_score, icon: HeartPulse },
      { label: "身体维度", value: todayLog?.body_score, icon: Activity },
      { label: "心理维度", value: todayLog?.mental_score, icon: Sparkles }
    ],
    [todayLog]
  );

  useEffect(() => {
    refreshDashboard();
    getRuntimeConfig()
      .then(setRuntime)
      .catch(() => setRuntime(null));
    refreshSdkStatus("capture");
  }, []);

  async function run<T>(message: string, task: () => Promise<T>): Promise<T | undefined> {
    setBusy(true);
    setNotice(message);
    try {
      return await task();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "操作失败，请稍后重试。");
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  async function refreshDashboard() {
    const data = await getHealthDashboard(userId);
    setDashboard(data);
    if (data.profile?.latest_metric) {
      setProfile({
        user_id: data.profile.user_id,
        name: data.profile.name,
        age: data.profile.age,
        gender: data.profile.gender,
        vital_signs: data.profile.latest_metric.vital_signs
      });
    }
  }

  async function refreshSdkStatus(operation: Insta360SdkOperation = sdkOperation) {
    try {
      const [status, plan] = await Promise.all([getInsta360SdkStatus(), getInsta360CommandPlan(operation)]);
      setSdkStatus(status);
      setSdkPlan(plan);
    } catch {
      setSdkStatus(null);
      setSdkPlan(null);
    }
  }

  function updateVital(key: keyof HealthProfilePayload["vital_signs"], value: string) {
    setProfile((current) => ({
      ...current,
      vital_signs: {
        ...current.vital_signs,
        [key]: value === "" ? null : Number(value)
      }
    }));
  }

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run("正在保存体征数据并执行医学范围校验。", async () => {
      await saveHealthProfile(profile);
      await refreshDashboard();
      setNotice("体征数据已保存，异常指标会进入日报和周报评估。");
    });
  }

  async function handleBindDevice() {
    await run("正在按 Insta360 SDK v1.9.11 桥接契约绑定设备。", async () => {
      await bindHealthDevice({
        user_id: userId,
        device_name: "Insta360 X4",
        device_model: "Insta360 X4",
        connection_type: "mock",
        auto_capture_enabled: true,
        capture_interval_minutes: 10,
        capture_window: "08:00-22:00"
      });
      await refreshDashboard();
      await refreshSdkStatus("bind");
      setNotice("Insta360 设备已绑定，默认每10分钟自动采集一次。");
    });
  }

  async function handleSdkOperationChange(operation: Insta360SdkOperation) {
    setSdkOperation(operation);
    await run(`正在加载 Insta360 SDK ${operation} 流程指令。`, async () => {
      const plan = await getInsta360CommandPlan(operation);
      setSdkPlan(plan);
      setNotice(`已加载 ${plan.title} 指令计划，共 ${plan.steps.length} 步。`);
    });
  }

  async function handleDeviceOffline() {
    if (!device) return;
    await run("正在模拟设备断网离线，后续采集会进入本地缓存。", async () => {
      await updateHealthDevice(device.device_id, {
        status: "offline",
        battery_percent: Math.min(device.battery_percent, 18),
        status_detail: "Device offline; waiting for Wi-Fi reconnect."
      });
      await refreshDashboard();
      setNotice("设备已切换为离线状态，自动采集将先缓存，联网后可批量同步。");
    });
  }

  async function handleSyncCache() {
    if (!device) return;
    await run("正在同步离线缓存影像并补做 AI 分析。", async () => {
      const result = await syncHealthDevice(device.device_id);
      await refreshDashboard();
      setNotice(`已同步 ${result.synced_captures.length} 条离线缓存采集。`);
    });
  }

  async function handleCapture(mode: CaptureCreatePayload["capture_mode"]) {
    await run(mode === "manual" ? "正在执行手动抓拍并优先分析。" : "正在模拟自动定时采集。", async () => {
      await createHealthCapture({
        user_id: userId,
        device_id: device?.device_id,
        capture_mode: mode,
        scene_hint: sceneHint
      });
      await refreshDashboard();
      setNotice(device?.status === "offline" ? "设备离线，影像已进入缓存队列。" : "影像已完成 AI 场景识别、行为拆解和身心健康评分。");
    });
  }

  async function handleFailedCaptureReview() {
    await run("正在模拟识别失败并提交人工补充场景。", async () => {
      const failed = await createHealthCapture({
        user_id: userId,
        device_id: device?.device_id,
        capture_mode: "manual",
        scene_hint: "unknown"
      });
      await reviewHealthCapture(failed.capture_id, {
        scene_hint: "workout",
        manual_note: "用户补充：这是一次中等强度运动。"
      });
      await refreshDashboard();
      setNotice("识别失败图片已通过人工备注补充，并重新生成行为分析。");
    });
  }

  async function handleDaily() {
    await run("正在生成今日健康日志。", async () => {
      await generateDailyLog(userId);
      await refreshDashboard();
      setNotice("今日健康日志已生成，包含行为汇总、异常标记和风险提示。");
    });
  }

  async function handleWeekly() {
    await run("正在生成周度健康报告。", async () => {
      await generateWeeklyReport(userId);
      await refreshDashboard();
      setNotice("周度健康报告已生成，包含趋势、评估和下周目标。");
    });
  }

  async function handleDownloadWeeklyPdf() {
    if (!weeklyReport) return;
    await run("正在导出周度健康报告 PDF。", async () => {
      const blob = await downloadWeeklyReportPdf(weeklyReport.report_id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${weeklyReport.report_id}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setNotice("周度健康报告 PDF 已导出。");
    });
  }

  async function handleLoadTrends() {
    await run("正在加载近30天趋势数据。", async () => {
      const result = await getHealthTrends(userId, 30);
      setTrend(result);
      setNotice("趋势数据已加载，可查看分数、体征和行为统计。");
    });
  }

  async function handleDeletePrivacyData() {
    await run("正在删除当前演示用户的健康隐私数据。", async () => {
      const result = await deleteHealthUserData(userId, "all");
      await refreshDashboard();
      setTrend(null);
      setNotice(`隐私数据已删除：共清理 ${Object.values(result.deleted_counts).reduce((sum, count) => sum + count, 0)} 条记录。`);
    });
  }

  async function handleDemo() {
    await run("正在一键跑通 PRD 演示闭环。", async () => {
      await resetDemo();
      await runHealthDemo(userId);
      await refreshDashboard();
      setNotice("演示闭环完成：体征录入、设备绑定、影像采集、AI分析、日报和周报均已生成。");
    });
  }

  async function handleReset() {
    await run("正在重置健康监测演示数据。", async () => {
      await resetDemo();
      setDashboard(await getHealthDashboard(userId));
      setProfile(defaultProfile);
      setNotice("演示数据已重置，可以重新开始。");
    });
  }

  return (
    <main className="app-shell health-app">
      <header className="topbar">
        <div className="brand">
          <HeartPulse size={24} />
          <div>
            <strong>智能影像健康监测系统</strong>
            <span>Insta360 + AI 行为分析 + 身心健康周报</span>
          </div>
        </div>
        <div className="runtime-strip" title="当前运行模式">
          <span>AI: {runtime?.ai_mode ?? "mock"}</span>
          <span>Device: {device?.provider ?? sdkStatus?.provider ?? "insta360_bridge"}</span>
        </div>
        <button className="ghost-button" onClick={handleReset} type="button">
          <RefreshCcw size={18} />
          重置
        </button>
      </header>

      <section className="health-hero">
        <div>
          <p className="eyebrow">Health Imaging MVP</p>
          <h1>用全景影像还原日常行为，把饮食、运动、作息变成可追踪的健康建议。</h1>
        </div>
        <div className="hero-actions">
          <button className="demo-run-button" data-testid="run-demo-button" disabled={busy} onClick={handleDemo} type="button">
            {busy ? <Loader2 className="spin" size={18} /> : <FastForward size={18} />}
            一键演示
          </button>
          <div className="status-pill">
            {busy ? <Loader2 className="spin" size={18} /> : <ShieldCheck size={18} />}
            <span data-testid="notice-text">{notice}</span>
          </div>
        </div>
      </section>

      <section className="score-grid" data-testid="score-grid">
        {scoreCards.map((card) => {
          const Icon = card.icon;
          return (
            <article className={`score-card is-${scoreTone(card.value)}`} key={card.label}>
              <div>
                <span>{card.label}</span>
                <strong>{card.value ?? "--"}</strong>
              </div>
              <Icon size={28} />
            </article>
          );
        })}
        <article className="score-card">
          <div>
            <span>今日采集</span>
            <strong>{dashboard?.status.capture_count ?? 0}</strong>
          </div>
          <Camera size={28} />
        </article>
      </section>

      <div className="health-workspace">
        <aside className="health-sidebar">
          <SystemStatusPanel />

          <section className="panel-block">
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">Step 1</p>
                <h2>基础体征</h2>
              </div>
              <HeartPulse size={20} />
            </div>
            <form className="vital-form" onSubmit={handleProfileSubmit}>
              <label>
                姓名
                <input value={profile.name} onChange={(event) => setProfile({ ...profile, name: event.target.value })} />
              </label>
              <div className="form-pair">
                <label>
                  年龄
                  <input min={1} max={120} type="number" value={profile.age} onChange={(event) => setProfile({ ...profile, age: Number(event.target.value) })} />
                </label>
                <label>
                  身高 cm
                  <input type="number" value={profile.vital_signs.height_cm} onChange={(event) => updateVital("height_cm", event.target.value)} />
                </label>
              </div>
              <div className="form-pair">
                <label>
                  体重 kg
                  <input type="number" value={profile.vital_signs.weight_kg} onChange={(event) => updateVital("weight_kg", event.target.value)} />
                </label>
                <label>
                  心率
                  <input type="number" value={profile.vital_signs.heart_rate} onChange={(event) => updateVital("heart_rate", event.target.value)} />
                </label>
              </div>
              <div className="form-pair">
                <label>
                  高压
                  <input type="number" value={profile.vital_signs.systolic_bp} onChange={(event) => updateVital("systolic_bp", event.target.value)} />
                </label>
                <label>
                  低压
                  <input type="number" value={profile.vital_signs.diastolic_bp} onChange={(event) => updateVital("diastolic_bp", event.target.value)} />
                </label>
              </div>
              <div className="form-pair">
                <label>
                  血氧 %
                  <input type="number" value={profile.vital_signs.blood_oxygen} onChange={(event) => updateVital("blood_oxygen", event.target.value)} />
                </label>
                <label>
                  血糖
                  <input type="number" value={profile.vital_signs.blood_glucose ?? ""} onChange={(event) => updateVital("blood_glucose", event.target.value)} />
                </label>
              </div>
              <button className="primary-button" disabled={busy} type="submit">
                <CheckCircle2 size={18} />
                保存体征
              </button>
            </form>
            {(latestMetric?.warnings ?? []).length > 0 && (
              <div className="warning-list" data-testid="warning-list">
                {latestMetric?.warnings.map((warning) => (
                  <p key={warning}>
                    <AlertTriangle size={15} />
                    {warning}
                  </p>
                ))}
              </div>
            )}
          </section>

          <section className="panel-block">
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">Step 2</p>
                <h2>Insta360 设备</h2>
              </div>
              <Smartphone size={20} />
            </div>
            {device ? (
              <div className="device-card" data-testid="device-card">
                <div className="device-head">
                  <strong>{device.device_name}</strong>
                  <span>{device.status}</span>
                </div>
                <p>
                  <Wifi size={15} />
                  {device.connection_type} / 每{device.capture_interval_minutes}分钟采集 / {device.capture_window}
                </p>
                <p>
                  <BatteryMedium size={15} />
                  电量 {device.battery_percent}% / 剩余 {device.storage_free_gb}GB
                </p>
                <p>
                  <Clock3 size={15} />
                  缓存 {device.offline_cache_count ?? 0} 条{device.status_detail ? ` / ${device.status_detail}` : ""}
                </p>
              </div>
            ) : (
              <p className="small-muted">尚未绑定设备。</p>
            )}
            <div className="device-actions">
              <button className="secondary-button" disabled={busy} onClick={handleBindDevice} type="button">
                <Camera size={18} />
                绑定 Insta360
              </button>
              <button className="secondary-button" disabled={busy || !device} onClick={handleDeviceOffline} type="button">
                <Wifi size={18} />
                模拟离线
              </button>
              <button className="primary-button" data-testid="sync-cache-button" disabled={busy || !device} onClick={handleSyncCache} type="button">
                <RefreshCcw size={18} />
                同步缓存
              </button>
            </div>
          </section>

          <section className="panel-block sdk-panel" data-testid="sdk-panel">
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">SDK Bridge</p>
                <h2>影石 SDK 接入</h2>
              </div>
              <Camera size={20} />
            </div>
            <div className="sdk-status-card">
              <div>
                <span>SDK</span>
                <strong>v{sdkStatus?.sdk_version ?? "1.9.11"}</strong>
              </div>
              <div>
                <span>模式</span>
                <strong>{sdkStatus?.bridge_mode ?? "contract_only"}</strong>
              </div>
            </div>
            <div className="sdk-demo-ref">
              <p>
                本地 demo：{sdkStatus?.demo_reference.exists ? "已检测到" : "未检测到"}
                <span>{sdkStatus?.demo_reference.committed ? "会提交" : "不会提交到 GitHub"}</span>
              </p>
              <small>{sdkStatus?.demo_reference.path ?? runtime?.insta360_sdk_demo_path ?? "../sdk_demo_1.9.11"}</small>
            </div>
            <div className="sdk-operation-tabs">
              {sdkOperations.map((operation) => (
                <button
                  className={sdkOperation === operation.value ? "is-active" : ""}
                  disabled={busy}
                  key={operation.value}
                  onClick={() => handleSdkOperationChange(operation.value)}
                  type="button"
                >
                  {operation.label}
                </button>
              ))}
            </div>
            {sdkPlan ? (
              <div className="sdk-plan">
                <div className="sdk-plan-head">
                  <strong>{sdkPlan.title}</strong>
                  <span>{sdkPlan.recommended_connection}</span>
                </div>
                <p>{sdkPlan.backend_handoff}</p>
                {sdkPlan.steps.slice(0, 4).map((step) => (
                  <article key={`${sdkPlan.operation}-${step.order}`}>
                    <b>{step.order}. {step.name}</b>
                    <span>{step.sdk_calls.slice(0, 2).join(" / ")}</span>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-note">SDK 指令计划加载中。</p>
            )}
          </section>
        </aside>

        <section className="health-main">
          <div className="content-grid">
            <section className="panel-block capture-panel">
              <div className="section-heading compact">
                <div>
                  <p className="eyebrow">Step 3</p>
                  <h2>影像采集与 AI 分析</h2>
                </div>
                <Camera size={20} />
              </div>
              <div className="scene-grid" data-testid="scene-grid">
                {sceneOptions.map((option) => {
                  const Icon = option.icon;
                  return (
                    <button className={sceneHint === option.value ? "scene-button is-active" : "scene-button"} key={option.value} onClick={() => setSceneHint(option.value)} type="button">
                      <Icon size={18} />
                      {option.label}
                    </button>
                  );
                })}
              </div>
              <div className="action-row">
                <button className="primary-button" data-testid="manual-capture-button" disabled={busy} onClick={() => handleCapture("manual")} type="button">
                  <Camera size={18} />
                  手动抓拍
                </button>
                <button className="secondary-button" disabled={busy} onClick={() => handleCapture("auto")} type="button">
                  <Clock3 size={18} />
                  模拟定时采集
                </button>
                <button className="secondary-button" data-testid="review-capture-button" disabled={busy} onClick={handleFailedCaptureReview} type="button">
                  <AlertTriangle size={18} />
                  人工补充
                </button>
              </div>
              <div className="behavior-list" data-testid="behavior-list">
                {(dashboard?.recent_behaviors ?? []).slice(0, 5).map((behavior) => (
                  <article className="behavior-item" key={behavior.behavior_id}>
                    <div>
                      <strong>{behavior.label}</strong>
                      <span>{categoryName(behavior.category)} / 置信度 {Math.round(behavior.confidence * 100)}%</span>
                    </div>
                    <div className="mini-score">
                      <b>{behavior.body_score}</b>
                      <b>{behavior.mental_score}</b>
                    </div>
                    <p>{behavior.impact}</p>
                  </article>
                ))}
                {(dashboard?.recent_behaviors ?? []).length === 0 && <p className="empty-note">暂无行为分析记录。</p>}
              </div>
            </section>

            <section className="panel-block">
              <div className="section-heading compact">
                <div>
                  <p className="eyebrow">Step 4</p>
                  <h2>日度健康日志</h2>
                </div>
                <TrendingUp size={20} />
              </div>
              <button className="secondary-button wide-button" disabled={busy} onClick={handleDaily} type="button">
                <FileText size={18} />
                生成今日日志
              </button>
              {todayLog ? (
                <div className="daily-card" data-testid="daily-card">
                  <div className="ring-score">
                    <strong>{todayLog.overall_score}</strong>
                    <span>{todayLog.date}</span>
                  </div>
                  <div className="summary-grid">
                    <span>饮食 {todayLog.behavior_summary.diet_count ?? 0}</span>
                    <span>运动 {todayLog.behavior_summary.exercise_count ?? 0}</span>
                    <span>睡眠 {todayLog.behavior_summary.sleep_count ?? 0}</span>
                    <span>日常 {todayLog.behavior_summary.daily_count ?? 0}</span>
                  </div>
                  <div className="tag-list">
                    {(todayLog.abnormal_behaviors.length ? todayLog.abnormal_behaviors : ["暂无异常"]).map((item) => (
                      <span key={item}>{item}</span>
                    ))}
                  </div>
                  {todayLog.risk_tips.slice(0, 3).map((tip) => (
                    <p className="tip-line" key={tip}>{tip}</p>
                  ))}
                </div>
              ) : (
                <p className="empty-note">采集影像后可生成今日日志。</p>
              )}
            </section>
          </div>

          <section className="panel-block weekly-panel">
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">Step 5</p>
                <h2>周度健康报告与建议</h2>
              </div>
              <div className="action-row no-margin">
                <button className="primary-button" data-testid="weekly-report-button" disabled={busy} onClick={handleWeekly} type="button">
                  <FileText size={18} />
                  生成周报
                </button>
                <button className="secondary-button" data-testid="download-weekly-pdf-button" disabled={busy || !weeklyReport} onClick={handleDownloadWeeklyPdf} type="button">
                  <FileText size={18} />
                  导出 PDF
                </button>
              </div>
            </div>
            {weeklyReport ? (
              <div className="weekly-grid" data-testid="weekly-report">
                <div className="weekly-score">
                  <span>{weeklyReport.week_start} 至 {weeklyReport.week_end}</span>
                  <strong>{weeklyReport.average_overall_score}</strong>
                  <p>{weeklyReport.comparison}</p>
                </div>
                <div className="trend-chart">
                  {weeklyReport.trend.map((point) => (
                    <div className="trend-bar" key={point.date}>
                      <span style={{ height: `${Math.max(point.overall_score, 12)}%` }} />
                      <small>{point.date.slice(5)}</small>
                    </div>
                  ))}
                </div>
                <article>
                  <h3>身体评估</h3>
                  <p>{weeklyReport.body_assessment}</p>
                  <h3>心理评估</h3>
                  <p>{weeklyReport.mental_assessment}</p>
                </article>
                <article>
                  <h3>个性化建议</h3>
                  {Object.entries(weeklyReport.suggestions).map(([key, suggestions]) => (
                    <div className="suggestion-group" key={key}>
                      <strong>{key}</strong>
                      {suggestions.slice(0, 2).map((suggestion) => (
                        <p key={suggestion}>{suggestion}</p>
                      ))}
                    </div>
                  ))}
                </article>
                <article className="goal-card">
                  <h3>下周目标</h3>
                  {weeklyReport.next_week_goals.map((goal) => (
                    <p key={goal}>
                      <CheckCircle2 size={15} />
                      {goal}
                    </p>
                  ))}
                </article>
              </div>
            ) : (
              <p className="empty-note">生成日报后，可汇总近7日数据并输出周报。</p>
            )}
          </section>

          <section className="panel-block capture-history">
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">Timeline</p>
                <h2>最近采集记录</h2>
              </div>
            </div>
            <div className="capture-strip">
              {(dashboard?.recent_captures ?? []).map((capture) => (
                <article key={capture.capture_id}>
                  <span>{capture.status}</span>
                  <strong>{capture.analysis?.label ?? "待同步分析"}</strong>
                  <p>{capture.capture_mode} / {formatTime(capture.captured_at)}</p>
                </article>
              ))}
              {(dashboard?.recent_captures ?? []).length === 0 && <p className="empty-note">暂无采集记录。</p>}
            </div>
          </section>

          <section className="panel-block history-panel">
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">History</p>
                <h2>历史回溯</h2>
              </div>
            </div>
            <div className="history-grid" data-testid="history-panel">
              <div>
                <strong>日度日志</strong>
                {(dashboard?.daily_history ?? []).slice(0, 5).map((log) => (
                  <p key={log.daily_log_id}>{log.date} / {log.overall_score}分 / {log.behavior_summary.total_records ?? 0}条</p>
                ))}
              </div>
              <div>
                <strong>周度报告</strong>
                {(dashboard?.weekly_history ?? []).slice(0, 5).map((report) => (
                  <p key={report.report_id}>{report.week_start} / {report.average_overall_score}分</p>
                ))}
              </div>
            </div>
          </section>

          <section className="panel-block privacy-panel">
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">Privacy</p>
                <h2>趋势与隐私</h2>
              </div>
              <div className="action-row no-margin">
                <button className="secondary-button" data-testid="load-trends-button" disabled={busy} onClick={handleLoadTrends} type="button">
                  <TrendingUp size={18} />
                  趋势
                </button>
                <button className="ghost-button" data-testid="delete-user-data-button" disabled={busy} onClick={handleDeletePrivacyData} type="button">
                  <AlertTriangle size={18} />
                  删除隐私数据
                </button>
              </div>
            </div>
            <div className="history-grid" data-testid="trend-panel">
              <div>
                <strong>分数趋势</strong>
                <p>日度点位 {trend?.score_series.length ?? 0} 个</p>
                <p>风险标签 {Object.keys(trend?.risk_flags ?? {}).length} 类</p>
              </div>
              <div>
                <strong>体征与行为</strong>
                <p>体征记录 {trend?.vital_series.length ?? 0} 条</p>
                <p>行为日期 {trend?.behavior_series.length ?? 0} 天</p>
              </div>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}
