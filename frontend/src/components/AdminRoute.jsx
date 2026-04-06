"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getRole, getToken } from "@/lib/auth";
import FullPageSpinner from "@/components/FullPageSpinner";

export default function AdminRoute({ children }) {
  const router = useRouter();
  const token = getToken();
  const role = getRole();

  useEffect(() => {
    if (!token) {
      router.replace("/login");
      return;
    }

    if (role !== "admin") {
      router.replace("/dashboard");
    }
  }, [router, token, role]);

  if (!token || role !== "admin") {
    return <FullPageSpinner label="Loading admin workspace..." />;
  }

  return children;
}
