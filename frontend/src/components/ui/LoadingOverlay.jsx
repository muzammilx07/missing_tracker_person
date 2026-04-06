import Spinner from "@/components/ui/Spinner";

export default function LoadingOverlay({ label = "Loading..." }) {
  return (
    <div className="loading-overlay" role="status" aria-live="polite" aria-label={label}>
      <Spinner className="h-8 w-8" label={label} />
    </div>
  );
}
