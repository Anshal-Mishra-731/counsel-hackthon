import { formatBpd } from "../lib/format";

export default function SupplierTable({ suppliers }) {
  if (!suppliers?.length) {
    return <p className="empty-note">No suppliers currently route through this corridor.</p>;
  }
  const maxNormal = Math.max(...suppliers.map((s) => s.normal_bpd));

  return (
    <div className="supplier-table">
      {suppliers.map((s) => (
        <div className="supplier-row" key={s.country}>
          <span className="supplier-row__name">{s.country}</span>
          <div className="supplier-row__bar-track">
            <div className="supplier-row__bar-lost" style={{ width: `${(s.lost_bpd / maxNormal) * 100}%` }} />
            <div className="supplier-row__bar-surviving" style={{ width: `${(s.surviving_bpd / maxNormal) * 100}%` }} />
          </div>
          <span className="supplier-row__value mono">-{formatBpd(s.lost_bpd)}</span>
        </div>
      ))}
      <style>{`
        .supplier-table { display: flex; flex-direction: column; gap: 10px; }
        .supplier-row { display: grid; grid-template-columns: 120px 1fr 90px; align-items: center; gap: 10px; }
        .supplier-row__name { font-size: 12.5px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .supplier-row__bar-track { display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: var(--bg-raised); }
        .supplier-row__bar-lost { background: var(--tier-critical); }
        .supplier-row__bar-surviving { background: var(--bg-panel-2); border-left: 1px solid var(--bg-deep); }
        .supplier-row__value { font-size: 11.5px; color: var(--tier-critical); text-align: right; }
        .empty-note { font-size: 12.5px; color: var(--text-muted); font-style: italic; }
      `}</style>
    </div>
  );
}
