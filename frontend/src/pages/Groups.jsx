import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../AuthContext.jsx";

export default function Groups() {
  const { user } = useAuth();
  const [groups, setGroups] = useState([]);
  const [selected, setSelected] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [invite, setInvite] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const loadGroups = () => api.groups().then(setGroups).catch((e) => setError(e.message));
  const openGroup = (id) => api.group(id).then(setSelected).catch((e) => setError(e.message));
  useEffect(() => { loadGroups(); }, []);

  async function run(action, success) {
    setError(""); setMsg("");
    try { await action(); setMsg(success); } catch (e) { setError(e.message); }
  }

  const create = (e) => {
    e.preventDefault();
    run(async () => {
      const g = await api.createGroup({ name, description });
      setName(""); setDescription("");
      await loadGroups(); await openGroup(g.id);
    }, "Group created");
  };
  const add = (e) => {
    e.preventDefault();
    run(async () => { await api.addMember(selected.id, invite.trim()); setInvite(""); await openGroup(selected.id); await loadGroups(); },
      `${invite} added`);
  };
  const remove = (uid) => run(async () => {
    await api.removeMember(selected.id, uid);
    if (uid === user.id) { setSelected(null); } else { await openGroup(selected.id); }
    await loadGroups();
  }, uid === user.id ? "You left the group" : "Member removed");

  const isOwner = selected && selected.owner.id === user.id;

  return (
    <div className="two-col">
      <div>
        <form className="card form" onSubmit={create}>
          <h2>New friend group</h2>
          <label>Name<input value={name} onChange={(e) => setName(e.target.value)} required maxLength={100} /></label>
          <label>Description<input value={description} onChange={(e) => setDescription(e.target.value)} /></label>
          <button>Create group</button>
        </form>
        <div className="card">
          <h2>My groups</h2>
          {groups.length === 0 && <p className="muted">You are not in any group yet.</p>}
          {groups.map((g) => (
            <button key={g.id} className={`group-item ${selected?.id === g.id ? "active" : ""}`} onClick={() => openGroup(g.id)}>
              <b>{g.name}</b><span className="muted"> · {g.member_count} member{g.member_count === 1 ? "" : "s"}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        {msg && <p className="success">{msg}</p>}
        {error && <p className="error">{error}</p>}
        {!selected ? <p className="muted">Select a group to see its members.</p> : (
          <>
            <h2>{selected.name}</h2>
            {selected.description && <p>{selected.description}</p>}
            <h3>Members</h3>
            <ul className="members">
              {selected.members.map((m) => (
                <li key={m.user.id}>
                  @{m.user.username} {m.role === "owner" && <span className="tag">owner</span>}
                  {m.role !== "owner" && (isOwner || m.user.id === user.id) && (
                    <button className="link danger-text" onClick={() => remove(m.user.id)}>{m.user.id === user.id ? "Leave" : "Remove"}</button>
                  )}
                </li>
              ))}
            </ul>
            <form className="row" onSubmit={add}>
              <input placeholder="Friend's username" value={invite} onChange={(e) => setInvite(e.target.value)} required />
              <button>Add friend</button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
