import Spinner from "@/components/ui/Spinner";

export default function FullPageSpinner({ label = "Loading..." }) {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <Spinner className="h-10 w-10" label={label} />
    </div>
  );
}
