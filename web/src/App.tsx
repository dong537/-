import { Compass, FastForward, Loader2, Map, Play, RotateCcw, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  analyzeCompanion,
  createDemoMedia,
  createExport,
  createTrip,
  extractFrames,
  generateRoute,
  getExportBundle,
  getRuntimeConfig,
  getTripDetail,
  markFrame,
  rerouteTrip,
  resetDemo,
  uploadMedia
} from "./api/client";
import { MapView } from "./components/MapView";
import { MediaPanel } from "./components/MediaPanel";
import { OutputPanel } from "./components/OutputPanel";
import { ResumeTripPanel } from "./components/ResumeTripPanel";
import { RouteTimeline } from "./components/RouteTimeline";
import { StoryTimeline } from "./components/StoryTimeline";
import { StatusActions } from "./components/StatusActions";
import { SystemStatusPanel } from "./components/SystemStatusPanel";
import { useTripStore } from "./store/useTripStore";
import type { FrameAsset, TripDetail, UserStatus } from "./types";

const preferenceOptions = ["风景", "拍视频", "轻松", "美食", "人文", "小众"];

export function App() {
  const store = useTripStore();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("准备好后，AI 会先帮你规划一条可演示路线。");
  const [runtime, setRuntime] = useState<{ ai_provider: string; ai_mode?: string; map_provider: string; map_mode?: string }>();

  const canShowRoute = Boolean(store.route);
  const selectedFrame = useMemo(() => store.frames[0], [store.frames]);

  useEffect(() => {
    getRuntimeConfig()
      .then((config) =>
        setRuntime({
          ai_provider: config.ai_provider,
          ai_mode: config.ai_mode,
          map_provider: config.map_provider,
          map_mode: config.map_mode
        })
      )
      .catch(() => setRuntime({ ai_provider: "offline", map_provider: "offline" }));
  }, []);

  async function run<T>(message: string, task: () => Promise<T>): Promise<T | undefined> {
    setBusy(true);
    setNotice(message);
    try {
      return await task();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "操作失败，请稍后再试。");
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  async function refreshTripEvents(tripId = store.tripId) {
    if (!tripId) return;
    const detail = await getTripDetail(tripId);
    store.setEvents(detail.events);
  }

  function handleResumeTrip(_tripId: string, detail: TripDetail) {
    store.hydrateFromDetail(detail);
    setNotice("已恢复最近演示，可继续改路线、讲解或导出。");
  }

  async function handleCreateTrip(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run("正在生成路线，地图和 AI 正在对齐节奏。", async () => {
      const trip = await createTrip({
        destination: store.destination,
        duration_minutes: store.durationMinutes,
        preferences: store.preferences,
        use_panorama_camera: true
      });
      store.setTripId(trip.trip_id);
      const route = await generateRoute(trip.trip_id);
      store.setRoute(route);
      await refreshTripEvents(trip.trip_id);
      setNotice("路线已生成。你可以点击状态按钮，让 AI 现场改路线。");
    });
  }

  async function handleStatus(status: UserStatus) {
    if (!store.tripId) return;
    store.setUserStatus(status);
    await run("正在根据你的状态重新规划路线。", async () => {
      const route = await rerouteTrip(store.tripId!, status);
      store.setRoute(route);
      await refreshTripEvents();
      setNotice(route.change_summary ?? "路线已更新。");
    });
  }

  async function handleUpload(file: File) {
    if (!store.tripId) return;
    await run("正在上传并抽取候选帧。", async () => {
      const media = await uploadMedia(store.tripId!, file);
      store.setMedia(media);
      const response = await extractFrames(media.media_id);
      store.setFrames(response.frames);
      await refreshTripEvents();
      setNotice(`已生成 ${response.frames.length} 张候选帧。`);
    });
  }

  async function handleDemoMedia() {
    if (!store.tripId) return;
    await run("正在准备演示全景素材。", async () => {
      const media = await createDemoMedia(store.tripId!);
      store.setMedia(media);
      const response = await extractFrames(media.media_id);
      store.setFrames(response.frames);
      await refreshTripEvents();
      setNotice("演示素材已就绪，可以生成伴游讲解。");
    });
  }

  async function handleAnalyze(frameId?: string) {
    if (!store.tripId) return;
    await run("AI 正在观察当前画面。", async () => {
      const response = await analyzeCompanion(store.tripId!, {
        frame_id: frameId ?? selectedFrame?.frame_id,
        route_node_id: store.route?.nodes[0]?.id,
        user_status: store.userStatus
      });
      store.setCompanion(response);
      await refreshTripEvents();
      setNotice("伴游讲解已生成。");
    });
  }

  async function handleMarkFrame(frame: FrameAsset) {
    await run(frame.marked ? "正在取消精彩标记。" : "正在标记精彩瞬间。", async () => {
      const updated = await markFrame(frame.frame_id, !frame.marked);
      store.updateFrame(updated);
      await refreshTripEvents();
      setNotice(updated.marked ? "已标记精彩瞬间，自动出片会优先考虑它。" : "已取消精彩标记。");
    });
  }

  async function handleCreateExport() {
    if (!store.tripId) return;
    await run("正在精选图片并生成旅行文案。", async () => {
      const response = await createExport(store.tripId!);
      store.setExportResult(response);
      await refreshTripEvents();
      setNotice("自动出片结果已生成。");
    });
  }

  async function handleRunDemo() {
    await run("正在一键跑通演示闭环。", async () => {
      await resetDemo();
      store.reset();
      setNotice("Step 1/5：创建旅行并生成路线。");
      const trip = await createTrip({
        destination: "杭州西湖附近",
        duration_minutes: 120,
        preferences: ["风景", "拍视频", "轻松"],
        use_panorama_camera: true
      });
      store.setTripId(trip.trip_id);
      const route = await generateRoute(trip.trip_id);
      store.setRoute(route);

      setNotice("Step 2/5：模拟用户状态变化并改路线。");
      store.setUserStatus("tired");
      const rerouted = await rerouteTrip(trip.trip_id, "tired");
      store.setRoute(rerouted);

      setNotice("Step 3/5：准备演示素材并标记精彩瞬间。");
      const media = await createDemoMedia(trip.trip_id);
      store.setMedia(media);
      const frameResponse = await extractFrames(media.media_id);
      let frames = frameResponse.frames;
      if (frames[1]) {
        const marked = await markFrame(frames[1].frame_id, true);
        frames = frames.map((frame) => (frame.frame_id === marked.frame_id ? marked : frame));
      }
      store.setFrames(frames);

      setNotice("Step 4/5：生成 AI 伴游讲解。");
      const companion = await analyzeCompanion(trip.trip_id, {
        frame_id: frames[1]?.frame_id ?? frames[0]?.frame_id,
        route_node_id: rerouted.nodes[0]?.id,
        user_status: "tired"
      });
      store.setCompanion(companion);

      setNotice("Step 5/5：生成自动出片结果。");
      const exportResult = await createExport(trip.trip_id);
      store.setExportResult(exportResult);
      await refreshTripEvents(trip.trip_id);
      setNotice("一键演示已完成：路线、改路线、伴游讲解、精彩标记和自动出片都已生成。");
    });
  }

  async function handleDownloadManifest(exportId: string) {
    await run("正在生成可下载素材包。", async () => {
      const blob = await getExportBundle(exportId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${exportId}-bundle.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setNotice("ZIP 素材包已下载，包含 manifest 和精选帧。");
    });
  }

  async function handleCopyText(text: string) {
    await run("正在复制发布文案。", async () => {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }
      setNotice("发布文案已复制。");
    });
  }

  function togglePreference(option: string) {
    const next = store.preferences.includes(option) ? store.preferences.filter((item) => item !== option) : [...store.preferences, option];
    store.setTripInput({ destination: store.destination, durationMinutes: store.durationMinutes, preferences: next });
  }

  async function handleReset() {
    await run("正在重置演示状态。", async () => {
      await resetDemo();
      store.reset();
      setNotice("演示状态已重置，可以重新开始。");
    });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Compass size={24} />
          <div>
            <strong>Panorama Companion</strong>
            <span>AI 全景旅行伴游</span>
          </div>
        </div>
        <div className="runtime-strip" title="当前运行模式">
          <span>AI: {runtime?.ai_provider ?? "..."} / {runtime?.ai_mode ?? "..."}</span>
          <span>Map: {runtime?.map_provider ?? "..."} / {runtime?.map_mode ?? "..."}</span>
        </div>
        <button className="ghost-button" onClick={handleReset} type="button">
          <RotateCcw size={18} />
          重置
        </button>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">Hackathon MVP</p>
          <h1>让地图、全景画面和 AI 一起陪你走完一段 City Walk</h1>
        </div>
        <div className="hero-actions">
          <button className="demo-run-button" disabled={busy} onClick={handleRunDemo} type="button">
            <FastForward size={18} />
            一键演示
          </button>
          <div className="status-pill">
            {busy ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />}
            <span>{notice}</span>
          </div>
        </div>
      </section>

      <div className="workspace">
        <aside className="control-panel">
          <form onSubmit={handleCreateTrip}>
            <div className="section-heading">
              <div>
                <p className="eyebrow">Step 1</p>
                <h2>旅行目标</h2>
              </div>
              <button className="primary-button" disabled={busy} type="submit">
                <Play size={18} />
                生成路线
              </button>
            </div>
            <label>
              想去哪里
              <input
                onChange={(event) =>
                  store.setTripInput({
                    destination: event.target.value,
                    durationMinutes: store.durationMinutes,
                    preferences: store.preferences
                  })
                }
                value={store.destination}
              />
            </label>
            <label>
              想玩多久
              <input
                min={15}
                onChange={(event) =>
                  store.setTripInput({
                    destination: store.destination,
                    durationMinutes: Number(event.target.value),
                    preferences: store.preferences
                  })
                }
                type="number"
                value={store.durationMinutes}
              />
            </label>
            <div>
              <span className="field-title">偏好</span>
              <div className="chip-grid">
                {preferenceOptions.map((option) => (
                  <button className={store.preferences.includes(option) ? "chip is-active" : "chip"} key={option} onClick={() => togglePreference(option)} type="button">
                    {option}
                  </button>
                ))}
              </div>
            </div>
          </form>

          <div className="divider" />

          <SystemStatusPanel />

          <div className="divider" />

          <ResumeTripPanel activeTripId={store.tripId} busy={busy} onResume={handleResumeTrip} />

          <div className="divider" />

          <section>
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">Step 2</p>
                <h2>实时状态</h2>
              </div>
            </div>
            <StatusActions disabled={!canShowRoute || busy} onChange={handleStatus} value={store.userStatus} />
          </section>

          <div className="divider" />

          <section>
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">路线节点</p>
                <h2>AI 规划</h2>
              </div>
            </div>
            <RouteTimeline route={store.route} />
          </section>

          <div className="divider" />

          <StoryTimeline events={store.events} />
        </aside>

        <section className="main-panel">
          <div className="map-grid">
            <MapView route={store.route} />
            <section className="tips-panel">
              <div className="section-heading compact">
                <div>
                  <p className="eyebrow">地图建议</p>
                  <h2>下一步</h2>
                </div>
                <Map size={20} />
              </div>
              {(store.route?.tips ?? ["先生成路线，再查看 AI 给出的路线建议。"]).map((tip) => (
                <p key={tip}>{tip}</p>
              ))}
            </section>
          </div>

          <div className="lower-grid">
            <MediaPanel busy={busy} companion={store.companion} frames={store.frames} media={store.media} onAnalyze={handleAnalyze} onDemo={handleDemoMedia} onMark={handleMarkFrame} onUpload={handleUpload} />
            <OutputPanel busy={busy || !store.tripId} onCopy={handleCopyText} onCreate={handleCreateExport} onDownload={handleDownloadManifest} result={store.exportResult} />
          </div>
        </section>
      </div>
    </main>
  );
}
