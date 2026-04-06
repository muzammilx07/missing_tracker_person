"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Bell, Brain, FileText, Shield, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getRole, isLoggedIn } from "@/lib/auth";

export default function Home() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("families");

  useEffect(() => {
    if (!isLoggedIn()) return;

    const role = getRole();
    router.replace(role === "admin" ? "/admin" : "/dashboard");
  }, [router]);

  const fadeIn = {
    initial: { opacity: 0, y: 8 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, amount: 0.2 },
    transition: { duration: 0.24, ease: "easeOut" },
  };

  const featureCards = [
    {
      title: "Case tracking",
      description: "Structured tracking from registration to resolution.",
      icon: FileText,
    },
    {
      title: "AI matching",
      description: "Confidence-ranked facial matching for every upload.",
      icon: Brain,
    },
    {
      title: "Alerts",
      description: "Clear updates for families and response teams.",
      icon: Bell,
    },
    {
      title: "Reports",
      description: "Operational summaries with a clean activity trail.",
      icon: Shield,
    },
    {
      title: "Operator views",
      description: "Fast interfaces optimized for investigation workflows.",
      icon: Users,
    },
    {
      title: "Case history",
      description: "Timeline visibility across every case update.",
      icon: ArrowRight,
    },
  ];

  const features = [
    {
      label: "Case intake",
      title: "Structured registration",
      description:
        "Capture person profile, last-seen evidence, and jurisdiction metadata.",
      preview: "Case draft with validation and role checks.",
    },
    {
      label: "AI scoring",
      title: "Face match confidence",
      description:
        "Review ranked match candidates with confidence and audit notes.",
      preview: "Batch processing status and top confidence results.",
    },
    {
      label: "Operations",
      title: "Investigation workflows",
      description:
        "Track case verification, dispatch handoff, and completion state.",
      preview: "Task list aligned to operator roles.",
    },
    {
      label: "Alerts",
      title: "Reliable notifications",
      description:
        "Surface updates for families, police units, and NGO coordinators.",
      preview: "Event stream with priority badges.",
    },
  ];

  const useCases = useMemo(
    () => ({
      families: {
        title: "Families",
        text: "Submit a missing person report, upload supporting images, and receive verified updates in a single secure workflow.",
      },
      police: {
        title: "Police",
        text: "Review AI confidence results, manage FIR actions, and coordinate dispatch from a shared operational dashboard.",
      },
      ngos: {
        title: "NGOs",
        text: "Track active cases across regions and coordinate volunteers using a structured activity stream.",
      },
    }),
    [],
  );

  return (
    <main className="mx-auto max-w-300 px-6 py-18">
      <motion.section
        {...fadeIn}
        className="vercel-grid rounded-xl border border-(--border) px-6 py-16"
      >
        <div className="mx-auto grid max-w-200 grid-cols-12 gap-4 text-center">
          <div className="col-span-12 space-y-4">
            <p className="text-xs uppercase tracking-[0.14em] text-[#a1a1aa]">
              Missing Person Tracker System
            </p>
            <h1 className="mx-auto max-w-3xl text-[56px] font-semibold leading-[1.1] tracking-tight">
              Operational clarity for missing person investigations.
            </h1>
            <p className="mx-auto max-w-2xl text-base text-[#52525b]">
              Case registration, match review, and investigation tracking in one
              professional workspace.
            </p>
            <div className="flex justify-center gap-2">
              <Link href="/register">
                <Button className="gap-2">
                  Register
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/report-sighting">
                <Button variant="outline">Report sighting</Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="outline">Open dashboard</Button>
              </Link>
            </div>
          </div>

          <article className="col-span-12 panel p-4 text-left">
            <p className="mb-3 text-sm font-medium">Dashboard preview</p>
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="rounded-md border border-(--border) bg-(--secondary) p-3">
                <p className="text-xs text-[#a1a1aa]">Active cases</p>
                <p className="mt-1 text-2xl font-semibold">148</p>
              </div>
              <div className="rounded-md border border-(--border) bg-(--secondary) p-3">
                <p className="text-xs text-[#a1a1aa]">Match confidence</p>
                <p className="mt-1 text-2xl font-semibold">92%</p>
              </div>
              <div className="rounded-md border border-(--border) bg-(--secondary) p-3 sm:col-span-2">
                <p className="text-xs text-[#a1a1aa]">Recent events</p>
                <div className="mt-2 space-y-1 text-xs text-[#52525b]">
                  <p>MP-1021 sighting uploaded</p>
                  <p>MP-0994 confidence increased to 94%</p>
                  <p>MP-0952 case moved to verified</p>
                </div>
              </div>
            </div>
          </article>
        </div>
      </motion.section>

      <motion.section {...fadeIn} className="py-18">
        <div className="rounded-xl border border-(--border) bg-white p-4">
          <p className="text-xs uppercase tracking-[0.14em] text-[#a1a1aa]">
            Product preview
          </p>
          <div className="mt-3 rounded-xl border border-(--border) bg-(--secondary) p-4">
            <div className="grid gap-2 sm:grid-cols-4">
              {[
                "Case queue",
                "Evidence panel",
                "Activity stream",
                "Operator notes",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-md border border-(--border) bg-white p-3 text-sm text-[#52525b]"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section {...fadeIn} className="py-18">
        <div className="grid gap-4 md:grid-cols-3">
          {featureCards.map((feature) => (
            <article
              key={feature.title}
              className="hover-card rounded-xl border border-(--border) bg-white p-4"
            >
              <feature.icon className="h-4 w-4 text-[#52525b]" />
              <h3 className="mt-3 text-xl font-medium tracking-tight">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-[#52525b]">
                {feature.description}
              </p>
            </article>
          ))}
        </div>
      </motion.section>

      <motion.section
        id="features"
        {...fadeIn}
        className="vercel-grid space-y-6 border-t border-(--border) py-20"
      >
        {features.map((feature, index) => (
          <article
            key={feature.title}
            className="grid items-start gap-4 border-b border-(--border) pb-6 md:grid-cols-2"
          >
            <div className={index % 2 ? "md:order-2" : ""}>
              <p className="text-xs uppercase tracking-[0.14em] text-[#a1a1aa]">
                {feature.label}
              </p>
              <h2 className="mt-2 text-[30px] font-semibold tracking-tight">
                {feature.title}
              </h2>
              <p className="mt-2 max-w-xl text-base text-[#52525b]">
                {feature.description}
              </p>
            </div>
            <div className={index % 2 ? "md:order-1" : ""}>
              <div className="section-alt p-4">
                <p className="text-sm font-medium">UI preview</p>
                <p className="mt-2 text-sm text-[#52525b]">{feature.preview}</p>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  <div className="rounded-md border border-(--border) bg-white p-3 text-xs text-[#52525b]">
                    Status queue
                  </div>
                  <div className="rounded-md border border-(--border) bg-white p-3 text-xs text-[#52525b]">
                    Operator notes
                  </div>
                </div>
              </div>
            </div>
          </article>
        ))}
      </motion.section>

      <motion.section
        {...fadeIn}
        className="grid gap-4 border-t border-(--border) py-20 md:grid-cols-2"
      >
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-[#a1a1aa]">
            Platform depth
          </p>
          <h2 className="mt-2 text-[30px] font-semibold tracking-tight">
            Built for fast and reliable investigations.
          </h2>
          <p className="mt-2 text-base text-[#52525b]">
            A focused interface for high-signal decision making with consistent
            structure across every workflow.
          </p>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {[
            ["Case tracking", FileText],
            ["AI matching", Brain],
            ["Alerts", Bell],
            ["Reports", Shield],
          ].map(([label, Icon]) => (
            <div
              key={label}
              className="rounded-md border border-(--border) bg-white p-3"
            >
              <Icon className="h-4 w-4 text-[#52525b]" />
              <p className="mt-2 text-sm font-medium">{label}</p>
            </div>
          ))}
        </div>
      </motion.section>

      <motion.section {...fadeIn} className="py-18">
        <div className="rounded-xl border border-(--border) bg-white p-5">
          <p className="mb-3 text-sm font-medium">Dashboard preview block</p>
          <div className="grid gap-2 md:grid-cols-3">
            <div className="rounded-md border border-(--border) bg-(--secondary) p-3 text-sm text-[#52525b]">
              Case distribution panel
            </div>
            <div className="rounded-md border border-(--border) bg-(--secondary) p-3 text-sm text-[#52525b]">
              AI confidence + investigations
            </div>
            <div className="rounded-md border border-(--border) bg-(--secondary) p-3 text-sm text-[#52525b]">
              Activity feed and timeline
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section {...fadeIn} className="border-t border-(--border) py-20">
        <h2 className="text-[30px] font-semibold tracking-tight">Use cases</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.entries(useCases).map(([key, value]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              className={
                activeTab === key
                  ? "rounded-md border border-black bg-black px-3 py-1.5 text-sm text-white"
                  : "rounded-md border border-(--border) bg-white px-3 py-1.5 text-sm text-[#52525b]"
              }
            >
              {value.title}
            </button>
          ))}
        </div>
        <div className="mt-4 rounded-md border border-(--border) bg-(--secondary) p-4">
          <p className="text-base font-medium">{useCases[activeTab].title}</p>
          <p className="mt-2 text-sm text-[#52525b]">
            {useCases[activeTab].text}
          </p>
        </div>
      </motion.section>

      <motion.section
        {...fadeIn}
        className="border-t border-(--border) py-18 text-center"
      >
        <h2 className="text-[30px] font-semibold tracking-tight">
          Start with a reliable workflow.
        </h2>
        <p className="mt-2 text-sm text-[#52525b]">
          Create a case, verify sightings, and coordinate action quickly.
        </p>
        <div className="mt-4 flex justify-center gap-2">
          <Link href="/register">
            <Button>Register case</Button>
          </Link>
          <Link href="/volunteer">
            <Button variant="outline" className="gap-2">
              <Users className="h-4 w-4" />
              Join network
            </Button>
          </Link>
        </div>
      </motion.section>

      <footer
        id="docs"
        className="border-t border-(--border) py-12 text-sm text-[#a1a1aa]"
      >
        <div className="grid gap-6 md:grid-cols-4">
          <div>
            <p className="font-semibold text-(--foreground)">Missing Tracker</p>
            <p className="mt-2 text-sm">
              A structured platform for missing person investigations.
            </p>
          </div>
          <div>
            <p className="font-medium text-(--foreground)">Product</p>
            <div className="mt-2 space-y-1">
              <Link href="/dashboard">Dashboard</Link>
              <p>Case management</p>
            </div>
          </div>
          <div>
            <p className="font-medium text-(--foreground)">Resources</p>
            <div className="mt-2 space-y-1">
              <p>Documentation</p>
              <p>Testing guide</p>
            </div>
          </div>
          <div>
            <p className="font-medium text-(--foreground)">Company</p>
            <div className="mt-2 space-y-1">
              <p>Privacy</p>
              <p>Contact</p>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
