"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Gauge, MapPin, ShieldCheck } from "lucide-react";
import { toast } from "react-toastify";
import AdminRoute from "@/components/AdminRoute";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function AdminMatchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;

  const [data, setData] = useState(null);
  const [firId, setFirId] = useState("");
  const [dispatches, setDispatches] = useState([]);

  const load = async () => {
    const response = await api.get(`/matches/${id}`);
    setData(response.data);
  };

  useEffect(() => {
    if (!id) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const review = async (action) => {
    try {
      await api.patch(`/matches/${id}/review`, { action });
      toast.success(`Match ${action}ed`);
      load();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Action failed");
    }
  };

  const generateFir = async () => {
    try {
      const response = await api.post(`/fir/generate/${data.case_id}`);
      setFirId(String(response.data.fir_id || response.data.id || ""));
      toast.success("FIR generated");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to generate FIR");
    }
  };

  const dispatchToPolice = async () => {
    if (!firId) {
      toast.error("Provide FIR id first");
      return;
    }

    try {
      try {
        await api.post(`/fir/${firId}/sign`);
      } catch (signError) {
        const detail = signError?.response?.data?.detail || "";
        if (!detail.includes("cannot sign")) {
          throw signError;
        }
      }

      const response = await api.post(`/fir/${firId}/dispatch-auto`);
      setDispatches(response.data.dispatches || []);
      toast.success("Dispatched to nearest police stations");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Dispatch failed");
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
          <CardHeader><CardTitle>Match Review #{id}</CardTitle></CardHeader>
          <CardContent className="space-y-2">
          {data ? (
            <>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-md border border-(--border) bg-(--muted) p-3">
                  <p className="text-xs text-(--muted-foreground)">Case</p>
                  <p className="font-semibold">{data.case_number}</p>
                </div>
                <div className="rounded-md border border-(--border) bg-(--muted) p-3">
                  <p className="text-xs text-(--muted-foreground)">Missing Person</p>
                  <p className="font-semibold">{data?.missing_person?.name || "-"}</p>
                </div>
                <div className="rounded-md border border-(--border) bg-(--muted) p-3">
                  <p className="inline-flex items-center gap-2 text-xs text-(--muted-foreground)"><Gauge className="h-3 w-3" /> Confidence</p>
                  <p className="text-xl font-semibold text-emerald-700">{(data.confidence * 100).toFixed(2)}%</p>
                </div>
                <div className="rounded-md border border-(--border) bg-(--muted) p-3">
                  <p className="text-xs text-(--muted-foreground)">Status</p>
                  <p className="font-semibold capitalize">{data.status}</p>
                </div>
              </div>
            </>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {[...Array(4)].map((_, idx) => (
                <div key={idx} className="h-16 animate-pulse rounded-md bg-(--muted)" />
              ))}
            </div>
          )}
          </CardContent>
        </Card>

        {data ? (
          <Card>
            <CardHeader><CardTitle>Side-by-side Review</CardTitle></CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="rounded-md border border-(--border) bg-(--muted) p-3 text-sm">
                <p className="mb-2 font-semibold">Missing Person Profile</p>
                <p>Name: {data?.missing_person?.name || "-"}</p>
                <p>City: {data?.missing_person?.city || "-"}</p>
                <p>State: {data?.missing_person?.state || "-"}</p>
              </div>
              <div className="rounded-md border border-(--border) bg-(--muted) p-3 text-sm">
                <p className="mb-2 font-semibold">Sighting Snapshot</p>
                <p>City: {data?.sighting?.city || "-"}</p>
                <p className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" /> {data?.sighting?.lat || "-"}, {data?.sighting?.lng || "-"}</p>
                <p>Reported: {data?.sighting?.created_at ? new Date(data.sighting.created_at).toLocaleString() : "-"}</p>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {data?.sighting ? (
          <Card>
            <CardHeader><CardTitle>Sighting Location</CardTitle></CardHeader>
            <CardContent>
            <MapView
              lat={data.sighting.lat}
              lng={data.sighting.lng}
              label={data.sighting.city || "Sighting"}
            />
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardHeader><CardTitle>Actions</CardTitle></CardHeader>
          <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={() => review("confirm")}>Confirm</Button>
            <Button type="button" variant="outline" onClick={() => review("reject")}>Reject</Button>
            <Button type="button" onClick={generateFir}>Generate FIR</Button>
          </div>

          <label className="text-sm font-medium">
            FIR ID
            <Input value={firId} onChange={(event) => setFirId(event.target.value)} />
          </label>

          <Button type="button" onClick={dispatchToPolice}>
            <ShieldCheck className="mr-2 h-4 w-4" />
            Dispatch to Police
          </Button>

          {firId ? (
            <Link href={`/admin/fir/${firId}`}>Open FIR Detail</Link>
          ) : null}

          {dispatches.length ? (
            <div className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm">
              <p className="font-semibold">Nearest Stations Dispatched</p>
              {dispatches.map((item) => (
                <div key={item.dispatch_id} className="rounded-md border border-(--border) bg-(--card) p-2">
                  <p className="font-medium">{item.station_name}</p>
                  <p className="text-xs text-(--muted-foreground)">{item.station_address || "Address unavailable"}</p>
                </div>
              ))}
            </div>
          ) : null}
          </CardContent>
        </Card>
      </main>
      {!data ? <LoadingOverlay label="Loading match..." /> : null}
      </div>
    </AdminRoute>
  );
}
