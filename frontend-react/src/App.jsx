import ClimateNews from "./pages/ClimateNews";
import { useState } from "react";
import {
  LayoutDashboard,
  Map,
  MapPin,
  BrainCircuit,
  TriangleAlert,
  Newspaper,
  History,
  Bookmark,
  Settings,
  Info,
} from "lucide-react";

import Header from "./components/Header";
import MapTilerMap from "./components/MapTilerMap";
import NetworkVisualizer from "./components/NetworkVisualizer";
import AIPrediction from "./pages/AIPrediction";
import FireWarnings from "./pages/FireWarnings";

import "./App.css";

const DEV_MODE = false;

function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [location, setLocation] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyseRisk = async () => {
    if (!location) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch("/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          latitude: location.lat,
          longitude: location.lng,
        }),
      });

      if (!response.ok) {
        throw new Error("Prediction request failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Unable to analyse this location.");
    } finally {
      setLoading(false);
    }
  };

  const navigation = [
    {
      label: "Dashboard",
      icon: LayoutDashboard,
    },
    {
      label: "Risk Map",
      icon: Map,
    },
    {
      label: "AI Prediction",
      icon: BrainCircuit,
    },
    {
      label: "Fire Warnings",
      icon: TriangleAlert,
    },
    {
      label: "Climate News",
      icon: Newspaper,
    },
    {
      label: "History",
      icon: History,
    },
  ];

  const secondaryNavigation = [
    {
      label: "Saved Locations",
      icon: Bookmark,
    },
    {
      label: "Settings",
      icon: Settings,
    },
    {
      label: "About",
      icon: Info,
    },
  ];

  return (
    <div className="app">
      <Header setLocation={setLocation} />

      <div className="app-body">
        <aside className="sidebar">
          <nav
            className="sidebar-nav"
            aria-label="Main navigation"
          >
            <div className="sidebar-section">
              <span className="sidebar-section-label">
                Intelligence
              </span>

              {navigation.map((item) => {
                const Icon = item.icon;

                return (
                  <button
                    key={item.label}
                    className={`sidebar-item ${
                      activePage === item.label ? "active" : ""
                    }`}
                    onClick={() => setActivePage(item.label)}
                    type="button"
                  >

                    <Icon
                      className="sidebar-icon"
                      size={18}
                      strokeWidth={1.8}
                    />

                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="sidebar-divider" />

            <div className="sidebar-section">
              <span className="sidebar-section-label">
                Workspace
              </span>

              {secondaryNavigation.map((item) => {
                const Icon = item.icon;

                return (
                  <button
                     key={item.label}
                     className={`sidebar-item ${
                      activePage === item.label ? "active" : ""
                     }`}
                     onClick={() => setActivePage(item.label)}
                     type="button"
                     
                  >

                    <Icon
                      className="sidebar-icon"
                      size={18}
                      strokeWidth={1.8}
                    />

                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </nav>

          <div className="sidebar-footer">
            <span className="sidebar-system-dot" />

            <div>
              <strong>System operational</strong>
              <span>Bushfire intelligence platform</span>
            </div>
          </div>
        </aside>

        <main className="main">
        {activePage === "Fire Warnings" ? (
          <FireWarnings />
        ) : activePage === "Climate News" ? (
          <ClimateNews />
        ) : activePage === "AI Prediction" ? (
          <AIPrediction
          location={location}
          result={result}
          loading={loading}
          error={error}
          onAnalyse={analyseRisk}
          />
        ) : (
          <>
          <header className="dashboard-header">
            <div>
              <span className="dashboard-eyebrow">
                Bushfire Intelligence
              </span>

              <h1>Bushfire Risk Dashboard</h1>

              <p>
                Explore locations and assess bushfire risk
                using environmental data and AI analysis.
              </p>
            </div>
          </header>

          <div className="dashboard">
            <section className="map-card">
              <MapTilerMap
                location={location}
                setLocation={setLocation}
              />
            </section>

            {DEV_MODE && (
              <NetworkVisualizer
                activations={result?.activations}
                riskScore={result?.risk_score}
                riskLevel={result?.risk_level}
              />
            )}

            <section className="risk-card">
              <div className="risk-card-header">
                <div>
                  <span className="panel-eyebrow">
                    Location Intelligence
                  </span>

                  <h2>Selected Location</h2>
                </div>
              </div>

              <div className="location-box">
  {location ? (
    <>
      {location.name && (
        <div className="selected-place">
          <MapPin
            size={17}
            strokeWidth={1.8}
          />

          <div>
            <strong>{location.name}</strong>

            <span>
              Selected location
            </span>
          </div>
        </div>
      )}

      <div className="coordinates">
        <div>
          <span>Latitude</span>
          <strong>
            {location.lat.toFixed(4)}
          </strong>
        </div>

        <div>
          <span>Longitude</span>
          <strong>
            {location.lng.toFixed(4)}
          </strong>
        </div>
      </div>
    </>
  ) : (
                  <div className="empty-location">
                    <Map
                      size={18}
                      strokeWidth={1.8}
                    />

                    <span>
                      Select a point on the map to begin
                      analysis.
                    </span>
                  </div>
                )}
              </div>

              <div className="risk-result">
                <div className="risk-result-heading">
                  <span>Predicted Risk</span>

                  {result && (
                    <span className="risk-status">
                      AI assessment
                    </span>
                  )}
                </div>

                <strong className="risk-level">
                  {result
                    ? result.risk_level
                    : "--"}
                </strong>

                <p>
                  {result
                    ? `${result.risk_score}% predicted risk score`
                    : "Run an analysis to calculate the current bushfire risk."}
                </p>
              </div>

              <div className="conditions-header">
                <span className="panel-eyebrow">
                  Current Inputs
                </span>

                <h2>Environmental Conditions</h2>
              </div>

              <div className="conditions">
                <div className="condition-item">
                  <span>Temperature</span>

                  <strong>
                    {result
                      ? `${result.current_temp}°C`
                      : "--"}
                  </strong>
                </div>

                <div className="condition-item">
                  <span>Humidity</span>

                  <strong>
                    {result
                      ? `${result.current_humidity}%`
                      : "--"}
                  </strong>
                </div>

                <div className="condition-item">
                  <span>Wind</span>

                  <strong>
                    {result
                      ? `${result.current_wind} km/h`
                      : "--"}
                  </strong>
                </div>

                <div className="condition-item">
                  <span>Rainfall · 30d</span>

                  <strong>
                    {result
                      ? `${result.rain_last_30_days} mm`
                      : "--"}
                  </strong>
                </div>
              </div>

              <button
                className="analyse"
                disabled={!location || loading}
                onClick={analyseRisk}
                type="button"
              >
                <BrainCircuit
                  size={18}
                  strokeWidth={1.9}
                />

                <span>
                  {loading
                    ? "Analysing..."
                    : "Analyse Bushfire Risk"}
                </span>
              </button>

              {error && (
                <p className="error-message">
                  {error}
                </p>
              )}
            </section>
          </div>
        </>
        )}
        </main>
      </div>
    </div>
  );
}

export default App;