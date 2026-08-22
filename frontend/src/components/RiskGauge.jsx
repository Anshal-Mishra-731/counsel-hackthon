import { tierForSeverity, TIER_COLOR_VAR } from "../lib/format";

// Semi-circular gauge. severity is 0-1.
export default function RiskGauge({ severity, size = 96 }) {
  const tier = tierForSeverity(severity);
  const color = `var(${TIER_COLOR_VAR[tier]})`;

  const radius = size / 2 - 8;
  const circumference = Math.PI * radius; // half circle
  const filled = circumference * severity;

  const cx = size / 2;
  const cy = size / 2;

  return (
    <div className="risk-gauge" style={{ width: size, height: size / 2 + 20 }}>
      <svg width={size} height={size / 2 + 10} viewBox={`0 0 ${size} ${size / 2 + 10}`}>
        <path
          d={`M 8 ${cy} A ${radius} ${radius} 0 0 1 ${size - 8} ${cy}`}
          fill="none"
          stroke="var(--bg-raised)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        <path
          d={`M 8 ${cy} A ${radius} ${radius} 0 0 1 ${size - 8} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
      </svg>
      <div className="risk-gauge__value mono" style={{ color }}>
        {Math.round(severity * 100)}%
      </div>
      <style>{`
        .risk-gauge {
          position: relative;
          display: flex;
          align-items: flex-end;
          justify-content: center;
        }
        .risk-gauge__value {
          position: absolute;
          bottom: 2px;
          font-size: 15px;
          font-weight: 700;
        }
      `}</style>
    </div>
  );
}
