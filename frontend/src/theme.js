// Sentra Authority Instrument Palette
// Warm-white canvas, deep navy typography, oxblood for authority refusal,
// pale blue evidence surfaces, small green for verified healthy states.

export const COLORS = {
  bg: "#f8fafc",          // Warm-white / slate-50 canvas
  card: "#ffffff",        // Pure white instrument card
  surface: "#f0f9ff",     // Pale blue evidence surface (sky-50)
  surfaceAlt: "#f1f5f9",  // Subtle pale gray surface (slate-100)
  border: "#cbd5e1",       // Precise slate border (slate-300)
  line: "#e2e8f0",         // Subtle divider line (slate-200)
  
  ink: "#0f172a",          // Deep navy primary text (slate-900)
  muted: "#334155",        // Slate navy secondary text (slate-700)
  faint: "#64748b",        // Slate caption text (slate-500)
  
  oxblood: "#881337",      // Restrained oxblood for DENY / refusal (rose-900)
  oxbloodLight: "#fff1f2", // Soft oxblood background (rose-50)
  
  amber: "#b45309",        // Restrained amber for ESCALATE / FREEZE / caution
  amberLight: "#fffbeb",   // Soft amber background
  
  green: "#15803d",        // Green only for verified ALLOW / healthy (emerald-700)
  greenLight: "#f0fdf4",   // Soft green background
  
  navyHeader: "#020617",   // Deepest navy for header bar
  accentBlue: "#0284c7",   // Precision blue accent (sky-600)
};

export const VERDICT_COLOR = {
  ALLOW: { text: COLORS.green, bg: COLORS.greenLight, border: "#bbf7d0" },
  DENY: { text: COLORS.oxblood, bg: COLORS.oxbloodLight, border: "#fecdd3" },
  ESCALATE: { text: COLORS.amber, bg: COLORS.amberLight, border: "#fde68a" },
  FREEZE: { text: COLORS.amber, bg: COLORS.amberLight, border: "#fde68a" },
};
