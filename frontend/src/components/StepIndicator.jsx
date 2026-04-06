export default function StepIndicator({ steps, current }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {steps.map((item, index) => {
        const stepNumber = index + 1;
        const completed = current > stepNumber;
        const active = current === stepNumber;

        return (
          <div key={item} className="flex items-center gap-2">
            <div
              className={`grid h-8 w-8 place-items-center rounded-xl border text-xs font-semibold transition-all duration-200 ${
                completed || active
                  ? "border-transparent bg-(--primary) text-(--primary-foreground)"
                  : "border-(--border) bg-(--muted) text-(--muted-foreground)"
              }`}
            >
              {stepNumber}
            </div>
            <span
              className={`text-sm ${
                completed || active ? "text-(--foreground)" : "text-(--muted-foreground)"
              }`}
            >
              {item}
            </span>
            {index !== steps.length - 1 ? (
              <span
                className={`mx-1 h-0.5 w-8 rounded-md ${
                  completed ? "bg-(--primary)" : "bg-(--border)"
                }`}
              />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
