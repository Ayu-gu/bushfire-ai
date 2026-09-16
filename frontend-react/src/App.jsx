const DEV_MODE = false;
import { useState } from "react";
import { useMap } from "react-leaflet";
import {
  MapContainer,
  TileLayer,
  Marker,
  useMapEvents,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";
import NetworkVisualizer
  from "./components/NetworkVisualizer";


function LocationSelector({ setLocation }) {

  useMapEvents({
    click(event) {
      setLocation({
        lat: event.latlng.lat,
        lng: event.latlng.lng,
      });
    },
  });

  return null;
}
function CurrentLocationButton({ setLocation }) {
  const map = useMap();

  const useCurrentLocation = () => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };

        setLocation(newLocation);

        map.setView(
          [newLocation.lat, newLocation.lng],
          11
        );
      },
      () => {
        alert("Unable to get your current location.");
      }
    );
  };

  return (
    <button
      className="location-button"
      onClick={useCurrentLocation}
      type="button"
    >
      Use My Location
    </button>
  );
}

function App() {

  const [location, setLocation] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyseRisk = async () => {
    if (!location) return;
  
    setLoading(true);
    setError("");
  
    try {
      const response = await fetch(
        "http://localhost:3000/predict",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            latitude: location.lat,
            longitude: location.lng,
          }),
        }
      );
  
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

  return (
    <div className="app">

      <aside className="sidebar">

        <h1>Bushfire AI</h1>
        <p>AI-powered bushfire risk prediction</p>

        <nav>
          <button className="active">
            Dashboard
          </button>

          <button>Risk Prediction</button>
          <button>Image Detection</button>
          <button>History</button>
        </nav>

      </aside>


      <main className="main">

        <header>
          <h2>Bushfire Risk Dashboard</h2>

          <p>
            Select a location to analyse
            bushfire risk using our AI model.
          </p>
        </header>


        <div className="dashboard">

          <section className="map-card">

            <div className="card-title">
              <h3>Interactive Risk Map</h3>
            </div>

            <MapContainer
              center={[-33.5, 147]}
              zoom={6}
              className="map"
            >

              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              <LocationSelector
                setLocation={setLocation}
              />
              <CurrentLocationButton
                setLocation={setLocation}
              />

              {location && (
                <Marker
                  position={[
                    location.lat,
                    location.lng,
                  ]}
                />
              )}

            </MapContainer>

          </section>
          {DEV_MODE && (
            <NetworkVisualizer
            activations={result?.activations}
            riskScore={result?.risk_score}
            riskLevel={result?.risk_level}
            />
          )}


          <section className="risk-card">

            <h3>Selected Location</h3>

            <div className="location-box">

              {location ? (
                <>
                  <p>
                    Latitude:{" "}
                    {location.lat.toFixed(4)}
                  </p>

                  <p>
                    Longitude:{" "}
                    {location.lng.toFixed(4)}
                  </p>
                </>
              ) : (
                <p>Click anywhere on the map</p>
              )}

            </div>


            <div className="risk-result">
              <span>Predicted Risk</span>
              
              <strong>
                {result ? result.risk_level : "--"}
              </strong>
              
              <p>
                {result
                  ? `${result.risk_score}% risk score`
                  : "Select a location and run analysis"}
              </p>
            </div>


            <h3>Environmental Conditions</h3>

            <div className="conditions">

              <div>
                <span>Temperature</span>
                <strong>
                  {result ? `${result.current_temp}°C` : "--"}
                </strong>
              </div>

              <div>
                <span>Humidity</span>
                <strong>
                  {result ? `${result.current_humidity}%` : "--"}
                </strong>
              </div>

              <div>
                <span>Wind</span>
                <strong>
                  {result ? `${result.current_wind} km/h` : "--"}
                </strong>
              </div>

              <div>
                <span>Rainfall 30d</span>
                <strong>
                  {result ? `${result.rain_last_30_days} mm` : "--"}
                </strong>
              </div>

            </div>


            <button
              className="analyse"
              disabled={!location || loading}
              onClick={analyseRisk}
            >
              {loading
                ? "Analysing..."
                : "Analyse Bushfire Risk"}
            </button>

            {error && (
              <p className="error-message">
                {error}
              </p>
            )}

          </section>


        </div>

      </main>

    </div>
  );
}

export default App;