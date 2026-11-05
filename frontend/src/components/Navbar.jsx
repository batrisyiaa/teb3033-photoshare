import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <header className="navbar">
      <Link to="/" className="brand">PhotoShare</Link>
      {user && (
        <nav>
          <NavLink to="/" end>Feed</NavLink>
          <NavLink to="/upload">Upload</NavLink>
          <NavLink to="/groups">Groups</NavLink>
          <span className="who">@{user.username}</span>
          <button className="link" onClick={() => { logout(); navigate("/login"); }}>Log out</button>
        </nav>
      )}
    </header>
  );
}
