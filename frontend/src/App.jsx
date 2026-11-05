import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";
import Navbar from "./components/Navbar.jsx";
import Feed from "./pages/Feed.jsx";
import Groups from "./pages/Groups.jsx";
import Login from "./pages/Login.jsx";
import PhotoDetail from "./pages/PhotoDetail.jsx";
import Register from "./pages/Register.jsx";
import Upload from "./pages/Upload.jsx";

function Private({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Private><Feed /></Private>} />
          <Route path="/upload" element={<Private><Upload /></Private>} />
          <Route path="/groups" element={<Private><Groups /></Private>} />
          <Route path="/photos/:id" element={<Private><PhotoDetail /></Private>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
