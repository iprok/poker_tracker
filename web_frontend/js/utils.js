function formatDate(d) {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function calculateStats(actions, startStr, endStr) {
    const start = new Date(startStr + 'T00:00:00').getTime();
    const end = new Date(endStr + 'T23:59:59').getTime();

    const filtered = actions.filter(a => {
        const t = new Date(a.timestamp).getTime();
        return t >= start && t <= end;
    });

    const games = new Set();
    let totalBuyin = 0;
    let totalQuit = 0;
    let buyinCount = 0;

    filtered.forEach(a => {
        games.add(a.game_id);
        if (a.action === 'buyin') {
            totalBuyin += a.amount || 0;
            buyinCount++;
        } else if (a.action === 'quit') {
            totalQuit += a.amount || 0;
        }
    });

    const gamesPlayed = games.size;
    const profit = totalQuit - totalBuyin;
    const roi = totalBuyin > 0 ? (profit / totalBuyin * 100) : 0;
    const avgBuyins = gamesPlayed > 0 ? (buyinCount / gamesPlayed) : 0;

    return {
        games_played: gamesPlayed,
        total_buyin: totalBuyin,
        avg_buyins_per_game: avgBuyins,
        profit: profit,
        roi: roi
    };
}

function calculateRoiHistory(actions) {
    if (!actions || actions.length === 0) return [];

    // Sort actions by timestamp
    const sorted = [...actions].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    const dailyRoiSet = {};
    let cumulativeBuyin = 0;
    let cumulativeQuit = 0;

    sorted.forEach(a => {
        if (a.action === 'buyin') {
            cumulativeBuyin += a.amount || 0;
        } else if (a.action === 'quit') {
            cumulativeQuit += a.amount || 0;
        }

        const currentDate = a.timestamp.split('T')[0];
        const roi = cumulativeBuyin > 0 ? ((cumulativeQuit - cumulativeBuyin) / cumulativeBuyin) * 100 : 0;
        dailyRoiSet[currentDate] = parseFloat(roi.toFixed(1));
    });

    return Object.entries(dailyRoiSet).map(([date, roi]) => ({ date, roi }));
}
