import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";

export default function Upload() {
  const navigate = useNavigate();
  const [groups, setGroups] = useState(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [groupId, setGroupId] = useState("");
  const [caption, setCaption] = useState("");
  const [tags, setTags] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.groups().then((g) => { setGroups(g); if (g[0]) setGroupId(String(g[0].id)); })
      .catch((e) => setError(e.message));
  }, []);

  function pick(e) {
    const f = e.target.files[0];
    setFile(f || null);
    setPreview(f ? URL.createObjectURL(f) : "");
  }

  async function submit(e) {
    e.preventDefault();
    if (!file) return setError("Please choose a photo");
    setError("");
    setBusy(true);
    const form = new FormData();
    form.append("photo", file);
    form.append("group_id", groupId);
    form.append("caption", caption);
    form.append("tags", tags);
    try {
      const photo = await api.upload(form);
      navigate(`/photos/${photo.id}`);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  if (groups && groups.length === 0) {
    return <div className="card empty"><p>You need to join a group before uploading.</p><Link className="button" to="/groups">Go to Groups</Link></div>;
  }

  return (
    <form className="card form narrow" onSubmit={submit}>
      <h1>Upload photo</h1>
      {error && <p className="error">{error}</p>}
      <label>Photo<input type="file" accept="image/jpeg,image/png,image/gif,image/webp" onChange={pick} /></label>
      {preview && <img className="preview" src={preview} alt="preview" />}
      <label>Share with group
        <select value={groupId} onChange={(e) => setGroupId(e.target.value)}>
          {(groups || []).map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
      </label>
      <label>Caption<textarea value={caption} onChange={(e) => setCaption(e.target.value)} rows={3} /></label>
      <label>Tags (comma separated)<input placeholder="beach, holiday" value={tags} onChange={(e) => setTags(e.target.value)} /></label>
      <button disabled={busy}>{busy ? "Uploading..." : "Upload"}</button>
    </form>
  );
}
