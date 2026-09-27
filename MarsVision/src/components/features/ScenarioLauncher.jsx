import { motion } from 'framer-motion';
import { ArrowUpRight, Play, Radio } from 'lucide-react';

export default function ScenarioLauncher({ scenarios, onSelect }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.08 }}
      aria-label="Traffic scenario summaries"
      className="scenario-panel scenario-overview"
    >
      <div className="scenario-panel-heading">
        <div>
          <div className="scenario-section-kicker">CASE LIBRARY / FIXED SAMPLE OUTPUT</div>
          <h2>Three scenarios. At a glance.</h2>
          <p>Event types and peak risk are shown here without opening a replay.</p>
        </div>
        <span className="scenario-status">
          <Radio size={12} /> SIMULATION
        </span>
      </div>

      <motion.div className="scenario-grid" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.07 } } }} initial="hidden" animate="show">
        {scenarios.map((scenario, index) => (
          <motion.article
            key={scenario.id}
            variants={{ hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } }}
            whileHover={{ y: -2 }}
            className="scenario-card"
          >
            <div className="scenario-card-top">
              <span>CASE 0{index + 1}</span>
              <span className="scenario-location">{scenario.location}</span>
            </div>
            <strong className="scenario-card-title">{scenario.title}</strong>

            <p className="scenario-card-summary">{scenario.summary}</p>

            {(() => {
              const peakPoint = scenario.risk_curve.reduce((peak, point) => point[1] > peak[1] ? point : peak, scenario.risk_curve[0]);
              const labels = [...new Set(scenario.events.map((event) => event.label.replaceAll('_', ' ')))];
              const chartPoints = scenario.risk_curve.map(([time, risk]) => {
                const x = 5 + (time / scenario.duration) * 230;
                const y = 37 - Math.min(Math.max(risk, 0), 1) * 30;
                return `${x},${y}`;
              }).join(' ');
              const peakX = 5 + (peakPoint[0] / scenario.duration) * 230;
              const peakY = 37 - Math.min(Math.max(peakPoint[1], 0), 1) * 30;

              return (
                <>
                  <div className="scenario-sparkline" aria-label={`Risk trend peaks at ${peakPoint[1].toFixed(2)}`}>
                    <svg viewBox="0 0 240 42" role="img" aria-label={`${scenario.title} risk trend`}>
                      <line x1="5" x2="235" y1="22" y2="22" className="scenario-sparkline-threshold" />
                      <polyline points={chartPoints} className="scenario-sparkline-line" />
                      <circle cx={peakX} cy={peakY} r="3" className="scenario-sparkline-peak" />
                    </svg>
                  </div>

                  <div className="scenario-card-metrics">
                    <div><span>PEAK RISK</span><strong>{peakPoint[1].toFixed(2)}</strong></div>
                    <div><span>EVENTS</span><strong>{scenario.events.length}</strong></div>
                    <div><span>CLIP</span><strong>{scenario.duration}s</strong></div>
                  </div>

                  <div className="scenario-event-tags" aria-label="Included event types">
                    {labels.map((label) => <span key={label}>{label}</span>)}
                  </div>
                  <button type="button" className="scenario-replay-button" onClick={() => onSelect(scenario)}>
                    <Play size={12} fill="currentColor" /> Optional replay <ArrowUpRight size={13} />
                  </button>
                </>
              );
            })()}
          </motion.article>
        ))}
      </motion.div>

      <div className="scenario-disclaimer">
        <span>DEMO DATA</span>
        <span>These fixed previews are illustrative sample outputs; they do not run the detector or represent live camera footage.</span>
      </div>
    </motion.section>
  );
}
