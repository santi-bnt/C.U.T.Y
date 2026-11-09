import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { describe, it, expect } from "vitest";
import { connectionRows } from "./operationalWiring";
import { matchesFilter } from "./engineering";
import nido from "./nido.generated.json";
describe("user-confirmed wiring and revised assets", () => {
  it("keeps the proven modified display pinout and audio list separate from pending controls", () => {
    const display = connectionRows.filter((r) => r.to === "display");
    expect(display).toHaveLength(11);
    expect(display.every((r) => r.status === "confirmed")).toBe(true);
    expect(display.find((r) => r.net === "LCD DC / RS")?.pin).toBe("Pi 18");
    expect(display.find((r) => r.net === "LCD DC / RS")?.gpio).toBe("BCM 24");
    expect(display.find((r) => r.net === "LCD RESET")?.gpio).toBe("BCM 25");
    const audio = connectionRows.filter((r) => r.to === "audio");
    expect(audio).toHaveLength(11);
    expect(audio.every((r) => r.status === "confirmed")).toBe(true);
    expect(audio.map(({ pin, net, gpio }) => [pin, net, gpio])).toEqual([
      ["Pi 1", "3.3 V", "—"],
      ["Pi 3", "I2C SDA", "BCM 2"],
      ["Pi 4", "5 V", "—"],
      ["Pi 5", "I2C SCL", "BCM 3"],
      ["Pi 6", "GND", "—"],
      ["Pi 7", "MCLK", "BCM 4"],
      ["Pi 12", "I2S BCLK", "BCM 18"],
      ["Pi 35", "I2S LRCLK", "BCM 19"],
      ["Pi 37", "AUD_RST", "BCM 26"],
      ["Pi 38", "I2S DIN", "BCM 20"],
      ["Pi 40", "I2S DOUT", "BCM 21"],
    ]);
    expect(
      connectionRows
        .filter((r) => matchesFilter(r, "UART"))
        .every(
          (r) => r.status === "proposed" && !/PA2|PA3/.test(r.destination),
        ),
    ).toBe(true);
    const pwm = connectionRows.filter((r) => matchesFilter(r, "servo"));
    expect(pwm).toHaveLength(5);
    expect(pwm.every((r) => r.net.includes("TBD"))).toBe(true);
  });
  it("ships the optimized revised model and all supplied assembly imagery with provenance", () => {
    const manifest = JSON.parse(
      readFileSync("public/assembly/provenance.json", "utf8"),
    );
    expect(
      createHash("sha256")
        .update(readFileSync("public/models/cuty.glb"))
        .digest("hex"),
    ).toBe(manifest.webGlbSha256);
    expect(manifest.webGlbBytes).toBeLessThan(2000000);
    expect(manifest.images).toHaveLength(18);
    for (const image of manifest.images)
      expect(
        createHash("sha256")
          .update(readFileSync("public/assembly/" + image.name))
          .digest("hex"),
      ).toBe(image.sha256);
    expect(nido.revision).toContain("2026-11-06");
    expect(nido.meshes).toBe(113);
    expect(nido.pcb.meshes).toBe(45);
    expect(nido.pcb.simplified).toBe(true);
    expect(
      readFileSync("public/models/carrier-assembly.glb").byteLength,
    ).toBeGreaterThan(100000);
  });
});
