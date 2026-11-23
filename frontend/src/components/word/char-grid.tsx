/** Cuadrícula 米字格 detrás de un carácter. */
export function CharGrid() {
  return (
    <svg aria-hidden className="pointer-events-none absolute inset-0 size-full text-border" viewBox="0 0 100 100" preserveAspectRatio="none">
      <rect x="1" y="1" width="98" height="98" rx="8" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <g stroke="currentColor" strokeWidth="0.8" strokeDasharray="3 3">
        <line x1="50" y1="2" x2="50" y2="98" />
        <line x1="2" y1="50" x2="98" y2="50" />
        <line x1="4" y1="4" x2="96" y2="96" />
        <line x1="96" y1="4" x2="4" y2="96" />
      </g>
    </svg>
  );
}
