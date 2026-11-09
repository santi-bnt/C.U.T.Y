/** Reads the shared CSS palette for DOM and Three.js presentation effects. */
export function themeColor(token: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  return (
    getComputedStyle(document.documentElement).getPropertyValue(token).trim() ||
    fallback
  );
}
