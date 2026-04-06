"use client";

import { useMemo, useState } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  useMapEvent,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x.src,
  iconUrl: markerIcon.src,
  shadowUrl: markerShadow.src,
});

function ClickMarker({ onLocationSelect, setPosition }) {
  useMapEvent("click", (event) => {
    const next = {
      lat: Number(event.latlng.lat.toFixed(6)),
      lng: Number(event.latlng.lng.toFixed(6)),
    };
    setPosition(next);
    onLocationSelect(next);
  });

  return null;
}

export default function MapPicker({
  onLocationSelect,
  initialLat = 20.5937,
  initialLng = 78.9629,
  initialZoom = 5,
}) {
  const [position, setPosition] = useState(null);

  const center = useMemo(() => [initialLat, initialLng], [initialLat, initialLng]);

  return (
    <div>
      <p className="map-hint">
        {position
          ? `Lat: ${position.lat}, Lng: ${position.lng}`
          : "Drop pin on map"}
      </p>
      <MapContainer
        center={center}
        zoom={initialZoom}
        scrollWheelZoom
        className="leaflet-shell"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickMarker onLocationSelect={onLocationSelect} setPosition={setPosition} />
        <Marker
          draggable
          position={position ? [position.lat, position.lng] : center}
          eventHandlers={{
            dragend: (event) => {
              const marker = event.target;
              const latlng = marker.getLatLng();
              const next = {
                lat: Number(latlng.lat.toFixed(6)),
                lng: Number(latlng.lng.toFixed(6)),
              };
              setPosition(next);
              onLocationSelect(next);
            },
          }}
        />
      </MapContainer>
    </div>
  );
}
