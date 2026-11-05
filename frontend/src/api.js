// All communication with the Flask API (application tier) goes through here.
const BASE = import.meta.env.VITE_API_URL || "";

export function getToken() {
  return localStorage.getItem("token");
}

async function request(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = form; // FormData: browser sets the multipart header itself
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && token) {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

export const api = {
  register: (data) => request("/api/auth/register", { method: "POST", body: data }),
  login: (data) => request("/api/auth/login", { method: "POST", body: data }),

  groups: () => request("/api/groups"),
  group: (id) => request(`/api/groups/${id}`),
  createGroup: (data) => request("/api/groups", { method: "POST", body: data }),
  addMember: (id, username) => request(`/api/groups/${id}/members`, { method: "POST", body: { username } }),
  removeMember: (id, userId) => request(`/api/groups/${id}/members/${userId}`, { method: "DELETE" }),

  photos: (params = {}) => {
    const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null));
    return request(`/api/photos?${new URLSearchParams(clean)}`);
  },
  photo: (id) => request(`/api/photos/${id}`),
  upload: (form) => request("/api/photos", { method: "POST", form }),
  deletePhoto: (id) => request(`/api/photos/${id}`, { method: "DELETE" }),

  addComment: (photoId, content) => request(`/api/photos/${photoId}/comments`, { method: "POST", body: { content } }),
  editComment: (id, content) => request(`/api/comments/${id}`, { method: "PUT", body: { content } }),
  deleteComment: (id) => request(`/api/comments/${id}`, { method: "DELETE" }),
};

export function assetUrl(url) {
  // S3 presigned URLs are absolute; local-dev URLs start with /api.
  return url.startsWith("http") ? url : `${BASE}${url}`;
}

export function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
