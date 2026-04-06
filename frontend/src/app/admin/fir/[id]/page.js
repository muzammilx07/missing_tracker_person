"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { toast } from "react-toastify";
import AdminRoute from "@/components/AdminRoute";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import LoadingOverlay from "@/components/ui/LoadingOverlay";
import { Input } from "@/components/ui/input";

const FirStationsMap = dynamic(() => import("@/components/FirStationsMap"), { ssr: false });

export default function AdminFirDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;

  const [fir, setFir] = useState(null);
  const [selectedStationOsmId, setSelectedStationOsmId] = useState("");
  const [searchingStations, setSearchingStations] = useState(false);
  const baseApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const load = async () => {
    try {
      const response = await api.get(`/fir/${id}`);
      setFir(response.data);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Unable to fetch FIR");
    }
  };

  useEffect(() => {
    if (!id) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (fir?.nearest_stations?.length && !selectedStationOsmId) {
      setSelectedStationOsmId(String(fir.nearest_stations[0].osm_id));
    }
  }, [fir, selectedStationOsmId]);

  const signFir = async () => {
    try {
      await api.post(`/fir/${id}/sign`);
      toast.success("FIR signed");
      load();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Sign failed");
    }
  };

  const dispatchFirAuto = async () => {
    try {
      const response = await api.post(`/fir/${id}/dispatch-auto`);
      toast.success(response?.data?.message || "FIR dispatched");
      load();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Dispatch failed");
    }
  };

  const forwardFirToSelectedStation = async () => {
    if (!selectedStationOsmId) {
      toast.error("Select a station first");
      return;
    }

    try {
      if ((fir?.fir_status || fir?.status) === "draft") {
        await api.post(`/fir/${id}/sign`);
      }
      const response = await api.post(`/fir/${id}/dispatch`, null, {
        params: { station_osm_id: selectedStationOsmId },
      });
      toast.success(response?.data?.message || "FIR forwarded successfully");
      load();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Forward failed");
    }
  };

  const searchStationsFromFirLocation = async () => {
    if (!fir?.case_id) {
      toast.error("Case location unavailable for this FIR");
      return;
    }

    setSearchingStations(true);
    try {
      const response = await api.get(`/cases/${fir.case_id}/police-stations`, {
        params: { radius_km: 7, limit: 5 },
      });

      const nearby = response?.data?.stations || [];
      const message = response?.data?.message;
      setFir((prev) => ({
        ...prev,
        nearest_stations: nearby,
      }));

      if (nearby.length) {
        setSelectedStationOsmId(String(nearby[0].osm_id));
        toast.success(`Found ${nearby.length} nearby station(s)`);
      } else {
        toast.info(message || "No nearby stations found");
      }
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to search nearby stations");
    } finally {
      setSearchingStations(false);
    }
  };

  return (
    <AdminRoute>
      <div className="relative">
      <main className="space-y-6">
        <Button variant="outline" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <Card>
          <CardHeader><CardTitle>FIR Detail #{id}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
          {fir ? (
            <>
              <p>FIR Number: {fir.fir_number || fir.fir_id}</p>
              <p>Case Number: {fir.case_number || fir.case_id}</p>
              <p>Status: {fir.fir_status || fir.status}</p>
              <p>Generated At: {(fir.generated_at || fir.created_at) ? new Date(fir.generated_at || fir.created_at).toLocaleString() : "-"}</p>
              <p>Signed By: {fir.signed_by || "Not signed"}</p>
              <p>Missing Person: {fir?.missing_person?.name || "-"}</p>
              <p>Last Seen: {fir?.missing_person?.city || "-"}{fir?.missing_person?.state ? `, ${fir.missing_person.state}` : ""}</p>
              <p>Location Source: {fir?.station_search_location_source || fir?.location?.source || "unknown"}</p>
              <p>
                Dispatch Coordinates: {fir?.location?.lat ?? "-"}, {fir?.location?.lng ?? "-"}
              </p>

              <div className="flex flex-wrap gap-2">
                <Button type="button" onClick={signFir}>Sign</Button>
                <Button type="button" variant="outline" onClick={forwardFirToSelectedStation}>Forward to Selected Station</Button>
                <Button type="button" variant="outline" onClick={dispatchFirAuto}>Auto Dispatch</Button>
                <Button type="button" variant="outline" onClick={searchStationsFromFirLocation} disabled={searchingStations}>
                  {searchingStations ? "Searching..." : "Search Nearby Stations"}
                </Button>
                {fir.download_url || fir.pdf_url ? (
                  <a href={(fir.download_url || "").startsWith("http") ? fir.download_url : `${baseApiUrl}${fir.download_url || fir.pdf_url}`} target="_blank" rel="noreferrer">
                    <Button type="button" variant="outline">Download</Button>
                  </a>
                ) : null}
              </div>

              <div className="space-y-2 rounded-md border border-(--border) bg-(--muted) p-3">
                <p className="text-sm font-semibold">Forwarding Station</p>
                <Input
                  value={selectedStationOsmId}
                  onChange={(event) => setSelectedStationOsmId(event.target.value)}
                  placeholder="Select from nearest stations below"
                />
              </div>

              {fir?.dispatches?.length ? (
                <div className="space-y-2 rounded-md border border-(--border) bg-(--muted) p-3">
                  <p className="text-sm font-semibold">Dispatched Stations</p>
                  {fir.dispatches.map((item) => (
                    <div key={item.dispatch_id} className="rounded-md border border-(--border) bg-(--card) p-2 text-sm">
                      <p>{item.station_name}</p>
                      <p className="text-xs text-(--muted-foreground)">Status: {item.dispatch_status}</p>
                    </div>
                  ))}
                </div>
              ) : null}

              {fir?.nearest_stations?.length ? (
                <div className="space-y-2 rounded-md border border-(--border) bg-(--muted) p-3">
                  <p className="text-sm font-semibold">Nearest Available Stations</p>
                  {fir.nearest_stations.slice(0, 3).map((station) => (
                    <button
                      key={station.osm_id}
                      type="button"
                      onClick={() => setSelectedStationOsmId(String(station.osm_id))}
                      className="block w-full rounded-md border border-(--border) bg-(--card) p-2 text-left text-sm hover:bg-(--secondary)"
                    >
                      <p>{station.name}</p>
                      <p className="text-xs text-(--muted-foreground)">{station.address || "Address unavailable"}</p>
                    </button>
                  ))}

                  <div className="pt-2">
                    <FirStationsMap stations={fir.nearest_stations.slice(0, 3)} />
                  </div>
                </div>
              ) : null}
            </>
          ) : (
            <div className="space-y-2">
              {[...Array(6)].map((_, idx) => (
                <div key={idx} className="h-5 animate-pulse rounded-md bg-(--muted)" />
              ))}
            </div>
          )}
          </CardContent>
        </Card>
      </main>
      {!fir ? <LoadingOverlay label="Loading FIR..." /> : null}
      </div>
    </AdminRoute>
  );
}
