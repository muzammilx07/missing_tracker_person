"use client";

import { useEffect, useMemo, useState } from "react";
import { Camera, Save, UserCircle2 } from "lucide-react";
import { toast } from "react-toastify";
import ProtectedRoute from "@/components/ProtectedRoute";
import { getUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export default function SettingsPage() {
  const [hydrating, setHydrating] = useState(true);
  const user = getUser();
  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [avatarUrl, setAvatarUrl] = useState("");

  useEffect(() => {
    setHydrating(false);
  }, []);

  const initials = useMemo(() => {
    return (name || "User")
      .split(" ")
      .slice(0, 2)
      .map((part) => part[0] || "")
      .join("")
      .toUpperCase();
  }, [name]);

  const saveProfile = () => {
    const raw = localStorage.getItem("user");
    const parsed = raw ? JSON.parse(raw) : {};
    localStorage.setItem(
      "user",
      JSON.stringify({
        ...parsed,
        name,
        email,
        avatarUrl,
      })
    );
    toast.success("Profile updated");
  };

  return (
    <ProtectedRoute>
      <main className="space-y-6">
        <Card className="surface-grid">
          <CardHeader>
            <CardTitle>Profile & Settings</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-5 lg:grid-cols-3">
            <section className="rounded-xl border border-(--border) bg-(--muted) p-4">
              <div className="mb-4 grid place-items-center">
                {hydrating ? (
                  <Skeleton className="h-24 w-24" />
                ) : avatarUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={avatarUrl} alt="Avatar" className="h-24 w-24 rounded-xl object-cover" />
                ) : (
                  <div className="grid h-24 w-24 place-items-center rounded-xl bg-(--primary) text-2xl font-semibold text-(--primary-foreground)">
                    {initials}
                  </div>
                )}
              </div>
              <label className="text-sm font-medium">Avatar URL</label>
              <div className="mt-2 flex gap-2">
                <Input value={avatarUrl} onChange={(event) => setAvatarUrl(event.target.value)} placeholder="https://..." />
                <Button variant="outline" size="icon" aria-label="Avatar">
                  <Camera className="h-4 w-4" />
                </Button>
              </div>
            </section>

            <section className="lg:col-span-2">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium">Name</label>
                  {hydrating ? <Skeleton className="h-10 w-full" /> : <Input value={name} onChange={(event) => setName(event.target.value)} />}
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">Email</label>
                  {hydrating ? <Skeleton className="h-10 w-full" /> : <Input value={email} onChange={(event) => setEmail(event.target.value)} />}
                </div>
              </div>

              <div className="mt-4 rounded-xl border border-(--border) bg-(--muted) p-4">
                <p className="inline-flex items-center gap-2 font-semibold">
                  <UserCircle2 className="h-4 w-4 text-(--primary)" />
                  Activity Summary
                </p>
                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  <SummaryItem label="Cases created" value="12" />
                  <SummaryItem label="Sightings submitted" value="8" />
                  <SummaryItem label="Alerts received" value="27" />
                </div>
              </div>

              <Button onClick={saveProfile} className="mt-4 gap-2">
                <Save className="h-4 w-4" />
                Save Changes
              </Button>
            </section>
          </CardContent>
        </Card>
      </main>
    </ProtectedRoute>
  );
}

function SummaryItem({ label, value }) {
  return (
    <div className="rounded-xl border border-(--border) bg-(--card) p-3">
      <p className="text-xs text-(--muted-foreground)">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}
