import {
  Flame,
  ExternalLink,
  ArrowUpRight,
  ShieldAlert,
} from "lucide-react";

import "./Footer.css";

export default function Footer({ onNavigate }) {
  const navigate = (page) => {
    onNavigate?.(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <footer className="platform-footer">
      <div className="platform-footer-content">
        <div className="platform-footer-brand">
          <div className="platform-footer-logo">
            <Flame size={20} />
            <strong>Bushfire AI</strong>
          </div>

          <p>
            An intelligent platform for exploring
            Australian bushfire risk through environmental
            data, interactive mapping and machine learning.
          </p>

          <span className="platform-footer-project">
            Educational Research Project · 2026
          </span>
        </div>

        <div className="platform-footer-column">
          <h3>Explore</h3>

          <button onClick={() => navigate("Dashboard")}>
            Dashboard
          </button>

          <button onClick={() => navigate("Risk Map")}>
            Risk Map
          </button>

          <button onClick={() => navigate("AI Prediction")}>
            AI Prediction
          </button>

          <button onClick={() => navigate("Fire Warnings")}>
            Fire Warnings
          </button>
        </div>

        <div className="platform-footer-column">
          <h3>Platform</h3>

          <button onClick={() => navigate("About")}>
            About the Project
          </button>

          <button onClick={() => navigate("History")}>
            Prediction History
          </button>

          <button onClick={() => navigate("Settings")}>
            Settings & Privacy
          </button>

          <button onClick={() => navigate("Contact")}>
            Contact Developer
          </button>
        </div>

        <div className="platform-footer-column">
          <h3>Connect</h3>

          <a
            href="https://www.linkedin.com/in/ayubg"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink size={15} />
            LinkedIn
            <ArrowUpRight size={13} />
          </a>

          <a
            href="https://github.com/Ayu-gu"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink size={15} />
            GitHub
            <ArrowUpRight size={13} />
          </a>
        </div>
      </div>

      <div className="platform-footer-bottom">
        <div>
          © {new Date().getFullYear()} Bushfire AI
          <span className="platform-footer-divider">·</span>
          Developed by Ayub Gurung
        </div>

        <span className="platform-footer-disclaimer">
          <ShieldAlert size={13} />
          Experimental AI predictions. Not official emergency advice.
        </span>
      </div>
    </footer>
  );
}
