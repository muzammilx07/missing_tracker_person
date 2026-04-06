"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "react-toastify";
import { ImagePlus, Sparkles, UploadCloud } from "lucide-react";
import api from "@/lib/api";
import ProtectedRoute from "@/components/ProtectedRoute";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import StepIndicator from "@/components/StepIndicator";
import EmailUserPicker from "@/components/EmailUserPicker";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

const INITIAL = {
  full_name: "",
  age: "",
  gender: "",
  last_seen_date: "",
  last_seen_city: "",
  last_seen_state: "",
  last_seen_address: "",
  description: "",
  police_dispatch_mode: "manual",
  family_emails: "",
};

export default function NewCasePage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [photo, setPhoto] = useState(null);
  const [photoValidation, setPhotoValidation] = useState(null);
  const [validatingPhoto, setValidatingPhoto] = useState(false);
  const [selectedFamilyUsers, setSelectedFamilyUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  const setField = (name, value) => {
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const validatePhoto = async (file) => {
    const data = new FormData();
    data.append("image", file);
    setValidatingPhoto(true);
    try {
      const response = await api.post("/ai/validate-photo", data);
      setPhotoValidation(response.data);
      if (!response.data.is_person) {
        toast.error("Please upload a clear photo of a person");
      }
    } catch {
      setPhotoValidation({ is_person: false, confidence: 0 });
      toast.error("Could not validate image");
    } finally {
      setValidatingPhoto(false);
    }
  };

  const handleFile = (file) => {
    if (!file) return;
    setPhoto(file);
    setPhotoValidation(null);
    validatePhoto(file);
  };

  const submitCase = async () => {
    if (!photo) {
      toast.error("Photo is required");
      return;
    }

    if (!photoValidation?.is_person) {
      toast.error("Please upload a clear photo of a person");
      return;
    }

    setLoading(true);

    try {
      const payload = new FormData();
      payload.append("photo", photo);
      payload.append("full_name", form.full_name);
      payload.append("last_seen_city", form.last_seen_city);
      payload.append("police_dispatch_mode", form.police_dispatch_mode);

      if (form.age) payload.append("age", form.age);
      if (form.gender) payload.append("gender", form.gender);
      if (form.last_seen_date) payload.append("last_seen_date", form.last_seen_date);
      if (form.last_seen_state) payload.append("last_seen_state", form.last_seen_state);
      if (form.last_seen_address) payload.append("last_seen_address", form.last_seen_address);
      if (form.description) payload.append("description", form.description);

      const response = await api.post("/cases", payload);
      const caseId = response.data.case_id;

      const familyEmails = selectedFamilyUsers.map((item) => item.email);

      for (const email of familyEmails) {
        try {
          await api.post(`/cases/${caseId}/family`, { email });
        } catch {
          // Keep going even if one email fails.
        }
      }

      toast.success("Case created successfully");
      router.replace(`/cases/${caseId}`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to create case");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="relative">
      <main className="mx-auto mt-6 max-w-4xl space-y-6">
        <Card className="surface-grid">
          <CardHeader>
            <CardTitle>Create New Case</CardTitle>
            <CardDescription>Step-based flow for details, photo validation, and response settings.</CardDescription>
          </CardHeader>
          <CardContent>
            <StepIndicator steps={["Details", "Photo", "Settings"]} current={step} />
          </CardContent>
        </Card>

        {step === 1 ? (
          <Card className="fade-up">
            <CardHeader>
              <CardTitle>Step 1: Person details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-sm font-medium">Full Name</label>
                  <Input value={form.full_name} onChange={(event) => setField("full_name", event.target.value)} />
                  {errors.full_name ? <p className="text-xs text-red-600">{errors.full_name}</p> : null}
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Age</label>
                  <Input value={form.age} onChange={(event) => setField("age", event.target.value)} type="number" />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Gender</label>
                  <select
                    className="h-11 w-full rounded-xl border border-(--border) bg-(--card) px-3 text-sm outline-none focus:ring-2 focus:ring-(--ring)"
                    value={form.gender}
                    onChange={(event) => setField("gender", event.target.value)}
                  >
                    <option value="">Select</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Last Seen Date</label>
                  <Input type="date" value={form.last_seen_date} onChange={(event) => setField("last_seen_date", event.target.value)} />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Last Seen City</label>
                  <Input value={form.last_seen_city} onChange={(event) => setField("last_seen_city", event.target.value)} />
                  {errors.last_seen_city ? <p className="text-xs text-red-600">{errors.last_seen_city}</p> : null}
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Last Seen State</label>
                  <Input value={form.last_seen_state} onChange={(event) => setField("last_seen_state", event.target.value)} />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">Last Seen Address</label>
                <Input value={form.last_seen_address} onChange={(event) => setField("last_seen_address", event.target.value)} />
                <p className="text-xs text-(--muted-foreground)">Optional but improves nearby police station matching.</p>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">Description</label>
                <Textarea rows={4} value={form.description} onChange={(event) => setField("description", event.target.value)} />
              </div>

              <Button
                className="w-full"
                onClick={() => {
                  const nextErrors = {};
                  if (!form.full_name.trim()) nextErrors.full_name = "Full name is required";
                  if (!form.last_seen_city.trim()) nextErrors.last_seen_city = "City is required";
                  setErrors(nextErrors);
                  if (!Object.keys(nextErrors).length) setStep(2);
                }}
              >
                Continue
              </Button>
            </CardContent>
          </Card>
        ) : null}

        {step === 2 ? (
          <Card className="fade-up">
            <CardHeader>
              <CardTitle>Step 2: Upload photo</CardTitle>
              <CardDescription>AI checks whether photo clearly contains a person.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <label
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => {
                  event.preventDefault();
                  handleFile(event.dataTransfer.files?.[0] || null);
                }}
                className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-(--border) bg-(--muted) text-center"
              >
                <UploadCloud className="mb-2 h-6 w-6 text-(--primary)" />
                <p className="font-medium">Drop image here or click to upload</p>
                <p className="text-sm text-(--muted-foreground)">PNG/JPG recommended</p>
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(event) => handleFile(event.target.files?.[0] || null)}
                />
              </label>

              {photo ? (
                <p className="inline-flex items-center gap-2 rounded-xl bg-(--muted) px-3 py-1 text-sm">
                  <ImagePlus className="h-4 w-4 text-(--primary)" />
                  {photo.name}
                </p>
              ) : null}

              {validatingPhoto ? (
                <div className="rounded-xl border border-(--border) bg-(--muted) p-3 text-sm text-(--muted-foreground)">
                  AI validation in progress...
                </div>
              ) : null}

              {photoValidation && !photoValidation.is_person ? (
                <p className="text-sm text-red-600">Please upload a clear photo of a person</p>
              ) : null}

              {photoValidation?.is_person && photoValidation.confidence < 0.6 ? (
                <Badge variant="warning">Low confidence image quality</Badge>
              ) : null}

              {photoValidation?.is_person && photoValidation.confidence >= 0.6 ? (
                <div className="rounded-xl border border-emerald-300/50 bg-emerald-200/20 p-3 text-sm text-emerald-700">
                  <p className="inline-flex items-center gap-2 font-medium"><Sparkles className="h-4 w-4" />AI validation passed</p>
                  <p className="mt-1">Confidence: {(photoValidation.confidence * 100).toFixed(1)}%</p>
                </div>
              ) : null}

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
                <Button className="w-full" disabled={!photoValidation?.is_person} onClick={() => setStep(3)}>
                  Continue
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {step === 3 ? (
          <Card className="fade-up">
            <CardHeader>
              <CardTitle>Step 3: Settings and family alerts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">Police Dispatch Mode</label>
                <select
                  className="h-11 w-full rounded-xl border border-(--border) bg-(--card) px-3 text-sm outline-none focus:ring-2 focus:ring-(--ring)"
                  value={form.police_dispatch_mode}
                  onChange={(event) => setField("police_dispatch_mode", event.target.value)}
                >
                  <option value="manual">Manual</option>
                  <option value="auto">Auto</option>
                </select>
                <p className="text-xs text-(--muted-foreground)">Auto mode attempts FIR workflow automatically after confirmed match.</p>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">Add Family Members</label>
                <EmailUserPicker
                  selectedUsers={selectedFamilyUsers}
                  onSelectUser={(user) => setSelectedFamilyUsers((prev) => [...prev, user])}
                  onRemoveUser={(id) => setSelectedFamilyUsers((prev) => prev.filter((item) => item.id !== id))}
                />
                <p className="text-xs text-(--muted-foreground)">Only registered users can be selected.</p>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(2)}>Back</Button>
                <Button className="w-full" disabled={loading} onClick={submitCase}>
                  Submit Case
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : null}
      </main>
      {loading ? <LoadingOverlay label="Creating case..." /> : null}
      </div>
    </ProtectedRoute>
  );
}
