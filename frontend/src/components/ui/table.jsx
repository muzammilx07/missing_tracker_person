import { cn } from "@/lib/utils";

export function Table({ className, ...props }) {
  return (
    <div className="w-full overflow-x-auto rounded-lg border border-(--border) bg-(--card)">
      <table className={cn("w-full text-sm", className)} {...props} />
    </div>
  );
}

export function TableHeader(props) {
  return <thead className="bg-(--muted)" {...props} />;
}

export function TableBody(props) {
  return <tbody className="bg-(--card)" {...props} />;
}

export function TableRow({ className, ...props }) {
  return (
    <tr
      className={cn(
        "border-b border-(--border) transition duration-200 hover:bg-(--muted)",
        className
      )}
      {...props}
    />
  );
}

export function TableHead({ className, ...props }) {
  return (
    <th
      className={cn("px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-(--muted-foreground)", className)}
      {...props}
    />
  );
}

export function TableCell({ className, ...props }) {
  return <td className={cn("px-4 py-3 text-(--foreground)", className)} {...props} />;
}
