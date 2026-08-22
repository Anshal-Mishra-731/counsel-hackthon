import Header from "../components/Header";
import CorridorCard from "../components/CorridorCard";
import WorldMap from "../components/WorldMap";
import SimulationPanel from "../components/SimulationPanel";
import { usePipelineData } from "../lib/usePipelineData";

export default function Dashboard() {
  const { data, source, lastUpdated } = usePipelineData();
  const phase2 = data.phase2_disruption_report;
  const corridors = Object.entries(phase2.corridors);

  return (
    <div className="app">
      <Header
        baselineYear={phase2.baseline_year}
        totalBpd={phase2.india_total_import_bpd}
        source={source}
        lastUpdated={lastUpdated}
      />

      <main className="app__main">
        <div className="app__intro">
          <span className="app__eyebrow mono">01 · SUPPLY CHAIN DIGITAL TWIN</span>
          <h2>Live corridor map</h2>
          <p>
            A geospatial view of every route crude actually travels to reach India — the chokepoint
            it must pass, the suppliers behind it, and how exposed each one is right now. Select a
            corridor to trace its route and see who's affected.
          </p>
        </div>

        <div className="app__panel">
          <WorldMap corridors={phase2.corridors} />
        </div>

        <div className="app__intro app__intro--spaced">
          <span className="app__eyebrow mono">02 · WHAT-IF SIMULATOR</span>
          <h2>Escalate or de-escalate a corridor</h2>
          <p>
            Drag the severity slider to see how a corridor's shortfall, price impact and losses move
            before committing to a full backend re-run. Numbers update instantly on the client.
          </p>
        </div>

        <div className="app__panel">
          <SimulationPanel corridors={phase2.corridors} />
        </div>

        <div className="app__intro app__intro--spaced">
          <span className="app__eyebrow mono">03 · REROUTING RECOMMENDATIONS</span>
          <h2>Corridor disruption scenarios</h2>
          <p>
            Auto-derived from live geopolitical risk scoring. Severity comes from each corridor's
            risk score; replacement time comes from the real shipping lead-time of the fastest
            available alternative suppliers — not a fixed assumption.
          </p>
        </div>

        <div className="app__grid">
          {corridors.map(([key, value]) => (
            <CorridorCard key={key} corridorKey={key} corridorData={value} />
          ))}
        </div>
      </main>

      <footer className="app__footer">
        <span>Chokepoint · modelled estimates, not official forecasts</span>
      </footer>

      <style>{`
        .app {
          min-height: 100%;
          display: flex;
          flex-direction: column;
        }
        .app__main {
          flex: 1;
          padding: 32px;
          max-width: 1280px;
          margin: 0 auto;
          width: 100%;
        }
        .app__eyebrow {
          font-size: 10.5px;
          letter-spacing: 0.1em;
          color: var(--accent-cyan);
        }
        .app__intro {
          margin-bottom: 20px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .app__intro--spaced {
          margin-top: 40px;
        }
        .app__intro h2 {
          font-family: var(--font-display);
          font-size: 22px;
          margin: 0;
        }
        .app__intro p {
          max-width: 680px;
          font-size: 13px;
          color: var(--text-secondary);
          line-height: 1.6;
          margin: 0;
        }
        .app__panel {
          background: var(--ink-700);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          padding: 22px;
          box-shadow: var(--shadow-card);
        }
        .app__grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 20px;
        }
        .app__footer {
          text-align: center;
          padding: 20px;
          font-size: 11px;
          color: var(--text-muted);
          border-top: 1px solid var(--hairline);
        }
      `}</style>
    </div>
  );
}
