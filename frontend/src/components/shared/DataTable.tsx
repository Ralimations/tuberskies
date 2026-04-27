import { cn } from "@/lib/utils";

interface DataTableProps {
  rows: Record<string, unknown>[];
  columns: string[];
  emptyMessage?: string;
}

function fmt(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "number")
    return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(1);
  return String(v);
}

export function DataTable({ rows, columns, emptyMessage = "No data available." }: DataTableProps) {
  if (!rows.length)
    return <p className="text-sm text-[var(--color-aria-muted)] py-4">{emptyMessage}</p>;

  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--color-aria-border)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--color-aria-border)] bg-[var(--color-aria-surface-2)]">
            {columns.map((col) => (
              <th
                key={col}
                className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]"
              >
                {col.replaceAll("_", " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={cn(
                "border-b border-[var(--color-aria-border)] last:border-0 transition-colors",
                "hover:bg-[var(--color-aria-surface-2)]"
              )}
            >
              {columns.map((col) => (
                <td
                  key={col}
                  className="px-4 py-3 text-[var(--color-aria-ink)] font-mono text-xs"
                >
                  {fmt(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
