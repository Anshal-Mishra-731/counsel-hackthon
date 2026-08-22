import { formatBpd } from "../lib/format";

export default function AlternativeSourceTable({ sources }) {
  if (!sources?.length) {
    return <p className="empty-note">No alternative supply identified for this corridor.</p>;
  }
  const maxLeadTime = Math.max(...sources.map((s) => s.lead_time_days), 1);

  return (
    <div className="alt-table">
      <div className="alt-table__head mono">
        <span>SUPPLIER</span>
        <span>LEAD TIME</span>
        <span style={{ textAlign: "right" }}>OFFERED</span>
      </div>
      {sources.map((s) => (
        <div className="alt-row" key={s.supplier}>
          <span className="alt-row__name">{s.supplier}</span>
          <div className="alt-row__lead">
            <div className="alt-row__lead-track">
              <div className="alt-row__lead-fill" style={{ width: `${(s.lead_time_days / maxLeadTime) * 100}%` }} />
            </div>
            <span className="mono alt-row__lead-days">{s.lead_time_days}d</span>
          </div>
          <span className="alt-row__value mono">+{formatBpd(s.additional_bpd_offered)}</span>
        </div>
      ))}
      <style>{`
        .alt-table { display: flex; flex-direction: column; gap: 8px; }
        .alt-table__head { display: grid; grid-template-columns: 110px 1fr 90px; font-size: 9px; letter-spacing: 0.06em; color: var(--text-muted); padding-bottom: 4px; border-bottom: 1px solid var(--hairline); }
        .alt-row { display: grid; grid-template-columns: 110px 1fr 90px; align-items: center; gap: 8px; }
        .alt-row__name { font-size: 12.5px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .alt-row__lead { display: flex; align-items: center; gap: 6px; }
        .alt-row__lead-track { flex: 1; height: 5px; border-radius: 3px; background: var(--bg-raised); overflow: hidden; }
        .alt-row__lead-fill { height: 100%; background: var(--accent-cyan); }
        .alt-row__lead-days { font-size: 10.5px; color: var(--text-muted); width: 24px; }
        .alt-row__value { font-size: 11.5px; color: var(--tier-safe); text-align: right; }
      `}</style>
    </div>
  );
}
