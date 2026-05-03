"use client";
import { useEffect, useRef } from "react";

// ═══════════════════════════════════════════════════════════
//  3D CYBER GLOBE — Chaos-QA Background
//  Fixed: proper back-face culling, brighter wireframe,
//  glowing nodes & arcs, smooth resize, scan sweep.
// ═══════════════════════════════════════════════════════════

interface Vec3 { x: number; y: number; z: number }

function rotateY(p: Vec3, a: number): Vec3 {
  const c = Math.cos(a), s = Math.sin(a);
  return { x: p.x * c + p.z * s, y: p.y, z: -p.x * s + p.z * c };
}

function rotateX(p: Vec3, a: number): Vec3 {
  const c = Math.cos(a), s = Math.sin(a);
  return { x: p.x, y: p.y * c - p.z * s, z: p.y * s + p.z * c };
}

function project(p: Vec3, cx: number, cy: number, fov: number) {
  const z = p.z + fov;
  const scale = fov / (z || 1);
  return { x: p.x * scale + cx, y: p.y * scale + cy, z: p.z, scale };
}

function latLonToVec3(lat: number, lon: number, r: number): Vec3 {
  const phi   = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return {
    x: -r * Math.sin(phi) * Math.cos(theta),
    y:  r * Math.cos(phi),
    z:  r * Math.sin(phi) * Math.sin(theta),
  };
}

// Returns true when the point faces the viewer (positive z after projection)
function isFrontFacing(p: Vec3): boolean {
  return p.z < 0;
}

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let frame = 0;
    let rotY = 0;

    // ── Mutable viewport ──────────────────────────────────
    let W = 0, H = 0, R = 0, CX = 0, CY = 0;
    const FOV = 500;
    const TILT = 0.3;

    function resize() {
      W = window.innerWidth;
      H = window.innerHeight;
      canvas!.width  = W;
      canvas!.height = H;
      R  = Math.min(W, H) * 0.30;
      CX = W * 0.5;
      CY = H * 0.52;
    }
    resize();

    // ── Geometry helpers ──────────────────────────────────
    function xform(p: Vec3) {
      return project(rotateY(rotateX(p, TILT), rotY), CX, CY, FOV);
    }

    // ── City nodes ────────────────────────────────────────
    const CITIES = [
      { lat: 40.7,  lon: -74.0  }, // New York
      { lat: 51.5,  lon:  -0.1  }, // London
      { lat: 35.7,  lon: 139.7  }, // Tokyo
      { lat:-33.9,  lon:  18.4  }, // Cape Town
      { lat: 28.6,  lon:  77.2  }, // Delhi
      { lat: 55.8,  lon:  37.6  }, // Moscow
      { lat:-23.5,  lon: -46.6  }, // São Paulo
      { lat:  1.3,  lon: 103.8  }, // Singapore
      { lat: 37.8,  lon:-122.4  }, // San Francisco
      { lat:-34.6,  lon: -58.4  }, // Buenos Aires
      { lat: 31.2,  lon: 121.5  }, // Shanghai
      { lat: 48.9,  lon:   2.35 }, // Paris
      { lat: 25.2,  lon:  55.3  }, // Dubai
      { lat: 13.8,  lon: 100.5  }, // Bangkok
      { lat: 59.3,  lon:  18.1  }, // Stockholm
      { lat:-37.8,  lon: 144.9  }, // Melbourne
    ];

    const ARCS = [
      [0,1],[1,5],[2,10],[3,7],[4,12],
      [6,0],[8,2],[9,6],[11,5],[7,13],
      [14,1],[15,7],[0,4],[10,2],[12,3],
    ];

    // ── Stars ─────────────────────────────────────────────
    const STARS = Array.from({ length: 200 }, () => ({
      x: Math.random(),
      y: Math.random(),
      r: 0.4 + Math.random() * 1.0,
      phase: Math.random() * Math.PI * 2,
      spd:   0.008 + Math.random() * 0.015,
    }));

    // ── Orbiting particles ────────────────────────────────
    const PARTS = Array.from({ length: 60 }, () => ({
      lat:  Math.random() * 180 - 90,
      lon:  Math.random() * 360 - 180,
      r:    0,   // set in draw
      spd:  0.12 + Math.random() * 0.35,
      sz:   0.6 + Math.random() * 1.4,
      tilt: (Math.random() - 0.5) * 0.5,
    }));

    // ── Draw helpers ──────────────────────────────────────
    function drawGlobeGrid(segments = 80) {
      const LAT_LINES = 14;
      const LON_LINES = 20;

      ctx!.lineWidth = 0.6;

      // Latitude rings
      for (let i = 1; i < LAT_LINES; i++) {
        const lat = -90 + (180 / LAT_LINES) * i;
        ctx!.beginPath();
        let first = true;
        for (let j = 0; j <= segments; j++) {
          const lon = -180 + (360 / segments) * j;
          const raw = latLonToVec3(lat, lon, R);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFrontFacing(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          if (first) { ctx!.moveTo(p.x, p.y); first = false; }
          else        ctx!.lineTo(p.x, p.y);
        }
        const isEquator = Math.abs(lat) < 1;
        ctx!.strokeStyle = isEquator
          ? "rgba(0,240,255,0.30)"
          : "rgba(0,240,255,0.09)";
        ctx!.lineWidth = isEquator ? 1.2 : 0.6;
        ctx!.stroke();
      }

      // Longitude meridians
      ctx!.lineWidth = 0.6;
      for (let i = 0; i < LON_LINES; i++) {
        const lon = -180 + (360 / LON_LINES) * i;
        ctx!.beginPath();
        let first = true;
        for (let j = 0; j <= segments; j++) {
          const lat = -90 + (180 / segments) * j;
          const raw = latLonToVec3(lat, lon, R);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFrontFacing(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          if (first) { ctx!.moveTo(p.x, p.y); first = false; }
          else        ctx!.lineTo(p.x, p.y);
        }
        ctx!.strokeStyle = "rgba(0,240,255,0.09)";
        ctx!.stroke();
      }
    }

    function drawArcs() {
      ARCS.forEach(([ai, bi], arcIdx) => {
        const A = CITIES[ai], B = CITIES[bi];
        if (!A || !B) return;

        const SEG = 50;
        const isRed = arcIdx % 3 === 0;
        const baseColor = isRed ? "255,0,64" : "0,240,255";

        // Animated alpha pulse
        const pulse = Math.sin(frame * 0.025 + arcIdx * 0.8);
        const alpha = 0.25 + 0.2 * pulse;

        ctx!.beginPath();
        let first = true;
        for (let i = 0; i <= SEG; i++) {
          const t   = i / SEG;
          const lat = A.lat + (B.lat - A.lat) * t;
          const lon = A.lon + (B.lon - A.lon) * t;
          const lift = Math.sin(t * Math.PI) * R * 0.28;
          const raw = latLonToVec3(lat, lon, R + lift);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFrontFacing(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          if (first) { ctx!.moveTo(p.x, p.y); first = false; }
          else        ctx!.lineTo(p.x, p.y);
        }
        ctx!.strokeStyle = `rgba(${baseColor},${alpha})`;
        ctx!.lineWidth   = 1.2;
        ctx!.shadowColor = `rgba(${baseColor},0.6)`;
        ctx!.shadowBlur  = 6;
        ctx!.stroke();
        ctx!.shadowBlur  = 0;

        // Traveling pulse dot
        const tP   = ((frame * 0.009 + arcIdx * 0.3) % 1);
        const pLat  = A.lat + (B.lat - A.lat) * tP;
        const pLon  = A.lon + (B.lon - A.lon) * tP;
        const pLift = Math.sin(tP * Math.PI) * R * 0.28;
        const rawP  = latLonToVec3(pLat, pLon, R + pLift);
        const rotP  = rotateY(rotateX(rawP, TILT), rotY);
        if (isFrontFacing(rotP)) {
          const pp = project(rotP, CX, CY, FOV);
          ctx!.beginPath();
          ctx!.arc(pp.x, pp.y, 5 * pp.scale, 0, Math.PI * 2);
          ctx!.fillStyle = `rgba(${baseColor},0.15)`;
          ctx!.fill();
          ctx!.beginPath();
          ctx!.arc(pp.x, pp.y, 2.2 * pp.scale, 0, Math.PI * 2);
          ctx!.fillStyle = `rgba(${baseColor},0.95)`;
          ctx!.fill();
        }
      });
    }

    function drawNodes() {
      CITIES.forEach(({ lat, lon }, idx) => {
        const raw = latLonToVec3(lat, lon, R);
        const rot = rotateY(rotateX(raw, TILT), rotY);
        if (!isFrontFacing(rot)) return;
        const p = project(rot, CX, CY, FOV);

        const pulse  = Math.sin(frame * 0.04 + idx * 1.5);
        const isRed  = idx % 4 === 0;
        const col    = isRed ? "255,0,64" : "0,240,255";
        const alpha  = 0.7 + pulse * 0.25;

        // Halo glow
        const grad = ctx!.createRadialGradient(p.x, p.y, 0, p.x, p.y, 14 * p.scale);
        grad.addColorStop(0, `rgba(${col},${alpha * 0.4})`);
        grad.addColorStop(1, "transparent");
        ctx!.fillStyle = grad;
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, 14 * p.scale, 0, Math.PI * 2);
        ctx!.fill();

        // Outer ring
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, (5 + pulse) * p.scale, 0, Math.PI * 2);
        ctx!.strokeStyle = `rgba(${col},${alpha * 0.5})`;
        ctx!.lineWidth   = 1;
        ctx!.stroke();

        // Core dot
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, 2.5 * p.scale, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(${col},${alpha})`;
        ctx!.fill();
      });
    }

    function drawOrbitalRings() {
      [[TILT + 0.15, 0, "0,240,255", 0.12], [TILT - 0.3, 0.5, "255,0,64", 0.07]].forEach(
        ([tilt, offset, col, opacity]) => {
          const ringR = R * 1.18;
          ctx!.beginPath();
          for (let i = 0; i <= 120; i++) {
            const a   = (i / 120) * Math.PI * 2;
            const raw: Vec3 = { x: ringR * Math.cos(a), y: 0, z: ringR * Math.sin(a) };
            const rot = rotateY(rotateX(raw, tilt as number), rotY + (offset as number));
            const p   = project(rot, CX, CY, FOV);
            i === 0 ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
          }
          ctx!.closePath();
          ctx!.strokeStyle = `rgba(${col},${opacity})`;
          ctx!.lineWidth   = 0.8;
          ctx!.setLineDash([4, 9]);
          ctx!.stroke();
          ctx!.setLineDash([]);
        }
      );
    }

    function drawScanSweep() {
      const sweepLon = (((frame * 0.014 * 180) / Math.PI) % 360) - 180;
      // Main sweep line
      ctx!.beginPath();
      let first = true;
      for (let lat = -85; lat <= 85; lat += 2) {
        const raw = latLonToVec3(lat, sweepLon, R * 1.004);
        const rot = rotateY(rotateX(raw, TILT), rotY);
        if (!isFrontFacing(rot)) { first = true; continue; }
        const p = project(rot, CX, CY, FOV);
        if (first) { ctx!.moveTo(p.x, p.y); first = false; }
        else        ctx!.lineTo(p.x, p.y);
      }
      ctx!.strokeStyle  = "rgba(0,240,255,0.5)";
      ctx!.lineWidth    = 1.8;
      ctx!.shadowColor  = "rgba(0,240,255,0.8)";
      ctx!.shadowBlur   = 10;
      ctx!.stroke();
      ctx!.shadowBlur   = 0;

      // Trailing fade lines
      for (let off = 1; off <= 8; off++) {
        const tLon = sweepLon - off * 2.5;
        ctx!.beginPath();
        let tf = true;
        for (let lat = -85; lat <= 85; lat += 4) {
          const raw = latLonToVec3(lat, tLon, R * 1.002);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFrontFacing(rot)) { tf = true; continue; }
          const p = project(rot, CX, CY, FOV);
          if (tf) { ctx!.moveTo(p.x, p.y); tf = false; }
          else      ctx!.lineTo(p.x, p.y);
        }
        ctx!.strokeStyle = `rgba(0,240,255,${0.15 - off * 0.017})`;
        ctx!.lineWidth   = 0.8;
        ctx!.stroke();
      }
    }

    // ── Main draw loop ────────────────────────────────────
    function draw() {
      frame++;
      rotY += 0.0025;

      ctx!.clearRect(0, 0, W, H);

      // Background radial glow
      const bgG = ctx!.createRadialGradient(CX, CY, 0, CX, CY, Math.max(W, H) * 0.75);
      bgG.addColorStop(0,   "rgba(0,20,40,0.35)");
      bgG.addColorStop(0.5, "rgba(4,8,20,0.15)");
      bgG.addColorStop(1,   "transparent");
      ctx!.fillStyle = bgG;
      ctx!.fillRect(0, 0, W, H);

      // Globe glow halo
      const gG = ctx!.createRadialGradient(CX, CY, R * 0.7, CX, CY, R * 1.7);
      gG.addColorStop(0,   "rgba(0,240,255,0.06)");
      gG.addColorStop(0.5, "rgba(0,240,255,0.025)");
      gG.addColorStop(1,   "transparent");
      ctx!.fillStyle = gG;
      ctx!.beginPath();
      ctx!.arc(CX, CY, R * 1.7, 0, Math.PI * 2);
      ctx!.fill();

      // Stars
      STARS.forEach(s => {
        s.phase += s.spd;
        const a = 0.25 + 0.45 * Math.sin(s.phase);
        ctx!.beginPath();
        ctx!.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(0,240,255,${a})`;
        ctx!.fill();
      });

      // Globe components
      drawGlobeGrid();
      drawArcs();
      drawNodes();
      drawOrbitalRings();

      // Orbiting particles
      PARTS.forEach(pt => {
        pt.lon += pt.spd;
        if (pt.lon > 180) pt.lon -= 360;
        const orbitR = R * (1.06 + (pt.sz - 0.6) * 0.12);
        const raw = latLonToVec3(pt.lat, pt.lon, orbitR);
        const rot = rotateY(rotateX(raw, TILT + pt.tilt), rotY);
        const pp  = project(rot, CX, CY, FOV);
        const depthA = Math.max(0, 1 - pp.z / (FOV * 0.9)) * 0.55;
        if (depthA > 0.04) {
          ctx!.beginPath();
          ctx!.arc(pp.x, pp.y, pt.sz * pp.scale, 0, Math.PI * 2);
          ctx!.fillStyle = `rgba(0,240,255,${depthA})`;
          ctx!.fill();
        }
      });

      drawScanSweep();

      animId = requestAnimationFrame(draw);
    }

    draw();

    const onResize = () => { resize(); };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0, left: 0,
        width: "100%", height: "100%",
        pointerEvents: "none",
        zIndex: 0,
      }}
      aria-hidden="true"
    />
  );
}
