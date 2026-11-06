# C.U.T.Y · Carcasa V17 «Nido»

Robot compañero de 36 cm que se arma a mano como un set de bloques: 30 piezas impresas que encajan con clips, ranuras, una bayoneta y dos llaves (los brazos), sobre una base con gimbal de dos servos. Todo cabe en la cama de 180 × 180 mm de la Bambu A1 mini.

![C.U.T.Y V17](renders/frente_34.png)

**Revisión 5 nov 2026:** ajustada a las piezas que sí se compraron. El rack de potencia (K5) ahora es para el XL4015 de 54 × 23 × 18 mm y el convertidor JRBLVL de 46 × 32 × 18 mm; el cajón (B3), la cubierta (B1) y el piso (B2) ahora reciben la batería OVONIC de hasta 109 mm de largo. Las demás piezas no cambiaron.

## Qué hay en esta carpeta

| Carpeta / archivo | Para qué sirve |
|---|---|
| `STL_imprimir/` | 30 STL listos para Bambu Studio, ya orientados para la cama. |
| `STEP_ensamble/CUTY_V17_Ensamble_completo.step` | Ensamble completo con colores, incluye placa, Pi 5, servos, batería, pantalla y cámara. Ábrelo en Fusion (Archivo › Abrir): entra como componentes. |
| `STEP_partes/` | Cada pieza en su posición final, para editarla en Fusion. |
| `CUTY_V17.glb` | Modelo 3D para visores web, presentaciones o Blender. |
| `renders/` | Frente, espalda, lado y rayos X. |
| `texturas/` | La cara real de `cuty.face` (feliz, tranquilo, escuchando, sorpresa) para renders. |
| `fuente_cad/` | El generador en CadQuery. Cambia una medida y reconstruye todo. |
| `partes.json`, `verificacion.json` | Medidas de impresión, volúmenes y resultados de la revisión de choques. |

## Arquitectura

- **Nido (base fija, Ø172 mm):** piso con bayoneta, cubierta tipo cojín con un plato cóncavo, cajón de batería trasero que corre en rieles, dos interruptores redondos y dos servos MG996R acostados que mueven el gimbal con manivelas y varillas.
- **Gimbal:** junta universal (cruceta de 14 mm con dos pernos M4). El fondo del cuerpo es una esfera concéntrica al gimbal, así el robot "rueda" dentro del plato con 3.5 mm de holgura constante.
- **Núcleo:** plataforma, columna, hombros, rack de potencia y cubo del cuello. Toda la electrónica se atornilla aquí antes de poner la carcasa.
- **Carcasa:** panza y espalda se deslizan horizontalmente y muerden la plataforma con clips. Los brazos pasan por la costura y las amarran.
- **Cabeza:** casco en dos mitades, visor negro con pantalla y cámara, servo de giro adentro. Orejas y antena atraviesan la costura y la cierran.

## Imprimir

Capa 0.2 mm, 3 perímetros, 15 % de relleno giroide, PLA. Holguras de encaje de 0.2 mm. Izquierda y derecha se leen viendo al robot de frente.

| Código | Pieza | Color | Medida en cama (mm) | Cómo imprimir |
|---|---|---|---|---|
| B1 | Cubierta del nido | Durazno | 175 × 173 × 67 | Sobre su base · soportes árbol solo por dentro · **sin brim** |
| B2 | Piso del nido | Gris | 165 × 167 × 26 | Plano · sin soportes |
| B3 | Cajón de batería | Durazno | 119 × 63 × 31 | Sobre el fondo · sin soportes |
| B4 | Poste del gimbal | Gris | 40 × 40 × 88 | De pie, brida abajo |
| G1 | Cruceta | Gris oscuro | 14 × 14 × 14 | 100 % relleno |
| G2, G3 | Manivelas | Gris oscuro | 22 × 12 × 5 | Planas · 100 % relleno |
| K1 | Plataforma del núcleo | Gris | 124 × 118 × 47 | Boca abajo · soportes bajo la placa (5 mm) |
| K2 | Columna | Gris | 110 × 96 × 10 | Acostada |
| K3 | Hombros | Gris | 114 × 32 × 66 | Viga abajo |
| K4 | Cubo del cuello | Gris oscuro | 32 × 32 × 15 | Brida abajo · 100 % relleno |
| K5 | Rack de potencia | Gris | 38 × 55 × 44 | De lado · soportes mínimos |
| S1 | Panza | Crema | 148 × 162 × 76 | Sobre la costura · soportes solo en los clips |
| S2 | Espalda | Crema | 148 × 162 × 67 | Sobre la costura · soportes solo en los clips |
| S3 | Rejilla de la panza | Naranja | 55 × 55 × 14 | Anillo abajo |
| S4 | Tapón USB | Naranja | 8 × 13 × 12 | De lado |
| A1, A2 | Brazos | Crema | 104 × 30 × 22 | Cara exterior abajo · 4 perímetros |
| A3, A4 | Manos | Naranja | 16 × 34 × 14 | Cara exterior abajo |
| A5, A6 | Tapas de brazo | Naranja | 14 × 14 × 4 | Cara abajo |
| H1 | Casco frontal | Crema | 160 × 135 × 59 | Sobre la costura · soportes árbol mínimos |
| H2 | Casco trasero | Crema | 160 × 135 × 56 | Sobre la costura (el nombre queda arriba) |
| H3 | Visor | Negro | 121 × 93 × 15 | Cara abajo en PEI texturizado · soportes en las orillas |
| H4 | Barras de la pantalla | Gris | 85 × 70 × 3 | Planas |
| H5 | Base de la cabeza | Gris | 96 × 48 × 10 | Plana |
| H6, H7 | Orejas | Naranja | 46 × 46 × 22 | Cara exterior abajo |
| H8 | Antena | Naranja | 18 × 18 × 34 | De pie · soporte bajo la bolita |

Filamento aproximado (PLA, 15 % de relleno): crema ≈ 380 g, gris ≈ 200 g, durazno ≈ 175 g, naranja ≈ 50 g, negro ≈ 25 g, gris oscuro ≈ 10 g. Total ≈ 0.85 kg.

**Primero imprime una prueba:** G2 (manivela) y K4 (cubo del cuello). Si el spline de 25 dientes de tu MG996R entra muy duro o muy flojo, ajusta `spline_25t` en `fuente_cad/v17/common.py` y reconstruye.

## Tornillería (ferretería)

| Cant. | Qué |
|---|---|
| 25 | M3 × 10 autorroscante (servos, poste, rack, base de la cabeza) |
| 10 | M3 × 8 autorroscante (placa C.U.T.Y, cubo del cuello) |
| 4 | M3 × 12 (columna a plataforma y a hombros) |
| 3 | M3 × 10 al spline: cabeza y brazos (los traen los servos) |
| 1 | M3 × 20 del cubo del cuello al servo de la cabeza |
| 2 | M4 × 30 + tuerca nyloc + 4 rondanas (ejes del gimbal) |
| 10 | M2.5 × 6–10 autorroscante (Pi 5, IMU, servo de cabeza) |
| 4 | M2.5 × 8 (barras de la pantalla) |
| 4 | M2 × 5 autorroscante (cámara) |
| 4 + 1 | Rótulas M3 de bola + 15 cm de varilla roscada M3, 49 mm entre centros |
| 4 | Pies de silicón Ø10 mm |
| 1 | Velcro de 20 mm × 25 cm |

## Piezas compradas para las que está diseñada

| Pieza | Medida que usa el modelo |
|---|---|
| Batería OVONIC 3S 2200 mAh 50C, XT60 | hasta 109 × 35 × 25 mm (la real: 107 × 35 × 22) |
| Buck XL4015 5 A (sin voltímetro) | 54 × 23 × 18 mm, de pie, terminales arriba |
| Convertidor JRBLVL 12→5 V 5 A, USB-C en cable | 46 × 32 × 18 mm, de pie, cables hacia abajo |
| 2 balancines redondos 12 V/20 A | agujero Ø20 mm |
| Cable de cámara Pi 5, 22→15 pines, 50 cm | pasa por la ranura trasera de la viga |
| Cable plano IDC de 40 vías hembra-hembra, 20 cm | J12 → Pi 5 |
| Extensión XT60 macho-hembra | batería → J1 |
| 5 × MG996R, Raspberry Pi 5, Display-G 3.5", ReSpeaker 2-Mics HAT V2.0, cámara OV5647, bocina Ø40 mm | ya los tienes |

La pantalla se conecta a J13 con cables Dupont (pasan por la ranura delantera de la viga). La MPU-6050 es opcional: si no la pones, su lugar en la plataforma queda vacío.

## Armado en 15 pasos

1. **Piso del nido.** Pega los pies. Desliza los dos servos del gimbal acostados contra sus muros (eje hacia el centro) y atorníllalos (8 × M3 × 10). Centra cada servo a 90° y pon su manivela apuntando al centro, con su rótula de bola.
2. **Poste del gimbal.** Brida en el anillo del piso, 3 × M3 × 10 desde abajo. La ranura del tubo mira al frente.
3. **Varillas.** Ajusta las dos a 49 mm entre centros y presiona la rótula inferior en cada manivela.
4. **Interruptores y cubierta.** Interruptores a presión en la cubierta (principal a la izquierda, servos a la derecha). Baja la cubierta sobre el piso, alinea las 3 pestañas y gira 14° hasta el clic.
5. **Cruceta.** Dentro de la horquilla del poste, perno M4 × 30 de adelante hacia atrás. Aprieta la nyloc hasta que gire sin juego.
6. **Plataforma.** Sobre la cruceta, segundo perno M4 de lado a lado. Presiona las rótulas superiores en las patas y atornilla la IMU (si la usas).
7. **Columna y placa C.U.T.Y.** Columna en la ranura de la plataforma (2 × M3 × 12 desde abajo). Placa en los 4 postes del frente (M3 × 8).
8. **Raspberry Pi 5.** En los postes detrás de la columna (4 × M2.5 × 6). Conecta el cable plano de 40 vías a J12 y a la Pi.
9. **Rack de potencia.** XL4015 contra la columna (terminales arriba), convertidor de 5 V de pie en su repisa con sus cables hacia abajo por la ranura, rack a la columna con sus 4 orejas (M3 × 10 desde el frente de la columna). El USB-C del convertidor va a la Pi.
10. **Hombros y cuello.** Servos de brazo desde adentro (8 × M3 × 10), hombros arriba de la columna (2 × M3 × 12), cubo del cuello sobre la viga (3 × M3 × 8).
11. **Visor.** Pantalla de cara contra el visor dentro de sus costillas, dos barras (4 × M2.5 × 8). Cámara arriba (4 × M2 × 5).
12. **Cabeza.** Servo de cabeza en su base. Visor dentro del casco frontal, cierra con el trasero, presiona orejas y antena. 4 × M3 × 10 desde abajo. Monta la cabeza en el cubo y fija con M3 × 20 desde abajo de la viga. Deja una vuelta de cable de cámara y de Dupont para que la cabeza gire ±90°.
13. **Panza y espalda.** Bocina en la rejilla con 3 puntos de silicón, rejilla en la panza. Desliza panza y espalda hasta que los clips muerdan la plataforma. Tapón USB.
14. **Brazos.** Cada brazo por su agujero hasta el spline (M3 × 10), tapas y manos a presión. Los brazos cierran el cuerpo.
15. **Batería.** Velcro, extensión XT60, desliza el cajón hasta el clic. Enciende el principal y luego el de servos.

## Límites de movimiento (ponlos en el firmware)

| Eje | Límite verificado |
|---|---|
| Cabeceo del gimbal | ±18° |
| Balanceo del gimbal | ±15° (a 18° las manos rozan el cojín) |
| Cabeceo + balanceo a la vez | ±14° / ±10° |
| Giro de cabeza | ±90° |
| Brazos | ±120° |

## Verificación (5 nov 2026, con las medidas de lo comprado)

- 30 piezas, cada una un sólido válido; STL herméticos.
- Todas caben en 180 × 180 × 180 mm (la cubierta B1 es la más grande: 175 × 173 × 67).
- 109 cuerpos (30 impresos y 79 comprados) revisados por pares con todo armado: 0 interferencias. Los contactos de superficies coincidentes se confirmaron en 0.000 mm³ con booleanas exactas.
- 18 zonas para cables y conectores (XT60, enchufes de servos, IDC, cables del convertidor, bornes del buck, ventilador de la Pi) libres de plástico.
- 34 posturas revisadas: gimbal, cabeza y brazos sin choques dentro de los límites de arriba.

## Antes de imprimir todo

Mide lo que ya tienes: MG996R 40.7 × 19.7 × 37 mm, pantalla 3.5" de 85 × 56 mm, cámara OV5647 de 25 × 24 mm y bocina Ø40 × 16 mm. Si alguna cambia, ajusta `fuente_cad/v17/refs.py` y corre:

```
cd fuente_cad/v17
pip install cadquery==2.8.0 trimesh manifold3d
python3 build.py --rebuild     # reconstruye todas las piezas
python3 meshcheck.py           # revisa choques en reposo y en movimiento
python3 export.py              # STEP, STL orientados y ensamble para Fusion
```

Diseñado por APL en Guadalajara.
