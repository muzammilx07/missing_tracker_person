"use client";

import { useEffect } from "react";
import { Activity, FileSearch, Radar, Users } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import AdminRoute from "@/components/AdminRoute";
import { useAdminStore } from "@/lib/adminStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import LoadingOverlay from "@/components/ui/LoadingOverlay";
import { Skeleton } from "@/components/ui/skeleton";

const PIE_COLORS = ["#2f5be7", "#4a72eb", "#6589ee", "#7f9ff1", "#9ab6f4", "#b4ccf7"];

export default function AdminDashboardPage() {
  const stats = useAdminStore((state) => state.stats);
  const loading = useAdminStore((state) => state.loading);
  const startAutoRefresh = useAdminStore((state) => state.startAutoRefresh);
  const stopAutoRefresh = useAdminStore((state) => state.stopAutoRefresh);

  useEffect(() => {
    startAutoRefresh();
    return () => {
      stopAutoRefresh();
    };
  }, [startAutoRefresh, stopAutoRefresh]);

  const cards = [
    { title: "Total Cases", value: stats?.total_cases ?? 0, icon: FileSearch },
    { title: "Open Cases", value: stats?.open_cases ?? 0, icon: Radar },
    { title: "Matches Found", value: stats?.matches_found ?? 0, icon: Activity },
    { title: "Active Volunteers", value: stats?.volunteers ?? 0, icon: Users },
    { title: "FIRs Generated", value: stats?.firs_generated ?? 0, icon: FileSearch },
  ];

  const showSkeleton = loading && !stats;

  return (
    <AdminRoute>
      <div className="relative">
      <main className="space-y-6">
        <section className="grid gap-4 md:grid-cols-5">
          {cards.map((item) => (
            <Card key={item.title}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-sm text-(--muted-foreground)">
                  {item.title}
                  <item.icon className="h-4 w-4 text-(--primary)" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                {showSkeleton ? <Skeleton className="h-9 w-16" /> : <p className="text-2xl font-semibold">{item.value}</p>}
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Cases Over Time</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              {showSkeleton ? <Skeleton className="h-full w-full" /> : <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stats?.cases_over_time || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="var(--primary)" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Matches Per Day</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              {showSkeleton ? <Skeleton className="h-full w-full" /> : <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.matches_over_time || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="var(--primary)" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Status Distribution</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              {showSkeleton ? <Skeleton className="h-full w-full" /> : <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats?.status_distribution || []}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label
                  >
                    {(stats?.status_distribution || []).map((entry, index) => (
                      <Cell key={`${entry.status}-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Activity Feed</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(stats?.recent_activity || []).slice(0, 10).map((item, index) => (
                <div key={`${item.time}-${index}`} className="rounded-xl border border-(--border) bg-(--muted) px-3 py-2">
                  <p className="text-sm font-semibold">{item.type}</p>
                  <p className="text-sm text-(--muted-foreground)">{item.message}</p>
                  <p className="text-xs text-(--muted-foreground)">{new Date(item.time).toLocaleString()}</p>
                </div>
              ))}
              {!stats?.recent_activity?.length ? (
                <p className="text-sm text-(--muted-foreground)">No recent activity found.</p>
              ) : null}
            </CardContent>
          </Card>
        </section>
      </main>
      {loading ? <LoadingOverlay label="Loading admin analytics..." /> : null}
      </div>
    </AdminRoute>
  );
}
