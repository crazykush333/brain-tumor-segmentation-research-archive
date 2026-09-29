import { status } from "@/lib/data";

/** Stage overview derived by the exporter from docs/project_status.yaml (never hand-edited). */
const ICON: Record<string, { icon: string; label: string; tone: string }> = {
  FROZEN: { icon: "✓", label: "Frozen", tone: "text-emerald-700 dark:text-emerald-400" },
  COMPLETED: { icon: "✓", label: "Completed", tone: "text-emerald-700 dark:text-emerald-400" },
  CLOSED: { icon: "✓", label: "Closed", tone: "text-emerald-700 dark:text-emerald-400" },
  AVAILABLE: { icon: "✓", label: "Available", tone: "text-emerald-700 dark:text-emerald-400" },
  PENDING: { icon: "⏳", label: "Pending", tone: "text-amber-700 dark:text-amber-400" },
  IN_PROGRESS: { icon: "⏳", label: "In progress", tone: "text-sky-700 dark:text-sky-400" },
  NOT_STARTED: { icon: "○", label: "Not started", tone: "text-slate-500 dark:text-slate-400" },
  NOT_AVAILABLE: { icon: "○", label: "Not available", tone: "text-slate-500 dark:text-slate-400" },
  LOCKED: { icon: "🔒", label: "Locked", tone: "text-slate-600 dark:text-slate-400" },
  BLOCKED: { icon: "✕", label: "Blocked", tone: "text-rose-700 dark:text-rose-400" },
};

export function StageOverview() {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
      <table className="table-base">
        <caption className="sr-only">Project stage overview</caption>
        <tbody>
          {status.overview.map((o) => {
            const s = ICON[o.status] ?? { icon: "?", label: o.status, tone: "" };
            return (
              <tr key={o.key}>
                <th scope="row" className="w-1/3 pl-4 font-medium">
                  {o.label}
                </th>
                <td className={`whitespace-nowrap font-medium ${s.tone}`}>
                  <span aria-hidden="true" className="mr-2 inline-block w-5 text-center">
                    {s.icon}
                  </span>
                  {o.key === "grouping" && o.status === "LOCKED" ? "Locked pending B2–B6" : s.label}
                </td>
                <td className="hidden text-sm text-slate-500 sm:table-cell">{o.detail}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
