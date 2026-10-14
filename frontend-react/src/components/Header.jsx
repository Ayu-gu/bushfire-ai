import { useEffect, useRef, useState } from "react";
import {
  Bell,
  ChevronDown,
  LogOut,
  LoaderCircle,
  MapPin,
  Search,
  UserRound,
} from "lucide-react";
import * as maptilersdk from "@maptiler/sdk";

import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "../firebase";
import "./Header.css";
import AuthModal from "./AuthModal";

function Header({ setLocation }) {
  const [authOpen, setAuthOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileWrapper = useRef(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setAuthReady(true);
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (
        profileWrapper.current &&
        !profileWrapper.current.contains(event.target)
      ) {
        setProfileOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, []);

  const handleSignOut = async () => {
    try {
      await signOut(auth);
      setProfileOpen(false);
    } catch (error) {
      console.error("Sign out failed:", error);
    }
  };
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const searchWrapper = useRef(null);

  useEffect(() => {
    maptilersdk.config.apiKey =
      import.meta.env.VITE_MAPTILER_KEY;
  }, []);

  useEffect(() => {
    const trimmedQuery = query.trim();

    if (trimmedQuery.length < 2) {
      setResults([]);
      setSearchOpen(false);
      setLoadingSearch(false);
      return;
    }

    const controller = new AbortController();

    const timer = window.setTimeout(async () => {
      setLoadingSearch(true);

      try {
        const response =
          await maptilersdk.geocoding.forward(
            trimmedQuery,
            {
              limit: 6,
              country: ["au"],
              language: ["en"],
            }
          );

        if (controller.signal.aborted) return;

        setResults(response.features ?? []);
        setSearchOpen(true);
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error(
            "Location search failed:",
            error
          );

          setResults([]);
          setSearchOpen(false);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoadingSearch(false);
        }
      }
    }, 350);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (
        searchWrapper.current &&
        !searchWrapper.current.contains(event.target)
      ) {
        setSearchOpen(false);
      }
    };

    document.addEventListener(
      "mousedown",
      handleOutsideClick
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick
      );
    };
  }, []);

  const selectLocation = (feature) => {
    const [lng, lat] = feature.center;

    setLocation({
      lat,
      lng,
      name:
        feature.place_name ||
        feature.text ||
        "Selected location",
      source: "search",
    });

    setQuery("");

    setResults([]);
    setSearchOpen(false);
  };

  return (
    <header className="top-header">
      <div className="header-brand">
        <img
          src="/bushfire-icon.svg"
          alt=""
          className="header-logo"
        />

        <div className="header-brand-text">
          <span className="header-name">
            Bushfire AI
          </span>

          <span className="header-product">
            Intelligence Platform
          </span>
        </div>
      </div>

      <div
        className="header-search-wrapper"
        ref={searchWrapper}
      >
        <div className="header-search">
          {loadingSearch ? (
            <LoaderCircle
              className="search-icon search-spinner"
              size={17}
              strokeWidth={1.8}
            />
          ) : (
            <Search
              className="search-icon"
              size={17}
              strokeWidth={1.8}
            />
          )}

          <input
            type="text"
            value={query}
            placeholder="Search a location..."
            aria-label="Search location"
            autoComplete="off"
            onChange={(event) => {
              setQuery(event.target.value);
            }}
            onFocus={() => {
              if (results.length > 0) {
                setSearchOpen(true);
              }
            }}
          />

          {query.length === 0 && (
            <span className="search-shortcut">
              ⌘ K
            </span>
          )}
        </div>

        {searchOpen && (
          <div className="search-results">
            {results.length > 0 ? (
              results.map((feature) => (
                <button
                  key={feature.id}
                  type="button"
                  className="search-result"
                  onClick={() =>
                    selectLocation(feature)
                  }
                >
                  <span className="search-result-icon">
                    <MapPin
                      size={16}
                      strokeWidth={1.8}
                    />
                  </span>

                  <span className="search-result-content">
                    <strong>
                      {feature.text ||
                        feature.place_name}
                    </strong>

                    <span>
                      {feature.place_name}
                    </span>
                  </span>
                </button>
              ))
            ) : (
              !loadingSearch && (
                <div className="search-empty">
                  No locations found
                </div>
              )
            )}
          </div>
        )}
      </div>

      <div className="header-actions">
        <div
          className="live-status"
          title="Data services operational"
        >
          <span className="live-dot" />
          <span>Live</span>
        </div>

        <button
          className="header-icon-button"
          type="button"
          aria-label="Notifications"
          title="Notifications"
        >
          <Bell
            size={18}
            strokeWidth={1.8}
          />
        </button>

        <div className="header-divider" />

        {!authReady ? (
          <span className="header-auth-loading">Loading...</span>
        ) : user ? (
          <div className="profile-wrapper" ref={profileWrapper}>
            <button
              className="profile-button"
              type="button"
              aria-label="Open account menu"
              aria-expanded={profileOpen}
              onClick={() => setProfileOpen((open) => !open)}
            >
              {user.photoURL ? (
                <img
                  className="profile-avatar profile-photo"
                  src={user.photoURL}
                  alt=""
                  referrerPolicy="no-referrer"
                />
              ) : (
                <span className="profile-avatar">
                  {(user.displayName || user.email || "U")
                    .slice(0, 2)
                    .toUpperCase()}
                </span>
              )}

              <span className="profile-details">
                <strong>
                  {user.displayName?.split(" ")[0] || "My Account"}
                </strong>
                <span>Signed In</span>
              </span>

              <ChevronDown
                className="profile-chevron"
                size={15}
                strokeWidth={1.8}
              />
            </button>

            {profileOpen && (
              <div className="profile-dropdown">
                <div className="profile-dropdown-user">
                  <strong>
                    {user.displayName || "Bushfire AI User"}
                  </strong>
                  <span>{user.email}</span>
                </div>

                <div className="profile-dropdown-divider" />

                <button
                  type="button"
                  onClick={() => setProfileOpen(false)}
                >
                  <UserRound size={16} />
                  My Account
                </button>

                <div className="profile-dropdown-divider" />

                <button
                  className="profile-signout"
                  type="button"
                  onClick={handleSignOut}
                >
                  <LogOut size={16} />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            className="header-signin-button"
            type="button"
            aria-label="Sign in to Bushfire AI"
            onClick={() => setAuthOpen(true)}
          >
            Sign In
          </button>
        )}
      </div>
      <AuthModal
        isOpen={authOpen}
        onClose={() => setAuthOpen(false)}
      />
    </header>
  );
}

export default Header;