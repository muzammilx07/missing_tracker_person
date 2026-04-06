"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { toast } from "react-toastify";
import AdminRoute from "@/components/AdminRoute";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function AdminSightingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!id) return;

    let active = true;

    const load = async () => {
      try {
        const response = await api.get(`/sightings/${id}`);
        if (active) setData(response.data);
      } catch (error) {
        toast.error(error?.response?.data?.detail || "Failed to load sighting");
        if (active) setData(null);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, [id]);

  return (
    <AdminRoute>
      <div className="relative">
        <main className="space-y-6">
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>

          <Card>
            <CardHeader>
              <CardTitle>Sighting Detail #{id}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {data ? (
                <>
                  <p>Reporter: {data.reporter_name || "Anonymous"}</p>
                  <p>Phone: {data.reporter_phone || "-"}</p>
                  <p>Status: {data.status || "-"}</p>
                  <p>City: {data.city || "-"}</p>
                  <p>State: {data.state || "-"}</p>
                  <p>Address: {data.address || "-"}</p>
                  <p>Coordinates: {data.lat}, {data.lng}</p>
                  <p>Reported At: {data.created_at ? new Date(data.created_at).toLocaleString() : "-"}</p>
                </>
              ) : (
                <p className="text-sm text-(--muted-foreground)">No sighting data loaded.</p>
              )}
            </CardContent>
          </Card>

          {data?.photo_url ? (
            <Card>
              <CardHeader>
                <CardTitle>Photo</CardTitle>
              </CardHeader>
              <CardContent>
                <img src={data.photo_url} alt="Sighting" className="max-h-96 rounded-md border border-(--border) object-cover" />
              </CardContent>
            </Card>
          ) : null}

          {data?.lat && data?.lng ? (
            <Card>
              <CardHeader>
                <CardTitle>Location</CardTitle>
              </CardHeader>
              <CardContent>
                <MapView lat={data.lat} lng={data.lng} label={data.city || "Sighting"} />
              </CardContent>
            </Card>
          ) : null}
        </main>
        {!data ? <LoadingOverlay label="Loading sighting..." /> : null}
      </div>
    </AdminRoute>
  );
}
