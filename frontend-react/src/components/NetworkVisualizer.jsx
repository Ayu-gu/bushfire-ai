import "./NetworkVisualizer.css";

function normalise(values = []) {
  if (!values.length) return [];

  const max = Math.max(
    ...values.map((value) => Math.abs(value)),
    0.0001
  );

  return values.map((value) => ({
    value,
    intensity: Math.min(
      Math.abs(value) / max,
      1
    ),
  }));
}


function Layer({
  title,
  values,
  delay,
  isOutput = false,
}) {

  const neurons = normalise(values);

  return (
    <div className="network-layer">

      <div className="layer-label">
        {title}
      </div>

      <div className="neurons">

        {neurons.map(
          (neuron, index) => {

            const style = {
              "--intensity":
                neuron.intensity,

              "--delay":
                `${delay + index * 20}ms`,
            };

            return (
              <div
                className={
                  isOutput
                    ? "neuron output-neuron"
                    : "neuron"
                }
                style={style}
                key={index}
                title={
                  `Neuron ${index + 1}: ` +
                  neuron.value.toFixed(4)
                }
              >
                <span />
              </div>
            );
          }
        )}

      </div>

      <div className="layer-count">
        {values.length} neurons
      </div>

    </div>
  );
}


function FlowArrow({ delay }) {
  return (
    <div
      className="flow-arrow"
      style={{
        "--delay": `${delay}ms`,
      }}
    >
      <div className="flow-line" />
      <span>›</span>
    </div>
  );
}


function NetworkVisualizer({
  activations,
  riskScore,
  riskLevel,
}) {

  if (!activations) {

    return (
      <section className="network-panel">

        <div className="network-header">

          <div>
            <h3>Live Neural Network</h3>

            <p>
              Run a bushfire analysis to inspect
              the model's forward pass.
            </p>
          </div>

        </div>

        <div className="network-empty">
          Waiting for model activations...
        </div>

      </section>
    );
  }


  const outputValue =
    activations.output ?? 0;


  return (
    <section className="network-panel">

      <div className="network-header">

        <div>
          <h3>Live Neural Network</h3>

          <p>
            Actual PyTorch activations from the
            latest prediction.
          </p>
        </div>

        <div className="network-result">

          <span>
            {riskLevel || "UNKNOWN"}
          </span>

          <strong>
            {riskScore?.toFixed
              ? riskScore.toFixed(2)
              : riskScore}%
          </strong>

        </div>

      </div>


      <div className="network-flow">

        <Layer
          title="Input"
          values={activations.input || []}
          delay={0}
        />

        <FlowArrow delay={250} />

        <Layer
          title="Hidden 1"
          values={activations.layer1 || []}
          delay={350}
        />

        <FlowArrow delay={650} />

        <Layer
          title="Hidden 2"
          values={activations.layer2 || []}
          delay={750}
        />

        <FlowArrow delay={1000} />

        <Layer
          title="Hidden 3"
          values={activations.layer3 || []}
          delay={1100}
        />

        <FlowArrow delay={1350} />

        <Layer
          title="Output"
          values={[outputValue]}
          delay={1450}
          isOutput
        />

      </div>


      <div className="network-explanation">

        <div>
          <span>Architecture</span>
          <strong>
            15 → 32 → 16 → 8 → 1
          </strong>
        </div>

        <div>
          <span>Activation</span>
          <strong>ReLU</strong>
        </div>

        <div>
          <span>Output</span>
          <strong>Sigmoid probability</strong>
        </div>

      </div>

    </section>
  );
}


export default NetworkVisualizer;