"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Clock3, MapPin, Sparkles } from "lucide-react";
import { toast } from "react-toastify";
import ProtectedRoute from "@/components/ProtectedRoute";
import StatusBadge from "@/components/StatusBadge";
import api from "@/lib/api";
import { getRole, getUser } from "@/lib/auth";
import EmailUserPicker from "@/components/EmailUserPicker";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;

  const [caseData, setCaseData] = useState(null);
  const [realtime, setRealtime] = useState(null);
  const [selectedFamilyUsers, setSelectedFamilyUsers] = useState([]);

  useEffect(() => {
    if (!id) return;

    let active = true;

    const loadBase = async () => {
      try {
        const response = await api.get(`/cases/${id}`);
        if (active) setCaseData(response.data);
      } catch {
        if (active) setCaseData(null);
      }
    };

    const loadRealtime = async () => {
      try {
        const response = await api.get(`/cases/${id}/realtime`);
        if (active) setRealtime(response.data);
      } catch {
        if (active) setRealtime(null);
      }
    };

    loadBase();
    loadRealtime();
    const timer = setInterval(loadRealtime, 30000);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [id]);

  const currentUser = getUser();
  const isAdmin = getRole() === "admin";
  const canManageFamily = Boolean(currentUser?.id || isAdmin);

  const addFamilyMember = async (user) => {
    try {
      await api.post(`/cases/${id}/family`, { email: user.email });
      setSelectedFamilyUsers((prev) => [...prev, user]);
      toast.success("Family member added");
      const response = await api.get(`/cases/${id}`);
      setCaseData(response.data);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to add family member");
    }
  };

  const removeFamilyMember = async (userId) => {
    try {
      await api.delete(`/cases/${id}/family/${userId}`);
      setSelectedFamilyUsers((prev) => prev.filter((item) => item.id !== userId));
      toast.success("Family member removed");
      const response = await api.get(`/cases/${id}`);
      setCaseData(response.data);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to remove family member");
    }
  };

  return (
    <ProtectedRoute>
      <div className="relative">
      <main className="space-y-6">
        <Button variant="outline" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <div className="grid gap-4 xl:grid-cols-5">
          <Card className="xl:col-span-2">
            <CardHeader><CardTitle>Missing Person</CardTitle></CardHeader>
            <CardContent>
              {caseData?.missing_person?.photo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={caseData.missing_person.photo_url}
                  alt="Missing person"
                  className="h-80 w-full rounded-md object-cover"
                />
              ) : (
                <div className="grid h-80 place-items-center rounded-md border border-dashed border-(--border) text-sm text-(--muted-foreground)">
                  No image available
                </div>
              )}

              <div className="mt-4 grid gap-2 rounded-md bg-(--muted) p-3 text-sm">
                <p className="font-semibold">Quick Info</p>
                <p>Name: {caseData?.missing_person?.name || "-"}</p>
                <p>City: {caseData?.missing_person?.city || "-"}</p>
                <p>Status: <StatusBadge status={caseData?.status} /></p>
              </div>
            </CardContent>
          </Card>

          <Card className="xl:col-span-3">
            <CardHeader><CardTitle>Case Details</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {caseData ? (
                <>
                  <div className="grid gap-3 md:grid-cols-2">
                    <Info label="Case Number" value={caseData.case_number} />
                    <Info label="Person" value={caseData?.missing_person?.name || "-"} />
                    <Info label="Age" value={caseData?.missing_person?.age || "-"} />
                    <Info
                      label="Location"
                      value={`${caseData?.missing_person?.city || "-"}${caseData?.missing_person?.state ? `, ${caseData.missing_person.state}` : ""}`}
                    />
                    <Info label="Created" value={new Date(caseData.created_at).toLocaleString()} />
                    <div className="rounded-md border border-(--border) bg-(--muted) p-3">
                      <p className="text-xs text-(--muted-foreground)">Status</p>
                      <div className="mt-1"><StatusBadge status={caseData.status} /></div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {[...Array(6)].map((_, idx) => (
                    <div key={idx} className="h-16 animate-pulse rounded-md bg-(--muted)" />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader><CardTitle>Timeline</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {(realtime?.timeline || []).map((item, index) => (
              <div key={`${item.time}-${index}`} className="timeline-line pb-4">
                <p className="font-medium">{item.event}</p>
                <small className="inline-flex items-center gap-1 text-xs text-(--muted-foreground)">
                  <Clock3 className="h-3 w-3" />
                  {new Date(item.time).toLocaleString()}
                </small>
              </div>
            ))}
            {!realtime?.timeline?.length ? <p className="text-sm text-(--muted-foreground)">No timeline events.</p> : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Matches</CardTitle></CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {(caseData?.matches || []).map((item) => (
              <div key={item.id} className="hover-card rounded-md border border-(--border) bg-(--card) p-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium">Match #{item.id}</p>
                  <Badge variant={item.confidence >= 0.85 ? "success" : "warning"}>
                    {(item.confidence * 100).toFixed(1)}%
                  </Badge>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <Badge variant={item.confidence > 0.8 ? "success" : "warning"}>{item.label}</Badge>
                  <StatusBadge status={item.status} />
                </div>
                <p className="mt-3 inline-flex items-center gap-1 text-xs text-(--muted-foreground)">
                  <MapPin className="h-3 w-3" />
                  {item.sighting_city || realtime?.last_sighting?.city || "Unknown"}
                </p>
                <p className="mt-2 inline-flex items-center gap-1 text-xs text-(--muted-foreground)">
                  <Sparkles className="h-3 w-3" />
                  Confidence-driven review required for escalation
                </p>
              </div>
            ))}
            {!caseData?.matches?.length ? <p className="text-sm text-(--muted-foreground)">No matches yet.</p> : null}
          </CardContent>
        </Card>

        {canManageFamily ? (
          <Card>
            <CardHeader>
              <CardTitle>Family Access</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-(--muted-foreground)">
                Add or remove family members who can view this case. Current count: {caseData?.family_member_count ?? 0}
              </p>
              <EmailUserPicker
                selectedUsers={selectedFamilyUsers}
                onSelectUser={addFamilyMember}
                onRemoveUser={removeFamilyMember}
              />
            </CardContent>
          </Card>
        ) : null}
      </main>
      {!caseData ? <LoadingOverlay label="Loading case data..." /> : null}
      </div>
    </ProtectedRoute>
  );
}

function Info({ label, value }) {
  return (
    <div className="rounded-md border border-(--border) bg-(--muted) p-3">
      <p className="text-xs text-(--muted-foreground)">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}
