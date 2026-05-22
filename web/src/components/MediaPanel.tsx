import { ImagePlus, Sparkles, Star, Upload, Volume2, VolumeX } from "lucide-react";
import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";
import type { CompanionResponse, FrameAsset, MediaAsset } from "../types";

type MediaPanelProps = {
  media?: MediaAsset;
  frames: FrameAsset[];
  companion?: CompanionResponse;
  busy?: boolean;
  onUpload: (file: File) => void;
  onDemo: () => void;
  onAnalyze: (frameId?: string) => void;
  onMark: (frame: FrameAsset) => void;
};

export function MediaPanel({ media, frames, companion, busy, onUpload, onDemo, onAnalyze, onMark }: MediaPanelProps) {
  const [speaking, setSpeaking] = useState(false);
  const speechSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  useEffect(() => {
    setSpeaking(false);
    return () => {
      if (speechSupported) {
        window.speechSynthesis.cancel();
      }
    };
  }, [companion?.message, speechSupported]);

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onUpload(file);
  }

  function handleSpeak() {
    if (!companion || !speechSupported) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(companion.message);
    utterance.lang = "zh-CN";
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.cancel();
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  }

  return (
    <section className="media-panel">
      <div className="media-preview">
        {frames[0] ? (
          <img alt="候选帧预览" src={frames[0].image_url} />
        ) : (
          <div className="camera-placeholder">
            <ImagePlus size={42} />
            <span>上传素材或使用演示素材</span>
          </div>
        )}
      </div>
      <div className="media-controls">
        <label className="file-button">
          <Upload size={18} />
          <span>上传视频/图片</span>
          <input accept="image/*,video/*" onChange={handleFile} type="file" />
        </label>
        <button className="secondary-button" disabled={busy} onClick={onDemo} type="button">
          <Sparkles size={18} />
          使用演示素材
        </button>
        <button className="primary-button" disabled={busy || !media} onClick={() => onAnalyze(frames[0]?.frame_id)} type="button">
          生成伴游讲解
        </button>
      </div>
      {frames.length ? (
        <div className="frame-strip" aria-label="候选帧">
          {frames.map((frame) => (
            <div className={`frame-thumb ${frame.marked ? "is-marked" : ""}`} key={frame.frame_id}>
              <button className="frame-image-button" onClick={() => onAnalyze(frame.frame_id)} type="button">
                <img alt={frame.ai_caption ?? "候选帧"} src={frame.thumbnail_url} />
                <span>{Math.round(frame.timestamp_ms / 1000)}s</span>
              </button>
              <button
                className="mark-button"
                disabled={busy}
                onClick={(event) => {
                  event.stopPropagation();
                  onMark(frame);
                }}
                title={frame.marked ? "取消标记" : "标记精彩瞬间"}
                type="button"
              >
                <Star fill={frame.marked ? "currentColor" : "none"} size={15} />
              </button>
            </div>
          ))}
        </div>
      ) : null}
      {companion ? (
        <article className="companion-card">
          <div className="companion-title">
            <p className="eyebrow">AI 伴游</p>
            <button className="voice-button" disabled={!speechSupported} onClick={handleSpeak} title={speaking ? "停止播报" : "语音播报"} type="button">
              {speaking ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </button>
          </div>
          <h3>{companion.message}</h3>
          <div className="tag-row">
            {companion.shooting_tips.map((tip) => (
              <span key={tip}>{tip}</span>
            ))}
          </div>
        </article>
      ) : null}
    </section>
  );
}
