// src/api.js

const BASE_URL = "http://localhost:5000"; // Change if needed

export async function getVocabulary(username) {
  const res = await fetch(`${BASE_URL}/api/vocabulary/${username}`);
  return res.json();
}

export async function getUserResults(username) {
  const res = await fetch(`${BASE_URL}/api/profile/${username}`);
  return res.json();
}

export async function getLevel(level) {
  const res = await fetch(`${BASE_URL}/api/level`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level }),
  });
  return res.json();
}

export async function submitLevel(payload) {
  const res = await fetch(`${BASE_URL}/api/level/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function translateSentence(payload) {
  const res = await fetch(`${BASE_URL}/api/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function getAdminResults(password) {
  const res = await fetch(`${BASE_URL}/api/admin/results?password=${password}`);
  return res;
}

export async function verifyAdminPassword(password) {
    try {
      const res = await fetch(`http://localhost:5000/api/admin/results?password=${password}`);
      if (!res.ok) throw new Error("Invalid password");
      return true;
    } catch (err) {
      console.error("[API] Admin login failed:", err);
      return false;
    }
  }

  export async function fetchLevelData(level) {
    const res = await fetch("http://localhost:5000/api/level", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level }),
    });
    return await res.json();
  }
  
  export async function submitLevelAnswer(level, answer, username) {
    const res = await fetch("http://localhost:5000/api/level/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level, answer, username }),
    });
    return await res.json();
  }

  export async function fetchProfileResults(username) {
    const res = await fetch(`http://localhost:5000/api/profile/${username}`);
    return await res.json();
  }
  