import { cn } from "@/lib/utils";

export function Command({ className, ...props }) {
  return <div className={cn("rounded-lg border border-slate-200 bg-white", className)} {...props} />;
}

export function CommandInput({ className, ...props }) {
  return (
    <input
      className={cn(
        "h-10 w-full border-b border-slate-200 bg-transparent px-3 text-sm text-slate-700 outline-none placeholder:text-slate-400",
        className
      )}
      {...props}
    />
  );
}

export function CommandList({ className, ...props }) {
  return <div className={cn("max-h-56 overflow-y-auto p-1", className)} {...props} />;
}

export function CommandItem({ className, ...props }) {
  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-start justify-between rounded-md px-2 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-100",
        className
      )}
      {...props}
    />
  );
}

export function CommandEmpty({ className, ...props }) {
  return <p className={cn("p-3 text-sm text-slate-400", className)} {...props} />;
}
