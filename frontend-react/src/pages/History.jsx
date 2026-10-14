import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  CalendarClock,
  Clock3,
  History as HistoryIcon,
  MapPin,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { onAuthStateChanged } from "firebase/auth";
import {
  collection,
  deleteDoc,
  doc,
  onSnapshot,
  query,
  orderBy,
} from "firebase/firestore";
import { auth, db } from "../firebase";

import "./History.css";

function formatDate(timestamp) {
  if (!timestamp?.toDate) return "Processing date";

  return timestamp.toDate().toLocaleString("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function History({ onViewMap }) {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [records, setRecords] = useState([]);
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
      setRecords([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    const historyQuery = query(
      collection(db, "users", user.uid, "predictionHistory"),
      orderBy("createdAt", "desc")
    );

    return onSnapshot(
      historyQuery,
      (snapshot) => {
        setRecords(
          snapshot.docs.map((item) => ({
            id: item.id,
            ...item.data(),
          }))
        );
        setLoading(false);
      },
      (snapshotError) => {
        console.error("History loading failed:", snapshotError);
        setError("Unable to load prediction history.");
        setLoading(false);
      }
    );
  }, [authReady, user]);

  const removeRecord = async (record) => {
    if (!user || busy) return;

    if (!window.confirm(`Delete prediction for ${record.name}?`)) {
      return;
    }

    setBusy(true);
    setError("");

    try {
      await deleteDoc(
        doc(db, "users", user.uid, "predictionHistory", record.id)
      );
    } catch (deleteError) {
      console.error("History deletion failed:", deleteError);
      setError("Unable to delete prediction.");
    } finally {
      setBusy(false);
    }
  };

  const clearHistory = async () => {
    if (!user || busy || records.length === 0) return;

    if (
      !window.confirm(
        `Permanently delete all ${records.length} saved predictions?`
      )
    ) {
      return;
    }

    setBusy(true);
    setError("");

    try {
      for (const record of records) {
        await deleteDoc(
          doc(db, "users", user.uid, "predictionHistory", record.id)
        );
      }
    } catch (deleteError) {
      console.error("History clearing failed:", deleteError);
      setError("Some predictions could not be deleted.");
    } finally {
      setBusy(false);
    }
  };

  const highRiskCount = records.filter((record) =>
    ["HIGH", "VERY_HIGH", "EXTREME"].includes(
      String(record.risk_level || "")
        .toUpperCase()
        .replace(/\s+/g, "_")
    )
  ).length;

  const latestDate = records[0]?.createdAt;

  return (
    <div className="history-page">
      <div className="history-heading">
        <div>
          <span className="history-eyebrow">
            PERSONAL INTELLIGENCE
          </span>
          <h1>Prediction History</h1>
          <p>
            Review your previous bushfire risk assessments
            and revisit analysed locations.
          </p>
        </div>

        {user && records.length > 0 && (
          <button
            className="history-clear"
            type="button"
            onClick={clearHistory}
            disabled={busy}
          >
            <Trash2 size={15} />
            Clear History
          </button>
        )}
      </div>

      {!authReady || loading ? (
        <div className="history-message">
          Loading your prediction history...
        </div>
      ) : !user ? (
        <div className="history-message">
          <HistoryIcon size={36} strokeWidth={1.4} />
          <h2>Your history is private</h2>
          <p>
            Sign in with Google to save and access your
            bushfire risk assessments across devices.
          </p>
        </div>
      ) : (
        <>
          <div className="history-stats">
            <div className="history-stat">
              <HistoryIcon size={19} />
              <span>Total Predictions</span>
              <strong>{records.length}</strong>
            </div>

            <div className="history-stat">
              <ShieldAlert size={19} />
              <span>High Risk Results</span>
              <strong>{highRiskCount}</strong>
            </div>

            <div className="history-stat">
              <CalendarClock size={19} />
              <span>Latest Assessment</span>
              <strong className="history-stat-date">
                {latestDate ? formatDate(latestDate) : "None yet"}
              </strong>
            </div>
          </div>

          {error && (
            <div className="history-error" role="alert">
              {error}
            </div>
          )}

          {records.length === 0 ? (
            <div className="history-message">
              <HistoryIcon size={36} strokeWidth={1.4} />
              <h2>No predictions yet</h2>
              <p>
                Run your first bushfire risk assessment
                to start building your history.
              </p>
            </div>
          ) : (
            <div className="history-card">
              <div className="history-card-heading">
                <div>
                  <span className="history-eyebrow">
                    SAVED ASSESSMENTS
                  </span>
                  <h2>Recent Predictions</h2>
                </div>
                <span className="history-count">
                  {records.length} records
                </span>
              </div>

              <div className="history-list">
                {records.map((record) => {
                  const risk = String(
                    record.risk_level || "UNKNOWN"
                  ).toUpperCase();

                  return (
                    <div className="history-row" key={record.id}>
                      <div className="history-location-icon">
                        <MapPin size={18} />
                      </div>

                      <div className="history-location">
                        <strong>
                          {record.name || "Selected location"}
                        </strong>
                        <span>
                          <Clock3 size={13} />
                          {formatDate(record.createdAt)}
                        </span>
                      </div>

                      <span
                        className={`history-risk history-risk-${risk
                          .toLowerCase()
                          .replace(/\s+/g, "-")}`}
                      >
                        {risk.replace(/_/g, " ")}
                      </span>

                      <div className="history-score">
                        <strong>
                          {typeof record.risk_score === "number"
                            ? `${record.risk_score.toFixed(2)}%`
                            : "--"}
                        </strong>
                        <span>Risk score</span>
                      </div>

                      <div className="history-actions">
                        <button
                          type="button"
                          className="history-view"
                          onClick={() => onViewMap?.(record)}
                          title="View prediction on Risk Map"
                        >
                          <ArrowUpRight size={15} />
                          View Map
                        </button>

                        <button
                          type="button"
                          className="history-delete"
                          onClick={() => removeRecord(record)}
                          disabled={busy}
                          title="Delete prediction"
                          aria-label={`Delete ${record.name} prediction`}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default History;
