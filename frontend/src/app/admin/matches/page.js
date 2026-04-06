"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import AdminRoute from "@/components/AdminRoute";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAdminStore } from "@/lib/adminStore";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

export default function AdminMatchesPage() {
  const matches = useAdminStore((state) => state.matches);
  const pendingMatches = useAdminStore((state) => state.pendingMatches);
  const loading = useAdminStore((state) => state.loading);
  const startAutoRefresh = useAdminStore((state) => state.startAutoRefresh);
  const stopAutoRefresh = useAdminStore((state) => state.stopAutoRefresh);

  useEffect(() => {
    startAutoRefresh();
    return () => {
      stopAutoRefresh();
    };
  }, [startAutoRefresh, stopAutoRefresh]);

  return (
    <AdminRoute>
      <div className="relative">
      <main className="space-y-6">
        <section className="grid gap-3 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Pending Human Review</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">{pendingMatches?.review_needed ?? 0}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Auto-Confirmed Awaiting Signoff</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">{pendingMatches?.auto_pending_signoff ?? 0}</p>
            </CardContent>
          </Card>
        </section>

        <Card>
          <CardHeader>
            <CardTitle>All Matches</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Match ID</TableHead>
                  <TableHead>Person Name</TableHead>
                  <TableHead>Confidence %</TableHead>
                  <TableHead>Sighting City</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {matches.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.id}</TableCell>
                    <TableCell>{item.person_name || "-"}</TableCell>
                    <TableCell>
                      <Badge variant={item.confidence > 0.85 ? "success" : item.confidence > 0.75 ? "warning" : "default"}>
                        {(item.confidence * 100).toFixed(2)}%
                      </Badge>
                    </TableCell>
                    <TableCell>{item.sighting_city || "-"}</TableCell>
                    <TableCell className="capitalize">{item.status}</TableCell>
                    <TableCell>{new Date(item.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Link href={`/admin/matches/${item.id}`}>
                        <Button size="sm" variant="outline">Review</Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
                {!matches.length ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-(--muted-foreground)">No matches available.</TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
      {loading && !matches?.length ? <LoadingOverlay label="Loading matches..." /> : null}
      </div>
    </AdminRoute>
  );
}
