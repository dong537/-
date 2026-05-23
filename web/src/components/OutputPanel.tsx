import { Clipboard, Download, WandSparkles } from "lucide-react";
import type { ExportResponse } from "../types";

export function OutputPanel({
  result,
  busy,
  onCreate,
  onDownload,
  onCopy
}: {
  result?: ExportResponse;
  busy?: boolean;
  onCreate: () => void;
  onDownload: (exportId: string) => void;
  onCopy: (text: string) => void;
}) {
  return (
    <section className="output-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">自动出片</p>
          <h2>精选图片与社交文案</h2>
        </div>
        <button className="primary-button" disabled={busy} onClick={onCreate} type="button">
          <WandSparkles size={18} />
          生成结果
        </button>
      </div>

      {result ? (
        <>
          <div className="gallery" data-testid="selected-gallery">
            {result.selected_frames.map((frame) => (
              <figure key={frame.frame_id}>
                <img alt={frame.ai_caption ?? "精选图"} src={frame.image_url} />
                <figcaption>{frame.selected_reason}</figcaption>
              </figure>
            ))}
          </div>
          <article className="copy-card">
            <p className="eyebrow">路线回顾</p>
            <h3>{result.route_recap}</h3>
            <p>{result.social_copy}</p>
            <div className="copy-actions">
              <button className="secondary-button" onClick={() => onCopy(result.social_copy)} type="button">
                <Clipboard size={18} />
                复制文案
              </button>
              <button className="secondary-button" onClick={() => onDownload(result.export_id)} type="button">
                <Download size={18} />
                导出素材包
              </button>
            </div>
          </article>
          <article className="draft-card" data-testid="video-draft">
            <p className="eyebrow">视频草稿</p>
            <div className="draft-list">
              {result.video_draft.map((item) => (
                <div className="draft-item" key={item.frame_id}>
                  <span>{item.order}</span>
                  <div>
                    <strong>{item.shot_type} · {item.duration_seconds}s</strong>
                    <em>{item.route_node_name ?? "旅行素材"} · {item.transition}</em>
                    <p>{item.caption}</p>
                    <small>{item.edit_note}</small>
                  </div>
                </div>
              ))}
            </div>
          </article>
          <article className="story-card">
            <p className="eyebrow">旅程故事线</p>
            <div className="story-list">
              {result.story_events.map((event) => (
                <div className="story-item" key={event.event_id}>
                  <span>{event.title}</span>
                  <p>{event.detail}</p>
                </div>
              ))}
            </div>
          </article>
        </>
      ) : (
        <div className="soft-panel">上传素材并抽帧后，可以一键生成精选图、路线回顾和发布文案。</div>
      )}
    </section>
  );
}
