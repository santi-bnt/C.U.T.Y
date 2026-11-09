# Pedido real: placa C.U.T.Y v1.1 ensamblada en JLCPCB (nov 2026)

La placa se pidió a JLCPCB con ensamble THT, no a PCBWay. Esta carpeta guarda lo que se subió y las correcciones que se hicieron en el visor de JLCPCB, para que el pedido se pueda repetir igual.

| Archivo | Qué es |
| --- | --- |
| `BOM_JLCPCB.csv` | BOM en el formato de JLCPCB (Comment, Designator, Footprint, LCSC Part #) |
| `CPL_JLCPCB.csv` | Posiciones tal como se subieron (Designator, Mid X, Mid Y, Layer, Rotation) |
| `../gerbers/` | Los mismos Gerber v1.1 |
| `../pcba/cuty_carrier_PCBA_ensamble.pdf` | Dibujo de ensamble con polaridades |

## Lo que soldó JLCPCB

37 componentes: C1–C3, D1–D4, J1–J15, JP1 (solo la tira), R1–R12 y los dos zócalos hembra de la Black Pill (U1A, U1B).

**No los puso JLCPCB** (vienen en el pedido de Mouser y se sueldan a mano):

- F1 y F2: portafusibles Keystone 3568, uno por fusible.
- Los fusibles mini de 10 A (F1, servos) y 5 A (F2, Pi).
- El jumper de 2.54 mm para JP1.

## Correcciones en el visor de JLCPCB

El CPL se subió tal cual y estas piezas se giraron en el visor hasta que coincidieron con la serigrafía:

| Pieza | Corrección |
| --- | --- |
| J1 (XT60PW-M) | 90° en sentido horario: el conector sale por el borde izquierdo |
| D2, D3, D4 (LED 3 mm) | 180°: el cátodo (lado plano) en el pad cuadrado |
| J12 (header de 40 vías) | revisado, sin cambio: la muesca coincide con la serigrafía |

Si se vuelve a pedir, revisa esas cuatro piezas en el visor antes de pagar.
