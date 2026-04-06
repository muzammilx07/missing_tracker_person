"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useMemo, useState } from "react";
import { toast } from "react-toastify";
import { CheckCircle2, ImagePlus, LoaderCircle, MapPin, Send } from "lucide-react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import StepIndicator from "@/components/StepIndicator";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

const MapPicker = dynamic(() => import("@/components/MapPicker"), { ssr: false });

export default function ReportSightingPage() {
  const [step, setStep] = useState(1);
  const [photo, setPhoto] = useState(null);
  const [preview, setPreview] = useState("");
  const [photoValidation, setPhotoValidation] = useState(null);
  const [validatingPhoto, setValidatingPhoto] = useState(false);
  const [reporterName, setReporterName] = useState("");
  const [reporterPhone, setReporterPhone] = useState("");
  const [coords, setCoords] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const previewUrl = useMemo(() => preview, [preview]);

  const handlePhoto = (event) => {
    const file = event.target.files?.[0];
    setPhoto(file || null);
    setPhotoValidation(null);

    if (file) {
      setPreview(URL.createObjectURL(file));
      validatePhoto(file);
    } else {
      setPreview("");
    }
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
      toast.error("Could not validate photo");
    } finally {
      setValidatingPhoto(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!photo) {
      toast.error("Photo is required");
      return;
    }

    if (!photoValidation?.is_person) {
      toast.error("Please upload a clear photo of a person");
      return;
    }

    if (!coords) {
      toast.error("Location is required");
      return;
    }

    const formData = new FormData();
    formData.append("photo", photo);
    formData.append("sighting_lat", String(coords.lat));
    formData.append("sighting_lng", String(coords.lng));
    if (reporterName.trim()) formData.append("reporter_name", reporterName.trim());
    if (reporterPhone.trim()) formData.append("reporter_phone", reporterPhone.trim());

    setLoading(true);

    try {
      const response = await api.post("/sightings", formData);
      setResult(response.data);
      toast.success("Sighting submitted");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Submission failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
    <main className="mx-auto max-w-3xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Report Sighting</CardTitle>
          <CardDescription>Step-by-step flow for upload, AI check, location, and submit.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <StepIndicator steps={["Upload", "AI Validation", "Pin & Submit"]} current={step} />

          <form className="space-y-4" onSubmit={handleSubmit}>
            {step === 1 ? (
              <div className="space-y-4">
                <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-(--border) bg-(--muted) text-center">
                  <ImagePlus className="mb-2 h-6 w-6 text-(--primary)" />
                  <p className="font-medium">Upload Sighting Photo</p>
                  <p className="text-xs text-(--muted-foreground)">Clear face photo improves matching confidence.</p>
                  <Input type="file" accept="image/*" onChange={handlePhoto} required className="hidden" />
                </label>

                {previewUrl ? (
                  <Image
                    src={previewUrl}
                    alt="Preview"
                    width={360}
                    height={220}
                    unoptimized
                    className="rounded-xl border border-slate-200"
                  />
                ) : null}

                <Button className="w-full" disabled={!photo} onClick={() => setStep(2)}>
                  Next
                </Button>
              </div>
            ) : null}

            {step === 2 ? (
              <div className="space-y-4">
                <div className="rounded-xl border border-(--border) bg-(--muted) p-4 text-sm">
                  {validatingPhoto ? (
                    <p className="inline-flex items-center gap-2 text-(--muted-foreground)">
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                      Running AI validation...
                    </p>
                  ) : null}
                  {photoValidation && !photoValidation.is_person ? (
                    <p className="text-red-600">Please upload a clear photo of a person to continue.</p>
                  ) : null}
                  {photoValidation?.is_person ? (
                    <p className="inline-flex items-center gap-2 text-emerald-700">
                      <CheckCircle2 className="h-4 w-4" />
                      Validation passed with {(photoValidation.confidence * 100).toFixed(1)}% confidence
                    </p>
                  ) : null}
                  {photoValidation?.is_person && photoValidation.confidence < 0.6 ? (
                    <div className="mt-2"><Badge variant="warning">Low confidence image quality</Badge></div>
                  ) : null}
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
                  <Button className="w-full" disabled={!photoValidation?.is_person || validatingPhoto} onClick={() => setStep(3)}>
                    Continue
                  </Button>
                </div>
              </div>
            ) : null}

            {step === 3 ? (
              <div className="space-y-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium">Pin Location</label>
                  <MapPicker onLocationSelect={setCoords} />
                  {!coords ? (
                    <p className="inline-flex items-center gap-1 text-xs text-red-600">
                      <MapPin className="h-3 w-3" />
                      Location is required.
                    </p>
                  ) : (
                    <p className="text-xs text-(--muted-foreground)">Pin selected successfully.</p>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Name (optional)</label>
                  <Input value={reporterName} onChange={(event) => setReporterName(event.target.value)} />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Phone (optional)</label>
                  <Input value={reporterPhone} onChange={(event) => setReporterPhone(event.target.value)} />
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setStep(2)}>Back</Button>
                  <Button type="submit" className="w-full" disabled={loading || !photoValidation?.is_person}>
                    <Send className="mr-2 h-4 w-4" />
                    Submit
                  </Button>
                </div>

                {result ? (
                  <div className={`rounded-xl border p-4 text-sm ${result.match_found ? "border-emerald-300/60 bg-emerald-200/20 text-emerald-700" : "border-blue-300/60 bg-blue-200/20 text-blue-700"}`}>
                    <p>{result.message}</p>
                    {result.match_found ? (
                      <p className="mt-1 text-xs">
                        Matched Case: {result.case_id} | Confidence: {((result.confidence || 0) * 100).toFixed(2)}%
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </main>
    {loading ? <LoadingOverlay label="Analyzing sighting..." /> : null}
    </div>
  );
}
