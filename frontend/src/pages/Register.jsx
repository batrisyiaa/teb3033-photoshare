import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";

export default function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", display_name: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(form);
      navigate("/groups");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card form narrow" onSubmit={submit}>
      <h1>Create account</h1>
      {error && <p className="error">{error}</p>}
      <label>Username<input value={form.username} onChange={set("username")} required /></label>
      <label>Display name (optional)<input value={form.display_name} onChange={set("display_name")} /></label>
      <label>Email<input type="email" value={form.email} onChange={set("email")} required /></label>
      <label>Password (min 6 characters)<input type="password" value={form.password} onChange={set("password")} required minLength={6} /></label>
      <button disabled={busy}>{busy ? "Creating..." : "Register"}</button>
      <p className="muted">Already have an account? <Link to="/login">Log in</Link></p>
    </form>
  );
}
