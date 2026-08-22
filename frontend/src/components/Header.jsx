export function ChokepointMark({ size = 30 }) {
  // A narrowing strait glyph - the literal "chokepoint" mark, used as the brand icon.
  return (
    <svg width={size} height={size} viewBox="0 0 30 30" fill="none" aria-hidden="true">
      <path d="M2 6 C 10 6, 12 15, 15 15 C 18 15, 20 6, 28 6" stroke="var(--accent-cyan)" strokeWidth="1.6" fill="none" />
      <path d="M2 24 C 10 24, 12 15, 15 15 C 18 15, 20 24, 28 24" stroke="var(--accent-cyan)" strokeWidth="1.6" fill="none" />
      <circle cx="15" cy="15" r="2" fill="var(--accent-amber)" />
    </svg>
  );
}
