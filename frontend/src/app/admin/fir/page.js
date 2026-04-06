"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import AdminRoute from "@/components/AdminRoute";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAdminStore } from "@/lib/adminStore";
import LoadingOverlay from "@/components/ui/LoadingOverlay";
import { Input } from "@/components/ui/input";
import api from "@/lib/api";

export default function AdminFirListPage() {
  const [caseId, setCaseId] = useState("");
  const [generating, setGenerating] = useState(false);
  const [statusDraft, setStatusDraft] = useState({});
  const firs = useAdminStore((state) => state.firs);
  const cases = useAdminStore((state) => state.cases);
  const loading = useAdminStore((state) => state.loading);
  const startAutoRefresh = useAdminStore((state) => state.startAutoRefresh);
  const stopAutoRefresh = useAdminStore((state) => state.stopAutoRefresh);
  const loadAdminData = useAdminStore((state) => state.loadAdminData);

  useEffect(() => {
    startAutoRefresh();
    return () => {
      stopAutoRefresh();
    };
  }, [startAutoRefresh, stopAutoRefresh]);

  useEffect(() => {
    setStatusDraft(
      (firs || []).reduce((acc, item) => {
        acc[item.id] = item.status;
        return acc;
      }, {})
    );
  }, [firs]);

  const generateFir = async (selectedCaseId) => {
    const id = selectedCaseId || caseId;
    if (!id) {
      toast.error("Enter a case ID");
      return;
    }

    setGenerating(true);
    try {
      const response = await api.post(`/fir/generate/${id}`);
      toast.success("FIR generated");
      setCaseId("");
      loadAdminData();
      if (response?.data?.fir_id) {
        window.location.href = `/admin/fir/${response.data.fir_id}`;
      }
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to generate FIR");
    } finally {
      setGenerating(false);
    }
  };

  const updateFir = async (id) => {
    try {
      await api.patch(`/admin/firs/${id}`, { status: statusDraft[id] });
      toast.success("FIR updated");
      loadAdminData();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to update FIR");
    }
  };

  return (
    <AdminRoute>
      <div className="relative">
      <main className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Generate FIR</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Input
                value={caseId}
                onChange={(event) => setCaseId(event.target.value)}
                placeholder="Enter case ID (e.g., 12)"
                className="max-w-xs"
              />
              <Button onClick={() => generateFir()} disabled={generating}>
                {generating ? "Generating..." : "Generate FIR"}
              </Button>
            </div>
            <div className="text-xs text-(--muted-foreground)">
              Quick generate from recent cases:
            </div>
            <div className="flex flex-wrap gap-2">
              {cases.slice(0, 6).map((item) => (
                <Button key={item.id} size="sm" variant="outline" onClick={() => generateFir(item.id)}>
                  {item.case_number || `Case ${item.id}`}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>FIR List</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>FIR ID</TableHead>
                  <TableHead>Case ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created Date</TableHead>
                  <TableHead>Update Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {firs.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.fir_number || item.id}</TableCell>
                    <TableCell>{item.case_number || item.case_id}</TableCell>
                    <TableCell className="capitalize">{item.status}</TableCell>
                    <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <select
                          className="h-9 rounded-md border border-(--border) bg-(--card) px-2 text-xs outline-none focus:ring-2 focus:ring-(--ring)"
                          value={statusDraft[item.id] || item.status}
                          onChange={(event) =>
                            setStatusDraft((prev) => ({ ...prev, [item.id]: event.target.value }))
                          }
                        >
                          <option value="draft">Draft</option>
                          <option value="signed">Signed</option>
                          <option value="dispatched">Dispatched</option>
                        </select>
                        <Button size="sm" variant="outline" onClick={() => updateFir(item.id)}>
                          Save
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Link href={`/admin/fir/${item.id}`}>
                        <Button size="sm" variant="outline">View</Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
                {!firs.length ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-(--muted-foreground)">No FIR records.</TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
      {loading && !firs?.length ? <LoadingOverlay label="Loading FIR records..." /> : null}
      </div>
    </AdminRoute>
  );
}
