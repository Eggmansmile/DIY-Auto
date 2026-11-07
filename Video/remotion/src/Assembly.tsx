import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, Easing } from "remotion";
import { C, FONT } from "./theme";
import S from "../../steps.json";
import F from "../../frames.json";

export const TITLE = 90;                                   // title card before the animation
const ease = Easing.bezier(0.45, 0, 0.2, 1);
const ramp = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });

const BOM = ["16× heat insert M3x6", "14× M3x10 · 4× M3x6 · 2× M3 nut", "M4x30 ×2 · M4x20/25/30 pivots", "10× plain M4 nut (jammed pairs)",
  "2× M5x40 · 2× M5x20 · 4× M5 nut", "8× MR105 bearing · 4× shim 5×7×0.5"];

const Panel = ({ i, f }: { i: number; f: number }) => {
  const st = S.steps[i];
  const t0 = F.step_starts[i];
  const p = ramp(f, t0 + 2, t0 + 16) * (1 - ramp(f, t0 + S.step_frames - 10, t0 + S.step_frames));
  if (p <= 0) return null;
  return (
    <div style={{ position: "absolute", left: 70 - (1 - p) * 60, top: 150, width: 600, opacity: p, fontFamily: FONT }}>
      <div style={{ color: C.orange, fontWeight: 800, fontSize: 26, letterSpacing: 3 }}>
        STEP {String(i + 1).padStart(2, "0")} / {S.steps.length}
      </div>
      <div style={{ color: C.ink, fontWeight: 800, fontSize: 60, lineHeight: 1.05, margin: "10px 0 28px" }}>{st.title}</div>
      {st.lines.map((l, k) => {
        const q = ramp(f, t0 + 14 + 8 * k, t0 + 26 + 8 * k);
        return (
          <div key={k} style={{ display: "flex", gap: 16, fontSize: 30, lineHeight: 1.3, color: C.ink, marginBottom: 16,
            opacity: q, transform: `translateY(${(1 - q) * 12}px)` }}>
            <div style={{ width: 10, height: 10, borderRadius: 5, background: C.orange, marginTop: 14, flexShrink: 0 }} />
            <div>{l}</div>
          </div>
        );
      })}
      <div style={{ marginTop: 26, padding: "20px 24px", background: "rgba(255,255,255,0.88)", borderLeft: `6px solid ${C.orange}`,
        borderRadius: 6, fontSize: 26, lineHeight: 1.35, color: C.graphite, opacity: ramp(f, t0 + 34, t0 + 46),
        boxShadow: "0 6px 24px rgba(0,0,0,0.08)" }}>
        <span style={{ fontWeight: 800, color: C.ink }}>TIP  </span>{st.tip}
      </div>
    </div>
  );
};

export const Assembly = () => {
  const frame = useCurrentFrame();
  const f = Math.max(0, frame - TITLE);                     // animation frame
  const src = staticFile(`frames/${String(Math.min(f, F.frames - 1)).padStart(4, "0")}.png`);
  const title = 1 - ramp(frame, TITLE - 20, TITLE);
  const step = F.step_starts.filter((s) => f >= s).length; // 0 = intro, 1..N
  const outro = ramp(f, F.outro + 20, F.outro + 40);
  const prog = Math.min(1, f / F.outro);
  return (
    <AbsoluteFill style={{ background: "#E6E8EC", fontFamily: FONT }}>
      <Img src={src} style={{ width: 1920, height: 1080, filter: `blur(${title * 10}px)` }} />
      {/* soft white gradient behind the text panel */}
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(241,240,236,0.92) 0%, rgba(241,240,236,0.75) 30%, rgba(241,240,236,0) 46%)",
        opacity: 1 - title }} />
      {S.steps.map((_, i) => <Panel key={i} i={i} f={f} />)}

      {/* intro caption */}
      <div style={{ position: "absolute", left: 70, top: 150, width: 600, opacity: (1 - title) * (1 - ramp(f, F.intro - 15, F.intro)) }}>
        <div style={{ color: C.orange, fontWeight: 800, fontSize: 26, letterSpacing: 3 }}>START</div>
        <div style={{ color: C.ink, fontWeight: 800, fontSize: 60, lineHeight: 1.05, marginTop: 10 }}>One-piece body</div>
        <div style={{ color: C.graphite, fontSize: 30, marginTop: 20, lineHeight: 1.3 }}>Printed in black ASA on the H2D. Clean off the brim and support under the steering beam first.</div>
      </div>

      {/* outro */}
      <div style={{ position: "absolute", left: 70, top: 150, width: 620, opacity: outro }}>
        <div style={{ color: C.orange, fontWeight: 800, fontSize: 26, letterSpacing: 3 }}>DONE</div>
        <div style={{ color: C.ink, fontWeight: 800, fontSize: 64, lineHeight: 1.05, margin: "10px 0 26px" }}>Ready to drive</div>
        {BOM.map((b, k) => (
          <div key={k} style={{ fontSize: 28, color: C.ink, marginBottom: 12, opacity: ramp(f, F.outro + 30 + 6 * k, F.outro + 42 + 6 * k) }}>{b}</div>
        ))}
      </div>

      {/* title card */}
      <AbsoluteFill style={{ background: `rgba(23,23,23,${0.55 * title})`, justifyContent: "center", alignItems: "center", opacity: title }}>
        <div style={{ color: C.orange, fontSize: 30, letterSpacing: 6, fontWeight: 600 }}>DIY-AUTO · V1</div>
        <div style={{ color: "#fff", fontSize: 110, fontWeight: 800, marginTop: 10 }}>Assembly guide</div>
        <div style={{ color: "#ddd", fontSize: 32, marginTop: 16 }}>11 steps · heat inserts, bearings, jam nuts</div>
      </AbsoluteFill>

      {/* progress bar */}
      <div style={{ position: "absolute", left: 70, right: 70, bottom: 50, display: "flex", gap: 8, opacity: 1 - title }}>
        {S.steps.map((_, i) => {
          const a = F.step_starts[i], b = i + 1 < S.steps.length ? F.step_starts[i + 1] : F.outro;
          const fill = Math.min(1, Math.max(0, (f - a) / (b - a)));
          return (
            <div key={i} style={{ flex: 1, height: 8, borderRadius: 4, background: "rgba(23,23,23,0.15)", overflow: "hidden" }}>
              <div style={{ width: `${fill * 100}%`, height: "100%", background: step === i + 1 ? C.orange : C.ink }} />
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", right: 70, bottom: 72, fontSize: 22, color: C.graphite, opacity: (1 - title) * (prog < 1 ? 1 : 0) }}>
        {step > 0 ? `${step}/${S.steps.length}` : ""}
      </div>
    </AbsoluteFill>
  );
};
