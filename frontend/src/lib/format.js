export function formatNumber(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("en-IN").format(Math.round(n));
}

export function formatBarrels(n) {
  if (n === null || n === undefined) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M bbl`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K bbl`;
  return `${formatNumber(n)} bbl`;
}

export function formatBpd(n) {
  return `${formatNumber(n)} bpd`;
}

// severity is 0-1
export function tierForSeverity(severity) {
  if (severity >= 0.8) return "critical";
  if (severity >= 0.6) return "high";
  if (severity >= 0.3) return "moderate";
  return "safe";
}

export const TIER_LABEL = {
  safe: "Diplomatic tension",
  moderate: "Military posturing",
  high: "Serious escalation",
  critical: "Near-total breakdown",
};

export const TIER_COLOR_VAR = {
  safe: "--tier-safe",
  moderate: "--tier-moderate",
  high: "--tier-high",
  critical: "--tier-critical",
};

export const TIER_DIM_VAR = {
  safe: "--tier-safe-dim",
  moderate: "--tier-moderate-dim",
  high: "--tier-high-dim",
  critical: "--tier-critical-dim",
};

// "Iraq" -> "iraq", "United Arab Emirates" -> "united_arab_emirates"
export function slugifyCountry(name) {
  return name.trim().toLowerCase().replace(/[^a-z]+/g, "_").replace(/^_|_$/g, "");
}
