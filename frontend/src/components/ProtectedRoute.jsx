"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import FullPageSpinner from "@/components/FullPageSpinner";

export default function ProtectedRoute({ children }) {
  const router = useRouter();
  const token = getToken();

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [router, token]);

  if (!token) {
    return <FullPageSpinner label="Loading your dashboard..." />;
  }

  return children;
}
