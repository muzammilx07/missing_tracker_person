"use client";

import { useEffect } from "react";
import { BellRing } from "lucide-react";
import AdminRoute from "@/components/AdminRoute";
import { useAdminStore } from "@/lib/adminStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

export default function AdminAlertsPage() {
  const alerts = useAdminStore((state) => state.alerts);
  const loading = useAdminStore((state) => state.loading);
  const startAutoRefresh = useAdminStore((state) => state.startAutoRefresh);
  const stopAutoRefresh = useAdminStore((state) => state.stopAutoRefresh);

  useEffect(() => {
    startAutoRefresh();
    return () => stopAutoRefresh();
  }, [startAutoRefresh, stopAutoRefresh]);

  return (
    <AdminRoute>
      <div className="relative">
        <main className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="inline-flex items-center gap-2">
                <BellRing className="h-5 w-5" />
                Admin Alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(alerts || []).map((item) => (
                <article key={item.id} className="rounded-md border border-(--border) bg-(--card) p-3">
                  <p className="font-semibold">{item.type || "alert"}</p>
                  <p className="text-sm text-(--muted-foreground)">{item.message || "No message provided"}</p>
                  <p className="mt-1 text-xs text-(--muted-foreground)">
                    {item.case_id ? `Case ${item.case_id} • ` : ""}
                    {item.match_id ? `Match ${item.match_id} • ` : ""}
                    {item.sent_at ? new Date(item.sent_at).toLocaleString() : "Just now"}
                  </p>
                </article>
              ))}
              {!alerts?.length ? (
                <p className="text-sm text-(--muted-foreground)">No alerts available right now.</p>
              ) : null}
            </CardContent>
          </Card>
        </main>
        {loading && !alerts?.length ? <LoadingOverlay label="Loading alerts..." /> : null}
      </div>
    </AdminRoute>
  );
}
