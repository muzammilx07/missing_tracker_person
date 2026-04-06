"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "react-toastify";
import { Eye, EyeOff, LoaderCircle, UserRoundPlus } from "lucide-react";
import api from "@/lib/api";
import { saveAuth } from "@/lib/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import LoadingOverlay from "@/components/ui/LoadingOverlay";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = {};

    if (!form.name.trim()) nextErrors.name = "Name is required";
    if (!form.email.trim()) nextErrors.email = "Email is required";
    if (!form.password.trim()) nextErrors.password = "Password is required";
    if (form.password && form.password.length < 6) {
      nextErrors.password = "Password should be at least 6 characters";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setLoading(true);

    try {
      const response = await api.post("/auth/register", form);
      saveAuth(response.data);
      toast.success("Registration completed");
      router.replace("/dashboard");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
    <main className="grid min-h-[calc(100vh-8rem)] gap-6 lg:grid-cols-2">
      <section className="glass-panel relative hidden overflow-hidden p-8 lg:block">
        <div className="relative z-10 space-y-4">
          <span className="inline-flex items-center gap-2 rounded-xl bg-(--muted) px-3 py-1 text-xs font-semibold text-(--muted-foreground)">
            <UserRoundPlus className="h-4 w-4 text-(--primary)" />
            Fast onboarding for families and volunteers
          </span>
          <h1 className="max-w-sm text-4xl font-semibold leading-tight">Create your response account.</h1>
          <p className="max-w-sm text-(--muted-foreground)">
            Register once and stay connected to case updates, sighting alerts, and response workflows.
          </p>
        </div>
        <div className="absolute -bottom-10 -left-8 h-60 w-60 rounded-xl bg-(--primary)/25 blur-3xl" />
      </section>

      <Card className="mx-auto w-full max-w-xl self-center">
        <CardHeader>
          <CardTitle>Create Account</CardTitle>
          <CardDescription>Register to report and track missing person cases.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-1">
              <label htmlFor="name" className="text-sm font-medium">Full Name</label>
              <input
                id="name"
                name="name"
                value={form.name}
                onChange={handleChange}
                className="h-10 w-full rounded-md border border-(--border) bg-(--card) px-3 text-sm outline-none transition focus:ring-2 focus:ring-(--ring)"
              />
              {errors.name ? <p className="mt-1 text-xs text-red-600">{errors.name}</p> : null}
            </div>

            <div className="space-y-1">
              <label htmlFor="email" className="text-sm font-medium">Email</label>
              <input
                id="email"
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                className="h-10 w-full rounded-md border border-(--border) bg-(--card) px-3 text-sm outline-none transition focus:ring-2 focus:ring-(--ring)"
              />
              {errors.email ? <p className="mt-1 text-xs text-red-600">{errors.email}</p> : null}
            </div>

            <div className="space-y-1">
              <label htmlFor="phone" className="text-sm font-medium">Phone (optional)</label>
              <input
                id="phone"
                name="phone"
                value={form.phone}
                onChange={handleChange}
                className="h-10 w-full rounded-md border border-(--border) bg-(--card) px-3 text-sm outline-none transition focus:ring-2 focus:ring-(--ring)"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="password" className="text-sm font-medium">Password</label>
              <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                name="password"
                value={form.password}
                onChange={handleChange}
                className="h-10 w-full rounded-md border border-(--border) bg-(--card) px-3 pr-10 text-sm outline-none transition focus:ring-2 focus:ring-(--ring)"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-(--muted-foreground)"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
              </div>
              {errors.password ? <p className="mt-1 text-xs text-red-600">{errors.password}</p> : null}
            </div>

            <Button type="submit" className="h-11 w-full" disabled={loading}>
              {loading ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : null}
              Create account
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
    {loading ? <LoadingOverlay label="Creating account..." /> : null}
    </div>
  );
}
