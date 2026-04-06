"use client";

import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
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

export default function FirStationsMap({ stations = [] }) {
  const validStations = stations.filter((station) => station?.lat && station?.lng);

  if (!validStations.length) {
    return <p className="text-sm text-(--muted-foreground)">No station coordinates available.</p>;
  }

  const center = [validStations[0].lat, validStations[0].lng];

  return (
    <MapContainer center={center} zoom={12} scrollWheelZoom className="leaflet-shell">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {validStations.map((station) => (
        <Marker key={String(station.osm_id || station.name)} position={[station.lat, station.lng]}>
          <Popup>
            <div className="text-xs">
              <p className="font-semibold">{station.name || "Police Station"}</p>
              <p>{station.address || "Address unavailable"}</p>
              {station.distance_km ? <p>Distance: {station.distance_km} km</p> : null}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
