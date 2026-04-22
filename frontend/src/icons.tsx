import type { ReactElement } from "react";

type IconProps = {
  name: string;
};

const paths: Record<string, ReactElement> = {
  comments: <path d="M4 5h16v11H8l-4 4zM8 9h8M8 12h6" />,
  chart: <path d="M4 19V5M4 19h16m-13-4 4-4 3 3 5-7" />,
  reply: <path d="M9 7 4 12l5 5M5 12h9a6 6 0 0 1 6 6v1" />,
  upload: <path d="M12 16V4m-5 5 5-5 5 5M5 18h14" />,
  memory: <path d="M5 7h14M5 12h14M5 17h10M4 4h16v16H4z" />,
  spark: <path d="M12 2v5M12 17v5M4.9 4.9l3.5 3.5M15.6 15.6l3.5 3.5M2 12h5M17 12h5M4.9 19.1l3.5-3.5M15.6 8.4l3.5-3.5" />,
  music: <path d="M9 18V5l10-2v13M6.5 18a2.5 2.5 0 1 0 0 .1M16.5 16a2.5 2.5 0 1 0 0 .1" />,
  scissors: <path d="M6 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm0 12a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm2.5-12.5L20 20M8.5 15.5 20 4" />,
  vault: <path d="M4 7h16v13H4zM8 7V5a4 4 0 0 1 8 0v2m-4 4.5a2.5 2.5 0 1 0 0 .1" />
};

export function Icon({ name }: IconProps) {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      {paths[name] ?? paths.comments}
    </svg>
  );
}
