import ModelPerformance from "../components/ModelPerformance";
import {
  BrainCircuit,
  MapPin,
  Thermometer,
  Droplets,
  Wind,
  CloudRain,
  Mountain,
  Trees,
  Activity,
  ShieldCheck,
} from "lucide-react";

import NetworkVisualizer from "../components/NetworkVisualizer";
import "./AIPrediction.css";

function AIPrediction({
  location,
  result,
  loading,
  error,
  onAnalyse,
}) {
  const hasResult = Boolean(result);

  const environmentalFactors = [
    {
      label: "Temperature",
      value: result?.current_temp,
      unit: "°C",
      description: "Temperature influences how quickly vegetation can dry.",
    },
    {
      label: "Humidity",
      value: result?.current_humidity,
      unit: "%",
      description: "Lower humidity can contribute to drier vegetation.",
    },
    {
      label: "Wind",
      value: result?.current_wind,
      unit: " km/h",
      description: "Stronger winds can accelerate fire spread.",
    },
    {
      label: "Rainfall · 30 days",
      value: result?.rain_last_30_days,
      unit: " mm",
      description: "Recent rainfall provides context for environmental moisture.",
    },
  ];

  return (
    <div className="ai-page">
      <header className="ai-page-header">
        <div>
          <span className="dashboard-eyebrow">
            Artificial Intelligence
          </span>

          <h1>AI Prediction</h1>

          <p>
            Analyse environmental conditions and understand
            how the model assesses bushfire risk.
          </p>
        </div>

        <div className="model-status">
          <span className="model-status-dot" />

          <div>
            <strong>Prediction model</strong>
            <span>Ready for analysis</span>
          </div>
        </div>
      </header>

      <div className="ai-layout">
        <section className="ai-panel ai-input-panel">
          <div className="ai-panel-heading">
            <div className="ai-panel-icon">
              <MapPin size={18} strokeWidth={1.8} />
            </div>

            <div>
              <span className="panel-eyebrow">
                Analysis Target
              </span>
              <h2>Location & Environmental Inputs</h2>
            </div>
          </div>

          <div className="ai-location">
            {location ? (
              <>
                <div>
                  <span>Selected location</span>
                  <strong>
                    {location.name || "Custom location"}
                  </strong>
                </div>

                <div className="ai-location-coordinates">
                  {location.lat.toFixed(4)},{" "}
                  {location.lng.toFixed(4)}
                </div>
              </>
            ) : (
              <>
                <div>
                  <span>Selected location</span>
                  <strong>No location selected</strong>
                </div>

                <div className="ai-location-coordinates">
                  Select a location from the dashboard
                </div>
              </>
            )}
          </div>

          <div className="ai-input-grid">
            <div className="ai-input-card">
              <Thermometer size={17} />
              <span>Temperature</span>
              <strong>
                {hasResult
                  ? `${result.current_temp}°C`
                  : "--"}
              </strong>
            </div>

            <div className="ai-input-card">
              <Droplets size={17} />
              <span>Humidity</span>
              <strong>
                {hasResult
                  ? `${result.current_humidity}%`
                  : "--"}
              </strong>
            </div>

            <div className="ai-input-card">
              <Wind size={17} />
              <span>Wind</span>
              <strong>
                {hasResult
                  ? `${result.current_wind} km/h`
                  : "--"}
              </strong>
            </div>

            <div className="ai-input-card">
              <CloudRain size={17} />
              <span>Rainfall · 30d</span>
              <strong>
                {hasResult
                  ? `${result.rain_last_30_days} mm`
                  : "--"}
              </strong>
            </div>

            <div className="ai-input-card">
              <Mountain size={17} />
              <span>Elevation</span>
              <strong>
                {hasResult &&
                result.elevation !== undefined
                  ? `${result.elevation} m`
                  : "--"}
              </strong>
            </div>

            <div className="ai-input-card">
              <Trees size={17} />
              <span>Vegetation</span>
              <strong>
                {hasResult && result.vegetation
                  ? result.vegetation
                  : "--"}
              </strong>
            </div>
          </div>

          <button
            className="ai-analyse-button"
            disabled={!location || loading}
            onClick={onAnalyse}
            type="button"
          >
            <BrainCircuit size={18} strokeWidth={1.9} />

            {loading
              ? "Running AI Analysis..."
              : "Analyse Bushfire Risk"}
          </button>

          {error && (
            <p className="ai-error">
              {error}
            </p>
          )}
        </section>

        <div className="ai-results-column">
          <section className="ai-panel ai-risk-panel">
            <div className="ai-panel-heading compact">
              <div className="ai-panel-icon">
                <Activity size={18} strokeWidth={1.8} />
              </div>

              <div>
                <span className="panel-eyebrow">
                  Model Output
                </span>
                <h2>Predicted Risk</h2>
              </div>
            </div>

            <div className="ai-score">
              <strong>
                {hasResult
                  ? `${result.risk_score}%`
                  : "--"}
              </strong>

              <span>
                {hasResult
                  ? result.risk_level
                  : "Awaiting analysis"}
              </span>
            </div>

            <div className="ai-score-bar">
              <div
                className="ai-score-fill"
                style={{
                  width: hasResult
                    ? `${Math.min(
                        Number(result.risk_score),
                        100
                      )}%`
                    : "0%",
                }}
              />
            </div>

            <p className="ai-risk-description">
              {hasResult
                ? "This is an AI environmental risk score, not a probability of fire or an official Fire Danger Rating."
                : "Run an analysis to generate a bushfire risk assessment for the selected location."}
            </p>
          </section>

          <section className="ai-panel">
            <div className="ai-panel-heading compact">
              <div className="ai-panel-icon neutral">
                <ShieldCheck
                  size={18}
                  strokeWidth={1.8}
                />
              </div>

              <div>
                <span className="panel-eyebrow">
                  Intelligence
                </span>
                <h2>Risk Drivers</h2>
              </div>
            </div>

            {hasResult ? (
              <div className="environmental-factors">
                {environmentalFactors.map((factor) => (
                  <div
                    className="environmental-factor"
                    key={factor.label}
                  >
                    <div className="environmental-factor-top">
                      <span>{factor.label}</span>
                      <strong>
                        {factor.value !== undefined &&
                        factor.value !== null
                          ? `${factor.value}${factor.unit}`
                          : "--"}
                      </strong>
                    </div>
                    <p>{factor.description}</p>
                  </div>
                ))}

                <p className="environmental-note">
                  These are environmental observations, not
                  calculated neural-network feature contributions.
                </p>
              </div>
            ) : (
              <div className="risk-driver-empty">
                <BrainCircuit size={24} strokeWidth={1.5} />
                <strong>No analysis yet</strong>
                <p>
                  Run an analysis to view environmental
                  conditions relevant to bushfire behaviour.
                </p>
              </div>
            )}
          </section>
        </div>
      </div>

      <NetworkVisualizer
        activations={result?.activations}
        riskScore={result?.risk_score}
        riskLevel={result?.risk_level}
        loading={loading}
      />

      <ModelPerformance />

      <section className="ai-model-info">
        <div>
          <BrainCircuit size={19} strokeWidth={1.8} />

          <div>
            <span>Model</span>
            <strong>Bushfire AI Neural Network</strong>
          </div>
        </div>

        <div>
          <span>Analysis</span>
          <strong>Environmental Risk Classification</strong>
        </div>

        <div>
          <span>Inputs</span>
          <strong>Weather · Seasonal Indicators · Dryness</strong>
        </div>

        <div>
          <span>Status</span>
          <strong className="model-online">
            <i />
            Operational
          </strong>
        </div>
      </section>
    </div>
  );
}

export default AIPrediction;
