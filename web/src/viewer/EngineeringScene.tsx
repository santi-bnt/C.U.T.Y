import { useEffect, useMemo, useRef } from "react";
import {
  Canvas,
  useFrame,
  useThree,
  type ThreeEvent,
} from "@react-three/fiber";
import { Line, OrbitControls, useGLTF } from "@react-three/drei";
import {
  Box3,
  CatmullRomCurve3,
  Color,
  Mesh,
  MeshStandardMaterial,
  Vector3,
} from "three";
import type { OrbitControls as Controls } from "three-stdlib";
import type { EngineeringProps } from "../components/EngineeringViewport";
import { wiringEdges, wiringNodes } from "../data/operationalWiring";
import { modelInfo } from "../data/model";
import { partName } from "./robot";
import { useMedia } from "../state/useMedia";
import { themeColor } from "../theme";
const nodePatterns: Record<string, RegExp> = {
  pi: /^pi5_/,
  stm: /^pcb_(blackpill|U1)/,
  display: /^lcd_/,
  audio: /^respeaker_/,
  camera: /^camera_/,
  servos: /^servo_/,
  battery: /^battery_/,
  buck: /^buck_6v/,
  regulator: /^reg_5v1_usbc/,
};
function Content(props: EngineeringProps) {
  const colors = useMemo(
    () => ({
      power: themeColor("--orange", "#ff6a00"),
      ground: themeColor("--muted", "#676767"),
      signal: themeColor("--surface", "#f3f3f0"),
      accent: themeColor("--orange", "#ff6a00"),
      accentStrong: themeColor("--orange-strong", "#b94700"),
    }),
    [],
  );
  const { scene } = useGLTF(
    props.mode === "pcb"
      ? `${import.meta.env.BASE_URL}models/carrier-assembly.glb`
      : modelInfo.url,
  );
  const { invalidate } = useThree();
  const controls = useRef<Controls>(null);
  const goal = useRef(new Vector3()),
    target = useRef(new Vector3()),
    moving = useRef(true);
  const { object, owned, anchors } = useMemo(() => {
    const object = scene.clone(true),
      owned: MeshStandardMaterial[] = [];
    object.updateMatrixWorld(true);
    const boxes: Record<string, Box3> = {};
    object.traverse((child) => {
      if (!(child instanceof Mesh)) return;
      const name = partName(child);
      child.userData.part = name;
      const original = Array.isArray(child.material)
        ? child.material[0]
        : child.material;
      const material = original.clone() as MeshStandardMaterial;
      material.userData.baseEmissive =
        material.emissive?.clone() ?? new Color();
      child.material = material;
      owned.push(material);
      if (props.mode === "wiring") {
        child.visible = !/^(H[1-36-8]_|S[1-4]_|B[13]_|A[1-6]_)/.test(name);
        for (const [id, pattern] of Object.entries(nodePatterns))
          if (pattern.test(name)) {
            (boxes[id] ??= new Box3()).union(new Box3().setFromObject(child));
            child.userData.node = id;
          }
      }
    });
    const anchors = Object.fromEntries(
      Object.entries(boxes).map(([id, box]) => [
        id,
        box.getCenter(new Vector3()),
      ]),
    );
    return { object, owned, anchors };
  }, [scene, props.mode]);
  useEffect(() => () => owned.forEach((m) => m.dispose()), [owned]);
  useEffect(() => {
    object.traverse((child) => {
      if (!(child instanceof Mesh)) return;
      const ref = (child.userData.part as string).replace(/^pcb_/, "");
      const id = props.mode === "pcb" ? ref : child.userData.node;
      const selected = id && id === props.selected,
        hover = id && id === props.hover;
      const material = child.material as MeshStandardMaterial;
      if (material.emissive) {
        material.emissive.copy(material.userData.baseEmissive);
        if (selected || hover)
          material.emissive.set(
            selected ? colors.accent : colors.accentStrong,
          );
        material.emissiveIntensity = selected ? 0.65 : hover ? 0.35 : 0;
      }
    });
    invalidate();
  }, [object, props.selected, props.hover, props.mode, invalidate, colors]);
  useEffect(() => {
    let center = new Vector3(0, props.mode === "pcb" ? 0 : 180, 0);
    if (props.mode === "pcb" && props.selected) {
      const mesh = object.getObjectByName("pcb_" + props.selected);
      if (mesh)
        center = new Box3().setFromObject(mesh).getCenter(new Vector3());
    }
    if (props.mode === "wiring" && props.selected && anchors[props.selected])
      center = anchors[props.selected].clone();
    const distance =
      (props.mode === "pcb" ? 230 : 620) * Math.pow(0.85, props.zoom ?? 0);
    const dir =
      props.view === "back"
        ? new Vector3(0, 0.04, -1)
        : props.view === "front"
          ? new Vector3(0, 0.04, 1)
          : new Vector3(0.8, 0.45, 1).normalize();
    target.current.copy(center);
    goal.current.copy(center).addScaledVector(dir, distance);
    moving.current = true;
    invalidate();
  }, [
    props.selected,
    props.mode,
    props.zoom,
    props.view,
    props.reset,
    object,
    anchors,
    invalidate,
  ]);
  useFrame(({ camera }, delta) => {
    if (!moving.current || !controls.current) return;
    const k = 1 - Math.exp(-Math.min(delta, 0.05) * 10);
    camera.position.lerp(goal.current, k);
    controls.current.target.lerp(target.current, k);
    controls.current.update();
    if (camera.position.distanceTo(goal.current) < 0.02) moving.current = false;
    else invalidate();
  });
  const interact = (
    event: ThreeEvent<PointerEvent | MouseEvent>,
    hover: boolean,
  ) => {
    const mesh = event.object;
    if (!(mesh instanceof Mesh)) return;
    const id =
      props.mode === "pcb"
        ? (mesh.userData.part as string).replace(/^pcb_/, "")
        : mesh.userData.node;
    if (!id) return;
    if (props.mode === "pcb" && !/^(R\d+|C\d+|J\d+|D\d+|F\d+|U1|JP1)$/.test(id))
      return;
    event.stopPropagation();
    if (hover) props.onHover?.(id);
    else props.onSelect(id);
  };
  const edges = useMemo(
    () =>
      wiringEdges
        .filter(
          (e) =>
            (props.filter === "all" ||
              !props.filter ||
              e.kind === props.filter ||
              (props.filter === "signals" &&
                !["power", "ground"].includes(e.kind)) ||
              (props.filter === "GPIO" &&
                ["SPI", "I2C", "I2S", "UART"].includes(e.kind))) &&
            anchors[e.from] &&
            anchors[e.to],
        )
        .map((edge, i) => {
          const from = anchors[edge.from],
            to = anchors[edge.to];
          const mid = from.clone().lerp(to, 0.5);
          mid.z += 50 + (i % 3) * 18;
          mid.x += (i % 2 ? 1 : -1) * 24;
          return {
            ...edge,
            points: new CatmullRomCurve3([from, mid, to]).getPoints(36),
          };
        }),
    [anchors, props.filter],
  );
  return (
    <>
      <primitive
        object={object}
        onClick={(e: ThreeEvent<MouseEvent>) => interact(e, false)}
        onPointerOver={(e: ThreeEvent<PointerEvent>) => interact(e, true)}
        onPointerOut={() => props.onHover?.(null)}
      />
      {props.mode === "wiring" &&
        edges.map((edge, i) => (
          <Line
            key={edge.from + edge.to + edge.kind + i}
            points={edge.points}
            color={
              edge.kind === "power"
                ? colors.power
                : edge.kind === "ground"
                  ? colors.ground
                  : colors.signal
            }
            lineWidth={
              !props.selected ||
              edge.from === props.selected ||
              edge.to === props.selected
                ? 2.4
                : 0.8
            }
            dashed={edge.status !== "confirmed"}
            dashSize={6}
            gapSize={4}
            transparent
            opacity={
              !props.selected ||
              edge.from === props.selected ||
              edge.to === props.selected
                ? 0.95
                : 0.12
            }
          />
        ))}
      {props.mode === "wiring" &&
        wiringNodes
          .filter((n) => anchors[n.id])
          .map((n) => (
            <mesh
              key={n.id}
              position={anchors[n.id]}
              onClick={(e) => {
                e.stopPropagation();
                props.onSelect(n.id);
              }}
            >
              <sphereGeometry
                args={[props.selected === n.id ? 4.5 : 2.8, 12, 8]}
              />
              <meshBasicMaterial
                color={props.selected === n.id ? "#ffffff" : colors.accent}
              />
            </mesh>
          ))}
      <OrbitControls
        ref={controls}
        enablePan
        minDistance={props.mode === "pcb" ? 70 : 180}
        maxDistance={props.mode === "pcb" ? 450 : 1100}
        onStart={() => {
          moving.current = false;
        }}
        onChange={() => invalidate()}
      />
    </>
  );
}
export default function EngineeringScene(
  props: EngineeringProps & { active: boolean },
) {
  const compact = useMedia("(max-width:900px)");
  const orangeLight = themeColor("--orange-on-dark", "#ff9b5c");
  return (
    <Canvas
      frameloop={props.active ? "demand" : "never"}
      dpr={compact ? 1 : [1, 1.5]}
      camera={{
        position: props.mode === "pcb" ? [150, 90, 230] : [420, 300, 620],
        fov: 36,
        near: 0.5,
        far: 2000,
      }}
      gl={{ antialias: !compact, alpha: true, powerPreference: "low-power" }}
    >
      <ambientLight intensity={1.8} />
      <directionalLight position={[140, 350, 500]} intensity={3} />
      <directionalLight
        position={[-250, 120, -200]}
        intensity={1.3}
        color={orangeLight}
      />
      <Content {...props} />
    </Canvas>
  );
}
