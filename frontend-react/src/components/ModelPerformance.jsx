import { useState } from "react";
import { Activity, ChevronDown, FlaskConical } from "lucide-react";
import "./ModelPerformance.css";

const models = [
  {
    name: "Deep Neural Network",
    architecture: "111 → 256 → 128 → 64 → 1",
    auc: 0.6417028239877033,
    accuracy: 0.5908435472242249,
    precision: 0.5823529411764706,
    recall: 0.642393655371305,
    f1: 0.6109016112444292,
    trainAuc: 0.692103724584949,
  },
  {
    name: "Temporal LSTM",
    architecture: "31-day weather sequence",
    auc: 0.6515849875946644,
    accuracy: 0.6110310021629416,
    precision: 0.5947109471094711,
    recall: 0.6971881759192502,
    f1: 0.641885164288085,
    trainAuc: 0.6866173645180377,
  },
  {
    name: "Random Forest",
    architecture: "500 trees · Depth 20",
    auc: 0.6917717251915381,
    accuracy: 0.6272530641672674,
    precision: 0.5947396672034353,
    recall: 0.798846431146359,
    f1: 0.6818461538461539,
    trainAuc: 0.937448760110119,
  },
];

const percent = (value) => `${(value * 100).toFixed(2)}%`;

function ModelPerformance() {
  const [expanded, setExpanded] = useState(false);

  return (
    <section className="mp-section">
      <button
        className="mp-toggle"
        type="button"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span className="mp-toggle-left">
          <FlaskConical size={19} strokeWidth={1.8} />

          <span>
            <strong>Model Performance & Research</strong>
            <small>Historical validation · Experimental models</small>
          </span>
        </span>

        <ChevronDown
          size={18}
          className={expanded ? "mp-chevron open" : "mp-chevron"}
        />
      </button>

      {expanded && (
        <div className="mp-content">
          <div className="mp-intro">
            <Activity size={17} />
            <p>
              Research models were evaluated using matched historical
              fire/non-fire observations and event-aware data splitting.
              These results are separate from the deployed V04 model.
            </p>
          </div>

          <div className="mp-heading">
            <h3>Validation ROC-AUC</h3>
            <span>Higher is better · 1.0 = perfect ranking</span>
          </div>

          <div className="mp-bars">
            {models.map((model) => (
              <div className="mp-bar-row" key={model.name}>
                <div className="mp-bar-label">
                  <strong>{model.name}</strong>
                  <span>{model.architecture}</span>
                </div>

                <div className="mp-bar-track">
                  <div
                    className="mp-bar-fill"
                    style={{ width: `${model.auc * 100}%` }}
                  />
                </div>

                <strong className="mp-bar-value">
                  {model.auc.toFixed(4)}
                </strong>
              </div>
            ))}
          </div>

          <div className="mp-heading">
            <h3>Detailed validation metrics</h3>
            <span>Held-out validation data · Not final test scores</span>
          </div>

          <div className="mp-table-wrap">
            <table className="mp-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Accuracy</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>Train AUC</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.name}>
                    <td>{model.name}</td>
                    <td>{percent(model.accuracy)}</td>
                    <td>{percent(model.precision)}</td>
                    <td>{percent(model.recall)}</td>
                    <td>{model.f1.toFixed(4)}</td>
                    <td>{model.trainAuc.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mp-method">
            <div>
              <strong>18,494</strong>
              <span>Historical observations</span>
            </div>
            <div>
              <strong>9,247</strong>
              <span>Matched pairs</span>
            </div>
            <div>
              <strong>70 / 15 / 15</strong>
              <span>Train / validation / test split</span>
            </div>
            <div>
              <strong>31 days</strong>
              <span>LSTM weather history</span>
            </div>
          </div>

          <p className="mp-disclaimer">
            These are experimental validation results, not live fire
            probabilities, official Fire Danger Ratings, or measured
            performance of the deployed V04 model. The final test set
            was not used for these comparisons.
          </p>
        </div>
      )}
    </section>
  );
}

export default ModelPerformance;
