const API_URL = CONFIG.API_URL;

async function fetchUsers() {
    const res = await fetch(`${API_URL}/api/users`);
    return await res.json();
}

async function fetchUserActions(userId) {
    const res = await fetch(`${API_URL}/api/stats/${userId}/actions`);
    return await res.json();
}

async function fetchTournaments() {
    const res = await fetch(`${API_URL}/api/tournaments`);
    return await res.json();
}

async function fetchTournamentDetails(id) {
    const res = await fetch(`${API_URL}/api/tournaments/${id}`);
    if (!res.ok) throw new Error("Tournament not found");
    return await res.json();
}
