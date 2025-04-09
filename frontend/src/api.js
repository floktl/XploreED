const BASE_URL = "http://localhost:5050";

// ---------- Auth ----------
export const signup = async (username, password) => {
  const res = await fetch(`${BASE_URL}/api/signup`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  try {
    return await res.json();
  } catch {
    return { error: "❌ Invalid signup response from server" };
  }
};

export const login = async (username, password) => {
  const res = await fetch(`${BASE_URL}/api/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  try {
    return await res.json();
  } catch {
    return { error: "❌ Invalid login response from server" };
  }
};

export const logout = async () => {
  const res = await fetch(`${BASE_URL}/api/logout`, {
    method: "POST",
    credentials: "include",
  });

  try {
    return await res.json();
  } catch {
    return { error: "❌ Logout failed" };
  }
};

// ---------- Profile ----------
export const getMe = async () => {
  const res = await fetch(`${BASE_URL}/api/me`, {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) throw new Error("❌ Failed to fetch user");

  return await res.json();
};

export const getRole = async () => {
  const res = await fetch(`${BASE_URL}/api/role`, {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) throw new Error("❌ Failed to fetch role");

  return await res.json(); // returns { is_admin: true/false }
};

export const getProfile = async () => {
  const res = await fetch(`${BASE_URL}/api/profile`, {
    method: "GET",
    credentials: "include",
  });

  try {
    return await res.json();
  } catch {
    return { error: "❌ Profile response invalid" };
  }
};

export async function getUserResults() {
  const res = await fetch(`${BASE_URL}/api/profile`, {
    credentials: "include",
  });
  return res.json();
}

export async function fetchProfileResults() {
  return await fetch(`${BASE_URL}/api/profile`, {
    credentials: "include",
  });
}

export async function fetchProfileStats(username) {
  const res = await fetch(`${BASE_URL}/api/admin/profile-stats`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  });

  if (!res.ok) {
    throw new Error("❌ Failed to load user stats");
  }

  return await res.json();
}

// ---------- Vocabulary ----------
export async function getVocabulary() {
  const res = await fetch(`${BASE_URL}/api/vocabulary`, {
    credentials: "include",
  });
  return res.json();
}

// ---------- Game ----------
export async function getLevel(level) {
  const res = await fetch(`${BASE_URL}/api/level`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level }),
  });
  return res.json();
}

export async function fetchLevelData(level) {
  try {
    const res = await fetch(`${BASE_URL}/api/level`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level }),
    });

    const data = await res.json();
    return {
      scrambled: Array.isArray(data.scrambled) ? data.scrambled : [],
    };
  } catch (err) {
    console.error("[API] Failed to fetch level data:", err);
    return { scrambled: [] };
  }
}


export async function submitLevel(payload) {
  const res = await fetch(`${BASE_URL}/api/level/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function submitLevelAnswer(level, answer) {
  const res = await fetch(`${BASE_URL}/api/level/submit`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level, answer }),
  });

  return await res.json();
}

// ---------- Translation ----------
export async function translateSentence(payload) {
  const res = await fetch(`${BASE_URL}/api/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

// ---------- Admin ----------
export async function getAdminResults(password) {
  const res = await fetch(`${BASE_URL}/api/admin/results`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  return res;
}

export async function verifyAdminPassword(password) {
  try {
    const res = await fetch(`${BASE_URL}/api/admin/results`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });

    if (!res.ok) {
      console.warn("[API] Invalid response status:", res.status);
      return false;
    }

    const data = await res.json();

    if (Array.isArray(data)) {
      return true;
    }

    console.warn("[API] Unexpected response:", data);
    return false;
  } catch (err) {
    console.error("[API] Admin login failed:", err);
    return false;
  }
}
