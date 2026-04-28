interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export function PageHeader({ title, subtitle, action }: PageHeaderProps) {
  return (
    <div className="mb-8 flex flex-col gap-4 border-b border-[var(--color-aria-border)] pb-6 lg:flex-row lg:items-end lg:justify-between">
      <div className="max-w-2xl">
        <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[var(--color-aria-faint)]">
          Creator workflow
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em] text-[var(--color-aria-ink)] sm:text-4xl">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-3 text-sm leading-6 text-[var(--color-aria-muted)] sm:text-base">
            {subtitle}
          </p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
