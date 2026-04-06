import { cn } from "@/lib/utils";

const variants = {
  default: "border border-(--border) bg-white text-(--foreground)",
  secondary: "border border-(--border) bg-(--secondary) text-[#52525b]",
  success: "border border-[#bbf7d0] bg-[#f0fdf4] text-[#166534]",
  warning: "border border-[#fde68a] bg-[#fffbeb] text-[#92400e]",
  destructive: "border border-[#fecaca] bg-[#fef2f2] text-[#991b1b]",
  closed: "border border-(--border) bg-(--secondary) text-[#a1a1aa]",
};

export function Badge({ className, variant = "default", ...props }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
