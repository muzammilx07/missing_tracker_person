import { create } from "zustand";
import api from "@/lib/api";

const AUTO_REFRESH_MS = 12000;

export const useAdminStore = create((set, get) => ({
  stats: null,
  cases: [],
  matches: [],
  pendingMatches: { review_needed: 0, auto_pending_signoff: 0 },
  sightings: [],
  volunteers: { pending: [], approved: [], volunteers: [] },
  firs: [],
  alerts: [],
  loading: false,
  lastUpdated: null,
  refreshTimer: null,

  loadAdminData: async (filters = {}) => {
    set({ loading: true });
    try {
      const params = new URLSearchParams();
      if (filters.status) params.set("status", filters.status);
      if (filters.city) params.set("city", filters.city);
      const caseQuery = params.toString();

      const [statsRes, casesRes, matchesRes, pendingMatchesRes, sightingsRes, volunteersRes, firsRes, alertsRes] = await Promise.all([
        api.get("/admin/stats"),
        api.get(caseQuery ? `/admin/cases?${caseQuery}` : "/admin/cases"),
        api.get("/admin/matches"),
        api.get("/matches/pending-count"),
        api.get("/admin/sightings"),
        api.get("/admin/volunteers"),
        api.get("/admin/firs"),
        api.get("/admin/alerts"),
      ]);

      set({
        stats: statsRes.data,
        cases: casesRes.data.cases || [],
        matches: matchesRes.data.matches || [],
        pendingMatches: pendingMatchesRes.data || { review_needed: 0, auto_pending_signoff: 0 },
        sightings: sightingsRes.data.sightings || [],
        volunteers: volunteersRes.data || { pending: [], approved: [], volunteers: [] },
        firs: firsRes.data.firs || [],
        alerts: alertsRes.data.alerts || [],
        loading: false,
        lastUpdated: Date.now(),
      });
    } catch {
      set({ loading: false });
    }
  },

  startAutoRefresh: (filters = {}) => {
    get().stopAutoRefresh();
    get().loadAdminData(filters);
    const timer = setInterval(() => {
      get().loadAdminData(filters);
    }, AUTO_REFRESH_MS);
    set({ refreshTimer: timer });
  },

  stopAutoRefresh: () => {
    const timer = get().refreshTimer;
    if (timer) {
      clearInterval(timer);
      set({ refreshTimer: null });
    }
  },
}));
