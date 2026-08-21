// This mirrors the EXACT shape your Python backend (final_pipeline.py) produces:
// { phase1_risk_report, phase2_disruption_report: { baseline_year, india_total_import_bpd, corridors } }
export const sampleData = {
  phase1_risk_report: {
    strait_of_hormuz: { name: "Strait of Hormuz", risk_score: 40, traffic_halted: false },
    red_sea: { name: "Red Sea", risk_score: 80, traffic_halted: true },
    cape_of_good_hope: { name: "Cape of Good Hope", risk_score: 20, traffic_halted: false },
  },
  phase2_disruption_report: {
    baseline_year: "2025-26",
    india_total_import_bpd: 4931790,
    corridors: {
      strait_of_hormuz: {
        phase1_context: { name: "Strait of Hormuz", risk_score: 40, traffic_halted: false },
        scenario: { corridor: "Strait of Hormuz", severity: 0.3 },
        baseline: {
          india_total_import_bpd: 4931790,
          corridor_dependency_share: 0.4853,
          corridor_dependent_bpd: 2393561,
          daily_shortfall_bpd: 718068,
        },
        affected_suppliers: [
          { country: "Iraq", normal_bpd: 982978, lost_bpd: 294893, surviving_bpd: 688085 },
          { country: "Saudi Arabia", normal_bpd: 722673, lost_bpd: 216802, surviving_bpd: 505871 },
          { country: "United Arab Emirates", normal_bpd: 522619, lost_bpd: 156786, surviving_bpd: 365834 },
          { country: "Kuwait", normal_bpd: 161220, lost_bpd: 48366, surviving_bpd: 112854 },
          { country: "Iran", normal_bpd: 4070, lost_bpd: 1221, surviving_bpd: 2849 },
        ],
        alternative_sources: [
          { supplier: "Oman", corridor: "Gulf of Oman (outside Hormuz chokepoint)", current_bpd: 15643, additional_bpd_offered: 4693, lead_time_days: 5 },
          { supplier: "Nigeria", corridor: "Direct Indian Ocean route", current_bpd: 146838, additional_bpd_offered: 44052, lead_time_days: 18 },
          { supplier: "Russia", corridor: "Suez Canal / Red Sea", current_bpd: 1739575, additional_bpd_offered: 521872, lead_time_days: 18 },
          { supplier: "Angola", corridor: "Direct Indian Ocean route", current_bpd: 109084, additional_bpd_offered: 32725, lead_time_days: 20 },
          { supplier: "United States", corridor: "Cape of Good Hope", current_bpd: 264326, additional_bpd_offered: 79298, lead_time_days: 25 },
        ],
        derived_lead_time: {
          estimated_replacement_days: 20,
          covered_daily_bpd: 718068,
          residual_daily_shortfall_bpd: 0,
          note: "Duration derived from barrel-weighted average shipping lead-time of alternative suppliers actually used.",
        },
        supply_impact: {
          ramp_up_loss_bbl: 14361366,
          chronic_loss_bbl: 0,
          gross_loss_bbl: 14361366,
          inventory_offset_bbl: 9500000,
          net_gap_bbl: 4861366,
        },
        economic_estimates: {
          supply_drop_pct: 14.56,
          price_elasticity_assumption: 1.25,
          estimated_crude_price_spike_pct: 18.2,
        },
      },
      red_sea: {
        phase1_context: { name: "Red Sea", risk_score: 80, traffic_halted: true },
        scenario: { corridor: "Suez Canal / Red Sea", severity: 0.9 },
        baseline: {
          india_total_import_bpd: 4931790,
          corridor_dependency_share: 0.3556,
          corridor_dependent_bpd: 1753604,
          daily_shortfall_bpd: 1578244,
        },
        affected_suppliers: [
          { country: "Russia", normal_bpd: 1739575, lost_bpd: 1565617, surviving_bpd: 173957 },
          { country: "Azerbaijan", normal_bpd: 8939, lost_bpd: 8045, surviving_bpd: 894 },
          { country: "Kazakhstan", normal_bpd: 5091, lost_bpd: 4582, surviving_bpd: 509 },
        ],
        alternative_sources: [
          { supplier: "Iran", corridor: "Strait of Hormuz", current_bpd: 4070, additional_bpd_offered: 1221, lead_time_days: 5 },
          { supplier: "Oman", corridor: "Gulf of Oman (outside Hormuz chokepoint)", current_bpd: 15643, additional_bpd_offered: 4693, lead_time_days: 5 },
          { supplier: "United Arab Emirates", corridor: "Strait of Hormuz", current_bpd: 522619, additional_bpd_offered: 156786, lead_time_days: 5 },
          { supplier: "Iraq", corridor: "Strait of Hormuz", current_bpd: 982978, additional_bpd_offered: 294893, lead_time_days: 8 },
          { supplier: "Kuwait", corridor: "Strait of Hormuz", current_bpd: 161220, additional_bpd_offered: 48366, lead_time_days: 9 },
          { supplier: "Saudi Arabia", corridor: "Strait of Hormuz", current_bpd: 722673, additional_bpd_offered: 216802, lead_time_days: 9 },
        ],
        derived_lead_time: {
          estimated_replacement_days: 12,
          covered_daily_bpd: 953456,
          residual_daily_shortfall_bpd: 624788,
          note: "Duration derived from barrel-weighted average shipping lead-time of alternative suppliers actually used.",
        },
        supply_impact: {
          ramp_up_loss_bbl: 18938928,
          chronic_loss_bbl: 18743648,
          gross_loss_bbl: 37682576,
          inventory_offset_bbl: 9500000,
          net_gap_bbl: 28182576,
        },
        economic_estimates: {
          supply_drop_pct: 32.0,
          price_elasticity_assumption: 1.25,
          estimated_crude_price_spike_pct: 40.0,
        },
      },
      cape_of_good_hope: {
        phase1_context: { name: "Cape of Good Hope", risk_score: 20, traffic_halted: false },
        scenario: { corridor: "Cape of Good Hope", severity: 0.1 },
        baseline: {
          india_total_import_bpd: 4931790,
          corridor_dependency_share: 0.104,
          corridor_dependent_bpd: 513059,
          daily_shortfall_bpd: 51306,
        },
        affected_suppliers: [
          { country: "United States", normal_bpd: 264326, lost_bpd: 26433, surviving_bpd: 237893 },
          { country: "Canada", normal_bpd: 83291, lost_bpd: 8329, surviving_bpd: 74962 },
          { country: "Brazil", normal_bpd: 68687, lost_bpd: 6869, surviving_bpd: 61818 },
        ],
        alternative_sources: [
          { supplier: "Iran", corridor: "Strait of Hormuz", current_bpd: 4070, additional_bpd_offered: 1221, lead_time_days: 5 },
          { supplier: "Oman", corridor: "Gulf of Oman (outside Hormuz chokepoint)", current_bpd: 15643, additional_bpd_offered: 4693, lead_time_days: 5 },
          { supplier: "United Arab Emirates", corridor: "Strait of Hormuz", current_bpd: 522619, additional_bpd_offered: 45392, lead_time_days: 5 },
        ],
        derived_lead_time: {
          estimated_replacement_days: 5,
          covered_daily_bpd: 51306,
          residual_daily_shortfall_bpd: 0,
          note: "Duration derived from barrel-weighted average shipping lead-time of alternative suppliers actually used.",
        },
        supply_impact: {
          ramp_up_loss_bbl: 256530,
          chronic_loss_bbl: 0,
          gross_loss_bbl: 256530,
          inventory_offset_bbl: 256530,
          net_gap_bbl: 0,
        },
        economic_estimates: {
          supply_drop_pct: 1.04,
          price_elasticity_assumption: 1.25,
          estimated_crude_price_spike_pct: 1.3,
        },
      },
    },
  },
};
