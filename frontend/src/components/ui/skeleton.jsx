import { cn } from "@/lib/utils";

export function Skeleton({ className }) {
  return <div className={cn("skeleton", className)} />;
}
