import { useEffect, useRef, useState } from "react";
import * as maptilersdk from "@maptiler/sdk";

import "@maptiler/sdk/dist/maptiler-sdk.css";
import "./MapTilerMap.css";

function MapTilerMap({
  location,
  setLocation,
  analysedLocations = [],
  onSelectAnalysis,
}) {
  const mapContainer = useRef(null);
  const mapWrapper = useRef(null);

  const map = useRef(null);
  const marker = useRef(null);
  const analysisMarkers = useRef([]);

  const [mapStyle, setMapStyle] = useState(() => {
    const saved = localStorage.getItem("bushfire-map-style");

    return ["streets", "satellite", "terrain"].includes(saved)
      ? saved
      : "streets";
  });
  const mapTypes = [
    {
      id: "streets",
      label: "Streets",
    },
    {
      id: "satellite",
      label: "Satellite",
    },
    {
      id: "terrain",
      label: "Terrain",
    },
  ];
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [mapTypesOpen, setMapTypesOpen] = useState(false);

  // ==================================================
  // CREATE MAP
  // ==================================================

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    maptilersdk.config.apiKey =
      import.meta.env.VITE_MAPTILER_KEY;

    map.current = new maptilersdk.Map({
  container: mapContainer.current,
  style: {
    streets: maptilersdk.MapStyle.STREETS,
    satellite: maptilersdk.MapStyle.SATELLITE,
    terrain: maptilersdk.MapStyle.TOPO,
  }[mapStyle],

  center: [149.13, -35.28],
  zoom: 9,

  minZoom: 3,
  maxZoom: 18,

  // 3D terrain
  terrain: true,
  terrainControl: "top-right",
  terrainExaggeration: 2  ,

  // Allow a stronger 3D viewing angle
  maxPitch: 85,
});

    

    // ----------------------------------------------
    // MAP CLICK → SELECT LOCATION
    // ----------------------------------------------

    const handleMapClick = async (event) => {
  const lat = event.lngLat.lat;
  const lng = event.lngLat.lng;

  // Update immediately so the marker feels responsive.
  setLocation({
    lat,
    lng,
    source: "map",
  });

  try {
    const response =
      await maptilersdk.geocoding.reverse(
        [lng, lat],
        {
          language: ["en"],
        }
      );

    const feature = response.features?.[0];

    if (!feature) return;

    setLocation({
      lat,
      lng,
      name:
        feature.place_name ||
        feature.text ||
        "Selected location",
      source: "map",
    });
  } catch (error) {
    console.error(
      "Reverse geocoding failed:",
      error
    );
  }
};

    map.current.on("click", handleMapClick);

    // ----------------------------------------------
    // CLEANUP
    // ----------------------------------------------

    return () => {
      if (map.current) {
        map.current.off("click", handleMapClick);
      }

      marker.current?.remove();
      marker.current = null;

      map.current?.remove();
      map.current = null;
    };
  }, [setLocation]);

  // ==================================================
  // CREATE / MOVE MARKER
  // ==================================================

  useEffect(() => {
  if (!map.current || !location) return;

  const coordinates = [
    location.lng,
    location.lat,
  ];

  // Hide the temporary marker when this location
  // already has a colour-coded prediction marker.
  const alreadyAnalysed = analysedLocations.some(
    (item) =>
      Math.abs(item.lat - location.lat) < 0.00001 &&
      Math.abs(item.lng - location.lng) < 0.00001
  );

  if (alreadyAnalysed) {
    marker.current?.remove();
    marker.current = null;
    return;
  }

  // Create or move the location marker
  if (!marker.current) {
    marker.current = new maptilersdk.Marker({
      color: "#e5483f",
    })
      .setLngLat(coordinates)
      .addTo(map.current);
  } else {
    marker.current.setLngLat(coordinates);
  }

  // Locations selected through search should
  // move the camera to the result.
  if (
    location.source === "search" ||
    location.source === "saved-analysis"
  ) {
    map.current.flyTo({
      center: coordinates,
      zoom: 12,
      pitch: 0,
      bearing: 0,
      duration: 1400,
      essential: true,
    });
  }
}, [location, analysedLocations]);

  // ==================================================
  // COMPLETED AI PREDICTION MARKERS
  // ==================================================

  useEffect(() => {
    if (!map.current) return;

    analysisMarkers.current.forEach((item) => item.remove());
    analysisMarkers.current = [];

    const riskColors = {
      VERY_LOW: "#167347",
      LOW: "#22a06b",
      MODERATE: "#e6ae31",
      HIGH: "#eb7736",
      VERY_HIGH: "#dc3545",
      EXTREME: "#991b1b",
    };

    analysedLocations.forEach((item) => {
      const level = String(item.risk_level || "")
        .toUpperCase()
        .replace(/\\s+/g, "_");

      const color = riskColors[level] || "#64748b";

      const predictionMarker = new maptilersdk.Marker({
        color,
      })
        .setLngLat([item.lng, item.lat])
        .addTo(map.current);

      const element = predictionMarker.getElement();
      element.style.cursor = "pointer";
      element.title = `${item.name || "Analysed location"}: ${item.risk_level}`;

      element.addEventListener("click", (event) => {
        event.stopPropagation();
        onSelectAnalysis?.(item);
      });

      analysisMarkers.current.push(predictionMarker);
    });

    return () => {
      analysisMarkers.current.forEach((item) => item.remove());
      analysisMarkers.current = [];
    };
  }, [analysedLocations, onSelectAnalysis]);

  // ==================================================
  // FULLSCREEN STATE
  // ==================================================

  useEffect(() => {
    const handleFullscreenChange = () => {
      const fullscreen =
        document.fullscreenElement === mapWrapper.current;

      setIsFullscreen(fullscreen);

      // Give the browser a moment to resize,
      // then tell MapTiler to recalculate its canvas.
      window.setTimeout(() => {
        map.current?.resize();
      }, 100);
    };

    document.addEventListener(
      "fullscreenchange",
      handleFullscreenChange
    );

    return () => {
      document.removeEventListener(
        "fullscreenchange",
        handleFullscreenChange
      );
    };
  }, []);

  // ==================================================
  // CHANGE BASE MAP
  // ==================================================

  const changeMapStyle = (style) => {
  if (!map.current) return;

  const styles = {
    streets: maptilersdk.MapStyle.STREETS,
    satellite: maptilersdk.MapStyle.SATELLITE,
    terrain: maptilersdk.MapStyle.TOPO,
  };

  const selectedStyle = styles[style];

  if (!selectedStyle) return;

  map.current.setStyle(selectedStyle);
  setMapStyle(style);
  localStorage.setItem("bushfire-map-style", style);

  map.current.once("style.load", () => {
    map.current?.resize();
  });
};

  // ==================================================
  // FULLSCREEN
  // ==================================================

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await mapWrapper.current?.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (error) {
      console.error(
        "Unable to toggle fullscreen:",
        error
      );
    }
  };

  // ==================================================
  // UI
  // ==================================================

  return (
    <div
      ref={mapWrapper}
      className={`risk-map ${
        isFullscreen
          ? "risk-map--fullscreen"
          : ""
      }`}
    >
      {/* MAP */}

      <div
        ref={mapContainer}
        className="risk-map__canvas"
      />

      {/* ============================================
          FULLSCREEN CONTROL
          ============================================ */}

      <button
        type="button"
        className="map-fullscreen-control"
        onClick={toggleFullscreen}
        title={
          isFullscreen
            ? "Exit fullscreen"
            : "Fullscreen map"
        }
        aria-label={
          isFullscreen
            ? "Exit fullscreen map"
            : "Open map fullscreen"
        }
      >
        {isFullscreen ? (
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              d="M9 3v6H3M15 3v6h6M9 21v-6H3M15 21v-6h6"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        ) : (
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </button>

      {/* ============================================
    COMPACT BASE MAP SWITCHER
    ============================================ */}

<div
  className={`map-type-switcher ${
    mapTypesOpen ? "map-type-switcher--open" : ""
  }`}
  onMouseEnter={() => setMapTypesOpen(true)}
  onMouseLeave={() => setMapTypesOpen(false)}
>
  {mapTypes
    .filter((type) =>
      mapTypesOpen
        ? true
        : type.id === mapStyle
    )
    .sort((a, b) => {
      if (a.id === mapStyle) return -1;
      if (b.id === mapStyle) return 1;
      return 0;
    })
    .map((type) => (
      <button
        key={type.id}
        type="button"
        className={`map-type ${
          type.id === mapStyle
            ? "map-type--primary"
            : ""
        }`}
        onClick={() => {
          if (type.id === mapStyle) {
            setMapTypesOpen(
              (open) => !open
            );
            return;
          }

          changeMapStyle(type.id);
          setMapTypesOpen(false);
        }}
        title={
          type.id === "streets"
            ? "Street map"
            : type.id === "satellite"
            ? "Satellite imagery"
            : "Topographic terrain map"
        }
      >
        {/* STREETS PREVIEW */}

        {type.id === "streets" && (
          <span className="map-type__preview map-type__preview--streets">
            <span className="street-preview__road street-preview__road--one" />
            <span className="street-preview__road street-preview__road--two" />
            <span className="street-preview__road street-preview__road--three" />
          </span>
        )}

        {/* SATELLITE PREVIEW */}

        {type.id === "satellite" && (
          <span className="map-type__preview map-type__preview--satellite">
            <span className="satellite-preview__land" />
          </span>
        )}

        {/* TERRAIN PREVIEW */}

        {type.id === "terrain" && (
          <span className="map-type__preview map-type__preview--terrain">
            <span className="terrain-preview__mountain terrain-preview__mountain--back" />
            <span className="terrain-preview__mountain terrain-preview__mountain--front" />
          </span>
        )}

        <span className="map-type__label">
          {type.label}
        </span>
      </button>
    ))}
</div>

      
    </div>
  );
}

export default MapTilerMap;