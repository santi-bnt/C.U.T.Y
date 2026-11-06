import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, useGLTF, ContactShadows } from "@react-three/drei";
import { Group, Vector3 } from "three";
import type { StoryMotion } from "./storyMotion";
import type { OrbitControls as OrbitControlsType } from "three-stdlib";
import { cameraViews, type CameraView } from "./model";
import { modelInfo } from "../data/model";
import { prepareRobot } from "./robot";
import { useFaceTexture } from "./useFaceTexture";
import { useMedia } from "../state/useMedia";

function Robot({
  wireframe,
  onLoaded,
  reduced,
  active,
}: {
  wireframe: boolean;
  onLoaded: () => void;
  reduced: boolean;
  active: boolean;
}) {
  const root = useRef<Group>(null);
  const { invalidate } = useThree();
  useEffect(() => {
    if (reduced || !active) return;
    const timer = window.setInterval(invalidate, 1000 / 30);
    return () => window.clearInterval(timer);
  }, [reduced, active, invalidate]);
  useFrame(({ clock }) => {
    if (reduced || !active || !root.current) return;
    root.current.position.y = 1.53 + Math.sin(clock.elapsedTime * 0.8) * 0.018;
  });
  const { scene } = useGLTF(modelInfo.url);
  const faceTexture = useFaceTexture();
  const { object, measurement, materials, geometries } = useMemo(
    () => prepareRobot(scene, faceTexture, wireframe),
    [scene, faceTexture, wireframe],
  );
  useEffect(() => {
    onLoaded();
  }, [onLoaded]);
  useEffect(
    () => () => {
      materials.forEach((material) => material.dispose());
      geometries.forEach((geometry) => geometry.dispose());
    },
    [materials, geometries],
  );
  return (
    <group ref={root} position={[0, 1.53, 0]} scale={measurement.scale}>
      <primitive
        object={object}
        position={measurement.center.clone().negate()}
      />
    </group>
  );
}
function Rig({
  view,
  reset,
  zoom,
  autoRotate,
  reduced,
  motion,
  onManual,
}: {
  view: CameraView;
  reset: number;
  zoom: number;
  autoRotate: boolean;
  reduced: boolean;
  motion?: StoryMotion;
  onManual: () => void;
}) {
  const controls = useRef<OrbitControlsType>(null);
  const destination = useRef<Vector3 | null>(null);
  const viewTarget = useMemo(() => new Vector3(), []);
  const storyGoal = useMemo(() => new Vector3(), []);
  const { camera, invalidate } = useThree();
  useEffect(() => motion?.subscribe(invalidate), [motion, invalidate]);
  useEffect(() => {
    const target = viewTarget.set(0, view === "display" ? 2.2 : 1.5, 0);
    destination.current = new Vector3(...cameraViews[view])
      .sub(target)
      .multiplyScalar(Math.pow(0.85, zoom))
      .clampLength(view === "display" ? 2.5 : 4, 10.8)
      .add(target);
    if (reduced) {
      camera.position.copy(destination.current);
      controls.current?.target.copy(target);
      controls.current?.update();
      destination.current = null;
    }
    invalidate();
  }, [view, reset, zoom, reduced, camera, invalidate, viewTarget]);
  useFrame((_, delta) => {
    if (motion?.following && !reduced && controls.current) {
      const p = motion.progress;
      // Whole-assembly orbit only; no invented joints or component anchors.
      const angle = 0.22 + p * 1.18;
      const distance = 6.2 - Math.sin(p * Math.PI) * 0.4;
      const goal = storyGoal.set(
        Math.sin(angle) * distance,
        2.3 + p * 0.5,
        Math.cos(angle) * distance,
      );
      camera.position.lerp(goal, 1 - Math.exp(-delta * 5));
      controls.current.target.set(0, 1.5, 0);
      controls.current.autoRotate = false;
      controls.current.update();
      destination.current = null;
      if (camera.position.distanceTo(goal) > 0.003) invalidate();
      return;
    }
    if (controls.current)
      controls.current.autoRotate = autoRotate && !destination.current;
    if (!destination.current) return;
    camera.position.lerp(destination.current, 1 - Math.exp(-delta * 7));
    controls.current?.target.lerp(viewTarget, 1 - Math.exp(-delta * 7));
    controls.current?.update();
    if (camera.position.distanceTo(destination.current) < 0.005)
      destination.current = null;
    invalidate();
  });
  return (
    <OrbitControls
      ref={controls}
      target={[0, 1.5, 0]}
      autoRotate={autoRotate}
      autoRotateSpeed={0.6}
      enablePan={false}
      minDistance={2.5}
      maxDistance={11}
      maxPolarAngle={Math.PI * 0.92}
      enableDamping={!reduced}
      onStart={() => {
        onManual();
        destination.current = null;
      }}
    />
  );
}
export default function Scene({
  view,
  reset,
  zoom,
  autoRotate,
  wireframe,
  reduced,
  active,
  onLoaded,
  motion,
  onManual,
}: {
  view: CameraView;
  reset: number;
  zoom: number;
  autoRotate: boolean;
  wireframe: boolean;
  reduced: boolean;
  active: boolean;
  onLoaded: () => void;
  motion?: StoryMotion;
  onManual: () => void;
}) {
  const compact = useMedia("(max-width: 900px)");
  return (
    <Canvas
      frameloop={active ? "demand" : "never"}
      dpr={[1, 1.5]}
      camera={{ position: [4, 3.2, 6], fov: 35, near: 0.1, far: 50 }}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
    >
      <ambientLight intensity={1.2} />
      <directionalLight position={[4, 7, 5]} intensity={3.5} color="#f5faff" />
      <directionalLight position={[-4, 3, -4]} intensity={5} color="#c4b5fd" />
      <directionalLight position={[2, 1, -5]} intensity={1.5} color="#b5a2ff" />
      <Suspense fallback={null}>
        <Robot
          wireframe={wireframe}
          onLoaded={onLoaded}
          reduced={reduced || compact}
          active={active}
        />
        <ContactShadows
          position={[0, 0, 0]}
          scale={10}
          opacity={0.5}
          blur={2.8}
          far={5}
          resolution={256}
          frames={1}
          color="#050a12"
        />
      </Suspense>
      <Rig
        view={view}
        reset={reset}
        zoom={zoom}
        autoRotate={autoRotate && active}
        reduced={reduced}
        motion={motion}
        onManual={onManual}
      />
    </Canvas>
  );
}
