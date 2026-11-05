import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, assetUrl, formatDate } from "../api.js";
import { useAuth } from "../AuthContext.jsx";

const REFRESH_MS = 10000; // pick up other users' new comments automatically

export default function PhotoDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [photo, setPhoto] = useState(null);
  const [text, setText] = useState("");
  const [editing, setEditing] = useState(null); // { id, content }
  const [error, setError] = useState("");

  const load = useCallback(() => api.photo(id).then(setPhoto).catch((e) => setError(e.message)), [id]);

  useEffect(() => {
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => clearInterval(timer);
  }, [load]);

  async function run(action) {
    setError("");
    try { await action(); await load(); } catch (e) { setError(e.message); }
  }

  const addComment = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    run(async () => { await api.addComment(id, text); setText(""); });
  };
  const saveEdit = () => run(async () => { await api.editComment(editing.id, editing.content); setEditing(null); });
  const removeComment = (cid) => { if (confirm("Delete this comment?")) run(() => api.deleteComment(cid)); };
  const removePhoto = async () => {
    if (!confirm("Delete this photo?")) return;
    try { await api.deletePhoto(id); navigate("/"); } catch (e) { setError(e.message); }
  };

  if (!photo) return error ? <p className="error">{error}</p> : <p className="muted">Loading...</p>;

  return (
    <div className="detail">
      <div className="card">
        <img className="full" src={assetUrl(photo.url)} alt={photo.caption || "photo"} />
        <div className="card-body">
          {photo.caption && <p className="caption">{photo.caption}</p>}
          <p className="meta">Shared by <b>@{photo.uploader.username}</b> in <b>{photo.group.name}</b> · {formatDate(photo.created_at)}</p>
          {photo.tags.length > 0 && <div className="tags">{photo.tags.map((t) => <span key={t} className="tag">#{t}</span>)}</div>}
          {photo.uploader.id === user.id && <button className="danger" onClick={removePhoto}>Delete photo</button>}
        </div>
      </div>

      <div className="card comments">
        <h2>Comments ({photo.comments.length})</h2>
        {error && <p className="error">{error}</p>}
        {photo.comments.length === 0 && <p className="muted">No comments yet. Be the first!</p>}
        {photo.comments.map((c) => (
          <div key={c.id} className="comment">
            <p className="meta"><b>@{c.user.username}</b> · {formatDate(c.created_at)}{c.edited && " (edited)"}</p>
            {editing?.id === c.id ? (
              <>
                <textarea rows={2} value={editing.content} onChange={(e) => setEditing({ ...editing, content: e.target.value })} />
                <div className="row"><button onClick={saveEdit}>Save</button><button className="secondary" onClick={() => setEditing(null)}>Cancel</button></div>
              </>
            ) : <p>{c.content}</p>}
            <div className="row small">
              {c.user.id === user.id && editing?.id !== c.id && <button className="link" onClick={() => setEditing({ id: c.id, content: c.content })}>Edit</button>}
              {(c.user.id === user.id || photo.uploader.id === user.id) && <button className="link danger-text" onClick={() => removeComment(c.id)}>Delete</button>}
            </div>
          </div>
        ))}
        <form onSubmit={addComment} className="add-comment">
          <textarea rows={2} placeholder="Write a comment..." value={text} onChange={(e) => setText(e.target.value)} maxLength={1000} />
          <button>Post comment</button>
        </form>
        <Link to="/" className="muted">← Back to feed</Link>
      </div>
    </div>
  );
}
