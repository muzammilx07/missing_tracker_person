import { Badge } from "@/components/ui/badge";

const STATUS_STYLES = {
  open: "default",
  matched: "success",
  critical: "destructive",
  under_investigation: "warning",
  pending: "warning",
  closed: "closed",
};

export default function StatusBadge({ status }) {
  const value = status || "open";
  const variant = STATUS_STYLES[value] || "default";

  return (
    <Badge variant={variant} className="capitalize">
      {value.replaceAll("_", " ")}
    </Badge>
  );
}
