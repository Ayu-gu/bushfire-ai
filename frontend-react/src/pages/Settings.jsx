import { useEffect, useState } from "react";
import {
  CircleUserRound,
  Mail,
  ShieldCheck,
  UserRound,
  Map,
  Satellite,
  Mountain,
  History,
  Bookmark,
  ArrowUpRight,
  LockKeyhole,
  LogOut,
} from "lucide-react";
import { onAuthStateChanged, signOut } from "firebase/auth";

import { auth } from "../firebase";
import "./Settings.css";

export default function Settings({ onNavigate }) {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [accountError, setAccountError] = useState("");

  const handleSignOut = async () => {
    if (signingOut) return;

    setSigningOut(true);
    setAccountError("");

    try {
      await signOut(auth);
    } catch (error) {
      console.error("Unable to sign out:", error);
      setAccountError("Unable to sign out. Please try again.");
    } finally {
      setSigningOut(false);
    }
  };
  const [mapStyle, setMapStyle] = useState(() => {
    const saved = localStorage.getItem("bushfire-map-style");

    return ["streets", "satellite", "terrain"].includes(saved)
      ? saved
      : "streets";
  });

  const updateMapStyle = (style) => {
    localStorage.setItem("bushfire-map-style", style);
    setMapStyle(style);

    window.dispatchEvent(
      new CustomEvent("bushfire-map-style-change", {
        detail: style,
      })
    );
  };

  useEffect(() => {
    return onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setAuthReady(true);
    });
  }, []);

  return (
    <div className="settings-page">
      <header className="settings-heading">
        <span className="settings-eyebrow">
          PERSONAL WORKSPACE
        </span>

        <h1>Settings</h1>

        <p>
          Manage your Bushfire AI account and
          personalise your experience.
        </p>
      </header>

      <section className="settings-section">
        <div className="settings-section-heading">
          <div className="settings-section-icon">
            <UserRound size={20} />
          </div>

          <div>
            <h2>My Account</h2>
            <p>Your connected account information</p>
          </div>
        </div>

        {!authReady ? (
          <div className="settings-account">
            Loading account information...
          </div>
        ) : user ? (
          <div className="settings-account">
            <div className="settings-profile">
              {user.photoURL ? (
                <img
                  src={user.photoURL}
                  alt="Google profile"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="settings-avatar">
                  <CircleUserRound size={28} />
                </div>
              )}

              <div>
                <strong>
                  {user.displayName || "Bushfire AI User"}
                </strong>

                <span>Google Account</span>
              </div>

              <span className="settings-connected">
                <ShieldCheck size={14} />
                Connected
              </span>
            </div>

            <div className="settings-account-details">
              <div>
                <Mail size={16} />

                <span>Email Address</span>

                <strong>
                  {user.email || "Not available"}
                </strong>
              </div>

              <div>
                <ShieldCheck size={16} />

                <span>Account Status</span>

                <strong>Authenticated</strong>
              </div>
            </div>

            <p className="settings-account-note">
              Your prediction history and saved locations
              are associated with this Google account.
            </p>
          </div>
        ) : (
          <div className="settings-guest">
            <CircleUserRound size={36} strokeWidth={1.4} />

            <h3>You're browsing as a guest</h3>

            <p>
              Sign in with Google to access your
              personal history and saved locations
              across devices.
            </p>
          </div>
        )}
      </section>

      <section className="settings-section settings-map-section">
        <div className="settings-section-heading">
          <div className="settings-section-icon">
            <Map size={20} />
          </div>

          <div>
            <h2>Map Appearance</h2>
            <p>Choose your preferred map style</p>
          </div>
        </div>

        <div className="settings-map-options">
          {[
            {
              id: "streets",
              label: "Streets",
              description: "Roads, suburbs and place names",
              icon: Map,
            },
            {
              id: "satellite",
              label: "Satellite",
              description: "Aerial imagery and vegetation",
              icon: Satellite,
            },
            {
              id: "terrain",
              label: "Terrain",
              description: "Topography and elevation",
              icon: Mountain,
            },
          ].map((option) => {
            const Icon = option.icon;

            return (
              <button
                key={option.id}
                type="button"
                className={`settings-map-option ${
                  mapStyle === option.id ? "selected" : ""
                }`}
                onClick={() => updateMapStyle(option.id)}
                aria-pressed={mapStyle === option.id}
              >
                <Icon size={22} />

                <strong>{option.label}</strong>

                <span>{option.description}</span>

                <span className="settings-map-indicator">
                  {mapStyle === option.id ? "Selected" : "Select"}
                </span>
              </button>
            );
          })}
        </div>

        <p className="settings-map-note">
          Your selection is saved in this browser and will be
          applied to Dashboard and Risk Map.
        </p>
      </section>

      <section className="settings-section settings-data-section">
        <div className="settings-section-heading">
          <div className="settings-section-icon">
            <LockKeyhole size={20} />
          </div>

          <div>
            <h2>Privacy & Data</h2>
            <p>Manage your personal information and activity</p>
          </div>
        </div>

        <div className="settings-data-content">
          <button
            type="button"
            className="settings-data-row"
            onClick={() => onNavigate?.("History")}
          >
            <span className="settings-data-row-icon">
              <History size={19} />
            </span>

            <span className="settings-data-row-text">
              <strong>Prediction History</strong>
              <small>
                Review and delete your previous AI assessments
              </small>
            </span>

            <ArrowUpRight size={17} />
          </button>

          <button
            type="button"
            className="settings-data-row"
            onClick={() => onNavigate?.("Saved Locations")}
          >
            <span className="settings-data-row-icon">
              <Bookmark size={19} />
            </span>

            <span className="settings-data-row-text">
              <strong>Saved Locations</strong>
              <small>
                View and manage your bookmarked locations
              </small>
            </span>

            <ArrowUpRight size={17} />
          </button>

          <div className="settings-privacy-note">
            <LockKeyhole size={19} />

            <div>
              <strong>Your Data</strong>

              <p>
                When signed in, Bushfire AI stores your
                prediction history and saved locations in
                Firebase Firestore under your account ID.
                Your Google account provides your display
                name, email address and profile photo.
                Map appearance preferences are stored
                locally in your browser. When you submit
                the Contact Developer form, your name,
                email address, subject and message are
                processed by Formspree to deliver your
                enquiry to the developer. Contact form
                submissions are not stored in your
                Firebase prediction history.
              </p>
            </div>
          </div>

          {user && (
            <div className="settings-signout-row">
              <div>
                <strong>Sign Out</strong>
                <p>Disconnect your Google account from this session.</p>
              </div>

              <button
                type="button"
                onClick={handleSignOut}
                disabled={signingOut}
              >
                <LogOut size={16} />
                {signingOut ? "Signing Out..." : "Sign Out"}
              </button>
            </div>
          )}

          {accountError && (
            <p className="settings-account-error" role="alert">
              {accountError}
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
