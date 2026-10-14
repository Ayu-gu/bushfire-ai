import { useEffect, useState } from "react";
import {
  Bookmark,
  MapPin,
  ArrowUpRight,
  Trash2,
} from "lucide-react";
import { onAuthStateChanged } from "firebase/auth";
import {
  collection,
  deleteDoc,
  doc,
  onSnapshot,
  orderBy,
  query,
} from "firebase/firestore";

import { auth, db } from "../firebase";
import "./SavedLocations.css";

function SavedLocations({ onViewMap }) {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    return onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setAuthReady(true);
    });
  }, []);

  useEffect(() => {
    if (!authReady || !user) {
      setLocations([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    const savedQuery = query(
      collection(db, "users", user.uid, "savedLocations"),
      orderBy("createdAt", "desc")
    );

    return onSnapshot(
      savedQuery,
      (snapshot) => {
        setLocations(
          snapshot.docs.map((item) => ({
            id: item.id,
            ...item.data(),
          }))
        );
        setLoading(false);
      },
      (snapshotError) => {
        console.error("Saved locations failed:", snapshotError);
        setError("Unable to load saved locations.");
        setLoading(false);
      }
    );
  }, [authReady, user]);

  const removeLocation = async (location) => {
    if (!user || busy) return;

    if (
      !window.confirm(
        `Remove ${location.customName || location.name} from saved locations?`
      )
    ) {
      return;
    }

    setBusy(true);
    setError("");

    try {
      await deleteDoc(
        doc(db, "users", user.uid, "savedLocations", location.id)
      );
    } catch (deleteError) {
      console.error("Location deletion failed:", deleteError);
      setError("Unable to remove this location.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="saved-page">
      <div className="saved-heading">
        <div>
          <span className="saved-eyebrow">
            PERSONAL WORKSPACE
          </span>
          <h1>Saved Locations</h1>
          <p>
            Your bookmarked places, ready for future
            bushfire risk assessments.
          </p>
        </div>

        <span className="saved-count">
          {locations.length} saved
        </span>
      </div>

      {!authReady || loading ? (
        <div className="saved-empty">
          Loading saved locations...
        </div>
      ) : !user ? (
        <div className="saved-empty">
          <Bookmark size={36} strokeWidth={1.4} />
          <h2>Your places, securely saved</h2>
          <p>
            Sign in with Google to bookmark locations
            and access them across devices.
          </p>
        </div>
      ) : (
        <>
          {error && (
            <div className="saved-error" role="alert">
              {error}
            </div>
          )}

          {locations.length === 0 ? (
            <div className="saved-empty">
              <Bookmark size={36} strokeWidth={1.4} />
              <h2>No saved locations yet</h2>
              <p>
                Select a location on the map and save
                it here for quick access later.
              </p>
            </div>
          ) : (
            <div className="saved-grid">
              {locations.map((location) => (
                <article
                  className="saved-card"
                  key={location.id}
                >
                  <div className="saved-card-icon">
                    <MapPin size={20} />
                  </div>

                  <div className="saved-card-body">
                    <h2>
                      {location.customName ||
                        location.name ||
                        "Saved location"}
                    </h2>

                    {location.customName && (
                      <p>{location.name}</p>
                    )}

                    <span>
                      {Number(location.lat).toFixed(4)},
                      {" "}
                      {Number(location.lng).toFixed(4)}
                    </span>
                  </div>

                  <div className="saved-card-actions">
                    <button
                      type="button"
                      onClick={() => onViewMap?.(location)}
                    >
                      <ArrowUpRight size={15} />
                      View Map
                    </button>

                    <button
                      type="button"
                      className="saved-delete"
                      onClick={() => removeLocation(location)}
                      disabled={busy}
                      aria-label="Remove saved location"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default SavedLocations;
