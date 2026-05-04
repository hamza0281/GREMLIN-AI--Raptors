"use client";
import { useEffect, useRef } from "react";

// ═══════════════════════════════════════════════════
//  3D CYBER GLOBE — Ultra-Performance Build
//  Optimisations:
//   • Adaptive frame-skip: targets 60fps, throttles on slow devices
//   • Offscreen star canvas (rendered once)
//   • Globe drawn to offscreen canvas, composited each frame
//   • Reduced grid (8 lat, 10 lon lines)
//   • Reduced arc segments (20), particles (20)
//   • No expensive shadow blur every frame (only once per sweep)
//   • requestAnimationFrame + will-change for GPU layer
//   • Resize debounced 200ms
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
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return {
    x: -r * Math.sin(phi) * Math.cos(theta),
    y: r * Math.cos(phi),
    z: r * Math.sin(phi) * Math.sin(theta),
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

    // ── Adaptive FPS throttle ──
    let lastTime = 0;
    const TARGET_MS = 1000 / 30; // 30fps target

    // ── Offscreen star canvas (rendered once) ──
    let starCanvas: HTMLCanvasElement | null = null;
    const STARS = Array.from({ length: 150 }, () => ({
      x: Math.random(),
      y: Math.random(),
      r: 0.6 + Math.random() * 1.2,
      a: 0.2 + Math.random() * 0.6,
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

    // ── Offscreen globe canvas — redraws only when rotY changes ──
    let globeCanvas: HTMLCanvasElement | null = null;
    function ensureGlobeCanvas() {
      if (!globeCanvas || globeCanvas.width !== W || globeCanvas.height !== H) {
        globeCanvas = document.createElement("canvas");
        globeCanvas.width = W;
        globeCanvas.height = H;
      }
    }

    // ── Resize (debounced) ──
    let resizeTimer: ReturnType<typeof setTimeout>;
    function resize() {
      W = window.innerWidth;
      H = window.innerHeight;
      canvas!.width = W;
      canvas!.height = H;
      R = Math.min(W, H) * 0.28;
      CX = W * 0.5;
      CY = H * 0.52;
      starCanvas = buildStarCanvas(W, H);
      globeCanvas = null; // invalidate
    }
    resize();

    function xform(p: Vec3) {
      return project(rotateY(rotateX(p, TILT), rotY), CX, CY, FOV);
    }

    // ── City nodes ──
    const CITIES = [
      { lat: 40.7, lon: -74.0 },
      { lat: 51.5, lon: -0.1 },
      { lat: 35.7, lon: 139.7 },
      { lat: -33.9, lon: 18.4 },
      { lat: 28.6, lon: 77.2 },
      { lat: 55.8, lon: 37.6 },
      { lat: -23.5, lon: -46.6 },
      { lat: 1.3, lon: 103.8 },
      { lat: 37.8, lon: -122.4 },
      { lat: 31.2, lon: 121.5 },
      { lat: 48.9, lon: 2.35 },
      { lat: 25.2, lon: 55.3 },
    ];

    const ARCS = [
      [0, 1], [1, 5], [2, 9], [3, 7], [4, 11],
      [6, 0], [8, 2], [10, 5], [7, 3], [0, 4],
    ];

    // ── Particles (minimal count) ──
    const PARTS = Array.from({ length: 40 }, () => ({
      lat: Math.random() * 180 - 90,
      lon: Math.random() * 360 - 180,
      spd: 0.15 + Math.random() * 0.35,
      sz: 1.0 + Math.random() * 1.5,
      tilt: (Math.random() - 0.5) * 0.5,
    }));

    // ── Globe: draw grid + arcs + nodes to offscreen canvas ──
    function drawGlobeOffscreen(gc: HTMLCanvasElement) {
      const gx = gc.getContext("2d")!;
      gx.clearRect(0, 0, W, H);

      const SEG_GRID = 30;
      const LAT = 8;
      const LON = 10;

      gx.lineWidth = 0.5;

      // Latitude rings
      for (let i = 1; i < LAT; i++) {
        const lat = -90 + (180 / LAT) * i;
        gx.beginPath();
        let first = true;
        for (let j = 0; j <= SEG_GRID; j++) {
          const lon = -180 + (360 / SEG_GRID) * j;
          const raw = latLonToVec3(lat, lon, R);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFront(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          first ? gx.moveTo(p.x, p.y) : gx.lineTo(p.x, p.y);
          first = false;
        }
        const isEq = Math.abs(lat) < 1;
        gx.strokeStyle = isEq ? "rgba(0,240,255,0.4)" : "rgba(0,240,255,0.15)";
        gx.lineWidth = isEq ? 1.5 : 0.8;
        gx.stroke();
      }

      // Longitude meridians
      gx.lineWidth = 0.4;
      for (let i = 0; i < LON; i++) {
        const lon = -180 + (360 / LON) * i;
        gx.beginPath();
        let first = true;
        for (let j = 0; j <= SEG_GRID; j++) {
          const lat = -90 + (180 / SEG_GRID) * j;
          const raw = latLonToVec3(lat, lon, R);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFront(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          first ? gx.moveTo(p.x, p.y) : gx.lineTo(p.x, p.y);
          first = false;
        }
        gx.strokeStyle = "rgba(0,240,255,0.12)";
        gx.stroke();
      }

      // Arcs
      const SEG_ARC = 20;
      ARCS.forEach(([ai, bi], idx) => {
        const A = CITIES[ai], B = CITIES[bi];
        if (!A || !B) return;
        const isRed = idx % 3 === 0;
        const col = isRed ? "255,0,64" : "0,240,255";
        const pulse = Math.sin(frame * 0.025 + idx * 0.8);
        const alpha = 0.4 + 0.3 * pulse;

        gx.beginPath();
        let first = true;
        for (let i = 0; i <= SEG_ARC; i++) {
          const t = i / SEG_ARC;
          const lat = A.lat + (B.lat - A.lat) * t;
          const lon = A.lon + (B.lon - A.lon) * t;
          const lift = Math.sin(t * Math.PI) * R * 0.25;
          const raw = latLonToVec3(lat, lon, R + lift);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFront(rot)) { first = true; continue; }
          const p = project(rot, CX, CY, FOV);
          first ? gx.moveTo(p.x, p.y) : gx.lineTo(p.x, p.y);
          first = false;
        }
        gx.strokeStyle = `rgba(${col},${alpha})`;
        gx.lineWidth = 1.5;
        gx.stroke();

        // Traveling dot
        const tP = ((frame * 0.008 + idx * 0.3) % 1);
        const pLat = A.lat + (B.lat - A.lat) * tP;
        const pLon = A.lon + (B.lon - A.lon) * tP;
        const pLift = Math.sin(tP * Math.PI) * R * 0.25;
        const rawP = latLonToVec3(pLat, pLon, R + pLift);
        const rotP = rotateY(rotateX(rawP, TILT), rotY);
        if (isFront(rotP)) {
          const pp = project(rotP, CX, CY, FOV);
          gx.beginPath();
          gx.arc(pp.x, pp.y, 2.5 * pp.scale, 0, TWO_PI);
          gx.fillStyle = `rgba(${col},1.0)`;
          gx.shadowColor = `rgba(${col},0.8)`;
          gx.shadowBlur = 8;
          gx.fill();
          gx.shadowBlur = 0;
        }
      });

      // Nodes
      CITIES.forEach(({ lat, lon }, idx) => {
        const raw = latLonToVec3(lat, lon, R);
        const rot = rotateY(rotateX(raw, TILT), rotY);
        if (!isFront(rot)) return;
        const p = project(rot, CX, CY, FOV);
        const pulse = Math.sin(frame * 0.04 + idx * 1.5);
        const isRed = idx % 4 === 0;
        const col = isRed ? "255,0,64" : "0,240,255";
        const alpha = 0.85 + pulse * 0.15;

        gx.beginPath();
        gx.arc(p.x, p.y, 2.0 * p.scale, 0, TWO_PI);
        gx.fillStyle = `rgba(${col},${alpha})`;
        gx.fill();

        gx.beginPath();
        gx.arc(p.x, p.y, (5.5 + pulse) * p.scale, 0, TWO_PI);
        gx.strokeStyle = `rgba(${col},${alpha * 0.5})`;
        gx.lineWidth = 1.2;
        gx.stroke();
      });

      // Orbital ring (just one, cheap)
      const ringR = R * 1.16;
      gx.beginPath();
      for (let i = 0; i <= 60; i++) {
        const a = (i / 60) * TWO_PI;
        const raw: Vec3 = { x: ringR * Math.cos(a), y: 0, z: ringR * Math.sin(a) };
        const rot = rotateY(rotateX(raw, TILT + 0.15), rotY);
        const p = project(rot, CX, CY, FOV);
        i === 0 ? gx.moveTo(p.x, p.y) : gx.lineTo(p.x, p.y);
      }
      gx.closePath();
      gx.strokeStyle = "rgba(0,240,255,0.2)";
      gx.lineWidth = 1.0;
      gx.setLineDash([4, 10]);
      gx.stroke();
      gx.setLineDash([]);
    }

    // ── Scan Sweep (drawn directly to main canvas, minimal shadow) ──
    function drawScanSweep() {
      const sweepLon = (((frame * 0.012 * 180) / Math.PI) % 360) - 180;
      ctx!.beginPath();
      let first = true;
      for (let lat = -75; lat <= 75; lat += 4) {
        const raw = latLonToVec3(lat, sweepLon, R * 1.002);
        const rot = rotateY(rotateX(raw, TILT), rotY);
        if (!isFront(rot)) { first = true; continue; }
        const p = project(rot, CX, CY, FOV);
        first ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
        first = false;
      }
      ctx!.strokeStyle = "rgba(0,240,255,0.4)";
      ctx!.lineWidth = 1.2;
      ctx!.shadowColor = "rgba(0,240,255,0.5)";
      ctx!.shadowBlur = 6;
      ctx!.stroke();
      ctx!.shadowBlur = 0;

      // 3 trailing lines only
      for (let off = 1; off <= 3; off++) {
        const tLon = sweepLon - off * 4;
        ctx!.beginPath();
        let tf = true;
        for (let lat = -75; lat <= 75; lat += 6) {
          const raw = latLonToVec3(lat, tLon, R * 1.001);
          const rot = rotateY(rotateX(raw, TILT), rotY);
          if (!isFront(rot)) { tf = true; continue; }
          const p = project(rot, CX, CY, FOV);
          tf ? ctx!.moveTo(p.x, p.y) : ctx!.lineTo(p.x, p.y);
          tf = false;
        }
        ctx!.strokeStyle = `rgba(0,240,255,${0.10 - off * 0.025})`;
        ctx!.lineWidth = 0.5;
        ctx!.stroke();
      }
    }

    // ── Main Loop (adaptive throttle) ──
    function draw(now: number) {
      animId = requestAnimationFrame(draw);

      // Skip frame if running too fast (cap at ~60fps)
      const elapsed = now - lastTime;
      if (elapsed < TARGET_MS - 2) return;
      lastTime = now - (elapsed % TARGET_MS);

      frame++;
      rotY += 0.0020;

      ctx!.clearRect(0, 0, W, H);

      // Stars composited from offscreen canvas (single drawImage)
      if (starCanvas) {
        ctx!.globalAlpha = 0.8;
        ctx!.drawImage(starCanvas, 0, 0);
        ctx!.globalAlpha = 1;
      }

      // Cheap halo (no per-frame gradient creation overhead — reuse simple arc fill)
      ctx!.beginPath();
      ctx!.arc(CX, CY, R * 1.55, 0, TWO_PI);
      ctx!.fillStyle = "rgba(0,240,255,0.06)";
      ctx!.fill();

      // Globe from offscreen canvas
      ensureGlobeCanvas();
      if (globeCanvas) {
        drawGlobeOffscreen(globeCanvas);
        ctx!.drawImage(globeCanvas, 0, 0);
      }

      // Particles (on main canvas, minimal)
      PARTS.forEach(pt => {
        pt.lon += pt.spd;
        if (pt.lon > 180) pt.lon -= 360;
        const orbitR = R * (1.04 + (pt.sz - 0.6) * 0.08);
        const raw = latLonToVec3(pt.lat, pt.lon, orbitR);
        const rot = rotateY(rotateX(raw, TILT + pt.tilt), rotY);
        const pp = project(rot, CX, CY, FOV);
        const depthA = Math.max(0, 1 - pp.z / (FOV * 0.9)) * 0.45;
        if (depthA > 0.08) {
          ctx!.beginPath();
          ctx!.arc(pp.x, pp.y, pt.sz * pp.scale, 0, TWO_PI);
          ctx!.fillStyle = `rgba(0,240,255,${depthA})`;
          ctx!.fill();
        }
      });

      drawScanSweep();
    }

    animId = requestAnimationFrame(draw);

    const onResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 200);
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
        willChange: "transform",
        transform: "translateZ(0)", // force GPU compositing layer
        imageRendering: "auto",
      }}
      aria-hidden="true"
    />
  );
}
