const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function call(path, body) {
  const res = await fetch(BASE + path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

export const api = {
  createUser: (name) => call("/users", { name }),
  diagnostic: () => call("/diagnostic"),
  attempt: (user_id, question_id, choice) => call("/attempts", { user_id, question_id, choice }),
  explain: (user_id, question_id, choice) => call("/tutor/explain", { user_id, question_id, choice }),
  next: (user_id, concept_id) =>
    call(`/practice/next?user_id=${user_id}${concept_id ? `&concept_id=${concept_id}` : ""}`),
  insights: (user_id) => call(`/insights/${user_id}`),
  map: (user_id) => call(`/map/${user_id}`),
};
