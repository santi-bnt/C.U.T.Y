import { createContext, useContext, type ReactNode } from "react";
import type { FaceFrameSource } from "../communication/faceFrames";

const FrameSource = createContext<FaceFrameSource | null>(null);
/** Optional decoded-frame injection. No transport is created by the website. */
export function FaceFrameProvider({
  source,
  children,
}: {
  source: FaceFrameSource;
  children: ReactNode;
}) {
  return <FrameSource.Provider value={source}>{children}</FrameSource.Provider>;
}
export const useFaceFrameSource = () => useContext(FrameSource);
