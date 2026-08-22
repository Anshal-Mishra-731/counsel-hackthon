export default function EconomicPanel({ economics, supplyImpact }) {
  return (
    <div className="econ-panel">
      <div className="econ-stat">
        <span className="econ-stat__label">Est. price spike</span>
        <span className="econ-stat__value mono">+{economics.estimated_crude_price_spike_pct}%</span>
      </div>
      <div className="econ-stat">
        <span className="econ-stat__label">Supply drop</span>
        <span className="econ-stat__value mono">{economics.supply_drop_pct}%</span>
      </div>
      <div className="econ-stat">
        <span className="econ-stat__label">Net gap (after reserve)</span>
        <span className="econ-stat__value mono">{(supplyImpact.net_gap_bbl / 1_000_000).toFixed(1)}M bbl</span>
      </div>
      <p className="econ-note">
        Modelled estimate based on supply shock &amp; assumed elasticity ({economics.price_elasticity_assumption}×) — not an official forecast.
      </p>
      <style>{`
        .econ-panel { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .econ-stat { display: flex; flex-direction: column; gap: 3px; padding: 10px 12px; background: var(--bg-panel-2); border: 1px solid var(--hairline); border-radius: var(--radius-sm); }
        .econ-stat__label { font-size: 10px; color: var(--text-muted); letter-spacing: 0.02em; }
        .econ-stat__value { font-size: 16px; font-weight: 700; color: var(--text-primary); }
        .econ-note { grid-column: 1 / -1; margin: 0; font-size: 10.5px; color: var(--text-muted); line-height: 1.5; }
      `}</style>
    </div>
  );
}
