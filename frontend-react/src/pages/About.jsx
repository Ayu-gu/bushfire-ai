import {
  BrainCircuit,
  CloudSun,
  Database,
  Layers3,
  MapPinned,
  ShieldAlert,
  Code2,
  ArrowRight,
  Info,
  ExternalLink,
} from "lucide-react";

import "./About.css";

const process = [
  {
    number: "01",
    title: "Select a Location",
    description:
      "Choose an Australian location using the interactive map or location search.",
    icon: MapPinned,
  },
  {
    number: "02",
    title: "Collect Environmental Data",
    description:
      "Retrieve available weather observations and environmental information relevant to bushfire conditions.",
    icon: CloudSun,
  },
  {
    number: "03",
    title: "Process Model Inputs",
    description:
      "Prepare environmental measurements and derived features for the trained neural network.",
    icon: Database,
  },
  {
    number: "04",
    title: "Generate Risk Assessment",
    description:
      "Run the trained model and display its estimated bushfire risk alongside environmental context.",
    icon: BrainCircuit,
  },
];

const technologies = [
  {
    title: "Frontend",
    name: "React + Vite",
    description: "Interactive dashboard and responsive interface",
  },
  {
    title: "Backend",
    name: "Node.js + Express",
    description: "API requests and application services",
  },
  {
    title: "Machine Learning",
    name: "Python + PyTorch",
    description: "Neural network inference and model development",
  },
  {
    title: "Mapping",
    name: "MapTiler",
    description: "Interactive geographic visualisation",
  },
  {
    title: "Authentication & Storage",
    name: "Firebase",
    description: "Google sign-in and personal cloud storage",
  },
];

export default function About() {
  return (
    <div className="about-page">
      <header className="about-heading">
        <span className="about-eyebrow">
          ABOUT THE PLATFORM
        </span>

        <h1>Understanding Bushfire AI</h1>

        <p>
          An interactive Australian bushfire risk exploration
          platform combining environmental observations,
          geographic visualisation and machine learning.
        </p>
      </header>

      <section className="about-hero">
        <div className="about-hero-icon">
          <BrainCircuit size={30} />
        </div>

        <div>
          <span>THE PROJECT</span>

          <h2>Turning environmental data into actionable insights</h2>

          <p>
            Bushfire AI is an educational software project
            designed to explore how machine learning can
            support the assessment of environmental conditions
            associated with bushfire risk.
          </p>

          <p>
            Users can select locations, examine environmental
            information, generate model-based assessments,
            and explore results through interactive maps.
          </p>
        </div>
      </section>

      <section className="about-section">
        <div className="about-section-heading">
          <div className="about-section-icon">
            <Layers3 size={20} />
          </div>

          <div>
            <h2>How It Works</h2>
            <p>From location selection to AI-generated assessment</p>
          </div>
        </div>

        <div className="about-process">
          {process.map((step, index) => {
            const Icon = step.icon;

            return (
              <div className="about-process-step" key={step.number}>
                <div className="about-process-top">
                  <span className="about-process-number">
                    {step.number}
                  </span>

                  <Icon size={22} />

                  {index < process.length - 1 && (
                    <ArrowRight
                      size={16}
                      className="about-process-arrow"
                    />
                  )}
                </div>

                <h3>{step.title}</h3>

                <p>{step.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="about-section">
        <div className="about-section-heading">
          <div className="about-section-icon">
            <BrainCircuit size={20} />
          </div>

          <div>
            <h2>Machine Learning Model</h2>
            <p>Understanding the prediction engine</p>
          </div>
        </div>

        <div className="about-model">
          <div className="about-model-highlight">
            <strong>15</strong>
            <span>Environmental and derived input features</span>
          </div>

          <div className="about-model-content">
            <h3>Feedforward Neural Network</h3>

            <p>
              The prediction engine uses a trained PyTorch
              neural network with 15 input features and
              three hidden layers containing 32, 16 and
              8 neurons respectively.
            </p>

            <p>
              Inputs include temperature, humidity, wind,
              rainfall history, seasonal information and
              derived environmental indicators.
            </p>

            <p>
              The model produces a numerical prediction
              that the application uses to communicate
              its estimated risk level.
            </p>
          </div>
        </div>
      </section>

      <section className="about-section">
        <div className="about-section-heading">
          <div className="about-section-icon">
            <Code2 size={20} />
          </div>

          <div>
            <h2>Technology Stack</h2>
            <p>Technologies powering the platform</p>
          </div>
        </div>

        <div className="about-tech-grid">
          {technologies.map((technology) => (
            <div className="about-tech-card" key={technology.title}>
              <span>{technology.title}</span>
              <strong>{technology.name}</strong>
              <p>{technology.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="about-section">
        <div className="about-section-heading">
          <div className="about-section-icon">
            <Database size={20} />
          </div>

          <div>
            <h2>Environmental Data</h2>
            <p>Observations and geographic context</p>
          </div>
        </div>

        <div className="about-text-content">
          <p>
            The platform integrates Australian weather
            observations and geographic mapping information
            to support location-based environmental analysis.
          </p>

          <p>
            Weather observations can vary in freshness,
            geographic coverage and availability. Some
            environmental features may be estimated or
            derived from available inputs.
          </p>

          <p>
            These limitations can affect model predictions,
            particularly when conditions change rapidly
            or observations do not represent the selected
            location precisely.
          </p>
        </div>
      </section>

      <section className="about-warning">
        <div className="about-warning-icon">
          <ShieldAlert size={24} />
        </div>

        <div>
          <h2>Important Safety Information</h2>

          <p>
            Bushfire AI is an educational and experimental
            platform. Its predictions are model-generated
            estimates, not official fire danger ratings,
            emergency alerts or forecasts.
          </p>

          <p>
            Do not use these predictions to make evacuation,
            firefighting or other safety-critical decisions.
            Always follow official emergency services,
            government warnings and local authorities.
          </p>

          <a
            href="https://www.emergency.wa.gov.au/"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink size={15} />
            Example official emergency information
          </a>
        </div>
      </section>

      <footer className="about-footer">
        <Info size={17} />

        <p>
          Bushfire AI is an educational information technology
          project developed to demonstrate the integration
          of artificial intelligence, environmental data,
          cloud services and modern web technologies.
        </p>
      </footer>
    </div>
  );
}
