"use client";

import Link from "next/link";
import { useEffect } from "react";
import AdminRoute from "@/components/AdminRoute";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAdminStore } from "@/lib/adminStore";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

export default function AdminSightingsPage() {
  const sightings = useAdminStore((state) => state.sightings);
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
        <Card>
          <CardHeader>
            <CardTitle>All Sightings</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sighting ID</TableHead>
                  <TableHead>City</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Matches Found</TableHead>
                  <TableHead>Submitted By</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sightings.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.id}</TableCell>
                    <TableCell>{item.city || "-"}</TableCell>
                    <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                    <TableCell>{item.matches_found}</TableCell>
                    <TableCell>{item.submitted_by || "Anonymous"}</TableCell>
                    <TableCell>
                      <Link href={`/admin/sightings/${item.id}`} className="text-sm text-(--primary) hover:underline">
                        View Detail
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
                {!sightings.length ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-(--muted-foreground)">No sightings available.</TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
      {loading && !sightings?.length ? <LoadingOverlay label="Loading sightings..." /> : null}
      </div>
    </AdminRoute>
  );
}
