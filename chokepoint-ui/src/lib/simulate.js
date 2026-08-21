// Lightweight client-side re-derivation of the backend's disruption math,
// so the "what-if" slider in the Simulation panel can respond instantly
// without a round trip. The exponents below aren't guesses — they're the
// exact relationships found by reverse-checking final_pipeline.py's own
// sample output:
//
//   daily_shortfall_bpd  = corridor_dependent_bpd * severity
//   supply_drop_pct      = daily_shortfall_bpd / india_total_import_bpd * 100
//   price_spike_pct      = supply_drop_pct * price_elasticity_assumption
//
// gross_loss_bbl is approximated by holding the replacement lead-time fixed
// at the backend's last computed value for that corridor — a fair estimate
// for "what if this got worse/better today", not a replacement for a fresh
// backend run (which re-solves the alternative-source routing too).
export function simulateCorridor(corridorData, severity) {
  const { baseline, economic_estimates, derived_lead_time } = corridorData;

  const dailyShortfallBpd = baseline.corridor_dependent_bpd * severity;
  const supplyDropPct = (dailyShortfallBpd / baseline.india_total_import_bpd) * 100;
  const priceSpikePct = supplyDropPct * economic_estimates.price_elasticity_assumption;
  const grossLossBbl = dailyShortfallBpd * derived_lead_time.estimated_replacement_days;

  return {
    dailyShortfallBpd,
    supplyDropPct,
    priceSpikePct,
    grossLossBbl,
  };
}
