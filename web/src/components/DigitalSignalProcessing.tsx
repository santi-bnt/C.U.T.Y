import { useMemo, useState } from "react";
import { useLocale } from "../state/Locale";
import "./digital-signal-processing.css";

type Mode = "head" | "speech";
type View = "compare" | "original" | "filtered";
const RATE = 16_000;
const TAPS = 511;
const N = 320;

function coefficients(mode: Mode) {
  if (mode === "head") return Array(5).fill(0.2) as number[];
  const low = 150, high = 4000, middle = (TAPS - 1) / 2;
  const lp = (cutoff: number, n: number) => n === 0 ? 2 * cutoff / RATE : Math.sin(2 * Math.PI * cutoff / RATE * n) / (Math.PI * n);
  const taps = Array.from({ length: TAPS }, (_, i) => {
    const n = i - middle;
    return (lp(high, n) - lp(low, n)) * (0.54 - 0.46 * Math.cos(2 * Math.PI * i / (TAPS - 1)));
  });
  const center = (low + high) / 2;
  const gain = Math.hypot(
    taps.reduce((sum, c, i) => sum + c * Math.cos(2 * Math.PI * center * i / RATE), 0),
    taps.reduce((sum, c, i) => sum - c * Math.sin(2 * Math.PI * center * i / RATE), 0),
  );
  return taps.map((c) => c / gain);
}

function response(h: number[], hz: number, rate = RATE) {
  const re = h.reduce((sum, c, i) => sum + c * Math.cos(2 * Math.PI * hz * i / rate), 0);
  const im = h.reduce((sum, c, i) => sum - c * Math.sin(2 * Math.PI * hz * i / rate), 0);
  return { magnitude: Math.hypot(re, im), phase: Math.atan2(im, re) };
}

function signal(mode: Mode, testHz: number, h: number[]) {
  const count = 320;
  const input = Array.from({ length: count }, (_, i) => mode === "head"
    ? 0.22 + (i >= 45 ? 0.38 : 0) + 0.035 * Math.sin(2 * Math.PI * 7 * i / 50)
    : 0.42 * Math.sin(2 * Math.PI * testHz * i / RATE) + 0.26 * Math.sin(2 * Math.PI * 6000 * i / RATE));
  const filtered = input.map((_, i) => h.reduce((sum, c, k) => sum + c * (input[i - k] ?? 0), 0));
  return { input, filtered };
}

function spectrum(values: number[], rate: number) {
  const bins = values.length / 2;
  return Array.from({ length: bins + 1 }, (_, bin) => {
    const re = values.reduce((sum, sample, n) => sum + sample * Math.cos(2 * Math.PI * bin * n / values.length), 0);
    const im = values.reduce((sum, sample, n) => sum - sample * Math.sin(2 * Math.PI * bin * n / values.length), 0);
    return { hz: bin * rate / values.length, amplitude: Math.hypot(re, im) / values.length };
  });
}

function path(values: number[], width: number, height: number, scale: number) {
  return values.map((value, i) => `${i ? "L" : "M"}${(i / (values.length - 1) * width).toFixed(1)},${(height / 2 - value * scale * height / 2).toFixed(1)}`).join(" ");
}

function Plot({ title, input, filtered, compare = false }: { title: string; input: number[]; filtered: number[]; compare?: boolean }) {
  const width = 640, height = 170;
  const peak = Math.max(1, ...input.map(Math.abs), ...filtered.map(Math.abs));
  return <figure className="dsp-plot"><figcaption>{title}</figcaption>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
      <path className="dsp-axis" d={`M0 ${height / 2}H${width}`} />
      {(compare || !filtered.length) && <path className="dsp-original" d={path(input, width, height, 1 / peak)} />}
      {filtered.length > 0 && <path className="dsp-filtered" d={path(filtered, width, height, 1 / peak)} />}
    </svg>
    {compare && <div className="dsp-legend"><span className="dsp-legend-original">Original</span><span className="dsp-legend-filtered">FIR output</span></div>}
  </figure>;
}

export default function DigitalSignalProcessing() {
  const { locale } = useLocale();
  const es = locale === "es";
  const [mode, setMode] = useState<Mode>("head");
  const [view, setView] = useState<View>("compare");
  const [tone, setTone] = useState(1000);
  const h = useMemo(() => coefficients(mode), [mode]);
  const samples = useMemo(() => signal(mode, tone, h), [mode, tone, h]);
  const signalRate = mode === "head" ? 50 : RATE;
  const frequency = Array.from({ length: 129 }, (_, i) => {
    const hz = i * (signalRate / 2) / 128;
    const { magnitude, phase } = response(h, hz, signalRate);
    return { hz, db: Math.max(-80, 20 * Math.log10(Math.max(magnitude, 1e-8))), phase };
  });
  const visibleInput = view === "filtered" ? [] : samples.input.slice(0, N);
  const visibleFiltered = view === "original" ? [] : samples.filtered.slice(0, N);
  const spectrumInput = useMemo(() => spectrum(samples.input, signalRate), [samples.input, signalRate]);
  const spectrumFiltered = useMemo(() => spectrum(samples.filtered, signalRate), [samples.filtered, signalRate]);
  const visibleSpectrumInput = view === "filtered" ? [] : spectrumInput.map((bin) => bin.amplitude);
  const visibleSpectrumFiltered = view === "original" ? [] : spectrumFiltered.map((bin) => bin.amplitude);
  return <section id="dsp-filters" className="dsp-section ink" aria-labelledby="dsp-title">
    <div className="dsp-heading"><span className="eyebrow">09 / DIGITAL SIGNAL PROCESSING</span>
      <h2 id="dsp-title">Digital Signal Processing / FIR Filters</h2>
      <p>{es ? "Dos filtros FIR de fase lineal para seguimiento PAN y preprocesamiento de voz. Gráficas sintéticas calculadas en el navegador; ninguna señal viene del robot." : "Two linear-phase FIR filters for PAN tracking and speech preprocessing. Synthetic plots are calculated in-browser; no signal comes from the robot."}</p>
    </div>
    <div className="dsp-status"><span>{es ? "C en STM32: integrado en lógica portable" : "STM32 C: integrated in portable control logic"}</span><span>{es ? "Python: integrado; audio desactivado por defecto" : "Python: integrated; audio disabled by default"}</span><span>{es ? "Pruebas de software; validación física pendiente" : "Software tests; physical validation pending"}</span></div>
    <div className="dsp-tabs" role="group" aria-label={es ? "Seleccionar filtro" : "Select filter"}>
      <button type="button" aria-pressed={mode === "head"} onClick={() => setMode("head")}>{es ? "Seguimiento de cabeza · pasa-bajas" : "Head tracking · low-pass"}</button>
      <button type="button" aria-pressed={mode === "speech"} onClick={() => setMode("speech")}>{es ? "Voz · pasa-banda" : "Speech · band-pass"}</button>
    </div>
    <div className="dsp-flow" aria-label={es ? "Flujo de procesamiento de señales" : "Signal processing flow"}>
      {(mode === "head"
        ? ["Camera", "Raspberry Pi · FaceTracker", "UART target", "STM32 · FreeRTOS · FIR", "PAN trajectory"]
        : ["ReSpeaker · mono PCM16", `FIR · ${RATE / 1000} kHz`, "Gemini Live"]).map((label, i, all) => <span key={label}>{label}{i < all.length - 1 && <b aria-hidden="true">→</b>}</span>)}
    </div>
    <div className="dsp-facts">
      <article><small>{es ? "Coeficientes / orden" : "Coefficients / order"}</small><strong>{h.length} / {h.length - 1}</strong></article>
      <article><small>{es ? "Fs / retardo de grupo" : "Fs / group delay"}</small><strong>{mode === "head" ? "50 Hz · 40 ms" : "16 kHz · 15.94 ms"}</strong></article>
      <article><small>{es ? "Ecuación" : "Difference equation"}</small><strong className="dsp-equation">y[n] = Σ h[k] x[n−k]</strong></article>
      <article><small>{es ? "Respuesta / fase" : "Response / phase"}</small><strong>{es ? "Simétrica · lineal" : "Symmetric · linear"}</strong></article>
    </div>
    <p className="dsp-coefficients"><strong>{es ? "Coeficientes h[k]:" : "Coefficients h[k]:"}</strong> {mode === "head" ? "[0.2, 0.2, 0.2, 0.2, 0.2]" : `511 ${es ? "coeficientes simétricos con ventana Hamming · normalizados a" : "symmetric Hamming-windowed taps · normalized at"} ${(150 + 4000) / 2} Hz`}</p>
    <div className="dsp-controls">
      <div className="dsp-tabs" role="group" aria-label={es ? "Vista de señal" : "Signal view"}>
        {(["original", "filtered", "compare"] as const).map((item) => <button type="button" key={item} aria-pressed={view === item} onClick={() => setView(item)}>{item === "compare" ? (es ? "Comparar" : "Compare") : item === "original" ? (es ? "Original" : "Original") : (es ? "Filtrada" : "Filtered")}</button>)}
      </div>
      {mode === "speech" && <label className="dsp-slider">{es ? "Tono de prueba" : "Test tone"} {tone} Hz<input type="range" min="50" max="7000" step="50" value={tone} onChange={(event) => setTone(Number(event.target.value))} /></label>}
    </div>
    <div className="dsp-plots">
      <Plot title={mode === "head"
        ? (es ? "Referencia PAN sintética · primeros 6.4 s" : "Synthetic PAN target · first 6.4 s")
        : (es ? "Audio sintético · primeros 20 ms" : "Synthetic audio · first 20 ms")} input={visibleInput} filtered={visibleFiltered} compare={view === "compare"} />
      <figure className="dsp-plot"><figcaption>{es ? "Respuesta en frecuencia · magnitud dB y fase" : "Frequency response · magnitude dB and phase"}</figcaption>
        <svg viewBox="0 0 640 170" role="img" aria-label="FIR magnitude and phase response">
          <path className="dsp-axis" d="M0 15H640M0 85H640M0 155H640" />
          <path className="dsp-filtered" d={path(frequency.map((p) => (p.db + 80) / 80 * 2 - 1), 640, 170, 0.46)} />
          <path className="dsp-phase" d={path(frequency.map((p) => p.phase / Math.PI), 640, 170, 0.46)} />
        </svg><div className="dsp-legend"><span className="dsp-legend-magnitude">{es ? "Magnitud (−80 a 0 dB)" : "Magnitude (−80 to 0 dB)"}</span><span className="dsp-legend-phase">{es ? "Fase (rad, escalada)" : "Phase (rad, scaled)"}</span><span className="dsp-legend-range">{es ? `0–${signalRate / 2} Hz` : `0–${signalRate / 2} Hz`}</span></div>
      </figure>
      <Plot title={es ? "Espectro sintético · amplitud relativa" : "Synthetic signal spectrum · relative amplitude"} input={visibleSpectrumInput} filtered={visibleSpectrumFiltered} compare={view === "compare"} />
    </div>
    <p className="dsp-caption">{mode === "head"
      ? (es ? "Media móvil: retardo de grupo 2 muestras. FaceTracker ya suaviza detecciones y su controlador limita movimiento; este FIR se aplica una sola vez en cada actualización STM32 de 20 ms. El sistema completo de cámara a servo aún no está conectado ni validado en hardware." : "Moving average: 2-sample group delay. FaceTracker already smooths detections and its controller limits motion; this FIR runs once per 20 ms STM32 update. The camera-to-servo system is not yet connected or hardware validated.")
      : (es ? "Pasa-banda Hamming diseñado para fs=16 kHz, banda nominal 150–4,000 Hz. Se eligieron 511 taps para mejorar el rechazo cerca del borde bajo; a 100 Hz la ganancia calculada es ≈−45.1 dB y a 5 kHz ≈−69.9 dB. No cancela ruido ambiental ni demuestra mejor reconocimiento." : "Hamming band-pass designed for fs=16 kHz, nominal 150–4,000 Hz. 511 taps improve rejection near the lower edge; calculated gain is ≈−45.1 dB at 100 Hz and ≈−69.9 dB at 5 kHz. It does not cancel ambient noise or prove better recognition.")}</p>
  </section>;
}
