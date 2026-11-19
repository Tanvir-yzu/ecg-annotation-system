const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.status === 204 ? null : res.json();
}

export const api = {
  labels: () => request("/labels/"),
  records: () => request("/records/"),
  signal: (id, start, end, lead, filtered) =>
    request(`/records/${id}/signal/?start=${start}&end=${end}&lead=${lead}&filtered=${filtered ? 1 : 0}`),
  annotations: (recordId) => request(`/annotations/?record=${recordId}`),
  createAnnotation: (data) => request("/annotations/", { method: "POST", body: JSON.stringify(data) }),
  updateAnnotation: (id, data) => request(`/annotations/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteAnnotation: (id) => request(`/annotations/${id}/`, { method: "DELETE" }),
  verify: (id, data) => request(`/annotations/${id}/verify/`, { method: "POST", body: JSON.stringify(data) }),
  detect: (id, lead) => request(`/records/${id}/detect/`, { method: "POST", body: JSON.stringify({ lead }) }),
  exportUrl: (id, fmt = "csv") => `${BASE}/records/${id}/export/?fmt=${fmt}`,
};
