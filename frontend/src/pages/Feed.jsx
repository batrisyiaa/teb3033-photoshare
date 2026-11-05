import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import PhotoCard from "../components/PhotoCard.jsx";

const EMPTY = { q: "", group_id: "", uploader: "", tag: "", date_from: "", date_to: "", sort: "newest" };

export default function Feed() {
  const [groups, setGroups] = useState(null);
  const [filters, setFilters] = useState(EMPTY);
  const [applied, setApplied] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { api.groups().then(setGroups).catch((e) => setError(e.message)); }, []);

  useEffect(() => {
    setError("");
    api.photos({ ...applied, page }).then(setData).catch((e) => setError(e.message));
  }, [applied, page]);

  const set = (key) => (e) => setFilters({ ...filters, [key]: e.target.value });
  const apply = (e) => { e.preventDefault(); setPage(1); setApplied(filters); };
  const reset = () => { setFilters(EMPTY); setPage(1); setApplied(EMPTY); };

  if (groups && groups.length === 0) {
    return (
      <div className="card empty">
        <h2>Welcome!</h2>
        <p>Create a friend group or ask a friend to add you to theirs. Then you can share photos.</p>
        <Link className="button" to="/groups">Go to Groups</Link>
      </div>
    );
  }

  return (
    <>
      <form className="card filters" onSubmit={apply}>
        <input placeholder="Search caption, tags, comments, people..." value={filters.q} onChange={set("q")} />
        <select value={filters.group_id} onChange={set("group_id")}>
          <option value="">All groups</option>
          {(groups || []).map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
        <input placeholder="Uploader username" value={filters.uploader} onChange={set("uploader")} />
        <input placeholder="Tag" value={filters.tag} onChange={set("tag")} />
        <label className="inline">From <input type="date" value={filters.date_from} onChange={set("date_from")} /></label>
        <label className="inline">To <input type="date" value={filters.date_to} onChange={set("date_to")} /></label>
        <select value={filters.sort} onChange={set("sort")}>
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
        </select>
        <button>Search</button>
        <button type="button" className="secondary" onClick={reset}>Clear</button>
      </form>

      {error && <p className="error">{error}</p>}
      {!data ? <p className="muted">Loading...</p> : (
        <>
          <p className="muted">{data.total} photo{data.total === 1 ? "" : "s"}</p>
          <div className="grid">{data.items.map((p) => <PhotoCard key={p.id} photo={p} />)}</div>
          {data.pages > 1 && (
            <div className="pager">
              <button className="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
              <span>Page {data.page} of {data.pages}</span>
              <button className="secondary" disabled={page >= data.pages} onClick={() => setPage(page + 1)}>Next</button>
            </div>
          )}
        </>
      )}
    </>
  );
}
