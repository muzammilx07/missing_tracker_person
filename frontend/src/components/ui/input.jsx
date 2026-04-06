import { cn } from "@/lib/utils";

export function Input({ className, ...props }) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-(--border) bg-(--card) px-3 py-2 text-sm text-(--foreground) placeholder:text-[#a1a1aa] focus:border-(--border-strong) focus:outline-none",
        className
      )}
      {...props}
    />
  );
}
