import { useEffect, useRef } from "react";

export function DropdownMenu({ open, onOpenChange, trigger, children }) {
  const wrapRef = useRef(null);

  useEffect(() => {
    const onClick = (event) => {
      if (!wrapRef.current?.contains(event.target)) {
        onOpenChange(false);
      }
    };

    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [onOpenChange]);

  return (
    <div className="relative" ref={wrapRef}>
      {trigger}
      {open ? (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border border-slate-200 bg-white p-2 shadow-lg">
          {children}
        </div>
      ) : null}
    </div>
  );
}
