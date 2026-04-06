"use client";

import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import { CheckCircle2, Hourglass, Users } from "lucide-react";
import api from "@/lib/api";
import ProtectedRoute from "@/components/ProtectedRoute";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function VolunteerPage() {
  const [profile, setProfile] = useState(null);
  const [casesData, setCasesData] = useState(null);
  const [form, setForm] = useState({
    coverage_type: "city",
    coverage_city: "",
    coverage_state: "",
    bio: "",
  });

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const response = await api.get("/volunteers");
        const mine = (response.data.volunteers || []).find((item) => item.user_id);
        if (active && mine) {
          setProfile(mine);
        }
      } catch {
        setProfile(null);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!profile || profile.status !== "approved") return;

    let active = true;

    const loadCases = async () => {
      try {
        const response = await api.get("/volunteers/my-cases");
        if (active) {
          setCasesData(response.data);
        }
      } catch {
        if (active) setCasesData({ assigned: [], area_cases: [] });
      }
    };

    loadCases();
    return () => {
      active = false;
    };
  }, [profile]);

  const submitApplication = async (event) => {
    event.preventDefault();
    try {
      await api.post("/volunteers/apply", form);
      toast.success("Application submitted");
      setProfile({ status: "pending", ...form });
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not submit application");
    }
  };

  return (
    <ProtectedRoute>
      <main className="space-y-6">
        <Card className="surface-grid">
          <CardHeader>
            <CardTitle>Volunteer Network</CardTitle>
            <CardDescription>Apply, track approval, and support nearby open cases with coordinated response.</CardDescription>
          </CardHeader>
        </Card>

        {!profile ? (
          <Card>
            <CardHeader>
              <CardTitle className="inline-flex items-center gap-2">
                <Users className="h-5 w-5 text-(--primary)" />
                Apply as Volunteer
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submitApplication}>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Coverage Type</label>
                  <select
                    className="h-11 w-full rounded-xl border border-(--border) bg-(--card) px-3 text-sm outline-none focus:ring-2 focus:ring-(--ring)"
                    value={form.coverage_type}
                    onChange={(event) => setForm((prev) => ({ ...prev, coverage_type: event.target.value }))}
                  >
                    <option value="city">City</option>
                    <option value="state">State</option>
                    <option value="any">Any</option>
                  </select>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Coverage City</label>
                    <Input
                      value={form.coverage_city}
                      onChange={(event) => setForm((prev) => ({ ...prev, coverage_city: event.target.value }))}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Coverage State</label>
                    <Input
                      value={form.coverage_state}
                      onChange={(event) => setForm((prev) => ({ ...prev, coverage_state: event.target.value }))}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Bio</label>
                  <Textarea
                    rows={3}
                    value={form.bio}
                    onChange={(event) => setForm((prev) => ({ ...prev, bio: event.target.value }))}
                  />
                </div>
                <Button type="submit" className="w-full">Submit Application</Button>
              </form>
            </CardContent>
          </Card>
        ) : null}

        {profile?.status === "pending" ? (
          <Card>
            <CardHeader>
              <CardTitle className="inline-flex items-center gap-2">
                <Hourglass className="h-5 w-5 text-amber-600" />
                Application Pending
              </CardTitle>
            </CardHeader>
            <CardContent><p className="text-sm text-(--muted-foreground)">Your request is under review by admins.</p></CardContent>
          </Card>
        ) : null}

        {profile?.status === "approved" ? (
          <Card>
            <CardHeader>
              <CardTitle className="inline-flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-700" />
                Volunteer Cases
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-xl bg-(--muted) p-4">
                  <p className="text-sm text-(--muted-foreground)">Assigned Cases</p>
                  <p className="text-2xl font-semibold">{(casesData?.assigned || []).length}</p>
                </div>
                <div className="rounded-xl bg-(--muted) p-4">
                  <p className="text-sm text-(--muted-foreground)">Area Cases</p>
                  <p className="text-2xl font-semibold">{(casesData?.area_cases || []).length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}
      </main>
    </ProtectedRoute>
  );
}
