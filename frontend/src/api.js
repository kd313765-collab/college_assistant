// backend se baat karne ke saare functions yahin hain

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = "Bearer " + token;

  const res = await fetch("/api" + path, { ...options, headers });

  if (res.status === 401 && token) {
    // token expire ho gaya
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.reload();
  }
  return res;
}

async function json(path, options) {
  const res = await request(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Kuch gadbad ho gayi");
  return data;
}

function postJson(path, body) {
  return json(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export const api = {
  login: (email, password) => postJson("/login", { email, password }),
  register: (body) => postJson("/register", body),
  chat: (message) => postJson("/chat", { message }),
  subjects: () => json("/subjects"),
  assignments: () => json("/assignments"),
  solve: (id) => postJson("/assignments/" + id + "/solve", {}),
  topics: () => json("/topics"),
  results: () => json("/results"),

  // file ke liye login token chahiye, isliye seedha link nahi chalta
  download: async (id, name) => {
    const res = await request("/assignments/" + id + "/file");
    if (!res.ok) throw new Error("File download nahi hui");
    const url = URL.createObjectURL(await res.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = name || "assignment";
    link.click();
    URL.revokeObjectURL(url);
  },
  notifications: () => json("/notifications"),
  markRead: () => postJson("/notifications/read", {}),
  setTopic: (body) => postJson("/topics", body),

  uploadResults: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return json("/results/upload", { method: "POST", body: fd });
  },

  postAssignment: (formData) => json("/assignments", { method: "POST", body: formData }),

  speechToText: async (blob) => {
    const fd = new FormData();
    fd.append("audio", blob, "voice.webm");
    return json("/voice/stt", { method: "POST", body: fd });
  },

  textToSpeech: async (text) => {
    const res = await request("/voice/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error("tts fail");
    return res.blob();
  },
};
