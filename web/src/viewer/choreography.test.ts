import { describe, expect, it } from "vitest";
import { chapterIds, emptyShot, resolveShot } from "./choreography";

describe("continuous robot choreography", () => {
  it("resolves the same shot after forward, backward and anchor jumps", () => {
    const expected = resolveShot(2, false, false, emptyShot());
    const output = emptyShot();
    [0, 3.7, 7, 1, 2].forEach((p) => resolveShot(p, false, false, output));
    expect(output).toEqual(expected);
    expect(expected.targetY).toBeGreaterThan(2);
    expect(expected.distance).toBeLessThan(
      resolveShot(0, false, false, emptyShot()).distance,
    );
  });
  it("keeps every interpolated pose finite and hides the robot for engineering diagrams", () => {
    const output = emptyShot();
    for (let p = 0; p < chapterIds.length - 1; p += 0.025) {
      expect(resolveShot(p, false, false, output)).toBe(output);
      expect(Object.values(output).every(Number.isFinite)).toBe(true);
      expect(output.visible).toBeGreaterThanOrEqual(0);
      expect(output.visible).toBeLessThanOrEqual(1);
    }
    expect(resolveShot(4, false, false, output).visible).toBe(0);
    expect(resolveShot(5, false, false, output).visible).toBe(0);
    expect(resolveShot(6, false, false, output).visible).toBe(1);
  });
  it("uses a separate centered mobile track and removes orbit under reduced motion", () => {
    const mobile = resolveShot(0, true, false, emptyShot());
    expect(mobile.x).toBe(0);
    expect(mobile.distance).toBeGreaterThan(9);
    const before = resolveShot(0, false, true, emptyShot());
    const after = resolveShot(6, false, true, emptyShot());
    expect(after.azimuth).toBe(before.azimuth);
    expect(after.distance).toBe(before.distance);
    expect(resolveShot(Number.NaN, false, false, emptyShot())).toEqual(
      emptyShot(),
    );
  });
});
