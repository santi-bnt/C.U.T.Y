import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  OrbitControls,
  useGLTF,
  Environment,
  Lightformer,
  ContactShadows,
} from "@react-three/drei";
import { Group, PerspectiveCamera, Vector3 } from "three";
import type { OrbitControls as OrbitControlsType } from "three-stdlib";
import { cameraViews, type CameraView } from "./model";
import type { StoryMotion } from "./storyMotion";
import { emptyShot, resolveShot } from "./choreography";
import { modelInfo } from "../data/model";
import { prepareRobot } from "./robot";
import { batchStaticAssembly } from "./batchAssembly";
import { useFaceTexture } from "./useFaceTexture";
import { useMedia } from "../state/useMedia";
import { updateAssembly, type AssemblyView, type PoseDemo } from "./assembly";
import { themeColor } from "../theme";

function Robot({
  wireframe,
  assemblyView,
  pose,
  reduced,
}: {
  wireframe: boolean;
  assemblyView: AssemblyView;
  pose: PoseDemo;
  reduced: boolean;
}) {
  const { scene } = useGLTF(modelInfo.url);
  const face = useFaceTexture();
  const root = useRef<Group>(null);
  const prepared = useMemo(
    () => prepareRobot(scene, face, wireframe),
    [scene, face, wireframe],
  );
  const batched = useMemo(
    () => batchStaticAssembly(prepared.object),
    [prepared],
  );
  const invalidate = useThree((state) => state.invalidate);
  const start = useRef<number | null>(null);
  useFrame(({ clock }) => {
    if (start.current === null) start.current = clock.elapsedTime;
    updateAssembly(
      prepared.object,
      assemblyView,
      reduced ? "none" : pose,
      clock.elapsedTime - start.current,
    );
    if (pose !== "none" && !reduced) invalidate();
  });
  useEffect(() => {
    updateAssembly(prepared.object, assemblyView, "none", 0);
    invalidate();
  }, [prepared, assemblyView, pose, invalidate]);
  useEffect(
    () => () => {
      prepared.materials.forEach((material) => material.dispose());
      prepared.geometries.forEach((geometry) => geometry.dispose());
      batched.geometries.forEach((geometry) => geometry.dispose());
    },
    [prepared, batched],
  );
  return (
    <group
      ref={root}
      position={[0, 1.53, 0]}
      scale={prepared.measurement.scale}
    >
      <primitive
        object={
          assemblyView === "assembled" && pose === "none"
            ? batched.object
            : prepared.object
        }
        position={prepared.measurement.center.clone().negate()}
      />
    </group>
  );
}

interface SceneProps {
  assemblyView: AssemblyView;
  pose: PoseDemo;
  view: CameraView;
  reset: number;
  zoom: number;
  autoRotate: boolean;
  wireframe: boolean;
  reduced: boolean;
  active: boolean;
  exploring: boolean;
  motion: StoryMotion;
  onLoaded: () => void;
}
function Director({
  view,
  reset,
  zoom,
  autoRotate,
  reduced,
  exploring,
  motion,
  compact,
  assemblyView,
}: SceneProps & { compact: boolean }) {
  const controls = useRef<OrbitControlsType>(null);
  const destination = useRef<Vector3 | null>(null);
  const goal = useMemo(() => new Vector3(), []);
  const target = useMemo(() => new Vector3(), []);
  const shot = useMemo(() => emptyShot(), []);
  const { camera, invalidate, size, gl } = useThree();
  useEffect(() => motion.subscribe(invalidate), [motion, invalidate]);
  useEffect(() => {
    if (!exploring) return;
    target.set(0, view === "display" ? 2.36 : 1.5, 0);
    destination.current = new Vector3(...cameraViews[view])
      .sub(target)
      .multiplyScalar(
        Math.pow(0.85, zoom) * (assemblyView === "exploded" ? 1.25 : 1.05),
      )
      .clampLength(view === "display" ? 2.2 : 3.6, 12)
      .add(target);
    if (compact && view !== "display")
      destination.current.sub(target).multiplyScalar(1.3).add(target);
    invalidate();
  }, [view, reset, zoom, exploring, target, compact, invalidate, assemblyView]);
  useFrame((_, delta) => {
    if (!(camera instanceof PerspectiveCamera)) return;
    const damping = reduced ? 1 : 1 - Math.exp(-Math.min(delta, 0.05) * 8);
    if (!exploring) {
      resolveShot(motion.progress, compact, reduced, shot);
      const azimuth =
        shot.azimuth + (reduced || compact ? 0 : motion.pointer.x * 0.025);
      const elevation =
        shot.elevation + (reduced || compact ? 0 : motion.pointer.y * 0.009);
      goal.set(
        Math.sin(azimuth) * Math.cos(elevation) * shot.distance,
        shot.targetY + Math.sin(elevation) * shot.distance,
        Math.cos(azimuth) * Math.cos(elevation) * shot.distance,
      );
      camera.position.lerp(goal, damping);
      target.set(0, shot.targetY, 0);
      camera.lookAt(target);
      camera.setViewOffset(
        size.width,
        size.height,
        (-shot.x * size.width) / 2,
        (shot.y * size.height) / 2,
        size.width,
        size.height,
      );
      gl.domElement.setAttribute(
        "data-shot",
        String(Math.round(motion.progress)),
      );
      gl.domElement.setAttribute(
        "data-camera",
        camera.position
          .toArray()
          .map((n) => n.toFixed(3))
          .join(","),
      );
      if (camera.position.distanceTo(goal) > 0.002) invalidate();
      return;
    }
    camera.setViewOffset(
      size.width,
      size.height,
      0,
      size.height * (compact ? 0.12 : 0.08),
      size.width,
      size.height,
    );
    if (controls.current) {
      controls.current.autoRotate = autoRotate && !destination.current;
      if (destination.current) {
        camera.position.lerp(destination.current, damping);
        controls.current.target.lerp(target, damping);
        controls.current.update();
        if (camera.position.distanceTo(destination.current) < 0.002)
          destination.current = null;
        invalidate();
      }
    }
  }, -1);
  return (
    <OrbitControls
      ref={controls}
      enabled={exploring}
      enablePan={false}
      enableDamping={!reduced}
      target={[0, 1.5, 0]}
      minDistance={2.2}
      maxDistance={12}
      maxPolarAngle={Math.PI * 0.92}
      autoRotate={autoRotate && exploring}
      autoRotateSpeed={0.5}
      onStart={() => {
        destination.current = null;
      }}
    />
  );
}
function Loaded({ onLoaded }: { onLoaded: () => void }) {
  useEffect(onLoaded, [onLoaded]);
  return null;
}
export default function Scene(props: SceneProps) {
  const compact = useMedia("(max-width: 900px)");
  const highlight = themeColor("--orange-on-dark", "#ff9b5c");
  const warmWhite = themeColor("--orange-soft", "#fff0e6");
  const ink = themeColor("--ink", "#171717");
  return (
    <Canvas
      frameloop={props.active ? "demand" : "never"}
      dpr={compact ? 1 : [1, 1.5]}
      camera={{ position: [1, 1.9, 5.8], fov: 35, near: 0.1, far: 60 }}
      gl={{ antialias: !compact, alpha: true, powerPreference: "low-power" }}
    >
      <ambientLight intensity={0.65} />
      <directionalLight position={[3, 7, 5]} intensity={2.8} color="#fffaf6" />
      <directionalLight position={[-5, 2, 3]} intensity={1.1} color="#ffffff" />
      <directionalLight position={[4, 4, -4]} intensity={1.2} color={highlight} />
      <Environment resolution={128} frames={1}>
        <Lightformer
          position={[-4, 4, 3]}
          rotation-y={Math.PI / 4}
          scale={[4, 7, 1]}
          intensity={2.4}
          color="#ffffff"
        />
        <Lightformer
          position={[5, 2, 1]}
          rotation-y={-Math.PI / 3}
          scale={[3, 6, 1]}
          intensity={1.7}
          color={warmWhite}
        />
        <Lightformer
          position={[0, 6, -2]}
          rotation-x={Math.PI / 2}
          scale={[7, 4, 1]}
          intensity={2.2}
        />
      </Environment>
      <Suspense fallback={null}>
        <Robot
          wireframe={props.wireframe}
          assemblyView={props.assemblyView}
          pose={props.pose}
          reduced={props.reduced}
        />
        <Loaded onLoaded={props.onLoaded} />
        <ContactShadows
          position={[0, 0.01, 0]}
          scale={7}
          opacity={0.3}
          blur={3.5}
          far={4}
          resolution={compact ? 128 : 256}
          frames={1}
          color={ink}
        />
      </Suspense>
      <Director {...props} compact={compact} />
    </Canvas>
  );
}
