"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function Navbar() {
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);

  const links = useMemo(() => {
    return [
      { href: "/login", label: "Login" },
      { href: "/register", label: "Register" },
    ];
  }, []);

  useEffect(() => {
    const onScroll = () => {
      setIsScrolled(window.scrollY > 8);
    };

    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={`sticky top-0 z-50 w-full border-b transition duration-200 ${
        isScrolled
          ? "border-(--border) bg-(--card)"
          : "border-(--border) bg-(--card)"
      }`}
    >
      <div className="mx-auto flex max-w-300 items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Missing Tracker
        </Link>

        <div className="flex items-center gap-2">
          <Link href="/report-sighting">
            <Button>Report Sighting</Button>
          </Link>

          {links.map((item) => (
            <Link key={`${item.href}-${item.label}`} href={item.href}>
              <Button variant="ghost" className={pathname === item.href ? "bg-slate-100" : ""}>
                {item.label}
              </Button>
            </Link>
          ))}

        </div>
      </div>
    </nav>
  );
}
