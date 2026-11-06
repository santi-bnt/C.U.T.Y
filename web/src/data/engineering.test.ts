import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { carrier, connectionRows, matchesFilter, netKind } from "./engineering";

describe("engineering source integrity", () => {
  it("matches the native PCB/netlist and unmodified downloadable project files", () => {
    const root = "../hardware/electronics/kicad/cuty_carrier/";
    const hash = (path: string) =>
      createHash("sha256").update(readFileSync(path)).digest("hex");
    expect(hash(`${root}cuty_carrier.kicad_pcb`)).toBe(carrier.pcbSha256);
    expect(hash(`${root}scripts/netlist.py`)).toBe(carrier.netlistSha256);
    for (const [source, target] of [
      ["cuty_carrier.kicad_pcb", "carrier.kicad_pcb"],
      ["cuty_carrier.kicad_sch", "carrier.kicad_sch"],
      ["fab/cuty_carrier_esquematico.pdf", "carrier-schematic.pdf"],
      ["fab/cuty_carrier_BOM.csv", "carrier-bom.csv"],
      ["fab/preview/cuty_carrier_top.png", "carrier-front.png"],
      ["fab/preview/cuty_carrier_bottom.png", "carrier-back.png"],
    ])
      expect(hash(root + source)).toBe(hash("public/engineering/" + target));
    expect(carrier.components).toHaveLength(43);
    expect(carrier.pcbModel).toBeNull();
  });
  it("keeps conflicting HAT pads open and preserves actual header numbering", () => {
    const hat = carrier.components.find((p) => p.ref === "J14")!;
    for (const pin of carrier.respeakerMustBeOpen)
      expect(hat.pins.find((p) => p.pin === String(pin))!.net).toBe("");
    const lcd = carrier.components.find((p) => p.ref === "J13")!;
    expect(lcd.pins.find((p) => p.pin === "19")!.net).toBe("SPI0_MOSI");
    expect(lcd.pins.find((p) => p.pin === "26")!.net).toBe("TP_CS");
    expect(hat.pins.find((p) => p.pin === "37")!.net).toBe("AUD_RST");
    expect(netKind("AUD_RST")).toBe("GPIO");
  });
  it("does not promote design mappings to tested wiring, and filters the actual UART/PWM rows", () => {
    expect(connectionRows.some((row) => row.status === "confirmed")).toBe(
      false,
    );
    const uart = connectionRows.filter((row) => matchesFilter(row, "UART"));
    expect(uart).toHaveLength(2);
    expect(uart.find((row) => row.net === "PI_TXD")!.destination).toContain(
      "PA3 RX",
    );
    expect(uart.find((row) => row.net === "PI_RXD")!.pin).toContain("PA2 TX");
    expect(
      connectionRows.filter((row) => matchesFilter(row, "servo")),
    ).toHaveLength(5);
    for (let i = 7; i <= 11; i++) {
      const part = carrier.components.find((p) => p.ref === `J${i}`)!;
      expect(part.pins.find((p) => p.pin === "2")!.net).toBe("+6V_SERVO");
      expect(part.pins.find((p) => p.pin === "3")!.net).toBe("PGND");
    }
  });
});
