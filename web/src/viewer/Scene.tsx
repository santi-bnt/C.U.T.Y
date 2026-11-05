import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, useGLTF, ContactShadows } from "@react-three/drei";
import { Mesh, MeshStandardMaterial, Vector3, type Material } from "three";
import type { OrbitControls as OrbitControlsType } from "three-stdlib";
import { cameraViews, measureModel, type CameraView } from "./model";
import { modelInfo } from "../data/model";

function Robot({
  wireframe,
  onLoaded,
}: {
  wireframe: boolean;
  onLoaded: () => void;
}) {
  const { scene } = useGLTF(modelInfo.url);
  const { object, measurement, materials } = useMemo(() => {
    const object = scene.clone(true);
    const measurement = measureModel(object);
    const materials = new Map<Material, Material>();
    const copyMaterial = (original: Material) => {
      if (!materials.has(original)) {
        const clone = original.clone();
        if (clone instanceof MeshStandardMaterial) clone.wireframe = wireframe;
        materials.set(original, clone);
      }
      return materials.get(original)!;
    };
    object.traverse((child) => {
      if (child instanceof Mesh) {
        child.material = Array.isArray(child.material)
          ? child.material.map(copyMaterial)
          : copyMaterial(child.material);
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
    return { object, measurement, materials };
  }, [scene, wireframe]);
  useEffect(() => {
    onLoaded();
  }, [onLoaded]);
  useEffect(
    () => () => {
      materials.forEach((material) => material.dispose());
    },
    [materials],
  );
  return (
    <group position={[0, 1.53, 0]} scale={measurement.scale}>
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
}: {
  view: CameraView;
  reset: number;
  zoom: number;
  autoRotate: boolean;
  reduced: boolean;
}) {
  const controls = useRef<OrbitControlsType>(null);
  const destination = useRef<Vector3 | null>(null);
  const { camera, invalidate } = useThree();
  useEffect(() => {
    const target = new Vector3(0, 1.5, 0);
    destination.current = new Vector3(...cameraViews[view])
      .sub(target)
      .multiplyScalar(Math.pow(0.85, zoom))
      .clampLength(4, 10.8)
      .add(target);
    if (reduced) {
      camera.position.copy(destination.current);
      controls.current?.target.set(0, 1.5, 0);
      controls.current?.update();
      destination.current = null;
    }
    invalidate();
  }, [view, reset, zoom, reduced, camera, invalidate]);
  useFrame((_, delta) => {
    if (controls.current)
      controls.current.autoRotate = autoRotate && !destination.current;
    if (!destination.current) return;
    camera.position.lerp(destination.current, 1 - Math.exp(-delta * 7));
    controls.current?.target.set(0, 1.5, 0);
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
      minDistance={3.8}
      maxDistance={11}
      maxPolarAngle={Math.PI * 0.92}
      enableDamping={!reduced}
      onStart={() => {
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
}: {
  view: CameraView;
  reset: number;
  zoom: number;
  autoRotate: boolean;
  wireframe: boolean;
  reduced: boolean;
  active: boolean;
  onLoaded: () => void;
}) {
  return (
    <Canvas
      frameloop={active ? "demand" : "never"}
      dpr={[1, 1.5]}
      camera={{ position: [5, 3.2, 5], fov: 35, near: 0.1, far: 50 }}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
    >
      <ambientLight intensity={1.2} />
      <directionalLight position={[4, 7, 5]} intensity={3.5} color="#f5faff" />
      <directionalLight position={[-4, 3, -4]} intensity={4} color="#72c9ec" />
      <directionalLight position={[2, 1, -5]} intensity={1.5} color="#b5a2ff" />
      <Suspense fallback={null}>
        <Robot wireframe={wireframe} onLoaded={onLoaded} />
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
      />
    </Canvas>
  );
}
