const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

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
        credentials: "include",
    });
    if (!res.ok) throw new Error("unauthorized");
    return await res.json();
};

export const getRole = async () => {
    const res = await fetch(`${BASE_URL}/api/role`, {
        credentials: "include",
    });
    if (!res.ok) throw new Error("unauthorized");
    return await res.json();
};

export const fetchProfileResults = async () => {
    const res = await fetch(`${BASE_URL}/api/profile`, {
        credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch profile");
    return await res.json();
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
        credentials: "include",
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        const errorText = await res.text();
        console.error("[API] Server error response:", errorText);
        throw new Error(`❌ Server error: ${res.status}`);
    }

    return await res.json();
}


// ---------- Admin ----------

export async function verifyAdminPassword(password) {
    try {
        const res = await fetch(`${BASE_URL}/api/admin/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ password }),
        });

        if (!res.ok) {
            console.warn("[API] Invalid response status:", res.status);
            return false;
        }

        const data = await res.json();
        return data.msg === "Login successful"; // ✅ this matches your Flask response
    } catch (err) {
        console.error("[API] Admin login failed:", err);
        return false;
    }
}


// ---------- Admin ----------
export const getAdminRole = async () =>
    fetch(`${BASE_URL}/api/role`, { credentials: "include" }).then(res => res.json());

export const getAdminResults = async () =>
    fetch(`${BASE_URL}/api/admin/results`, { credentials: "include" }).then(res => res.json());

export const getLessonProgressSummary = async () =>
    fetch(`${BASE_URL}/api/admin/lesson-progress-summary`, { credentials: "include" }).then(res => res.json());

export const saveLesson = async (lesson, isEdit = false) => {
    const url = isEdit
        ? `${BASE_URL}/api/admin/lesson-content/${lesson.lesson_id}`
        : `${BASE_URL}/api/admin/lesson-content`;

    const method = isEdit ? "PUT" : "POST";

    return fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(lesson),
    });
};


export async function togglePublishLesson(lessonId, updatedLesson) {
    return await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedLesson),
    });
}



// Get detailed lesson progress
export const getLessonProgressDetails = async (lessonId) => {
    const res = await fetch(`${BASE_URL}/api/admin/lesson-progress/${lessonId}`, {
        credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch progress details");
    return await res.json();
};

// Update publish state
export const updateLessonPublished = async (lessonId, publish) => {
    const res = await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ published: publish ? 1 : 0 }),
    });
    return res.ok;
};

// Delete a lesson
export const deleteLesson = async (lessonId) => {
    const res = await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
        method: "DELETE",
        credentials: "include",
    });
    return res.ok;
};

// Refresh lessons
export const getLessons = async () => {
    const res = await fetch(`${BASE_URL}/api/admin/lesson-content`, {
        credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch lessons");
    return await res.json();
};


//----------------Lesson-edit------------
export const getLessonById = async (lessonId) => {
    const res = await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
        credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch lesson");
    return await res.json();
};

export const updateLesson = async (lessonId, lessonData) => {
    return await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(lessonData),
    });
};

//----------------Lessons------------
export const getStudentLessons = async () => {
    const res = await fetch(`${BASE_URL}/api/lessons`, {
        method: "GET",
        credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch lessons");
    return await res.json();
};

export async function updatePassword(current_password, new_password) {
    const res = await fetch(`${BASE_URL}/api/settings/password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ current_password, new_password }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    return data;
}

export async function uploadAvatar(file) {
    const formData = new FormData();
    formData.append("avatar", file);

    const res = await fetch(`${BASE_URL}/api/settings/avatar`, {
        method: "POST",
        credentials: "include",
        body: formData,
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    return data;
}

export async function deactivateAccount() {
    const res = await fetch(`${BASE_URL}/api/settings/deactivate`, {
        method: "POST",
        credentials: "include",
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    return data;
}

export const getLesson = async (lessonId) => {
    const res = await fetch(`${BASE_URL}/api/lesson/${lessonId}`, {
        method: "GET",
        credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch lesson content");
    return res.json();
};

export const getLessonProgress = async (lessonId) => {
    const res = await fetch(`${BASE_URL}/api/lesson-progress/${lessonId}`, {
        credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch progress");
    return res.json();
};

export const isLessonCompleted = async (lessonId) => {
    const res = await fetch(`${BASE_URL}/api/lesson-completed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ lesson_id: parseInt(lessonId) }),
    });
    if (!res.ok) throw new Error("Failed to check completion status");
    return res.json();
};

export const markLessonComplete = async (lessonId) => {
    const res = await fetch(`${BASE_URL}/api/mark-as-completed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ lesson_id: parseInt(lessonId) }),
    });
    if (!res.ok) throw new Error("Failed to mark lesson as complete");
    return res.json();
};

export const updateLessonBlockProgress = async (lessonId, blockId, completed) => {
    const res = await fetch(`${BASE_URL}/api/lesson-progress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
            lesson_id: parseInt(lessonId),
            block_id: blockId,
            completed,
        }),
    });
    if (!res.ok) throw new Error("Failed to update block progress");
    return res.json();
};

export const getAiExercises = async (payload = {}) =>
{
    // === MOCKED RESPONSE ===
    return {
        lessonId: "mock-ai-lesson-001",
        title: "Using 'sein' in the Present Tense",
        instructions: "Fill in the correct form of the verb 'sein' in each sentence.",
        level: "A1",
        type: "gap-fill",
        exercises: [
            {
                id: "ex1",
                question: "Ich ___ müde.",
                options: ["bist", "bin", "ist", "seid"],
                correctAnswer: "bin",
                explanation: "‘Ich’ uses the form ‘bin’ of the verb ‘sein’ in present tense."
            },
            {
                id: "ex2",
                question: "Du ___ mein Freund.",
                options: ["bin", "bist", "ist", "seid"],
                correctAnswer: "bist",
                explanation: "‘Du’ requires ‘bist’ in the present tense of ‘sein’."
            },
            {
                id: "ex3",
                question: "Wir ___ in Berlin.",
                options: ["seid", "bin", "ist", "sind"],
                correctAnswer: "sind",
                explanation: "‘Wir’ uses ‘sind’ as the plural form of ‘sein’."
            }
        ],
        vocabHelp: [
            { word: "sein", meaning: "to be" },
            { word: "müde", meaning: "tired" },
            { word: "Freund", meaning: "friend" }
        ],
        feedbackPrompt: "Great work! Review any incorrect answers and try again if needed."
    };

    // === REAL REQUEST ===
    /*
    const res = await fetch(`${BASE_URL}/api/ai-exercises`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to fetch AI exercises");
    return res.json();
    */
};

