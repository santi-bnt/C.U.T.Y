#!/usr/bin/env python3
"""C.U.T.Y Wi-Fi panel, Raspberry Pi framebuffer + ADS7846."""
import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from evdev import InputDevice, ecodes, list_devices

FB = Path('/dev/fb1')
SYS = Path('/sys/class/graphics/fb1')
WIFI = 'wlan0'
USER = 'santi'

if os.geteuid() != 0:
    raise SystemExit('Ejecuta con sudo')
if not FB.exists():
    raise SystemExit('No existe /dev/fb1. Comprueba waveshare35a.')
W, H = map(int, (SYS/'virtual_size').read_text().strip().split(','))
if int((SYS/'bits_per_pixel').read_text()) != 16:
    raise SystemExit('La pantalla debe utilizar RGB565 de 16 bits')

fontpath = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
boldpath = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
F = ImageFont.truetype(fontpath, 17)
SM = ImageFont.truetype(fontpath, 14)
BIG = ImageFont.truetype(boldpath, 22)
KEY = ImageFont.truetype(boldpath, 18)
BG, CARD, FG, MUTED, BLUE = '#0c1523', '#1a2b40', '#ffffff', '#b7c7d8', '#285f91'


def cmd(*args, timeout=35):
    return subprocess.run(args, text=True, capture_output=True,
                          timeout=timeout, check=False)


def nm(*args, timeout=35):
    return cmd('nmcli', *args, timeout=timeout)


def label(d, xy, txt, font=F, color=FG, maxw=460):
    txt = str(txt)
    while txt and d.textbbox((0, 0), txt, font=font)[2] > maxw:
        txt = txt[:-2].rstrip('…') + '…'
    d.text(xy, txt, font=font, fill=color)


class Panel:
    def __init__(self):
        self.screen = 'home'
        self.networks = []
        self.page = 0
        self.hotspots = []
        self.ssid = ''
        self.enterprise = False
        self.identity = ''
        self.field = ''
        self.value = ''
        self.symbols = False
        self.upper = False
        self.show_password = False
        self.notice = ''
        self.last_touch = 0
        self.cal = json.loads(Path('/home/santi/cuty_touch_calibration.json').read_text())
        self.touch = next((d for p in list_devices()
                           if (d := InputDevice(p)).name == 'ADS7846 Touchscreen'), None)
        if not self.touch:
            raise SystemExit('No se detectó ADS7846')
        self.touch.grab()  # No enviar estos toques al escritorio HDMI.

    def render(self):
        im = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(im)
        self.hotspots = []
        label(d, (14, 8), 'C.U.T.Y  /  Wi-Fi', BIG)
        d.line((0, 43, W, 43), fill='#36516c', width=2)
        if self.screen == 'home':
            profile = nm('-g', 'GENERAL.CONNECTION', 'device', 'show', WIFI).stdout.strip()
            ip = nm('-g', 'IP4.ADDRESS', 'device', 'show', WIFI).stdout.splitlines()
            ip = ip[0].split('/')[0] if ip else 'Sin conexion'
            if not profile or profile == '--':
                profile = 'Sin conexion'
            elif profile.startswith('CUTY-'):
                actual_ssid = nm('-g', '802-11-wireless.ssid', 'connection', 'show', profile).stdout.strip()
                profile = actual_ssid or self.ssid or 'Wi-Fi conectado'
            ssh = 'Activo' if cmd('systemctl', 'is-active', 'ssh').stdout.strip() == 'active' else 'Inactivo'
            d.rounded_rectangle((10, 54, W-10, 171), radius=12, fill=CARD)
            label(d, (22, 63), 'Red: ' + profile, F, maxw=W-40)
            label(d, (22, 95), 'IP: ' + ip, BIG)
            label(d, (22, 140), 'SSH: ' + ssh + '  |  ssh ' + USER + '@' + ip, SM)
            self.button(d, (12, 187, 229, 245), 'Buscar Wi-Fi', 'scan')
            self.button(d, (244, 187, W-12, 245), 'Red Tec', 'tec')
            self.button(d, (12, 260, W-12, 307), 'Actualizar IP', 'home')
        elif self.screen == 'networks':
            label(d, (15, 50), 'Selecciona una red:', F)
            subset = self.networks[self.page*4:self.page*4+4]
            for i, (ssid, sec, sig) in enumerate(subset):
                y = 78 + i*45
                desc = f'{ssid}  ({sig}%)'
                self.button(d, (12, y, W-12, y+40), desc, ('network', ssid, sec))
            self.button(d, (12, 275, 115, 313), 'Atras', 'home')
            self.button(d, (124, 275, 245, 313), 'Anterior', 'prev')
            self.button(d, (254, 275, 365, 313), 'Siguiente', 'next')
            self.button(d, (374, 275, W-12, 313), 'Scan', 'scan')
        elif self.screen == 'keyboard':
            label(d, (12, 50), self.field, SM)
            is_password = 'clave' in self.field.lower()
            visible = self.value if (not is_password or self.show_password) else '•' * len(self.value)
            d.rounded_rectangle((8, 68, W-8, 105), radius=6, fill=CARD)
            label(d, (15, 76), visible[-38:] or 'Toca para escribir',
                  F, maxw=(W-145 if is_password else W-30))
            if is_password:
                self.button(d, (W-107, 70, W-12, 103),
                            'Ocultar' if self.show_password else 'Ver',
                            'toggle_password', font=SM)
            if self.symbols:
                rows = ['1234567890', '!#$%&*()?:', '[]{}<>/\\+=', "@.-_,';\"~^"]
            else:
                rows = ['1234567890', 'qwertyuiop', 'asdfghjkl@', 'zxcvbnm.-_']
            for rowi, text in enumerate(rows):
                y = 111 + rowi*35
                count = len(text)
                kw = (W-14)//count
                for j, ch in enumerate(text):
                    x1 = 5+j*kw
                    self.button(d, (x1, y, x1+kw-3, y+32),
                                ch.upper() if self.upper else ch, ('key', ch), font=SM)
            controls = [
                ((5, 257, 65, 313), 'SIMB', 'symbols'),
                ((69, 257, 125, 313), 'Aa', 'shift'),
                ((129, 257, 244, 313), 'Espacio', ('key', ' ')),
                ((248, 257, 326, 313), 'Borrar', 'erase'),
                ((330, 257, 397, 313), 'OK', 'confirm'),
                ((401, 257, W-5, 313), 'Salir', 'cancel')
            ]
            for rect, txt, act in controls:
                self.button(d, rect, txt, act, font=SM)
        else:
            label(d, (18, 82), self.notice, F, maxw=W-35)
            self.button(d, (95, 215, W-95, 277), 'Volver', 'home')
        # framebuffer RGB565 little-endian; matches fb_ili9486 in this setup.
        raw = bytearray(W*H*2)
        for i, (r, g, b) in enumerate(im.getdata()):
            v = ((r>>3)<<11) | ((g>>2)<<5) | (b>>3)
            raw[2*i] = v & 255
            raw[2*i+1] = v >> 8
        with FB.open('r+b', buffering=0) as f:
            f.write(raw)

    def button(self, d, rect, txt, action, font=F):
        d.rounded_rectangle(rect, radius=7, fill=BLUE)
        label(d, (rect[0]+7, rect[1]+max(2, (rect[3]-rect[1]-19)//2)), txt,
              font, maxw=rect[2]-rect[0]-14)
        self.hotspots.append((rect, action))

    def message(self, msg):
        self.screen, self.notice = 'message', msg
        self.render()

    def ask(self, title):
        self.screen, self.field, self.value = 'keyboard', title, ''
        self.symbols = self.upper = False
        self.show_password = False
        self.render()

    def scan(self):
        self.message('Buscando redes Wi-Fi...')
        result = nm('-t', '--escape', 'no', '-f', 'SSID,SECURITY,SIGNAL',
                    'device', 'wifi', 'list', 'ifname', WIFI, '--rescan', 'yes', timeout=30)
        if result.returncode:
            self.message('No fue posible escanear redes')
            return
        seen = {}
        for ln in result.stdout.splitlines():
            parts = ln.rsplit(':', 2)
            if len(parts) != 3:
                continue
            ssid, sec, sig = parts
            if ssid and (ssid not in seen or sig.isdecimal() and int(sig)>seen[ssid][2]):
                seen[ssid] = (ssid, sec, int(sig) if sig.isdecimal() else 0)
        self.networks = sorted(seen.values(), key=lambda e: -e[2])
        self.page = 0
        self.screen = 'networks'
        self.render()

    def connect_saved(self):
        """Reuse a saved Wi-Fi profile by SSID, including older CUTY profiles."""
        try:
            profiles = nm('-t', '-f', 'UUID,TYPE', 'connection', 'show')
            if profiles.returncode:
                self.message('No se pudieron consultar las redes guardadas')
                return True
            for line in profiles.stdout.splitlines():
                uid, _, kind = line.partition(':')
                if kind not in ('802-11-wireless', 'wifi'):
                    continue
                info = nm('-g', '802-11-wireless.ssid', 'connection', 'show',
                          'uuid', uid)
                if info.returncode or info.stdout.rstrip('\n') != self.ssid:
                    continue
                iface = nm('-g', 'connection.interface-name', 'connection',
                           'show', 'uuid', uid)
                if iface.returncode or iface.stdout.strip() not in ('', '--', WIFI):
                    continue
                self.message('Conectando a red guardada: ' + self.ssid)
                result = nm('-w', '50', 'connection', 'up', 'uuid', uid,
                            'ifname', WIFI, timeout=60)
                if result.returncode:
                    self.message('No se pudo conectar. Perfil guardado conservado.')
                else:
                    self.screen = 'home'
                    self.render()
                return True
            return False
        except (OSError, subprocess.TimeoutExpired):
            self.message('Error consultando o activando la red guardada')
            return True

    def connect(self, password=''):
        name = str(uuid.uuid4())
        self.message('Conectando a ' + self.ssid + '...')
        add = nm('connection', 'add', 'type', 'wifi', 'ifname', WIFI,
                 'con-name', self.ssid, 'ssid', self.ssid,
                 'connection.uuid', name)
        if add.returncode:
            self.message('Error creando perfil de red')
            return
        try:
            if self.enterprise:
                props = ('wifi-sec.key-mgmt', 'wpa-eap',
                         '802-1x.eap', 'peap',
                         '802-1x.phase2-auth', 'mschapv2',
                         '802-1x.identity', self.identity,
                         '802-1x.system-ca-certs', 'yes',
                         '802-1x.domain-suffix-match', 'wireless.itesm.mx')
                key = '802-1x.password'
            elif password:
                props = ('wifi-sec.key-mgmt', 'wpa-psk')
                key = '802-11-wireless-security.psk'
            else:
                props, key = (), None
            if props:
                mod = nm('connection', 'modify', 'uuid', name, *props)
                if mod.returncode:
                    raise RuntimeError(mod.stderr.strip()[:120])
            path = None
            if key:
                fd, path = tempfile.mkstemp(prefix='cuty-', dir='/run', text=True)
                try:
                    with os.fdopen(fd, 'w') as f:
                        f.write(f'{key}:{password}\n')
                    up = nm('-w', '50', 'connection', 'up', 'uuid', name,
                            'ifname', WIFI, 'passwd-file', path, timeout=60)
                finally:
                    os.unlink(path)
            else:
                up = nm('-w', '50', 'connection', 'up', 'uuid', name,
                        'ifname', WIFI, timeout=60)
            if up.returncode:
                raise RuntimeError(up.stderr.strip()[:120])
            self.screen = 'home'
            self.render()
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            nm('connection', 'delete', 'uuid', name)
            self.message('Conexion fallida. Revisa credenciales o senal.')
        finally:
            password = ''

    def action(self, act):
        if act == 'home':
            self.screen = 'home'
        elif act == 'scan':
            self.scan()
            return
        elif act == 'prev':
            self.page = max(0, self.page-1)
        elif act == 'next':
            self.page = min(max(0, (len(self.networks)-1)//4), self.page+1)
        elif act == 'tec':
            self.ssid, self.enterprise = 'Tec', True
            if self.connect_saved():
                return
            self.ask('Usuario institucional')
            return
        elif isinstance(act, tuple) and act[0] == 'network':
            _, self.ssid, sec = act
            if self.connect_saved():
                return
            self.enterprise = self.ssid.casefold() == 'tec' or '802.1X' in sec.upper() or 'ENT' in sec.upper()
            if self.enterprise:
                self.ask('Usuario institucional')
            elif sec.strip() in ('', '--'):
                self.connect()
            else:
                self.ask('Clave Wi-Fi')
            return
        elif isinstance(act, tuple) and act[0] == 'key':
            if len(self.value) < 100:
                ch = act[1]
                self.value += ch.upper() if self.upper else ch
        elif act == 'cancel':
            self.value = ''
            self.screen = 'home'
        elif act == 'toggle_password':
            self.show_password = not self.show_password
        elif act == 'erase':
            self.value = self.value[:-1]
        elif act == 'symbols':
            self.symbols = not self.symbols
        elif act == 'shift':
            self.upper = not self.upper
        elif act == 'confirm':
            if self.field == 'Usuario institucional':
                if not self.value:
                    return
                self.identity = self.value
                self.ask('Clave institucional')
                return
            if self.field == 'Clave Wi-Fi' and len(self.value) < 8:
                self.message('La clave Wi-Fi debe tener 8 caracteres o mas')
                return
            secret = self.value
            self.value = ''
            self.connect(secret)
            return
        self.render()

    def run(self):
        self.render()
        x = y = None
        down = False
        try:
            for ev in self.touch.read_loop():
                if ev.type == ecodes.EV_ABS:
                    if ev.code == ecodes.ABS_X:
                        x = ev.value
                    elif ev.code == ecodes.ABS_Y:
                        y = ev.value
                elif ev.type == ecodes.EV_KEY and ev.code == ecodes.BTN_TOUCH:
                    if ev.value:
                        down = True
                    else:
                        if down and x is not None and y is not None:
                            now = time.monotonic()
                            if now-self.last_touch > .20:
                                # Orientacion observada en las pruebas de calibracion.
                                sx = round(self.cal['a']*x + self.cal['b']*y + self.cal['c'])
                                sy = round(self.cal['d']*x + self.cal['e']*y + self.cal['f'])
                                sx = max(0, min(W-1, sx))
                                sy = max(0, min(H-1, sy))
                                for (l,t,r,b), action in self.hotspots:
                                    if l <= sx <= r and t <= sy <= b:
                                        self.last_touch = now
                                        self.action(action)
                                        break
                        down = False
        finally:
            self.touch.ungrab()
            self.touch.close()


if __name__ == '__main__':
    Panel().run()
