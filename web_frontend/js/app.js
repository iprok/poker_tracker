function userStatsTable() {
    return {
        users: [],
        search: "",
        sortField: "roi",
        sortAsc: false,
        hideSmallSample: true,

        // Main table date filter
        tableStartDate: '',
        tableEndDate: '',

        // Chart state
        showRoiModal: false,
        chartInstance: null,
        chartUser: null,
        roiData: [],
        startDate: '',
        endDate: '',

        headers: [
            { field: "username", label: "👤 Имя / ID", tooltip: "" },
            { field: "games_played", label: "🎲 Игры (шт)", tooltip: "" },
            { field: "total_buyin", label: "💰 Объём закупов (EUR)", tooltip: "Общий объём закупов за выбранный период" },
            { field: "avg_buyins_per_game", label: "📊 Ср. кол-во закупов (шт)", tooltip: "Среднее количество закупов за одну игру за выбранный период" },
            { field: "profit", label: "📈 Прибыль (EUR)", tooltip: "" },
            { field: "roi", label: "📉 ROI (%)", tooltip: "Return on Investment (ROI) — окупаемость вложений за выбранный период. Рассчитывается как отношение чистой прибыли (выигрыш минус закуп) к общей сумме закупов. Формула: ((Profit / Total Buyin) * 100%)." },
        ],

        async init() {
            // Set default dates for main table: current year
            const now = new Date();
            const startOfYear = new Date(now.getFullYear(), 0, 1);

            this.tableStartDate = formatDate(startOfYear);
            this.tableEndDate = formatDate(now);

            // Fetch users
            const userList = await fetchUsers();

            // Fetch full actions history for each user
            const enriched = await Promise.all(
                userList.users.map(async (user) => {
                    try {
                        const data = await fetchUserActions(user.user_id);
                        return { ...user, actions: data.actions };
                    } catch (e) {
                        console.error("Error fetching actions for user:", user.user_id, e);
                        return { ...user, actions: [] };
                    }
                })
            );

            this.users = enriched;
        },

        setAllTime() {
            let earliest = new Date();
            this.users.forEach(u => {
                u.actions.forEach(a => {
                    const d = new Date(a.timestamp);
                    if (d < earliest) earliest = d;
                });
            });

            this.tableStartDate = formatDate(earliest);
            this.tableEndDate = formatDate(new Date());
        },

        setThisYear() {
            const now = new Date();
            const startOfYear = new Date(now.getFullYear(), 0, 1);
            this.tableStartDate = formatDate(startOfYear);
            this.tableEndDate = formatDate(now);
        },

        setSort(field) {
            if (this.sortField === field) {
                this.sortAsc = !this.sortAsc;
            } else {
                this.sortField = field;
                this.sortAsc = false;
            }
        },

        get filteredAndSorted() {
            // Add displayStats to each user based on current table date range
            const withStats = this.users.map(u => ({
                ...u,
                displayStats: calculateStats(u.actions, this.tableStartDate, this.tableEndDate)
            }));

            const filtered = withStats.filter((u) => {
                const name = u.username?.toLowerCase() ?? "";
                const id = u.user_id.toString();
                const nameMatches =
                    name.includes(this.search.toLowerCase()) || id.includes(this.search);
                const sampleOk = !this.hideSmallSample || u.displayStats.games_played >= 3;
                return nameMatches && sampleOk;
            });

            return filtered.sort((a, b) => {
                let valA, valB;
                if (this.sortField === 'username') {
                    valA = a.username || a.user_id.toString();
                    valB = b.username || b.user_id.toString();
                    if (valA === valB) return 0;
                    return this.sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                } else {
                    valA = a.displayStats[this.sortField];
                    valB = b.displayStats[this.sortField];
                    if (valA === valB) return 0;
                    return this.sortAsc ? valA - valB : valB - valA;
                }
            });
        },

        async openRoiChart(user) {
            this.chartUser = user;
            this.showRoiModal = true;

            try {
                this.roiData = calculateRoiHistory(user.actions);

                // Set dates based on data
                if (this.roiData.length > 0) {
                    // Data is already sorted by date in calculateRoiHistory
                    this.startDate = this.roiData[0].date;
                    this.endDate = this.roiData[this.roiData.length - 1].date;
                } else {
                    const today = new Date().toISOString().split('T')[0];
                    this.startDate = today;
                    this.endDate = today;
                }

                // Wait for modal to render canvas
                this.$nextTick(() => {
                    this.updateChart();
                });
            } catch (e) {
                console.error(e);
                alert("Не удалось загрузить историю ROI");
                this.showRoiModal = false;
            }
        },

        closeRoiChart() {
            this.showRoiModal = false;
            if (this.chartInstance) {
                this.chartInstance.destroy();
                this.chartInstance = null;
            }
        },

        get filteredRoiData() {
            if (!this.roiData) return [];
            const start = new Date(this.startDate).getTime();
            const end = new Date(this.endDate).getTime();

            return this.roiData.filter(item => {
                const itemDate = new Date(item.date).getTime();
                return itemDate >= start && itemDate <= end;
            });
        },

        updateChart() {
            const ctx = document.getElementById('roiChart').getContext('2d');
            if (this.chartInstance) {
                this.chartInstance.destroy();
            }
            this.chartInstance = renderRoiChart(ctx, this.filteredRoiData, this.chartUser.username ?? this.chartUser.user_id);
        }
    };
}
