"use client";

import { useState } from "react";
import { toast } from "react-toastify";
import AdminRoute from "@/components/AdminRoute";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function AdminToolsPage() {
  const [health, setHealth] = useState(null);
  const [adminTest, setAdminTest] = useState(null);
  const [reindexResult, setReindexResult] = useState(null);
  const [alertForm, setAlertForm] = useState({ case_id: "", confidence: "0.90", location: "" });
  const [testMatchResult, setTestMatchResult] = useState(null);
  const [testImageA, setTestImageA] = useState(null);
  const [testImageB, setTestImageB] = useState(null);

  const runHealth = async () => {
    try {
      const response = await api.get("/health");
      setHealth(response.data);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Health check failed");
    }
  };

  const runAdminTest = async () => {
    try {
      const response = await api.get("/admin/test");
      setAdminTest(response.data);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Admin test failed");
    }
  };

  const runReindex = async () => {
    try {
      const response = await api.post("/admin/reindex-case-embeddings");
      setReindexResult(response.data);
      toast.success("Reindex completed");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Reindex failed");
    }
  };

  const createAlert = async () => {
    if (!alertForm.case_id) {
      toast.error("Case ID is required");
      return;
    }

    try {
      await api.post("/alerts", {
        case_id: Number(alertForm.case_id),
        confidence: Number(alertForm.confidence || 0),
        location: alertForm.location || null,
      });
      toast.success("Alert created");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Alert creation failed");
    }
  };

  const runTestMatch = async () => {
    if (!testImageA || !testImageB) {
      toast.error("Upload both images first");
      return;
    }

    const body = new FormData();
    body.append("image_a", testImageA);
    body.append("image_b", testImageB);

    try {
      const response = await api.post("/test-match", body);
      setTestMatchResult(response.data);
      toast.success("Test match completed");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Test match failed");
    }
  };

  return (
    <AdminRoute>
      <main className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Diagnostics</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button onClick={runHealth}>Run Health Check</Button>
            <Button variant="outline" onClick={runAdminTest}>Run Admin Test</Button>
            <Button variant="outline" onClick={runReindex}>Reindex Face Embeddings</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Create Manual Alert</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 md:grid-cols-3">
              <Input
                placeholder="Case ID"
                value={alertForm.case_id}
                onChange={(event) => setAlertForm((prev) => ({ ...prev, case_id: event.target.value }))}
              />
              <Input
                placeholder="Confidence"
                value={alertForm.confidence}
                onChange={(event) => setAlertForm((prev) => ({ ...prev, confidence: event.target.value }))}
              />
              <Input
                placeholder="Location"
                value={alertForm.location}
                onChange={(event) => setAlertForm((prev) => ({ ...prev, location: event.target.value }))}
              />
            </div>
            <Button onClick={createAlert}>Create Alert</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Face Match Utility Test</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <Input type="file" accept="image/*" onChange={(event) => setTestImageA(event.target.files?.[0] || null)} />
              <Input type="file" accept="image/*" onChange={(event) => setTestImageB(event.target.files?.[0] || null)} />
            </div>
            <Button variant="outline" onClick={runTestMatch}>Run Test Match</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Latest Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {health ? <p>Health: {health.status} ({health.service})</p> : null}
            {adminTest ? <p>Admin: {adminTest.message} ({adminTest.email})</p> : null}
            {reindexResult ? (
              <p>
                Reindex: processed {reindexResult.processed}, updated {reindexResult.updated}, failed {reindexResult.failed}
              </p>
            ) : null}
            {testMatchResult ? (
              <p>
                Test Match Similarity: {(Number(testMatchResult.similarity || 0) * 100).toFixed(2)}%
              </p>
            ) : null}
            {!health && !adminTest && !reindexResult && !testMatchResult ? (
              <p className="text-(--muted-foreground)">No diagnostic output yet.</p>
            ) : null}
          </CardContent>
        </Card>
      </main>
    </AdminRoute>
  );
}
