// Single source of truth for the palette (BUILD_PLAN.md §9).
// Reskinned to premium navy+brass palette.
export const COLORS = {
  bg: "#081220", // deep navy
  panel: "rgba(16, 30, 56, 0.7)", // glass panel
  panelAlt: "rgba(8, 18, 32, 0.8)", // darker glass inset
  line: "rgba(212, 175, 55, 0.15)", // faint brass lines
  ink: "#F8FAFC", // primary text
  muted: "#9CA3AF", // secondary text
  faint: "#6B7280", // captions / eyebrows
  amber: "#D4AF37", // premium brass/gold
  green: "#10B981", // vibrant emerald
  red: "#EF4444", // vibrant crimson
};

// Budget bar fill by remaining ratio.
export function budgetColor(ratio) {
  if (ratio > 0.5) return COLORS.green;
  if (ratio > 0.2) return COLORS.amber;
  return COLORS.red;
}

// Ledger status -> color.
export const STATUS_COLOR = {
  allowed: COLORS.green,
  approved: COLORS.green,
  denied: COLORS.red,
  pending: COLORS.amber,
};

// Decision -> color.
export const DECISION_COLOR = {
  allow: COLORS.green,
  deny: COLORS.red,
  escalate: COLORS.amber,
  error: COLORS.red, // request failed (backend unreachable / bad input)
};
