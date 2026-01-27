const API_URL = CONFIG.API_URL;

async function fetchUsers() {
    const res = await fetch(`${API_URL}/api/users`);
    return await res.json();
}

async function fetchUserActions(userId) {
    const res = await fetch(`${API_URL}/api/stats/${userId}/actions`);
    return await res.json();
}
