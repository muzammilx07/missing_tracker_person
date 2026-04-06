export default function Spinner({ className = "h-8 w-8", label = "Loading" }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3" role="status" aria-live="polite" aria-label={label}>
      <div className={`animate-spin rounded-md border-2 border-(--muted) border-t-(--primary) ${className}`} />
      <span className="text-sm text-(--muted-foreground)">{label}</span>
    </div>
  );
}
