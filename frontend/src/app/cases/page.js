"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Filter, Plus } from "lucide-react";
import api from "@/lib/api";
import ProtectedRoute from "@/components/ProtectedRoute";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import LoadingOverlay from "@/components/ui/LoadingOverlay";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function CasesPage() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("query") || "";

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(initialQuery);
  const [status, setStatus] = useState("");

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const response = await api.get("/cases");
        if (active) setCases(response?.data?.cases || []);
      } catch {
        if (active) setCases([]);
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    return (cases || []).filter((item) => {
      const text = `${item.case_number || ""} ${item.missing_person_name || ""} ${item.city || ""}`.toLowerCase();
      const matchQuery = !query.trim() || text.includes(query.toLowerCase());
      const matchStatus = !status || item.status === status;
      return matchQuery && matchStatus;
    });
  }, [cases, query, status]);

  const showSkeleton = loading && !cases.length;

  return (
    <ProtectedRoute>
      <div className="relative">
        <main className="space-y-6">
          <section className="panel flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-2xl font-semibold">My Cases</h2>
              <p className="text-sm text-(--muted-foreground)">Track your registered missing person cases.</p>
            </div>
            <Link href="/cases/new">
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                New Case
              </Button>
            </Link>
          </section>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Filters</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-3">
              <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by case, person, or city" />
              <select
                value={status}
                onChange={(event) => setStatus(event.target.value)}
                className="h-10 rounded-md border border-(--border) bg-(--card) px-3 text-sm outline-none focus:ring-2 focus:ring-(--ring)"
              >
                <option value="">All statuses</option>
                <option value="open">Open</option>
                <option value="under_investigation">Under Investigation</option>
                <option value="matched">Matched</option>
                <option value="closed">Closed</option>
              </select>
              <Button variant="outline" className="gap-2" onClick={() => { setQuery(""); setStatus(""); }}>
                <Filter className="h-4 w-4" />
                Reset
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Case</TableHead>
                    <TableHead>Person</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {showSkeleton ? [1, 2, 3].map((row) => (
                    <TableRow key={`s-${row}`}>
                      {[1, 2, 3, 4, 5, 6].map((cell) => (
                        <TableCell key={cell}><Skeleton className="h-4 w-full" /></TableCell>
                      ))}
                    </TableRow>
                  )) : null}

                  {!showSkeleton && filtered.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.case_number || "-"}</TableCell>
                      <TableCell>{item.missing_person_name || item.missing_person?.name || "-"}</TableCell>
                      <TableCell>{item.city || item.missing_person?.city || "-"}</TableCell>
                      <TableCell><StatusBadge status={item.status} /></TableCell>
                      <TableCell>{item.created_at ? new Date(item.created_at).toLocaleDateString() : "-"}</TableCell>
                      <TableCell>
                        <Link href={`/cases/${item.id}`}>
                          <Button size="sm" variant="outline">Open</Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}

                  {!showSkeleton && !filtered.length ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-(--muted-foreground)">
                        No registered cases found.
                      </TableCell>
                    </TableRow>
                  ) : null}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </main>
        {loading ? <LoadingOverlay label="Loading your cases..." /> : null}
      </div>
    </ProtectedRoute>
  );
}
