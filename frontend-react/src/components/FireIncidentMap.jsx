import { useEffect, useRef, useState } from "react";
import * as maptilersdk from "@maptiler/sdk";
import "@maptiler/sdk/dist/maptiler-sdk.css";

import {
  ExternalLink,
  MapPin,
  Radio,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";

import "./FireIncidentMap.css";

const API_URL = "/api/fire-incidents";

const SOURCE_URL =
  "https://www.rfs.nsw.gov.au/fire-information/fires-near-me";

function getPoint(geometry) {
  if (!geometry || typeof geometry !== "object") return null;

  if (geometry.type === "Point") {
    const [lng, lat] = geometry.coordinates || [];

    if (
      Number.isFinite(lng) &&
      Number.isFinite(lat) &&
      lng >= -180 &&
      lng <= 180 &&
      lat >= -90 &&
      lat <= 90
    ) {
      return [lng, lat];
    }

    return null;
  }

  if (geometry.type === "GeometryCollection") {
    for (const child of geometry.geometries || []) {
      const point = getPoint(child);
      if (point) return point;
    }
  }

  return null;
}

function parseDescription(description = "") {
  const fields = {};

  description.split(/<br\s*\/?>/i).forEach((part) => {
    const separator = part.indexOf(":");

    if (separator < 0) return;

    const key = part.slice(0, separator).trim().toUpperCase();
    const value = part.slice(separator + 1).trim();

    fields[key] = value;
  });

  return fields;
}

function getMarkerColor(category) {
  switch ((category || "").toLowerCase()) {
    case "emergency warning":
      return "#dc2626";
    case "watch and act":
      return "#ea580c";
    case "advice":
      return "#eab308";
    case "planned burn":
      return "#64748b";
    default:
      return "#64748b";
  }
}

function FireIncidentMap() {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);

  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fetchedAt, setFetchedAt] = useState(null);

  useEffect(() => {
    if (!mapContainer.current || mapInstance.current) return;

    const key = import.meta.env.VITE_MAPTILER_KEY;

    if (!key) {
      setError("MapTiler API key is missing.");
      return;
    }

    maptilersdk.config.apiKey = key;

    const map = new maptilersdk.Map({
      container: mapContainer.current,
      style: maptilersdk.MapStyle.STREETS,
      center: [149.13, -35.28],
      zoom: 8,
      minZoom: 4,
      navigationControl: true,
      geolocateControl: false,
      terrainControl: false,
    });

    mapInstance.current = map;

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
      map.remove();
      mapInstance.current = null;
    };
  }, []);

  useEffect(() => {
    let active = true;
    let controller = null;

    async function loadIncidents() {
      if (controller) controller.abort();

      controller = new AbortController();

      try {
        const response = await fetch(API_URL, {
          signal: controller.signal,
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Incident feed returned HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!Array.isArray(data.features)) {
          throw new Error("Invalid incident feed response");
        }

        if (!active) return;

        const parsed = data.features
          .map((feature, index) => {
            const coordinates = getPoint(feature.geometry);

            if (!coordinates) return null;

            const properties = feature.properties || {};
            const details = parseDescription(
              properties.description || ""
            );

            return {
              id: properties.guid || `incident-${index}`,
              title: properties.title?.trim() || "Unnamed incident",
              category: properties.category || "Not specified",
              coordinates,
              location: details.LOCATION || "Not provided",
              status: details.STATUS || "Not provided",
              type: details.TYPE || "Not provided",
              size: details.SIZE || "Not provided",
              updated: details.UPDATED || properties.pubDate || "Not provided",
            };
          })
          .filter(Boolean);

        setIncidents(parsed);
        setFetchedAt(data.fetchedAt || new Date().toISOString());
        setError("");
      } catch (err) {
        if (!active || err.name === "AbortError") return;

        setError("Official NSW RFS incident feed is unavailable.");
        setIncidents([]);
        setSelectedIncident(null);
        setFetchedAt(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadIncidents();

    const interval = setInterval(loadIncidents, 60000);

    return () => {
      active = false;
      clearInterval(interval);
      if (controller) controller.abort();
    };
  }, []);

  useEffect(() => {
    const map = mapInstance.current;
    if (!map) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    incidents.forEach((incident) => {
      const element = document.createElement("button");

      element.type = "button";
      element.className = "fim-incident-marker";
      element.style.backgroundColor = getMarkerColor(
        incident.category
      );

      element.setAttribute(
        "aria-label",
        `${incident.title}, ${incident.category}`
      );

      element.addEventListener("click", () => {
        setSelectedIncident(incident);

        map.flyTo({
          center: incident.coordinates,
          zoom: Math.max(map.getZoom(), 10),
          essential: true,
        });
      });

      const marker = new maptilersdk.Marker({
        element,
        anchor: "center",
      })
        .setLngLat(incident.coordinates)
        .addTo(map);

      markersRef.current.push(marker);
    });

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
    };
  }, [incidents]);

  const adviceCount = incidents.filter(
    (incident) => incident.category === "Advice"
  ).length;

  const emergencyCount = incidents.filter(
    (incident) => incident.category === "Emergency Warning"
  ).length;

  const watchCount = incidents.filter(
    (incident) => incident.category === "Watch and Act"
  ).length;

  return (
    <section className="fim-section">
      <div className="fim-heading">
        <div>
          <div className="fim-heading-title">
            <MapPin size={19} />
            <h2>Fire Incident Map</h2>
          </div>
          <p>Official NSW RFS incident locations</p>
        </div>

        <span className="fim-status">
          <Radio size={14} />
          {loading
            ? "Loading incidents"
            : error
              ? "Feed unavailable"
              : `${incidents.length} incidents reported`}
        </span>
      </div>

      <div className="fim-layout">
        <div className="fim-map-wrap">
          <div ref={mapContainer} className="fim-map" />

          <div className="fim-map-label">
            <MapPin size={13} />
            NSW RFS incidents
          </div>
        </div>

        <aside className="fim-panel">
          <div className="fim-panel-icon">
            <ShieldAlert size={24} />
          </div>

          <h3>
            {selectedIncident
              ? selectedIncident.title
              : "Incident Intelligence"}
          </h3>

          {selectedIncident ? (
            <>
              <p className="fim-panel-description">
                Official NSW Rural Fire Service incident information.
              </p>

              <div className="fim-incident-details">
                <div>
                  <span>Warning category</span>
                  <strong>{selectedIncident.category}</strong>
                </div>
                <div>
                  <span>Location</span>
                  <strong>{selectedIncident.location}</strong>
                </div>
                <div>
                  <span>Status</span>
                  <strong>{selectedIncident.status}</strong>
                </div>
                <div>
                  <span>Incident type</span>
                  <strong>{selectedIncident.type}</strong>
                </div>
                <div>
                  <span>Reported size</span>
                  <strong>{selectedIncident.size}</strong>
                </div>
                <div>
                  <span>Last updated (source)</span>
                  <strong>{selectedIncident.updated}</strong>
                </div>
              </div>

              <button
                className="fim-back-button"
                onClick={() => setSelectedIncident(null)}
                type="button"
              >
                Back to overview
              </button>
            </>
          ) : (
            <>
              <p className="fim-panel-description">
                Incident locations are provided by the NSW Rural
                Fire Service. Select a marker to view details.
              </p>

              {error ? (
                <div className="fim-empty-state">
                  <Radio size={17} />
                  <div>
                    <strong>Feed unavailable</strong>
                    <span>{error}</span>
                  </div>
                </div>
              ) : (
                <div className="fim-incident-details">
                  <div>
                    <span>Total reported incidents</span>
                    <strong>{loading ? "Loading..." : incidents.length}</strong>
                  </div>
                  <div>
                    <span>Advice</span>
                    <strong>{adviceCount}</strong>
                  </div>
                  <div>
                    <span>Watch and Act</span>
                    <strong>{watchCount}</strong>
                  </div>
                  <div>
                    <span>Emergency Warning</span>
                    <strong>{emergencyCount}</strong>
                  </div>
                  <div>
                    <span>Other categories</span>
                    <strong>
                      {incidents.length -
                        adviceCount -
                        watchCount -
                        emergencyCount}
                    </strong>
                  </div>
                </div>
              )}
            </>
          )}

          <div className="fim-source-links">
            <a
              href={SOURCE_URL}
              target="_blank"
              rel="noopener noreferrer"
            >
              View official NSW warnings
              <ExternalLink size={14} />
            </a>
          </div>

          <div className="fim-panel-footer">
            <RefreshCw size={13} />
            {" "}
            {fetchedAt
              ? `Feed retrieved: ${new Date(fetchedAt).toLocaleString("en-AU")}`
              : "No verified feed update available"}
            <br />
            This map is informational. Always follow official
            emergency-service instructions.
          </div>
        </aside>
      </div>
    </section>
  );
}

export default FireIncidentMap;
