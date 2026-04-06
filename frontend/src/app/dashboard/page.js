"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Plus, SearchCheck } from "lucide-react";
import api from "@/lib/api";
import { getUser } from "@/lib/auth";
import ProtectedRoute from "@/components/ProtectedRoute";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ActivityTableCard,
  ActiveInvestigationsCard,
  CaseDistributionCard,
  MatchConfidenceCard,
  StatWidget,
  TimelineCard,
} from "@/components/dashboard/MissionControlWidgets";

export default function DashboardPage() {
  const user = getUser();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const fetchCases = async () => {
      try {
        const response = await api.get("/cases");
        if (active) {
          setCases(response.data.cases || []);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchCases();
    return () => {
      active = false;
    };
  }, []);

  const stats = useMemo(() => {
    const total = cases.length;
    const open = cases.filter((item) => item.status === "open").length;
    const matched = cases.filter((item) => item.status === "matched").length;
    const closed = cases.filter((item) => item.status === "closed").length;
    return { total, open, matched, closed };
  }, [cases]);

  const showSkeleton = loading;

  return (
    <ProtectedRoute>
      <main className="space-y-4">
        <section className="panel fade-up flex flex-wrap items-center justify-between gap-3 p-4">
          <div>
            <p className="text-xs uppercase tracking-[0.14em] text-[#a1a1aa]">Investigation dashboard</p>
            <h2 className="text-2xl font-semibold tracking-tight">Welcome back, {user?.name || "Operator"}</h2>
            <p className="mt-1 text-sm text-[#52525b]">Monitor case flow, confidence metrics, and investigation progress.</p>
          </div>
          <div className="flex gap-2">
            <Link href="/cases/new">
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Register Case
              </Button>
            </Link>
            <Link href="/report-sighting">
              <Button variant="outline" className="gap-2">
                <SearchCheck className="h-4 w-4" />
                Add Sighting
              </Button>
            </Link>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <StatWidget title="Total Cases" value={stats.total} subtitle="All registered cases" loading={showSkeleton} />
          <StatWidget title="Active Cases" value={stats.open} subtitle="Currently under investigation" loading={showSkeleton} />
          <StatWidget title="Resolved Cases" value={stats.closed} subtitle="Marked closed or found" loading={showSkeleton} />
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <ActivityTableCard loading={showSkeleton} />
          <CaseDistributionCard values={{ active: stats.open, resolved: stats.matched, closed: stats.closed }} loading={showSkeleton} />
          <MatchConfidenceCard confidence={Math.min(97, 70 + stats.matched * 5)} loading={showSkeleton} />
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <ActiveInvestigationsCard loading={showSkeleton} />
          </div>
          <TimelineCard loading={showSkeleton} />
        </section>

        {!showSkeleton && !cases.length ? (
          <Card>
            <CardHeader>
              <CardTitle>No active cases yet</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-(--muted-foreground)">Start by registering a missing person case to activate live tracking.</p>
              <Link href="/cases/new">
                <Button>Register First Case</Button>
              </Link>
            </CardContent>
          </Card>
        ) : null}
      </main>
    </ProtectedRoute>
  );
}
