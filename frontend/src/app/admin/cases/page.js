"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import { Plus } from "lucide-react";
import AdminRoute from "@/components/AdminRoute";
import StatusBadge from "@/components/StatusBadge";
import api from "@/lib/api";
import { useAdminStore } from "@/lib/adminStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import LoadingOverlay from "@/components/ui/LoadingOverlay";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function AdminCasesPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const cases = useAdminStore((state) => state.cases);
  const loading = useAdminStore((state) => state.loading);
  const startAutoRefresh = useAdminStore((state) => state.startAutoRefresh);
  const stopAutoRefresh = useAdminStore((state) => state.stopAutoRefresh);
  const loadAdminData = useAdminStore((state) => state.loadAdminData);
  const [statusDraft, setStatusDraft] = useState({});

  const syncFilters = () => ({ status: statusFilter, city: cityFilter });

  useEffect(() => {
    startAutoRefresh(syncFilters());
    return () => stopAutoRefresh();
  }, [startAutoRefresh, stopAutoRefresh, statusFilter, cityFilter]);

  useEffect(() => {
    setStatusDraft(
      (cases || []).reduce((acc, item) => {
        acc[item.id] = item.status;
        return acc;
      }, {})
    );
  }, [cases]);

  const updateStatus = async (id) => {
    try {
      await api.patch(`/cases/${id}/status`, { status: statusDraft[id] });
      toast.success("Status updated");
      loadAdminData(syncFilters());
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to update status");
    }
  };

  const generateFir = async (id) => {
    try {
      await api.post(`/fir/generate/${id}`);
      toast.success("FIR generated");
      loadAdminData(syncFilters());
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to generate FIR");
    }
  };

  const closeCase = async (id) => {
    try {
      await api.patch(`/admin/cases/${id}/close`);
      toast.success("Case closed");
      loadAdminData(syncFilters());
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to close case");
    }
  };

  const deleteCase = async (id, caseNumber) => {
    const confirmed = window.confirm(`Delete ${caseNumber || `case #${id}`} permanently?`);
    if (!confirmed) return;

    try {
      await api.delete(`/admin/cases/${id}`);
      toast.success("Case deleted");
      loadAdminData(syncFilters());
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to delete case");
    }
  };

  const showSkeleton = loading && !cases?.length;

  return (
    <AdminRoute>
      <div className="relative">
      <main className="space-y-6">
        <section className="flex items-center justify-end">
          <Link href="/cases/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Case
            </Button>
          </Link>
        </section>

        <Card>
          <CardHeader><CardTitle>All Cases</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1">
                <label className="text-sm font-medium">Status</label>
                <select className="h-10 w-full rounded-md border border-(--border) bg-(--card) px-3 text-sm outline-none focus:ring-2 focus:ring-(--ring)" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  <option value="">All</option>
                  <option value="open">Open</option>
                  <option value="matched">Matched</option>
                  <option value="under_investigation">Under Investigation</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">City</label>
                <Input value={cityFilter} onChange={(event) => setCityFilter(event.target.value)} />
              </div>
            </div>
            <Button onClick={() => loadAdminData(syncFilters())}>Apply Filters</Button>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Case#</TableHead>
                  <TableHead>Person</TableHead>
                  <TableHead>City</TableHead>
                  <TableHead>Created By</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {showSkeleton ? [1, 2, 3, 4, 5].map((row) => (
                  <TableRow key={`s-${row}`}>
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((cell) => (
                      <TableCell key={cell}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                )) : null}

                {!showSkeleton && cases.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.case_number}</TableCell>
                    <TableCell>{item.missing_person_name || "-"}</TableCell>
                    <TableCell>{item.city || "-"}</TableCell>
                    <TableCell>
                      <p className="font-semibold">{item.created_by?.name || "Unknown"}</p>
                      <p className="text-xs text-slate-500">{item.created_by?.email || "-"}</p>
                    </TableCell>
                    <TableCell><StatusBadge status={item.status} /></TableCell>
                    <TableCell className="capitalize">{item.priority || "-"}</TableCell>
                    <TableCell>{new Date(item.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-2">
                        <Link href={`/cases/${item.id}`}>
                          <Button variant="outline" size="sm">View</Button>
                        </Link>
                        <select
                          className="h-9 rounded-md border border-(--border) bg-(--card) px-2 text-xs outline-none focus:ring-2 focus:ring-(--ring)"
                          value={statusDraft[item.id] || item.status}
                          onChange={(event) =>
                            setStatusDraft((prev) => ({ ...prev, [item.id]: event.target.value }))
                          }
                        >
                          <option value="open">Open</option>
                          <option value="under_investigation">Under Investigation</option>
                          <option value="matched">Matched</option>
                          <option value="closed">Closed</option>
                        </select>
                        <Button variant="outline" size="sm" onClick={() => updateStatus(item.id)}>
                          Save Status
                        </Button>
                        <Button size="sm" onClick={() => generateFir(item.id)}>
                          Generate FIR
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => closeCase(item.id)}>
                          Close
                        </Button>
                        <Button variant="destructive" size="sm" onClick={() => deleteCase(item.id, item.case_number)}>
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {!showSkeleton && !cases.length ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-(--muted-foreground)">No records.</TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
      {loading ? <LoadingOverlay label="Loading cases..." /> : null}
      </div>
    </AdminRoute>
  );
}
