import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useMedia } from "./useMedia";
import { bi } from "../data/project";

export const faceExpressions = [
  { id: "idle", label: bi("Neutral", "Neutral") },
  { id: "listening", label: bi("Listening", "Escuchando") },
  { id: "happy", label: bi("Happy", "Feliz") },
  { id: "surprised", label: bi("Surprised", "Sorprendido") },
] as const;
export type FaceExpression = (typeof faceExpressions)[number]["id"];
interface FaceState {
  expression: FaceExpression;
  setExpression: (value: FaceExpression) => void;
  setGaze: (value: number) => void;
  talk: boolean;
  setTalk: (value: boolean | ((previous: boolean) => boolean)) => void;
  frame: number;
  reduced: boolean;
}
const Context = createContext<FaceState | null>(null);
export function FaceSimulationProvider({ children }: { children: ReactNode }) {
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [expression, setExpression] = useState<FaceExpression>("idle");
  const [gaze, setGaze] = useState(4);
  const [talk, setTalk] = useState(false);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (reduced) return;
    const timer = window.setInterval(() => setTick((value) => value + 1), 140);
    return () => window.clearInterval(timer);
  }, [reduced]);
  const mouth = talk && !reduced ? [0, 1, 3, 2, 1, 0][tick % 6] : 0;
  const blinking = !reduced && tick % 29 === 28;
  const frame = (blinking ? 9 : gaze) * 4 + mouth;
  const value = useMemo(
    () => ({
      expression,
      setExpression,
      setGaze,
      talk,
      setTalk,
      frame,
      reduced,
    }),
    [expression, talk, frame, reduced],
  );
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useFaceSimulation() {
  const value = useContext(Context);
  if (!value) throw new Error("FaceSimulationProvider required");
  return value;
}
