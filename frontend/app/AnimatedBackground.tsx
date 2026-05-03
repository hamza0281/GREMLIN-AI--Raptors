"use client";
import { useEffect, useRef } from "react";

// ═══════════════════════════════════════════════════
//  3D CYBER GLOBE — Performance-Optimised Build
//  Key fixes:
//   • Reduced grid segments (80→40) & lat/lon lines
//   • Stars pre-rendered to offscreen canvas
//   • Resize throttled with debounce
//   • will-change: transform on canvas for GPU layer
//   • Reduced particle count (60→30)
//   • Early-exit invisible particles
// ═══════════════════════════════════════════════════

interface Vec3 { x: number; y: number; z: number }

const TWO_PI = Math.PI * 2;

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
function isFront(p: Vec3) { return p.z < 0; }

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    let animId: number;
    let frame = 0;
    let rotY = 0;
    let W = 0, H = 0, R = 0, CX = 0, CY = 0;
    const FOV = 500;
    const TILT = 0.3;

    // ── Offscreen star canvas (rendered once, composited each frame) ──
    let starCanvas: HTMLCanvasElement | null = null;
    const STARS = Array.from({ length: 120 }, () => ({
      x: Math.random(),
      y: Math.random(),
      r: 0.4 + Math.random() * 0.9,
      a: 0.15 + Math.random() * 0.5,
    }));

    function buildStarCanvas(w: number, h: number) {
      const sc = document.createElement("canvas");
      sc.width = w; sc.height = h;
      const sx = sc.getContext("2d")!;
      STARS.forEach(s => {
        sx.beginPath();
        sx.arc(s.x * w, s.y * h, s.r, 0, TWO_PI);
        sx.fillStyle = `rgba(0,240,255,${s.a})`;
        sx.fill();
      });
      return sc;
    }

    // ── Resize (debounced) ──
    let resizeTimer: ReturnType<typeof setTimeout>;
    function resize() {
      W = window.innerWidth;
      H = window.innerHeight;
      canvas!.width  = W;
      canvas!.height = H;
      R  = Math.min(W, H) * 0.30;
      CX = W * 0.5;
      CY = H * 0.52;
      starCanvas = buildStarCanvas(W, H);
    }
    resize();

    function xform(p: Vec3) {
      return project(rotateY(rotateX(p, TILT), rotY), CX, CY, FOV);
    }

    // ── City nodes ──
    const CITIES = [
      { lat: 40.7,  lon: -74.0  },
      { lat: 51.5,  lon:  -0.1  },
      { lat: 35.7,  lon: 139.7  },
      { lat:-33.9,  lon:  18.4  },
      { lat: 28.6,  lon:  77.2  },
      { lat: 55.8,  lon:  37.6  },
      { lat:-23.5,  lon: -46.6  },
      { lat:  1.3,  lon: 103.8  },
      { lat: 37.8,  lon:-122.4  },
      { lat:-34.6,  lon: -58.4  },
      { lat: 31.2,  lon: 121.5  },
      { lat: 48.9,  lon:   2.35 },
      { lat: 25.2,  lon:  55.3  },
      { lat: 13.8,  lon: 100.5  },
      { lat: 59.3,  lon:  18.1  },
      { lat:-37.8,  lon: 144.9  },
    ];

    const ARCS = [
      [0,1],[1,5],[2,10],[3,7],[4,12],
      [6,0],[8,2],[9,6],[11,5],[7,13],
      [14,1],[15,7],[0,4],[10,2],[12,3],
    ];

    // ── Particles (reduced count) ──
    const PARTS = Array.from({ length: 30 }, () => ({
      lat:  Math.random() * 180 - 90,
      lon:  Math.random() * 360 - 180,
      spd:  0.15 + Math.random() * 0.3,
      sz:   0.7 + Math.random() * 1.2,
      tilt: (Math.random() - 0.5) * 0.5,
    }));

    // ── Globe Grid (reduced segments) ──
    function drawGrid() {
      const SEG = 40; // was 80
      const LAT  = 10; // was 14
      const LON  = 14; // was 20

      ctx!.lineWidth = 0.6;
      // Latitude rings
      for (let i = 1; i < LAT; i++) {
        const lat = -90 + (180 / LAT) * i;
        ctx!.beginPath();
        let first = true;
        for (let j = 0; j <= SEG; j++) {
          const lon = -180 + (360 / SEG) * j;
          const raw = latLonToVec3(lat, lon, R);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFront(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          first ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
          first = false;
        }
        const isEq = Math.abs(lat) < 1;
        ctx!.strokeStyle = isEq ? "rgba(0,240,255,0.28)" : "rgba(0,240,255,0.08)";
        ctx!.lineWidth   = isEq ? 1.2 : 0.5;
        ctx!.stroke();
      }
      // Longitude meridians
      ctx!.lineWidth = 0.5;
      for (let i = 0; i < LON; i++) {
        const lon = -180 + (360 / LON) * i;
        ctx!.beginPath();
        let first = true;
        for (let j = 0; j <= SEG; j++) {
          const lat = -90 + (180 / SEG) * j;
          const raw = latLonToVec3(lat, lon, R);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFront(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          first ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
          first = false;
        }
        ctx!.strokeStyle = "rgba(0,240,255,0.08)";
        ctx!.stroke();
      }
    }

    // ── Arcs ──
    function drawArcs() {
      const SEG = 35; // was 50
      ARCS.forEach(([ai, bi], idx) => {
        const A = CITIES[ai], B = CITIES[bi];
        if (!A || !B) return;
        const isRed = idx % 3 === 0;
        const col   = isRed ? "255,0,64" : "0,240,255";
        const pulse = Math.sin(frame * 0.025 + idx * 0.8);
        const alpha = 0.22 + 0.18 * pulse;

        ctx!.beginPath();
        let first = true;
        for (let i = 0; i <= SEG; i++) {
          const t   = i / SEG;
          const lat = A.lat + (B.lat - A.lat) * t;
          const lon = A.lon + (B.lon - A.lon) * t;
          const lift = Math.sin(t * Math.PI) * R * 0.28;
          const raw = latLonToVec3(lat, lon, R + lift);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFront(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          first ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
          first = false;
        }
        ctx!.strokeStyle = `rgba(${col},${alpha})`;
        ctx!.lineWidth   = 1.0;
        ctx!.stroke();

        // Traveling dot
        const tP = ((frame * 0.009 + idx * 0.3) % 1);
        const pLat  = A.lat + (B.lat - A.lat) * tP;
        const pLon  = A.lon + (B.lon - A.lon) * tP;
        const pLift = Math.sin(tP * Math.PI) * R * 0.28;
        const rawP  = latLonToVec3(pLat, pLon, R + pLift);
        const rotP  = rotateY(rotateX(rawP, TILT), rotY);
        if (isFront(rotP)) {
          const pp = project(rotP, CX, CY, FOV);
          ctx!.beginPath();
          ctx!.arc(pp.x, pp.y, 2 * pp.scale, 0, TWO_PI);
          ctx!.fillStyle = `rgba(${col},0.9)`;
          ctx!.fill();
        }
      });
    }

    // ── Nodes ──
    function drawNodes() {
      CITIES.forEach(({ lat, lon }, idx) => {
        const raw = latLonToVec3(lat, lon, R);
        const rot = rotateY(rotateX(raw, TILT), rotY);
        if (!isFront(rot)) return;
        const p = project(rot, CX, CY, FOV);
        const pulse = Math.sin(frame * 0.04 + idx * 1.5);
        const isRed = idx % 4 === 0;
        const col   = isRed ? "255,0,64" : "0,240,255";
        const alpha = 0.65 + pulse * 0.25;

        ctx!.beginPath();
        ctx!.arc(p.x, p.y, 2.2 * p.scale, 0, TWO_PI);
        ctx!.fillStyle = `rgba(${col},${alpha})`;
        ctx!.fill();

        // Outer ring (no gradient — cheaper)
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, (5 + pulse) * p.scale, 0, TWO_PI);
        ctx!.strokeStyle = `rgba(${col},${alpha * 0.4})`;
        ctx!.lineWidth = 0.8;
        ctx!.stroke();
      });
    }

    // ── Orbital Rings ──
    function drawOrbitalRings() {
      [[TILT + 0.15, 0, "0,240,255", 0.10], [TILT - 0.3, 0.5, "255,0,64", 0.06]].forEach(
        ([tilt, offset, col, opacity]) => {
          const ringR = R * 1.18;
          ctx!.beginPath();
          for (let i = 0; i <= 80; i++) { // was 120
            const a   = (i / 80) * TWO_PI;
            const raw: Vec3 = { x: ringR * Math.cos(a), y: 0, z: ringR * Math.sin(a) };
            const rot = rotateY(rotateX(raw, tilt as number), rotY + (offset as number));
            const p   = project(rot, CX, CY, FOV);
            i === 0 ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
          }
          ctx!.closePath();
          ctx!.strokeStyle = `rgba(${col},${opacity})`;
          ctx!.lineWidth   = 0.7;
          ctx!.setLineDash([4, 10]);
          ctx!.stroke();
          ctx!.setLineDash([]);
        }
      );
    }

    // ── Scan Sweep (lighter trail) ──
    function drawScanSweep() {
      const sweepLon = (((frame * 0.014 * 180) / Math.PI) % 360) - 180;
      ctx!.beginPath();
      let first = true;
      for (let lat = -80; lat <= 80; lat += 3) { // step 3 instead of 2
        const raw = latLonToVec3(lat, sweepLon, R * 1.003);
        const rot = rotateY(rotateX(raw, TILT), rotY);
        if (!isFront(rot)) { first = true; continue; }
        const p = project(rot, CX, CY, FOV);
        first ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
        first = false;
      }
      ctx!.strokeStyle  = "rgba(0,240,255,0.45)";
      ctx!.lineWidth    = 1.5;
      ctx!.shadowColor  = "rgba(0,240,255,0.6)";
      ctx!.shadowBlur   = 8;
      ctx!.stroke();
      ctx!.shadowBlur   = 0;

      // Only 4 trailing lines instead of 8
      for (let off = 1; off <= 4; off++) {
        const tLon = sweepLon - off * 3;
        ctx!.beginPath();
        let tf = true;
        for (let lat = -80; lat <= 80; lat += 5) {
          const raw = latLonToVec3(lat, tLon, R * 1.002);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFront(rot)) { tf = true; continue; }
          const p = project(rot, CX, CY, FOV);
          tf ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
          tf = false;
        }
        ctx!.strokeStyle = `rgba(0,240,255,${0.12 - off * 0.025})`;
        ctx!.lineWidth   = 0.6;
        ctx!.stroke();
      }
    }

    // ── Main Loop ──
    function draw() {
      frame++;
      rotY += 0.0022; // slightly slower = smoother feel

      ctx!.clearRect(0, 0, W, H);

      // Stars: composite offscreen canvas (one drawImage call)
      if (starCanvas) {
        ctx!.globalAlpha = 0.85;
        ctx!.drawImage(starCanvas, 0, 0);
        ctx!.globalAlpha = 1;
      }

      // Globe glow halo (simple arc fill, no gradient each frame)
      const gG = ctx!.createRadialGradient(CX, CY, R * 0.6, CX, CY, R * 1.6);
      gG.addColorStop(0,   "rgba(0,240,255,0.055)");
      gG.addColorStop(1,   "transparent");
      ctx!.fillStyle = gG;
      ctx!.beginPath();
      ctx!.arc(CX, CY, R * 1.6, 0, TWO_PI);
      ctx!.fill();

      drawGrid();
      drawArcs();
      drawNodes();
      drawOrbitalRings();

      // Particles
      PARTS.forEach(pt => {
        pt.lon += pt.spd;
        if (pt.lon > 180) pt.lon -= 360;
        const orbitR = R * (1.05 + (pt.sz - 0.7) * 0.1);
        const raw = latLonToVec3(pt.lat, pt.lon, orbitR);
        const rot = rotateY(rotateX(raw, TILT + pt.tilt), rotY);
        const pp  = project(rot, CX, CY, FOV);
        const depthA = Math.max(0, 1 - pp.z / (FOV * 0.9)) * 0.5;
        if (depthA > 0.06) { // higher threshold = skip more invisible ones
          ctx!.beginPath();
          ctx!.arc(pp.x, pp.y, pt.sz * pp.scale, 0, TWO_PI);
          ctx!.fillStyle = `rgba(0,240,255,${depthA})`;
          ctx!.fill();
        }
      });

      drawScanSweep();
      animId = requestAnimationFrame(draw);
    }

    draw();

    const onResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 150); // debounced
    };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(animId);
      clearTimeout(resizeTimer);
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
        willChange: "transform", // GPU compositing layer
      }}
      aria-hidden="true"
    />
  );
}
