"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "react-toastify";
import AdminRoute from "@/components/AdminRoute";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import api from "@/lib/api";
import { useAdminStore } from "@/lib/adminStore";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

export default function AdminVolunteersPage() {
  const [tab, setTab] = useState("pending");
  const [caseSelection, setCaseSelection] = useState({});
  const data = useAdminStore((state) => state.volunteers);
  const cases = useAdminStore((state) => state.cases);
  const loading = useAdminStore((state) => state.loading);
  const startAutoRefresh = useAdminStore((state) => state.startAutoRefresh);
  const stopAutoRefresh = useAdminStore((state) => state.stopAutoRefresh);
  const loadAdminData = useAdminStore((state) => state.loadAdminData);

  useEffect(() => {
    startAutoRefresh();
    return () => stopAutoRefresh();
  }, [startAutoRefresh, stopAutoRefresh]);

  const visibleRows = useMemo(() => {
    if (tab === "pending") return data.pending || [];
    return data.approved || [];
  }, [tab, data]);

  const actionVolunteer = async (id, action) => {
    try {
      await api.patch(`/volunteers/${id}/approve`, { action });
      toast.success(`Volunteer ${action}d`);
      loadAdminData();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Volunteer action failed");
    }
  };

  const assignVolunteer = async (userId) => {
    const caseId = caseSelection[userId];
    if (!caseId) {
      toast.error("Select a case first");
      return;
    }

    try {
      await api.post(`/admin/volunteers/${userId}/assign/${caseId}`);
      toast.success("Volunteer assigned to case");
      loadAdminData();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Assignment failed");
    }
  };

  const unassignVolunteer = async (userId) => {
    const caseId = caseSelection[userId];
    if (!caseId) {
      toast.error("Select a case first");
      return;
    }

    try {
      await api.delete(`/admin/volunteers/${userId}/assign/${caseId}`);
      toast.success("Volunteer removed from case");
      loadAdminData();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Unassign failed");
    }
  };

  const banVolunteer = async (volunteerId) => {
    const confirmed = window.confirm("Ban this volunteer profile?");
    if (!confirmed) return;

    try {
      await api.patch(`/admin/volunteers/${volunteerId}/ban`);
      toast.success("Volunteer banned");
      loadAdminData();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Ban failed");
    }
  };

  return (
    <AdminRoute>
      <div className="relative">
      <main className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Volunteer Management</CardTitle>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button variant={tab === "pending" ? "default" : "outline"} onClick={() => setTab("pending")}>Pending Applications</Button>
            <Button variant={tab === "approved" ? "default" : "outline"} onClick={() => setTab("approved")}>Approved Volunteers</Button>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Coverage</TableHead>
                  <TableHead>Bio</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visibleRows.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <p className="font-medium">{item.name}</p>
                      <p className="text-xs text-slate-500">{item.email}</p>
                    </TableCell>
                    <TableCell>{item.coverage || "-"}</TableCell>
                    <TableCell>{item.bio || "-"}</TableCell>
                    <TableCell className="capitalize">{item.status}</TableCell>
                    <TableCell>
                      {tab === "pending" ? (
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => actionVolunteer(item.id, "approve")}>Approve</Button>
                          <Button size="sm" variant="outline" onClick={() => actionVolunteer(item.id, "reject")}>Reject</Button>
                        </div>
                      ) : (
                        <div className="flex flex-wrap items-center gap-2">
                          <select
                            className="h-9 rounded-md border border-(--border) bg-(--card) px-2 text-xs outline-none focus:ring-2 focus:ring-(--ring)"
                            value={caseSelection[item.user_id] || ""}
                            onChange={(event) =>
                              setCaseSelection((prev) => ({ ...prev, [item.user_id]: event.target.value }))
                            }
                          >
                            <option value="">Select case</option>
                            {(cases || []).map((caseItem) => (
                              <option key={caseItem.id} value={caseItem.id}>
                                {caseItem.case_number || `Case ${caseItem.id}`}
                              </option>
                            ))}
                          </select>
                          <Button size="sm" variant="outline" onClick={() => assignVolunteer(item.user_id)}>
                            Assign
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => unassignVolunteer(item.user_id)}>
                            Remove
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => banVolunteer(item.id)}>
                            Ban
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {!visibleRows.length ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-(--muted-foreground)">No volunteer records.</TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
      {loading && !(data?.pending?.length || data?.approved?.length) ? <LoadingOverlay label="Loading volunteers..." /> : null}
      </div>
    </AdminRoute>
  );
}
