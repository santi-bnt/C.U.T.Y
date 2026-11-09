# Pedido en PCBWay con la placa ya ensamblada (PCBA)

La placa C.U.T.Y v1.1 es 100 % de agujero pasante (THT) y solo lleva componentes arriba. PCBWay compra todas las piezas (turnkey), las suelda y te manda la placa lista. Tú solo pones los módulos que se enchufan.

## Archivos que vas a subir

| Archivo | Dónde va en el formulario |
| --- | --- |
| `1_Gerber_CUTY_carrier_v1.1.zip` | Gerber file |
| `2_BOM_cuty_carrier_PCBA.xlsx` | BOM file |
| `3_Centroid_cuty_carrier_PCBA.xlsx` | Centroid / pick and place file |
| `4_Ensamble_cuty_carrier.pdf` | Adjúntalo en las notas o mándalo al ingeniero cuando revise el pedido |

## Paso a paso

1. Entra a pcbway.com → **PCB Assembly** → *Quote now*.
2. Llena los parámetros de ensamble:
   - **Supply mode:** Turnkey (PCBWay compra todo).
   - **Board type:** Single pieces.
   - **Assembly side:** Top side.
   - **Quantity:** 2 (una de repuesto). Con 1 también funciona.
   - **Sensitive components:** No.
   - **Number of unique parts:** 22
   - **Number of SMD parts:** 0
   - **Number of BGA/QFP parts:** 0
   - **Number of through-hole parts:** 39 (225 puntos de soldadura)
   - Sin conformal coating ni depaneling.
3. En la sección de la PCB elige *Enter PCB parameters*:
   - 100.1 × 92.1 mm, 2 capas, FR-4 TG130, 1.6 mm.
   - **Cobre 2 oz** si los cinco servos van a forzar al mismo tiempo; 1 oz si no.
   - HASL lead free, máscara verde, serigrafía blanca.
   - Cantidad de PCB: 5 (las que no se ensamblan te llegan vacías).
   - *Calculate* → *Save to cart*.
4. Sube los tres archivos (Gerber, BOM, centroid).
5. En **Remarks / Notes** pega este texto tal cual:

   > Turnkey THT assembly, top side only, lead-free. Follow the attached assembly drawing (4_Ensamble_cuty_carrier.pdf) for polarity: C1/C2 positive lead in the square pad; D1–D4 cathode in the square pad; J12/J13 box header key exactly as the silkscreen; J1 XT60PW-M male (LCSC C98732) inside the silkscreen outline. U1: solder the two 1x20 female sockets only, no module. F1/F2: fuse holders only, no fuses. Fit the jumper shunt on JP1. Substitutes with identical footprint are OK for resistors, C3, LEDs and pin headers. No substitutes for J1, F1/F2, J2–J6 or C1/C2 (max body height 20 mm). Please send photos of the finished boards before shipping.

6. Manda el pedido a revisión. Un ingeniero te mandará por correo la cotización con el BOM revisado. Revisa los sustitutos que propongan: acepta los de resistencias, LEDs y tiras de pines; rechaza cualquier cambio en el XT60, los portafusibles Keystone 3568, los bornes Phoenix o los capacitores de 1000 µF.
7. Paga cuando la cotización esté bien.

## Qué llega soldado

Todo lo de la lista: XT60, bornes, portafusibles, capacitores, LEDs, diodo, resistencias, tiras de pines, los dos box headers, la tira 2×20 del ReSpeaker y los dos zócalos 1×20 de la Black Pill. El jumper de JP1 ya viene puesto.

## Qué compras y pones tú

- Black Pill STM32F401CCU6 (WeAct), se enchufa en los zócalos de U1.
- Fusibles mini blade de 10 A (F1, servos) y 5 A (F2, Pi).
- 4 separadores M3 de 10 mm con tornillo.

## Cuando llegue la placa

Sigue la guía de ensamble de C.U.T.Y: revisión de la placa ensamblada, prueba de energía sin módulos, ajuste del buck a 6.0 V y luego los módulos y la carcasa.

## Cómo se generan estos archivos

Con el Python de KiCad, desde `scripts/`:

```sh
/usr/bin/python3 gen_pcba.py      # BOM y centroid (xlsx + csv) con números de parte del fabricante
/usr/bin/python3 gen_asm_svg.py   # dibujo de ensamble con marcas de polaridad
python3 gen_asm_pdf.py            # PDF de ensamble para PCBWay (usa Playwright)
```

`gen_pcba.py` se detiene si alguna referencia de la placa no aparece en el BOM o aparece dos veces.
