"use client";

import { useEffect, useState } from "react";
import { Bell, CheckCircle2 } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

export default function NotificationsPage() {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const response = await api.get("/notifications");
        if (active) setItems(response.data.notifications || []);
      } catch {
        if (active) setItems([]);
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <ProtectedRoute>
      <div className="relative">
      <main className="space-y-6">
        <Card className="surface-grid">
          <CardHeader>
            <CardTitle className="inline-flex items-center gap-2">
              <Bell className="h-5 w-5 text-(--primary)" />
              Notifications
            </CardTitle>
          </CardHeader>
        </Card>

        {!items.length ? (
          <Card>
            <CardContent className="grid min-h-56 place-items-center text-center">
              <div>
                <CheckCircle2 className="mx-auto mb-2 h-6 w-6 text-emerald-700" />
                <p className="font-semibold">You are all caught up</p>
                <p className="text-sm text-(--muted-foreground)">No unread alerts at the moment.</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="space-y-3">
              {items.map((item, index) => (
                <article key={`${item.id || index}`} className="hover-card rounded-md border border-(--border) bg-(--card) p-4">
                  <p className="font-semibold">{item.title || "Case update"}</p>
                  <p className="mt-1 text-sm text-(--muted-foreground)">{item.message || "An update was posted to one of your tracked cases."}</p>
                  <p className="mt-2 text-xs text-(--muted-foreground)">
                    {item.created_at ? new Date(item.created_at).toLocaleString() : "Just now"}
                  </p>
                </article>
              ))}
            </CardContent>
          </Card>
        )}
      </main>
      {loading ? <LoadingOverlay label="Loading notifications..." /> : null}
      </div>
    </ProtectedRoute>
  );
}
