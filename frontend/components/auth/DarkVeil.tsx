"use client";

import { useEffect, useRef } from "react";

type Props = {
  hueShift?: number;
  noiseIntensity?: number;
  scanlineIntensity?: number;
  speed?: number;
  scanlineFrequency?: number;
  warpAmount?: number;
  resolutionScale?: number;
};

export default function DarkVeil({
  noiseIntensity = 0.02,
  scanlineIntensity = 0.04,
  speed = 0.2,
  scanlineFrequency = 1.2,
  warpAmount = 0.25,
  resolutionScale = 1,
}: Props) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) {
      return;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }

    const resize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      const dpr = Math.min(window.devicePixelRatio, 2) * resolutionScale;
      canvas.width = Math.max(1, Math.floor(w * dpr));
      canvas.height = Math.max(1, Math.floor(h * dpr));
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    window.addEventListener("resize", resize);
    resize();

    const start = performance.now();
    let frameId = 0;

    const loop = () => {
      const elapsed = ((performance.now() - start) / 1000) * speed;
      const w = window.innerWidth;
      const h = window.innerHeight;

      ctx.clearRect(0, 0, w, h);

      const base = ctx.createLinearGradient(0, 0, w, h);
      base.addColorStop(0, "hsl(198 36% 14%)");
      base.addColorStop(1, "hsl(198 34% 10%)");
      ctx.fillStyle = base;
      ctx.fillRect(0, 0, w, h);

      const orbA = ctx.createRadialGradient(
        w * (0.16 + Math.sin(elapsed * 0.6) * warpAmount * 0.05),
        h * (0.18 + Math.cos(elapsed * 0.55) * warpAmount * 0.06),
        0,
        w * 0.18,
        h * 0.22,
        Math.max(w, h) * 0.52
      );
      orbA.addColorStop(0, "hsla(198, 55%, 56%, 0.36)");
      orbA.addColorStop(1, "hsla(198, 55%, 56%, 0)");
      ctx.fillStyle = orbA;
      ctx.fillRect(0, 0, w, h);

      const orbB = ctx.createRadialGradient(
        w * (0.84 + Math.cos(elapsed * 0.5) * warpAmount * 0.05),
        h * (0.82 + Math.sin(elapsed * 0.45) * warpAmount * 0.05),
        0,
        w * 0.82,
        h * 0.78,
        Math.max(w, h) * 0.48
      );
      orbB.addColorStop(0, "hsla(28, 86%, 56%, 0.24)");
      orbB.addColorStop(1, "hsla(28, 86%, 56%, 0)");
      ctx.fillStyle = orbB;
      ctx.fillRect(0, 0, w, h);

      if (scanlineIntensity > 0) {
        const step = Math.max(2, Math.floor(12 / Math.max(scanlineFrequency, 0.2)));
        ctx.fillStyle = `rgba(255,255,255,${0.012 * scanlineIntensity})`;
        for (let y = 0; y < h; y += step) {
          ctx.fillRect(0, y, w, 1);
        }
      }

      if (noiseIntensity > 0) {
        const dots = Math.floor((w * h) / 1800);
        ctx.fillStyle = `rgba(255,255,255,${0.05 * noiseIntensity})`;
        for (let i = 0; i < dots; i += 1) {
          const x = Math.random() * w;
          const y = Math.random() * h;
          ctx.fillRect(x, y, 1, 1);
        }
      }

      frameId = requestAnimationFrame(loop);
    };

    loop();

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", resize);
    };
  }, [noiseIntensity, scanlineIntensity, scanlineFrequency, speed, warpAmount, resolutionScale]);

  return <canvas ref={ref} className="block h-full w-full" aria-hidden="true" />;
}
