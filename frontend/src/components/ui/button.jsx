import { cn } from "@/lib/utils";

const variants = {
  default:
    "border border-transparent bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90",
  outline:
    "border border-(--border) bg-white text-(--foreground) hover:bg-(--secondary)",
  ghost: "bg-transparent text-[#52525b] hover:bg-(--secondary) hover:text-(--foreground)",
  destructive: "border border-transparent bg-[var(--danger)] text-white hover:brightness-105",
};

const sizes = {
  default: "h-10 px-4 py-2",
  sm: "h-9 px-3",
  lg: "h-11 px-6",
  icon: "h-10 w-10",
};

export function Button({
  className,
  variant = "default",
  size = "default",
  type = "button",
  ...props
}) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition duration-200 hover:-translate-y-px active:scale-[0.99] disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}
