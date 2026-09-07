import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Info, AlertCircle, Layers } from 'lucide-react';

export const OptimizationMap = ({ allocations = [] }) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Destroy previous map instance if re-initializing
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    // Default center (Bengaluru area fallback if no markers)
    const defaultCenter = [12.9716, 77.5946];
    const map = L.map(mapContainerRef.current, {
      zoomControl: true,
      scrollWheelZoom: false,
    }).setView(defaultCenter, 12);

    mapInstanceRef.current = map;

    // Dark-mode tile layer (CartoDB Dark Matter) matching ReSource aesthetic
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    // Track unique suppliers, receivers, and bounds
    const supplierMap = new Map();
    const receiverMap = new Map();
    const validLines = [];
    const bounds = [];

    allocations.forEach((alloc) => {
      const hasSupCoords = typeof alloc.supplier_lat === 'number' && typeof alloc.supplier_lon === 'number';
      const hasRecCoords = typeof alloc.receiver_lat === 'number' && typeof alloc.receiver_lon === 'number';

      if (hasSupCoords) {
        const supKey = `${alloc.supplier_lat},${alloc.supplier_lon}`;
        if (!supplierMap.has(supKey)) {
          supplierMap.set(supKey, {
            lat: alloc.supplier_lat,
            lon: alloc.supplier_lon,
            name: alloc.supplier_name || 'Resource Supplier',
            title: alloc.surplus_title || 'Surplus Listing',
            category: alloc.category_name || 'Food Surplus',
          });
        }
      }

      if (hasRecCoords) {
        const recKey = `${alloc.receiver_lat},${alloc.receiver_lon}`;
        if (!receiverMap.has(recKey)) {
          receiverMap.set(recKey, {
            lat: alloc.receiver_lat,
            lon: alloc.receiver_lon,
            name: alloc.receiver_name || 'Community Receiver',
            title: alloc.demand_title || 'Resource Need',
            category: alloc.category_name || 'Food Need',
          });
        }
      }

      if (hasSupCoords && hasRecCoords) {
        validLines.push({
          supLat: alloc.supplier_lat,
          supLon: alloc.supplier_lon,
          recLat: alloc.receiver_lat,
          recLon: alloc.receiver_lon,
          supName: alloc.supplier_name || 'Supplier',
          recName: alloc.receiver_name || 'Receiver',
          qty: alloc.allocated_quantity,
          unit: alloc.surplus_unit || 'kg',
          score: alloc.match_score,
          dist: alloc.distance_km,
          status: alloc.status,
        });
      }
    });

    // Custom Icon Creators
    const createSupplierIcon = (name) => L.divIcon({
      className: 'custom-leaflet-marker',
      html: `<div style="
        background: #10b981;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        border: 3px solid #064e3b;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #000;
        font-weight: 800;
        font-size: 12px;
      ">P</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });

    const createReceiverIcon = (name) => L.divIcon({
      className: 'custom-leaflet-marker',
      html: `<div style="
        background: #06b6d4;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        border: 3px solid #164e63;
        box-shadow: 0 0 12px rgba(6, 182, 212, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #000;
        font-weight: 800;
        font-size: 12px;
      ">R</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });

    // Render Supplier Markers
    supplierMap.forEach((sup) => {
      const latLng = [sup.lat, sup.lon];
      bounds.push(latLng);

      const marker = L.marker(latLng, { icon: createSupplierIcon(sup.name) }).addTo(map);
      marker.bindPopup(`
        <div style="font-family: sans-serif; padding: 4px;">
          <div style="font-size: 0.75rem; color: #10b981; font-weight: 700; text-transform: uppercase;">Resource Provider</div>
          <div style="font-size: 1rem; font-weight: 700; color: #fff; margin-top: 2px;">${sup.name}</div>
          <div style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">Surplus: <strong>${sup.title}</strong></div>
          <div style="font-size: 0.8rem; color: #6b7280; margin-top: 2px;">Category: ${sup.category}</div>
        </div>
      `);
    });

    // Render Receiver Markers
    receiverMap.forEach((rec) => {
      const latLng = [rec.lat, rec.lon];
      bounds.push(latLng);

      const marker = L.marker(latLng, { icon: createReceiverIcon(rec.name) }).addTo(map);
      marker.bindPopup(`
        <div style="font-family: sans-serif; padding: 4px;">
          <div style="font-size: 0.75rem; color: #06b6d4; font-weight: 700; text-transform: uppercase;">Community Partner</div>
          <div style="font-size: 1rem; font-weight: 700; color: #fff; margin-top: 2px;">${rec.name}</div>
          <div style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">Need: <strong>${rec.title}</strong></div>
          <div style="font-size: 0.8rem; color: #6b7280; margin-top: 2px;">Category: ${rec.category}</div>
        </div>
      `);
    });

    // Render Polylines for Allocations
    validLines.forEach((line) => {
      const latLngs = [
        [line.supLat, line.supLon],
        [line.recLat, line.recLon],
      ];

      const polyline = L.polyline(latLngs, {
        color: '#10b981',
        weight: 3,
        dashArray: '6, 8',
        opacity: 0.85,
      }).addTo(map);

      const statusBadgeClass = line.status === 'ALLOCATED' ? '#10b981' : '#f59e0b';
      const statusText = line.status === 'ALLOCATED' ? 'FULLY ALLOCATED' : 'PARTIALLY ALLOCATED';

      polyline.bindPopup(`
        <div style="font-family: sans-serif; padding: 4px; min-width: 200px;">
          <div style="font-size: 0.75rem; color: ${statusBadgeClass}; font-weight: 700; text-transform: uppercase;">
            ${statusText}
          </div>
          <div style="font-size: 0.95rem; font-weight: 700; color: #fff; margin-top: 4px;">
            ${line.supName} &rarr; ${line.recName}
          </div>
          <div style="font-size: 1.1rem; font-weight: 800; color: #10b981; margin-top: 6px;">
            Allocated: ${line.qty} ${line.unit}
          </div>
          <div style="display: flex; gap: 12px; font-size: 0.8rem; color: #9ca3af; margin-top: 6px;">
            <span>Match: <strong style="color: #22d3ee;">${Math.round(line.score)}%</strong></span>
            ${line.dist !== null && line.dist !== undefined ? `<span>Distance: <strong>${line.dist.toFixed(1)} km</strong></span>` : ''}
          </div>
        </div>
      `);
    });

    // Adjust map zoom/bounds to fit all markers
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    }

    // Invalidate size after brief delay to ensure container size is computed
    setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 150);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [allocations]);

  const validCoordsCount = allocations.filter(
    (a) =>
      typeof a.supplier_lat === 'number' &&
      typeof a.supplier_lon === 'number' &&
      typeof a.receiver_lat === 'number' &&
      typeof a.receiver_lon === 'number'
  ).length;

  const missingCoordsCount = allocations.length - validCoordsCount;

  return (
    <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <h3 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={20} style={{ color: 'var(--primary-emerald)' }} />
            Geographic Allocation Distribution Map
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Interactive Leaflet visualization of optimal transfers from resource providers to community partners.
          </p>
        </div>

        {/* Legend */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          backgroundColor: 'rgba(15, 23, 42, 0.7)',
          padding: '8px 14px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          fontSize: '0.8rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }}></span>
            <span>Provider (Supplier)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#06b6d4', display: 'inline-block' }}></span>
            <span>Community Partner</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '20px', height: '2px', backgroundColor: '#10b981', borderTop: '2px dashed #10b981', display: 'inline-block' }}></span>
            <span>Optimized Transfer</span>
          </div>
        </div>
      </div>

      {/* Map Container */}
      <div style={{ position: 'relative', width: '100%', height: '450px', borderRadius: 'var(--radius-sm)', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
        <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

        {allocations.length === 0 && (
          <div style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(10, 15, 29, 0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            zIndex: 400,
            gap: '8px'
          }}>
            <Info size={32} style={{ color: 'var(--text-dim)' }} />
            <p style={{ fontSize: '0.95rem' }}>No active allocations to display on map.</p>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Run optimization to generate geographic transfers.</span>
          </div>
        )}
      </div>

      {/* Missing Coordinates Indicator */}
      {missingCoordsCount > 0 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.8rem',
          color: 'var(--accent-amber)',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          padding: '8px 12px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(245, 158, 11, 0.2)'
        }}>
          <AlertCircle size={16} />
          <span>
            {missingCoordsCount} allocation{missingCoordsCount > 1 ? 's' : ''} missing geographic coordinates — listed below in tables but excluded from map polyline drawing.
          </span>
        </div>
      )}
    </div>
  );
};
