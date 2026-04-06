"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  ChevronDown,
  Compass,
  FileText,
  LayoutDashboard,
  LogOut,
  MapPin,
  Search,
  Settings,
  Shield,
  User,
  Users,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import api from "@/lib/api";
import { clearAuth, getRole, getUser, isLoggedIn } from "@/lib/auth";
import FullPageSpinner from "@/components/FullPageSpinner";

const PUBLIC_ROUTES = new Set(["/", "/login", "/register", "/report-sighting"]);

const PAGE_TITLES = {
  "/dashboard": "Dashboard",
  "/cases": "My Cases",
  "/cases/new": "Create Case",
  "/volunteer": "Volunteer Network",
  "/notifications": "Notifications",
  "/settings": "Profile & Settings",
  "/admin": "Admin Dashboard",
  "/admin/cases": "Case Management",
  "/admin/matches": "Match Review",
  "/admin/sightings": "Sighting Reports",
  "/admin/volunteers": "Volunteer Review",
  "/admin/fir": "FIR Management",
  "/admin/alerts": "Admin Alerts",
  "/admin/police-stations": "Police Stations",
  "/admin/tools": "Admin Tools",
};

export default function AppChrome({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [notifCount, setNotifCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifLoading, setNotifLoading] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    setMounted(true);
  }, []);

  const authed = mounted ? isLoggedIn() : false;
  const role = authed ? getRole() : null;
  const user = authed ? getUser() : null;

  const isPublic = PUBLIC_ROUTES.has(pathname);

  useEffect(() => {
    if (!authed || !isPublic) return;
    router.replace(role === "admin" ? "/admin" : "/dashboard");
  }, [authed, isPublic, role, router]);

  const links = useMemo(() => {
    if (role === "admin") {
      return [
        { href: "/admin", label: "Dashboard", icon: LayoutDashboard },
        { href: "/admin/cases", label: "Cases", icon: Compass },
        { href: "/admin/matches", label: "Matches", icon: Shield },
        { href: "/admin/sightings", label: "Sightings", icon: Bell },
        { href: "/admin/volunteers", label: "Volunteers", icon: Users },
        { href: "/admin/fir", label: "FIRs", icon: FileText },
        { href: "/admin/alerts", label: "Alerts", icon: Bell },
        { href: "/admin/police-stations", label: "Stations", icon: MapPin },
        { href: "/admin/tools", label: "Tools", icon: Settings },
      ];
    }

    return [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/cases", label: "My Cases", icon: Compass },
      { href: "/volunteer", label: "Volunteer", icon: Users },
      { href: "/notifications", label: "Notifications", icon: Bell },
    ];
  }, [role]);

  const pageTitle = useMemo(() => {
    if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
    const exact = Object.keys(PAGE_TITLES).find((key) => pathname.startsWith(`${key}/`));
    return exact ? PAGE_TITLES[exact] : "Missing Tracker";
  }, [pathname]);

  useEffect(() => {
    if (!authed) return;

    let active = true;

    const fetchCount = async () => {
      try {
        const response = await api.get("/notifications/count");
        if (active) {
          setNotifCount(response.data.count || 0);
        }
      } catch {
        if (active) setNotifCount(0);
      }
    };

    fetchCount();
    const timer = setInterval(fetchCount, 30000);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [authed]);

  const handleLogout = () => {
    clearAuth();
    router.replace("/login");
  };

  const handleSearch = (event) => {
    event.preventDefault();
    if (!searchText.trim()) return;
    router.push(`/cases?query=${encodeURIComponent(searchText.trim())}`);
  };

  const notificationHref = (item) => {
    const type = String(item?.type || "").toLowerCase();

    if (role === "admin") {
      if (type.includes("fir")) return "/admin/fir";
      if (type.includes("match")) return "/admin/matches";
      if (type.includes("sighting")) return "/admin/sightings";
      return "/admin/cases";
    }

    if (item?.case_id) return `/cases/${item.case_id}`;
    return "/notifications";
  };

  const openNotifications = async () => {
    setNotifOpen(true);
    setNotifLoading(true);
    try {
      const response = await api.get("/notifications", { params: { limit: 30 } });
      setNotifications(response?.data?.notifications || []);
    } catch {
      setNotifications([]);
    } finally {
      setNotifLoading(false);
    }
  };

  const openNotificationItem = (item) => {
    const nextHref = notificationHref(item);
    setNotifOpen(false);
    router.push(nextHref);
  };

  const isNavItemActive = (href) => {
    // Root dashboard routes should only be active on exact match.
    if (href === "/dashboard" || href === "/admin") {
      return pathname === href;
    }
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  if (!mounted) {
    return (
      <div className="mx-auto w-full max-w-300 p-6">
        <Card className="p-6">
          <FullPageSpinner label="Loading app..." />
        </Card>
      </div>
    );
  }

  if (!authed || isPublic) {
    const authedOnPublic = authed && isPublic;
    return (
      <div className="min-h-screen bg-(--background)">
        <header className="sticky top-0 z-40 border-b border-(--border) bg-white/85 backdrop-blur-sm">
          <div className="mx-auto flex h-16 w-full max-w-300 items-center justify-between px-6">
            <Link href="/" className="flex items-center gap-2 text-base font-semibold sm:text-lg">
              <span className="grid h-8 w-8 place-items-center rounded-md bg-(--primary) text-(--primary-foreground)">
                <Shield className="h-4 w-4" />
              </span>
              Missing Tracker
            </Link>

            <nav className="hidden items-center gap-6 text-sm text-[#52525b] md:flex">
              <Link href="/#features" className="hover:text-(--foreground)">Features</Link>
              <Link href="/dashboard" className="hover:text-(--foreground)">Dashboard</Link>
              <Link href="/#docs" className="hover:text-(--foreground)">Docs</Link>
            </nav>

            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button variant="ghost">Login</Button>
              </Link>
              <Link href="/register">
                <Button>Register</Button>
              </Link>
            </div>
          </div>
        </header>

        {authedOnPublic ? (
          <div className="mx-auto mt-10 max-w-xl">
            <FullPageSpinner label="Opening workspace..." />
          </div>
        ) : (
          <div className="mx-auto w-full max-w-6xl px-6 py-6">{children}</div>
        )}
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-full">
      <aside className="hidden w-72 shrink-0 border-r border-(--border) bg-white p-6 lg:flex lg:flex-col">
        <div className="mb-8 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-(--primary) text-(--primary-foreground)">
            <Shield className="h-5 w-5" />
          </span>
          <div>
            <p className="text-base font-semibold">Missing Tracker</p>
            <p className="text-xs text-(--muted-foreground)">{role === "admin" ? "Admin Workspace" : "Operations Workspace"}</p>
          </div>
        </div>

        <nav className="space-y-1.5">
          {links.map((item) => (
            <Link key={`${item.href}-${item.label}`} href={item.href}>
              <Button
                variant={isNavItemActive(item.href) ? "default" : "ghost"}
                className="w-full justify-start gap-2"
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Button>
            </Link>
          ))}
        </nav>

        <div className="mt-auto pt-8">
          <Link href="/settings">
            <Button variant={pathname === "/settings" ? "default" : "ghost"} className="w-full justify-start gap-2">
              <User className="h-4 w-4" />
              User
            </Button>
          </Link>

          <div className="rounded-xl border border-(--border) bg-(--muted) p-3 text-xs text-(--muted-foreground)">
            Unread notifications
            <Badge className="ml-2">{notifCount}</Badge>
          </div>

          <div className="relative mt-4">
            <button
              type="button"
              onClick={() => setProfileOpen((prev) => !prev)}
              className="flex w-full items-center justify-between rounded-md border border-(--border) bg-(--card) px-3 py-2 text-left hover:bg-(--muted)"
            >
              <span className="flex items-center gap-2">
                <span className="grid h-8 w-8 place-items-center rounded-md bg-(--muted)">
                  <User className="h-4 w-4" />
                </span>
                <span>
                  <span className="block text-sm font-semibold text-(--foreground)">{user?.name || "User"}</span>
                  <span className="block text-xs text-(--muted-foreground)">{user?.email || ""}</span>
                </span>
              </span>
              <ChevronDown className="h-4 w-4 text-(--muted-foreground)" />
            </button>

            {profileOpen ? (
              <div className="absolute bottom-14 left-0 right-0 z-20 rounded-md border border-(--border) bg-(--card) p-2">
                <Link href="/settings" className="block rounded-lg px-3 py-2 text-sm hover:bg-(--muted)">
                  Profile
                </Link>
                <Link href="/settings" className="block rounded-lg px-3 py-2 text-sm hover:bg-(--muted)">
                  Settings
                </Link>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-700 hover:bg-red-50"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 border-b border-(--border) bg-white px-6 py-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="mr-auto text-xl font-semibold">{pageTitle}</h1>

            <form onSubmit={handleSearch} className="relative w-full max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-(--muted-foreground)" />
              <input
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                className="h-10 w-full rounded-md border border-(--border) bg-white pl-9 pr-3 text-sm outline-none transition focus:ring-2 focus:ring-(--ring)"
                placeholder="Search cases..."
              />
            </form>

            <Button variant="outline" size="icon" className="relative" onClick={openNotifications}>
              <Bell className="h-4 w-4" />
              {notifCount ? (
                <span className="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-md bg-(--primary) px-1 text-[10px] text-(--primary-foreground)">
                  {notifCount}
                </span>
              ) : null}
            </Button>

            <Link href="/settings">
              <Button variant="ghost" size="icon" aria-label="Open settings">
                <Settings className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </header>

        <main className={role === "admin" ? "w-full p-6" : "mx-auto w-full max-w-300 p-6"}>{children}</main>
      </div>

      {notifOpen ? (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-white/55 p-6 backdrop-blur-sm">
          <div className="mt-20 w-full max-w-2xl rounded-xl border border-(--border) bg-white/85 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold">Notifications</h3>
              <button
                type="button"
                onClick={() => setNotifOpen(false)}
                className="rounded-md border border-(--border) p-1 hover:bg-(--secondary)"
                aria-label="Close notifications"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="max-h-[60vh] space-y-2 overflow-auto pr-1">
              {notifLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((item) => (
                    <div key={item} className="h-14 animate-pulse rounded-md bg-(--secondary)" />
                  ))}
                </div>
              ) : null}

              {!notifLoading && !notifications.length ? (
                <div className="rounded-md border border-(--border) bg-(--secondary) p-4 text-sm text-(--muted-foreground)">
                  No notifications right now.
                </div>
              ) : null}

              {!notifLoading && notifications.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => openNotificationItem(item)}
                  className="block w-full rounded-md border border-(--border) bg-white p-3 text-left hover:-translate-y-px hover:border-(--border-strong) hover:bg-(--secondary)"
                >
                  <p className="text-sm text-(--foreground)">{item.message || "Case update"}</p>
                  <p className="mt-1 text-xs text-(--muted-foreground)">
                    {item.type || "update"}
                    {item.case_id ? ` • Case ${item.case_id}` : ""}
                    {item.sent_at ? ` • ${new Date(item.sent_at).toLocaleString()}` : ""}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
