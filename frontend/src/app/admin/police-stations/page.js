"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { toast } from "react-toastify";
import AdminRoute from "@/components/AdminRoute";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const FirStationsMap = dynamic(() => import("@/components/FirStationsMap"), { ssr: false });
const MapPicker = dynamic(() => import("@/components/MapPicker"), { ssr: false });

export default function AdminPoliceStationsPage() {
  const [coords, setCoords] = useState({ latitude: "", longitude: "", radius_km: "5", limit: "10" });
  const [caseQuery, setCaseQuery] = useState({ caseId: "", radius_km: "5", limit: "10" });
  const [stations, setStations] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);

  const searchByCoords = async () => {
    if (!coords.latitude || !coords.longitude) {
      toast.error("Latitude and longitude are required");
      return;
    }

    setLoading(true);
    try {
      const response = await api.get("/police-stations", { params: coords });
      setStations(response?.data?.stations || []);
      setMeta(response?.data || null);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to load stations");
      setStations([]);
      setMeta(null);
    } finally {
      setLoading(false);
    }
  };

  const searchByCase = async () => {
    if (!caseQuery.caseId) {
      toast.error("Case ID is required");
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(`/cases/${caseQuery.caseId}/police-stations`, {
        params: { radius_km: caseQuery.radius_km, limit: caseQuery.limit },
      });
      setStations(response?.data?.stations || []);
      setMeta(response?.data || null);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to load case stations");
      setStations([]);
      setMeta(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminRoute>
      <main className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Find Nearby Police Stations By Map</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <MapPicker
              onLocationSelect={(location) =>
                setCoords((prev) => ({
                  ...prev,
                  latitude: String(location.lat),
                  longitude: String(location.lng),
                }))
              }
              initialZoom={7}
            />

            <div className="grid gap-3 md:grid-cols-2">
              <Input
                placeholder="Radius km"
                value={coords.radius_km}
                onChange={(event) => setCoords((prev) => ({ ...prev, radius_km: event.target.value }))}
              />
              <Input
                placeholder="Limit"
                value={coords.limit}
                onChange={(event) => setCoords((prev) => ({ ...prev, limit: event.target.value }))}
              />
            </div>
            <p className="text-xs text-(--muted-foreground)">
              Pin a location on map, then search nearby stations.
            </p>
            <Button onClick={searchByCoords} disabled={loading}>Search Nearby Stations</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Find Stations By Case</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
              <Input
                placeholder="Case ID"
                value={caseQuery.caseId}
                onChange={(event) => setCaseQuery((prev) => ({ ...prev, caseId: event.target.value }))}
              />
              <Input
                placeholder="Radius km"
                value={caseQuery.radius_km}
                onChange={(event) => setCaseQuery((prev) => ({ ...prev, radius_km: event.target.value }))}
              />
              <Input
                placeholder="Limit"
                value={caseQuery.limit}
                onChange={(event) => setCaseQuery((prev) => ({ ...prev, limit: event.target.value }))}
              />
            </div>
            <Button variant="outline" onClick={searchByCase} disabled={loading}>Search By Case</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {meta ? (
              <p className="text-sm text-(--muted-foreground)">
                Found {meta.count || 0} station(s)
                {meta.radius_km ? ` within ${meta.radius_km}km` : ""}
                {meta.location?.city ? ` near ${meta.location.city}` : ""}
              </p>
            ) : null}

            {stations.length ? (
              <>
                <div className="space-y-2">
                  {stations.map((station) => (
                    <article key={String(station.osm_id || station.name)} className="rounded-md border border-(--border) bg-(--card) p-3">
                      <p className="font-semibold">{station.name || "Police Station"}</p>
                      <p className="text-sm text-(--muted-foreground)">{station.address || "Address unavailable"}</p>
                      <p className="text-xs text-(--muted-foreground)">
                        {station.distance_km ? `Distance: ${station.distance_km}km` : ""}
                      </p>
                    </article>
                  ))}
                </div>
                <FirStationsMap stations={stations} />
              </>
            ) : (
              <p className="text-sm text-(--muted-foreground)">No stations loaded yet.</p>
            )}
          </CardContent>
        </Card>
      </main>
    </AdminRoute>
  );
}
