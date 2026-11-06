import type { CSSProperties } from "react";

const paths = {
  home: (
    <>
      <path d="m3 10 9-8 9 8M5 9v12h14V9" />
      <path d="M9 21v-8h6v8" />
    </>
  ),
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  back: <path d="m14 5-7 7 7 7" />,
  check: <path d="m4 12 5 5L20 6" />,
  sparkles: (
    <>
      <path d="m15 2 1.7 5.3L22 9l-5.3 1.7L15 16l-1.7-5.3L8 9l5.3-1.7L15 2ZM5 14l1.2 3.8L10 19l-3.8 1.2L5 24l-1.2-3.8L0 19l3.8-1.2L5 14Z" />
    </>
  ),
  pin: (
    <>
      <path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z" />
      <circle cx="12" cy="10" r="3" />
    </>
  ),
  money: (
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M16 7c-6-4-10 3-4 5s2 9-4 5m4-13v16" />
    </>
  ),
  calendar: (
    <>
      <rect x="3" y="5" width="18" height="17" rx="2" />
      <path d="M7 2v6m10-6v6M3 11h18" />
    </>
  ),
  heart: (
    <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" />
  ),
  edit: (
    <>
      <path d="m15 4 5 5M3 21l5-1L21 7a3.5 3.5 0 0 0-5-5L3 15v6ZM13 21h8" />
    </>
  ),
  lock: (
    <>
      <rect x="5" y="10" width="14" height="11" rx="2" />
      <path d="M8 10V6a4 4 0 0 1 8 0v4m-4 5v2" />
    </>
  ),
  eye: (
    <>
      <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  construction: (
    <>
      <path d="M4 21v-6m16 6v-6M3 7h18v8H3zM3 7l8 8m0-8 8 8M7 2h10M9 2v5m6-5V2" />
    </>
  ),
};
export type IconName = keyof typeof paths;

/** Render the small shared line icons used throughout the reference designs. */
export function Icon({
  name,
  className = "",
  style,
}: {
  name: IconName;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <svg
      className={`icon ${className}`}
      style={style}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
