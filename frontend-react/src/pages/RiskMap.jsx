import { useEffect, useState } from "react";
import { BrainCircuit, MapPin, ShieldAlert, Compass, Bookmark } from "lucide-react";
import {
  addDoc,
  collection,
  getDocs,
  onSnapshot,
  serverTimestamp,
} from "firebase/firestore";
import { auth, db } from "../firebase";
import MapTilerMap from "../components/MapTilerMap";
import "./RiskMap.css";

export default function RiskMap({
  location,
  setLocation,
  result,
  loading,
  error,
  onAnalyse,
  analysedLocations = [],
  onSelectAnalysis,
  onRemoveAnalysis,
  onClearAnalyses,
}) {
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [savedLocations, setSavedLocations] = useState([]);
  const [bookmarksReady, setBookmarksReady] = useState(false);

  useEffect(() => {
    let unsubscribeBookmarks = () => {};

    const unsubscribeAuth = auth.onAuthStateChanged((user) => {
      unsubscribeBookmarks();
      setSavedLocations([]);
      setBookmarksReady(false);

      if (!user) {
        setBookmarksReady(true);
        return;
      }

      unsubscribeBookmarks = onSnapshot(
        collection(db, "users", user.uid, "savedLocations"),
        (snapshot) => {
          setSavedLocations(snapshot.docs.map((item) => item.data()));
          setBookmarksReady(true);
        },
        (error) => {
          console.error("Unable to check bookmarks:", error);
          setBookmarksReady(false);
        }
      );
    });

    return () => {
      unsubscribeAuth();
      unsubscribeBookmarks();
    };
  }, []);

  useEffect(() => {
    setSaveMessage("");
  }, [location?.lat, location?.lng]);

  const alreadyBookmarked = Boolean(
    location &&
    savedLocations.some(
      (saved) =>
        Number(saved.lat).toFixed(5) ===
          Number(location.lat).toFixed(5) &&
        Number(saved.lng).toFixed(5) ===
          Number(location.lng).toFixed(5)
    )
  );

  const saveLocation = async () => {
    if (!location || saving || alreadyBookmarked || !bookmarksReady) return;

    const user = auth.currentUser;

    if (!user) {
      setSaveMessage("Please sign in to save locations.");
      return;
    }

    const customName = window.prompt(
      "Give this location a name (optional):",
      ""
    );

    if (customName === null) return;

    setSaving(true);
    setSaveMessage("");

    try {
      const savedCollection = collection(
        db,
        "users",
        user.uid,
        "savedLocations"
      );

      const existingLocations = await getDocs(savedCollection);

      const alreadySaved = existingLocations.docs.some((item) => {
        const saved = item.data();

        return (
          Number(saved.lat).toFixed(5) ===
            Number(location.lat).toFixed(5) &&
          Number(saved.lng).toFixed(5) ===
            Number(location.lng).toFixed(5)
        );
      });

      if (alreadySaved) {
        setSaveMessage("This location is already saved.");
        return;
      }

      await addDoc(
        collection(db, "users", user.uid, "savedLocations"),
        {
          name: location.name || "Selected location",
          customName: customName.trim(),
          lat: location.lat,
          lng: location.lng,
          createdAt: serverTimestamp(),
        }
      );

      setSaveMessage("Location saved successfully.");
    } catch (error) {
      console.error("Unable to save location:", error);
      setSaveMessage("Unable to save location. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const score = result?.risk_score;
  const level = result?.risk_level || "Not analysed";

  return (
    <div className="risk-explorer">
      <header className="risk-explorer-header">
        <div>
          <span className="risk-explorer-eyebrow">
            GEOSPATIAL INTELLIGENCE
          </span>
          <h1>Bushfire Risk Map</h1>
          <p>
            Explore Australian locations and assess bushfire risk
            using environmental observations and AI predictions.
          </p>
        </div>

        <span className="risk-explorer-badge">
          <Compass size={16} />
          Interactive Risk Explorer
        </span>
      </header>


      <div className="risk-explorer-legend">
        <span>MODEL RISK LEVELS</span>
        <div><i className="risk-dot very-low" /> Very Low</div>
        <div><i className="risk-dot low" /> Low</div>
        <div><i className="risk-dot moderate" /> Moderate</div>
        <div><i className="risk-dot high" /> High</div>
        <div><i className="risk-dot very-high" /> Very High</div>
        <div><i className="risk-dot extreme" /> Extreme</div>
        <small>Experimental AI predictions, not official fire danger ratings.</small>
      </div>

      <div className="risk-explorer-layout">
        <section className="risk-explorer-map-panel">
          <div className="risk-explorer-map-heading">
            <div>
              <h2>Geographical Risk Explorer</h2>
              <p>Select a location on the map to begin analysis.</p>
            </div>
            <div className="risk-map-toolbar">
              <span className="risk-explorer-map-status">
                Interactive Map
              </span>

              <button
                type="button"
                className="risk-clear-map"
                onClick={onClearAnalyses}
                disabled={analysedLocations.length === 0}
              >
                Clear Map
              </button>
            </div>
          </div>

          <div className="risk-explorer-map-container">
            <MapTilerMap
              location={location}
              setLocation={setLocation}
              analysedLocations={analysedLocations}
              onSelectAnalysis={onSelectAnalysis}
            />
          </div>

          <div className="risk-explorer-map-footer">
            <MapPin size={15} />
            Map markers indicate selected locations, not regional risk coverage.
          </div>
        </section>

        <aside className="risk-explorer-side">
          <section className="risk-explorer-panel">
            <span className="risk-explorer-panel-label">
              LOCATION INTELLIGENCE
            </span>
            <h2>Selected Location</h2>

            {location ? (
              <div className="risk-explorer-location">
                <strong>{location.name || "Selected map location"}</strong>

                <div className="risk-explorer-coordinates">
                  <div>
                    <span>Latitude</span>
                    <strong>{location.lat.toFixed(4)}</strong>
                  </div>
                  <div>
                    <span>Longitude</span>
                    <strong>{location.lng.toFixed(4)}</strong>
                  </div>
                </div>
              </div>
            ) : (
              <p className="risk-explorer-empty">
                Click anywhere on the map or search for a location.
              </p>
            )}

            <button
              className={`risk-save-location ${
                alreadyBookmarked ? "is-saved" : ""
              }`}
              type="button"
              onClick={saveLocation}
              disabled={
                !location ||
                saving ||
                alreadyBookmarked ||
                !bookmarksReady
              }
            >
              <Bookmark size={17} />
              {saving
                ? "Saving..."
                : alreadyBookmarked
                  ? "Already Saved"
                  : !bookmarksReady
                    ? "Checking Saved Locations..."
                    : "Save Location"}
            </button>

            {saveMessage && (
              <p className="risk-save-message" role="status">
                {saveMessage}
              </p>
            )}

            <button
              className="risk-explorer-analyse"
              type="button"
              onClick={onAnalyse}
              disabled={!location || loading}
            >
              <BrainCircuit size={17} />
              {loading ? "Analysing Location..." : "Analyse Bushfire Risk"}
            </button>

            {error && <p className="risk-explorer-error">{error}</p>}
          </section>

          <section className="risk-explorer-panel">
            <span className="risk-explorer-panel-label">
              AI RISK ASSESSMENT
            </span>
            <h2>Prediction Result</h2>

            <div className="risk-explorer-result">
              <span>Predicted Risk Level</span>
              <strong>{level}</strong>
              <p>
                {score !== undefined
                  ? `${score}% predicted risk score`
                  : "Select a location and run an analysis."}
              </p>
            </div>

            <div className="risk-explorer-conditions">
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
                <span>Wind Speed</span>
                <strong>
                  {result ? `${result.current_wind} km/h` : "--"}
                </strong>
              </div>
              <div>
                <span>Rainfall (30d)</span>
                <strong>
                  {result ? `${result.rain_last_30_days} mm` : "--"}
                </strong>
              </div>
            </div>
          </section>

          <section className="risk-explorer-panel risk-explorer-disclaimer">
            <ShieldAlert size={19} />
            <div>
              <strong>Research Prediction</strong>
              <p>
                AI-generated risk estimates are experimental and
                are not official Australian Fire Danger Ratings.
                Always follow emergency service warnings.
              </p>
            </div>
          </section>
        </aside>
      </div>

      <section className="risk-comparison">
        <div className="risk-comparison-header">
          <div>
            <span className="risk-explorer-panel-label">
              GEOGRAPHICAL COMPARISON
            </span>
            <h2>Analysed Locations</h2>
            <p>Compare AI predictions across selected locations.</p>
          </div>

          <div className="risk-comparison-actions">
            <span className="risk-comparison-count">
              {analysedLocations.length} locations
            </span>

            <button
              type="button"
              className="risk-clear-all"
              onClick={onClearAnalyses}
              disabled={analysedLocations.length === 0}
            >
              Clear All
            </button>
          </div>
        </div>

        {analysedLocations.length === 0 ? (
          <div className="risk-comparison-empty">
            No locations analysed yet. Select a location on the map
            and run an AI prediction to begin comparing locations.
          </div>
        ) : (
          <div className="risk-comparison-table-wrap">
            <table className="risk-comparison-table">
              <thead>
                <tr>
                  <th>Location</th>
                  <th>AI Risk</th>
                  <th>Risk Score</th>
                  <th>Temperature</th>
                  <th>Humidity</th>
                  <th>Wind</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {analysedLocations.map((item) => (
                  <tr
                    key={item.id}
                    className={`risk-comparison-row ${
                      location?.lat === item.lat &&
                      location?.lng === item.lng
                        ? "risk-comparison-row--selected"
                        : ""
                    }`}
                    onClick={() => onSelectAnalysis?.(item)}
                  >
                    <td>
                      <strong>{item.name}</strong>
                      <small>
                        {item.lat.toFixed(4)}, {item.lng.toFixed(4)}
                      </small>
                    </td>

                    <td>
                      <span
                        className={`risk-table-level ${String(
                          item.risk_level
                        ).toLowerCase().replace(/\s+/g, "-")}`}
                      >
                        {item.risk_level}
                      </span>
                    </td>

                    <td><strong>{item.risk_score}%</strong></td>
                    <td>{item.current_temp}°C</td>
                    <td>{item.current_humidity}%</td>
                    <td>{item.current_wind} km/h</td>
                    <td>
                      <button
                        type="button"
                        className="risk-remove-item"
                        onClick={(event) => {
                          event.stopPropagation();
                          onRemoveAnalysis?.(item.id);
                        }}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
