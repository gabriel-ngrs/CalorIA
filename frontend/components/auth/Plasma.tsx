"use client";

import { useEffect, useRef } from "react";
import { Renderer, Program, Mesh, Triangle } from "ogl";

interface PlasmaProps {
  speed?: number;
  scale?: number;
  opacity?: number;
}

const vertex = `#version 300 es
precision highp float;
in vec2 position;
in vec2 uv;
out vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const fragment = `#version 300 es
precision highp float;
uniform vec2 iResolution;
uniform float iTime;
uniform float uSpeed;
uniform float uScale;
uniform float uOpacity;
uniform vec2 uMouse;
out vec4 fragColor;

void mainImage(out vec4 o, vec2 C) {
  vec2 center = iResolution.xy * 0.5;
  C = (C - center) / uScale + center;

  vec2 mouseOffset = (uMouse - center) * 0.00015;
  C += mouseOffset * length(C - center);

  float i, d, z, T = iTime * uSpeed;
  vec3 O, p, S;

  for (vec2 r = iResolution.xy, Q; ++i < 60.; O += o.w/d*o.xyz) {
    p = z*normalize(vec3(C-.5*r,r.y));
    p.z -= 4.;
    S = p;
    d = p.y - T;

    p.x += .4*(1.+p.y)*sin(d + p.x*0.1)*cos(.34*d + p.x*0.05);
    Q = p.xz *= mat2(cos(p.y+vec4(0,11,33,0)-T));
    z+= d = abs(sqrt(length(Q*Q)) - .25*(5.+S.y))/3.+8e-4;
    o = 1.+sin(S.y+p.z*.5+S.z-length(S-p)+vec4(2,1,0,8));
  }

  o.xyz = tanh(O/1e4);
}

bool finite1(float x){ return !(isnan(x) || isinf(x)); }
vec3 sanitize(vec3 c){
  return vec3(
    finite1(c.r) ? c.r : 0.0,
    finite1(c.g) ? c.g : 0.0,
    finite1(c.b) ? c.b : 0.0
  );
}

void main() {
  vec4 o = vec4(0.0);
  mainImage(o, gl_FragCoord.xy);
  vec3 rgb = sanitize(o.rgb);

  /* Mapa de cor: empurra para o verde (#10B981) e azul (#60A5FA)
     que são as cores primárias do CalorIA, evitando magenta/vermelho intenso */
  vec3 mapped;
  mapped.r = rgb.r * 0.35 + rgb.b * 0.10;
  mapped.g = rgb.g * 0.70 + rgb.r * 0.25;
  mapped.b = rgb.b * 0.55 + rgb.g * 0.30;

  float alpha = length(mapped) * uOpacity;
  fragColor = vec4(mapped, alpha);
}
`;

export function Plasma({ speed = 0.35, scale = 1.0, opacity = 0.55 }: PlasmaProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mousePosRef  = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!containerRef.current) return;

    const renderer = new Renderer({
      webgl: 2,
      alpha: true,
      antialias: false,
      dpr: Math.min(window.devicePixelRatio || 1, 2),
    });
    const gl = renderer.gl;
    const canvas = gl.canvas as HTMLCanvasElement;
    canvas.style.cssText = "display:block;width:100%;height:100%;";
    containerRef.current.appendChild(canvas);

    const geometry = new Triangle(gl);

    const program = new Program(gl, {
      vertex,
      fragment,
      uniforms: {
        iTime:       { value: 0 },
        iResolution: { value: new Float32Array([1, 1]) },
        uSpeed:      { value: speed * 0.4 },
        uScale:      { value: scale },
        uOpacity:    { value: opacity },
        uMouse:      { value: new Float32Array([0, 0]) },
      },
      transparent: true,
    });

    const mesh = new Mesh(gl, { geometry, program });

    const onMouseMove = (e: MouseEvent) => {
      const rect = containerRef.current!.getBoundingClientRect();
      mousePosRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      const u = program.uniforms.uMouse.value as Float32Array;
      u[0] = mousePosRef.current.x;
      // ogl usa coordenadas Y invertidas em relação ao DOM
      u[1] = rect.height - mousePosRef.current.y;
    };
    window.addEventListener("mousemove", onMouseMove);

    const setSize = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      renderer.setSize(Math.max(1, Math.floor(rect.width)), Math.max(1, Math.floor(rect.height)));
      const res = program.uniforms.iResolution.value as Float32Array;
      res[0] = gl.drawingBufferWidth;
      res[1] = gl.drawingBufferHeight;
    };
    const ro = new ResizeObserver(setSize);
    ro.observe(containerRef.current);
    setSize();

    let raf = 0;
    const t0 = performance.now();
    const loop = (t: number) => {
      (program.uniforms.iTime as { value: number }).value = (t - t0) * 0.001;
      renderer.render({ scene: mesh });
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("mousemove", onMouseMove);
      try { containerRef.current?.removeChild(canvas); } catch {}
      gl.getExtension("WEBGL_lose_context")?.loseContext();
    };
  }, [speed, scale, opacity]);

  return <div ref={containerRef} className="absolute inset-0 w-full h-full" />;
}
