import {
  AlertTriangle,
  ArrowUpRight,
  Bell,
  ExternalLink,
  Info,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import FireIncidentMap from "../components/FireIncidentMap";
import "./FireWarnings.css";

const sources = [
  {
    name: "ACT Emergency Services Agency",
    region: "Australian Capital Territory",
    description:
      "Official emergency warnings, incidents and safety information for Canberra and the ACT.",
    url: "https://esa.act.gov.au/",
    shortName: "ACT ESA",
  },
  {
    name: "NSW Rural Fire Service",
    region: "New South Wales",
    description:
      "Official bushfire incidents, warnings and Fires Near Me information across NSW.",
    url: "https://www.rfs.nsw.gov.au/fire-information/fires-near-me",
    shortName: "NSW RFS",
  },
];

const warningLevels = [
  {
    name: "Advice",
    description: "An incident has started. Stay up to date.",
    className: "advice",
  },
  {
    name: "Watch and Act",
    description: "Conditions are changing. Take action to protect yourself.",
    className: "watch",
  },
  {
    name: "Emergency Warning",
    description: "You may be in danger. Take action immediately.",
    className: "emergency",
  },
];

function FireWarnings() {
  return (
    <div className="fw-page">
      <div className="fw-heading">
        <div>
          <div className="fw-eyebrow">EMERGENCY INTELLIGENCE</div>
          <h1>Fire Warnings</h1>
          <p>
            Official bushfire warnings and emergency information for
            the ACT and New South Wales.
          </p>
        </div>

        <div className="fw-source-badge">
          <ShieldCheck size={16} />
          Official sources
        </div>
      </div>

      <div className="fw-notice">
        <Info size={19} />
        <div>
          <strong>Official warning information</strong>
          <p>
            NSW Rural Fire Service incident data is connected and displayed
            on the map below. ACT emergency incident data is not yet
            integrated. Always check official emergency services for
            current warnings. Bushfire AI predictions are not
            emergency warnings.
          </p>
        </div>
      </div>

      <div className="fw-section-heading">
        <div>
          <h2>Australian Warning Levels</h2>
          <p>Understand the three levels used for emergency warnings.</p>
        </div>
      </div>

      <div className="fw-level-grid">
        {warningLevels.map((level) => (
          <div
            className={`fw-level-card ${level.className}`}
            key={level.name}
          >
            <div className="fw-level-top">
              <AlertTriangle size={20} />
              <span>{level.name}</span>
            </div>
            <p>{level.description}</p>
          </div>
        ))}
      </div>

      <FireIncidentMap />

      <div className="fw-section-heading fw-sources-heading">
        <div>
          <h2>Official Emergency Sources</h2>
          <p>
            Access verified incident updates directly from emergency services.
          </p>
        </div>
      </div>

      <div className="fw-sources">
        {sources.map((source) => (
          <a
            key={source.shortName}
            className="fw-source-card"
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            <div className="fw-source-icon">
              <Bell size={21} />
            </div>

            <div className="fw-source-info">
              <span className="fw-region">{source.region}</span>
              <h3>{source.name}</h3>
              <p>{source.description}</p>
              <span className="fw-visit">
                View official warnings <ArrowUpRight size={15} />
              </span>
            </div>

            <ExternalLink size={17} className="fw-external" />
          </a>
        ))}
      </div>

      <div className="fw-bottom-note">
        <RefreshCw size={16} />
        <span>
          Automated incident updates are planned. Until connected,
          always refer to official emergency services for current information.
        </span>
      </div>
    </div>
  );
}

export default FireWarnings;
