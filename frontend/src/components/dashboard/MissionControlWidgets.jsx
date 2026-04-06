"use client";

import { useMemo } from "react";
import { Activity, ChartBar, Gauge, ListTodo } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

function WidgetFrame({ title, icon: Icon, children, className }) {
  return (
    <Card className={cn("h-full", className)}>
      <CardHeader className="mb-0 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
        <Icon className="h-4 w-4 text-[#a1a1aa]" />
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export function StatWidget({ title, value, subtitle, loading = false }) {
  return (
    <WidgetFrame title={title} icon={ChartBar}>
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-4 w-32" />
        </div>
      ) : (
        <>
          <p className="text-3xl font-semibold leading-none">{value}</p>
          <p className="text-xs text-[#52525b]">{subtitle}</p>
        </>
      )}
    </WidgetFrame>
  );
}

export function CaseDistributionCard({ values = { active: 0, resolved: 0, closed: 0 }, loading = false }) {
  const max = Math.max(values.active, values.resolved, values.closed, 1);
  const bars = [
    { key: "Active", value: values.active },
    { key: "Resolved", value: values.resolved },
    { key: "Closed", value: values.closed },
  ];

  return (
    <WidgetFrame title="Case Distribution" icon={ChartBar}>
      {loading ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <div className="space-y-3">
          {bars.map((bar) => (
            <div key={bar.key} className="space-y-1">
              <div className="flex items-center justify-between text-xs text-[#52525b]">
                <span>{bar.key}</span>
                <span>{bar.value}</span>
              </div>
              <div className="h-2 rounded-md bg-[#f4f4f5]">
                <div className="h-2 rounded-md bg-black" style={{ width: `${Math.max((bar.value / max) * 100, 8)}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </WidgetFrame>
  );
}

export function MatchConfidenceCard({ confidence = 0, loading = false }) {
  return (
    <WidgetFrame title="AI Match Confidence" icon={Gauge}>
      {loading ? (
        <Skeleton className="h-28 w-full" />
      ) : (
        <div className="space-y-3">
          <p className="text-3xl font-semibold">{confidence}%</p>
          <div className="h-2 rounded-md bg-[#f4f4f5]">
            <div className="h-2 rounded-md bg-black" style={{ width: `${confidence}%` }} />
          </div>
          <p className="text-xs text-[#52525b]">Model output from latest matching cycle.</p>
        </div>
      )}
    </WidgetFrame>
  );
}

export function ActivityTableCard({ loading = false }) {
  const rows = useMemo(
    () => [
      { caseId: "MP-1011", activity: "New sighting uploaded", status: "Warning" },
      { caseId: "MP-0982", activity: "Confidence score updated", status: "Success" },
      { caseId: "MP-0920", activity: "Verification assigned", status: "Pending" },
    ],
    []
  );

  return (
    <WidgetFrame title="Activity Table" icon={Activity}>
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((item) => (
            <Skeleton key={item} className="h-10 w-full" />
          ))}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Case</TableHead>
              <TableHead>Activity</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={`${row.caseId}-${row.activity}`}>
                <TableCell>{row.caseId}</TableCell>
                <TableCell>{row.activity}</TableCell>
                <TableCell className="text-[#52525b]">{row.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </WidgetFrame>
  );
}

export function ActiveInvestigationsCard({ loading = false }) {
  const tasks = [
    { name: "Case verification", progress: 76 },
    { name: "Image processing", progress: 58 },
    { name: "Field review", progress: 88 },
  ];

  return (
    <WidgetFrame title="Active Investigations" icon={ListTodo}>
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((item) => (
            <Skeleton key={item} className="h-11 w-full" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <div key={task.name} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span>{task.name}</span>
                <span className="text-[#52525b]">{task.progress}%</span>
              </div>
              <div className="h-2 rounded-md bg-[#f4f4f5]">
                <div className="h-2 rounded-md bg-black" style={{ width: `${task.progress}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </WidgetFrame>
  );
}

export function TimelineCard({ loading = false }) {
  const events = [
    "Sighting verified by operator",
    "Case moved to police review",
    "Report package generated",
    "Family notified of update",
  ];

  return (
    <WidgetFrame title="Timeline" icon={Activity} className="h-full">
      {loading ? (
        <Skeleton className="h-28 w-full" />
      ) : (
        <div className="space-y-2">
          {events.map((event) => (
            <div key={event} className="timeline-line text-sm text-[#52525b]">{event}</div>
          ))}
        </div>
      )}
    </WidgetFrame>
  );
}
