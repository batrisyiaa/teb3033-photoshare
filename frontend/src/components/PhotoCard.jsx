import { Link } from "react-router-dom";
import { assetUrl, formatDate } from "../api.js";

export default function PhotoCard({ photo }) {
  return (
    <Link to={`/photos/${photo.id}`} className="card photo-card">
      <img src={assetUrl(photo.url)} alt={photo.caption || "photo"} loading="lazy" />
      <div className="card-body">
        {photo.caption && <p className="caption">{photo.caption}</p>}
        <p className="meta">
          @{photo.uploader.username} · {photo.group.name}<br />
          {formatDate(photo.created_at)} · {photo.comment_count} comment{photo.comment_count === 1 ? "" : "s"}
        </p>
        {photo.tags.length > 0 && (
          <div className="tags">{photo.tags.map((t) => <span key={t} className="tag">#{t}</span>)}</div>
        )}
      </div>
    </Link>
  );
}
