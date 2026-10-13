import { useEffect, useRef, useState } from "react";
import {
  Bell,
  ChevronDown,
  LoaderCircle,
  MapPin,
  Search,
} from "lucide-react";
import * as maptilersdk from "@maptiler/sdk";

import "./Header.css";

function Header({ setLocation }) {
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

        <button
          className="profile-button"
          type="button"
          aria-label="Open user menu"
        >
          <span className="profile-avatar">
            AG
          </span>

          <span className="profile-details">
            <strong>Ayub</strong>
            <span>Operator</span>
          </span>

          <ChevronDown
            className="profile-chevron"
            size={15}
            strokeWidth={1.8}
          />
        </button>
      </div>
    </header>
  );
}

export default Header;