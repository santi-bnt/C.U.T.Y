#!/usr/bin/env python3
"""C.U.T.Y 3.5in launcher: menu / basic terminal / Wi-Fi / demo face.

Reuses the already-calibrated cuty_wifi_panel.py and ADS7846 framebuffer.
Run on the Raspberry Pi as root. No HDMI, X11, Wayland or Internet needed.
"""
import json
import os
import re
import select
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from evdev import ecodes

# Import the WORKING Wi-Fi panel from the same directory, without rewriting it.
import cuty_wifi_panel as wifi

W, H = wifi.W, wifi.H
FB = wifi.FB
CAL_PATH = Path('/home/santi/cuty_touch_calibration.json')
NORM_USER = 'santi'

BG = '#0c1523'
CARD = '#1a2b40'
BLUE = '#285f91'
WHITE = '#f5f8ff'
MUTED = '#b7c7d8'
GREEN = '#48e0bd'
RED = '#ff7878'

FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT = ImageFont.truetype(FONT_PATH, 17)
SMALL = ImageFont.truetype(FONT_PATH, 13)
TINY = ImageFont.truetype(FONT_PATH, 11)
LARGE = ImageFont.truetype(BOLD_PATH, 26)
KEYFONT = ImageFont.truetype(BOLD_PATH, 17)


def command(args, timeout=5):
    try:
        return subprocess.run(args, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def text_of(args, timeout=5):
    result = command(args, timeout)
    return result.stdout.strip() if result and result.returncode == 0 else ''


def ipv4_info():
    """Obtain the actual wlan0 IPv4/gateway; never use a stale profile address."""
    lines = text_of(['ip', '-4', '-o', 'addr', 'show', 'dev', 'wlan0']).splitlines()
    ipv4 = 'Sin IPv4'
    for line in lines:
        match = re.search(r'\binet\s+(\d+\.\d+\.\d+\.\d+)', line)
        if match:
            ipv4 = match.group(1)
            break
    routes = text_of(['ip', '-4', 'route', 'show', 'default', 'dev', 'wlan0'])
    match = re.search(r'\bvia\s+(\d+\.\d+\.\d+\.\d+)', routes)
    gateway = match.group(1) if match else 'Sin puerta de enlace'
    return ipv4, gateway


def wifi_status():
    profile = text_of(['nmcli', '-g', 'GENERAL.CONNECTION', 'device', 'show', 'wlan0'])
    state = text_of(['nmcli', '-g', 'GENERAL.STATE', 'device', 'show', 'wlan0'])
    if not profile or profile == '--':
        name = 'Sin conexión'
    else:
        name = text_of(['nmcli', '-g', '802-11-wireless.ssid',
                        'connection', 'show', profile]) or profile
    ip, gateway = ipv4_info()
    connectivity = text_of(['nmcli', 'networking', 'connectivity'], timeout=4)
    ssh = text_of(['systemctl', 'is-active', 'ssh'], timeout=2) == 'active'
    return name, state, ip, gateway, connectivity, ssh


def render_frame(im):
    """RGB888 Pillow image -> RGB565 little-endian SPI framebuffer."""
    data = bytearray(W * H * 2)
    for i, (r, g, b) in enumerate(im.convert('RGB').getdata()):
        rgb = (r >> 3) << 11 | (g >> 2) << 5 | (b >> 3)
        data[2*i] = rgb & 255
        data[2*i + 1] = rgb >> 8
    with FB.open('r+b', buffering=0) as out:
        out.write(data)


def text(draw, xy, msg, font=FONT, fill=WHITE, max_width=None):
    s = str(msg).replace('\n', ' ')
    if max_width:
        while s and draw.textbbox((0, 0), s, font=font)[2] > max_width:
            s = s[:-2].rstrip('…') + '…'
    draw.text(xy, s, font=font, fill=fill)


class Launcher(wifi.Panel):
    def __init__(self):
        self.mode = 'menu'
        super().__init__()  # preserves the working wifi UI & touch grab
        if not CAL_PATH.exists():
            raise RuntimeError('Falta la calibración táctil: ' + str(CAL_PATH))
        self.calibration = json.loads(CAL_PATH.read_text())
        for name in ('a', 'b', 'c', 'd', 'e', 'f'):
            if name not in self.calibration:
                raise RuntimeError('Calibración incompleta: ' + name)
        self.term_cmd = ''
        self.term_lines = ['Terminal básica de C.U.T.Y', 'Comandos no interactivos.',
                           'Ejemplo: hostname -I']
        self.term_symbols = False
        self.term_shift = False
        self.test_lines = []
        self.face_blink_until = 0
        self.face_state = ''
        self.is_pressed = False
        self.hold_since = None
        self.released_at = None
        self.raw_x = self.raw_y = None
        self.last_release = 0
        self.ignore_next_release = False
        self.last_status_check = 0

    def draw_button(self, d, rect, title, action, font=FONT):
        x1, y1, x2, y2 = rect
        d.rounded_rectangle(rect, radius=9, fill=BLUE)
        tw = d.textbbox((0, 0), title, font=font)[2]
        th = d.textbbox((0, 0), title, font=font)[3]
        text(d, (x1 + max(4, (x2-x1-tw)//2),
                 y1 + max(2, (y2-y1-th)//2)), title, font)
        self.hotspots.append((rect, action))

    def back_button(self, d):
        # Not rendered in C.U.T.Y face mode.
        self.draw_button(d, (W-105, 4, W-7, 39), '< Menú', ('menu',), SMALL)

    def draw_menu(self, d):
        text(d, (18, 11), 'C.U.T.Y', LARGE)
        text(d, (18, 43), 'Selecciona un modo', SMALL, MUTED)
        options = [
            (70, 'Terminal', 'Comandos y diagnóstico', 'terminal'),
            (151, 'Internet', 'Wi-Fi, IP y conexión', 'internet'),
            (232, 'C.U.T.Y', 'Expresiones del robot', 'face'),
        ]
        for y, title, description, action in options:
            d.rounded_rectangle((12, y, W-12, y+70), radius=12, fill=CARD)
            text(d, (29, y+9), title, LARGE)
            text(d, (30, y+43), description, SMALL, MUTED)
            d.polygon([(W-38,y+24),(W-25,y+35),(W-38,y+46)], fill=GREEN)
            self.hotspots.append(((12, y, W-12, y+70), ('mode', action)))

    def draw_internet(self, d):
        text(d, (14, 9), 'Internet / Wi-Fi', LARGE)
        self.back_button(d)
        name, state, ip, gateway, connectivity, ssh = wifi_status()
        d.rounded_rectangle((10, 47, W-10, 192), radius=12, fill=CARD)
        text(d, (20, 55), 'Red: ' + name, FONT, max_width=W-40)
        text(d, (20, 83), 'IP Wi-Fi: ' + ip, FONT, GREEN if ip != 'Sin IPv4' else RED)
        text(d, (20, 110), 'Gateway: ' + gateway, SMALL, MUTED, W-40)
        states = {'full': 'Completa', 'limited': 'Limitada',
                  'portal': 'Portal de acceso', 'none': 'Sin Internet',
                  'unknown': 'No comprobada'}
        text(d, (20, 132), 'Internet: ' + states.get(connectivity, 'Sin verificar'),
             SMALL, MUTED)
        text(d, (20, 157), 'SSH: ' + ('Activo' if ssh else 'Inactivo'), SMALL, MUTED)
        self.draw_button(d, (10, 202, 232, 251), 'Buscar Wi-Fi', ('wifi', 'scan'))
        self.draw_button(d, (246, 202, W-10, 251), 'Red Tec', ('wifi', 'tec'))
        self.draw_button(d, (10, 260, 232, 311), 'Actualizar IP', ('wifi', 'home'), SMALL)
        self.draw_button(d, (246, 260, W-10, 311), 'Diagnosticar', ('diagnose',), SMALL)

    def draw_diagnosis(self, d):
        text(d, (13, 8), 'Diagnóstico de red', LARGE)
        self.back_button(d)
        d.rounded_rectangle((10, 47, W-10, 260), radius=10, fill=CARD)
        for i, line in enumerate(self.test_lines[:8]):
            text(d, (18, 57+i*24), line, SMALL, WHITE, W-37)
        self.draw_button(d, (105, 268, W-105, 314), 'Actualizar', ('diagnose',))

    def diagnose(self):
        self.screen = 'diagnosis'
        self.test_lines = ['Analizando conexión...']
        self.render()
        name, state, ip, gw, conn, ssh = wifi_status()
        lines = ['Red: ' + name, 'IP: ' + ip, 'Gateway: ' + gw]
        if ip == 'Sin IPv4':
            lines += ['No recibió dirección IPv4.', 'Revisar DHCP o la red.']
        elif gw == 'Sin puerta de enlace':
            lines += ['Falta ruta a Internet.', 'Revisar hotspot/router.']
        else:
            ping = command(['ping', '-n', '-c', '1', '-W', '2', '1.1.1.1'], timeout=4)
            if ping is not None and ping.returncode == 0:
                lines += ['Conexión IP externa: OK']
                dns = command(['getent', 'ahostsv4', 'google.com'], timeout=4)
                lines += ['DNS: ' + ('OK' if dns and dns.returncode == 0 else 'FALLÓ')]
            else:
                lines += ['Sin respuesta de 1.1.1.1.', 'Puede ser red sin salida,', 'portal o ICMP bloqueado.']
        self.test_lines = lines
        self.render()

    def draw_terminal(self, d):
        text(d, (11, 8), 'Terminal', LARGE)
        self.back_button(d)
        d.rounded_rectangle((7, 45, W-7, 139), radius=8, fill=CARD)
        for i, line in enumerate(self.term_lines[-5:]):
            text(d, (13, 49+i*17), line, TINY, max_width=W-25)
        d.rounded_rectangle((7, 145, W-7, 182), radius=6, fill='#243a53')
        text(d, (13, 154), '$ ' + self.term_cmd[-46:], SMALL, max_width=W-28)
        self.keyboard(d, top=188, terminal=True)

    def keyboard(self, d, top, terminal=False):
        if self.term_symbols:
            rows = ['1234567890', '-/.:_@+*?=', '!#$%&()[];', '<>\\|~^{}"\'']
        else:
            rows = ['1234567890', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm.-']
        for i, chars in enumerate(rows):
            y = top + 26*i
            width = (W-10) / len(chars)
            for j, char in enumerate(chars):
                x1 = round(5+j*width)
                x2 = round(5+(j+1)*width)-2
                disp = char.upper() if self.term_shift else char
                self.draw_button(d, (x1,y,x2,y+23), disp,
                                 ('term_key', disp), TINY)
        controls = [
            ((5, 293, 74, 318), 'SIMB', ('term_symbol',)),
            ((78, 293, 131, 318), 'Aa', ('term_shift',)),
            ((135, 293, 266, 318), 'ESPACIO', ('term_key', ' ')),
            ((270, 293, 360, 318), 'BORRAR', ('term_erase',)),
            ((364, 293, W-5, 318), 'ENTER', ('term_enter',))
        ]
        for rect, title, act in controls:
            self.draw_button(d, rect, title, act, TINY)

    def run_terminal_command(self):
        line = self.term_cmd.strip()
        self.term_cmd = ''
        if not line:
            self.render()
            return
        self.term_lines.append('$ ' + line)
        self.term_lines.append('Ejecutando...')
        self.render()
        # Never execute a terminal command as root, despite root owning /dev/fb1.
        result = command(['runuser', '-u', NORM_USER, '--',
                          '/bin/bash', '-lc', line], timeout=12)
        self.term_lines.pop()  # remove "Ejecutando..."
        if result is None:
            self.term_lines.append('Error o tiempo agotado (12 s)')
        else:
            combined = (result.stdout + result.stderr).strip()
            self.term_lines.extend(combined.splitlines()[-9:] or ['(sin salida)'])
            if result.returncode:
                self.term_lines.append('Código: ' + str(result.returncode))
        self.term_lines = self.term_lines[-40:]
        self.render()

    def draw_face(self, d):
        # Demo only; real robot/servos/voice integration is a later stage.
        blink = time.monotonic() < self.face_blink_until
        eye_y = H//2-18
        if blink:
            d.rounded_rectangle((92, eye_y+35, 197, eye_y+42), 4, fill=GREEN)
            d.rounded_rectangle((283, eye_y+35, 388, eye_y+42), 4, fill=GREEN)
        else:
            d.ellipse((100, eye_y-8, 191, eye_y+80), fill=GREEN)
            d.ellipse((289, eye_y-8, 380, eye_y+80), fill=GREEN)
            d.ellipse((141, eye_y+31, 158, eye_y+49), fill=BG)
            d.ellipse((330, eye_y+31, 347, eye_y+49), fill=BG)
        d.arc((200, 222, 280, 263), 12, 168, fill=GREEN, width=5)
        text(d, (W//2-41, 271), 'C.U.T.Y', FONT, MUTED)
        # Intentionally NO back button or exit hint.

    def add_wifi_back_overlay(self):
        """Draw a tiny Menu arrow on inherited Wi-Fi screens without editing them."""
        rect = (W-104, 3, W-7, 39)
        overlay = Image.new('RGB', (rect[2]-rect[0]+1, rect[3]-rect[1]+1), BG)
        d = ImageDraw.Draw(overlay)
        d.rounded_rectangle((0,0,overlay.width-1,overlay.height-1),
                            radius=7, fill=BLUE)
        text(d, (7, 9), '< Menú', SMALL)
        # Overwrite just the affected framebuffer rows; preserve the Wi-Fi panel.
        rowbytes = W*2
        packed = bytearray(overlay.width*2*overlay.height)
        for i, (r,g,b) in enumerate(overlay.getdata()):
            p = (r>>3)<<11 | (g>>2)<<5 | (b>>3)
            packed[2*i], packed[2*i+1] = p&255, p>>8
        with FB.open('r+b', buffering=0) as f:
            for iy in range(overlay.height):
                f.seek((rect[1]+iy)*rowbytes + rect[0]*2)
                start = iy*overlay.width*2
                f.write(packed[start:start+overlay.width*2])
        self.hotspots.insert(0, (rect, ('menu',)))

    def render(self):
        if self.mode == 'internet' and self.screen not in ('home', 'diagnosis'):
            super().render()  # reuse tested Wi-Fi scanning / password keyboard
            self.add_wifi_back_overlay()
            return
        im = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(im)
        self.hotspots = []
        if self.mode == 'menu':
            self.draw_menu(d)
        elif self.mode == 'internet':
            if self.screen == 'diagnosis':
                self.draw_diagnosis(d)
            else:
                self.draw_internet(d)
        elif self.mode == 'terminal':
            self.draw_terminal(d)
        elif self.mode == 'face':
            self.draw_face(d)
        render_frame(im)

    def action(self, act):
        if act == ('menu',):
            self.mode, self.screen = 'menu', 'home'
            self.value = ''  # never leave passwords displayed
            self.render()
            return
        if isinstance(act, tuple) and act[0] == 'mode':
            self.mode = act[1]
            self.screen = 'home'
            self.render()
            return
        if self.mode == 'internet':
            if act == ('diagnose',):
                self.diagnose()
                return
            if isinstance(act, tuple) and act[0] == 'wifi':
                self.screen = 'home'
                super().action(act[1])
                return
            # Existing Wi-Fi implementation, including show/hide password.
            super().action(act)
            return
        if self.mode == 'terminal':
            if not isinstance(act, tuple):
                return
            if act[0] == 'term_key' and len(self.term_cmd) < 140:
                self.term_cmd += act[1]
            elif act[0] == 'term_erase':
                self.term_cmd = self.term_cmd[:-1]
            elif act[0] == 'term_symbol':
                self.term_symbols = not self.term_symbols
            elif act[0] == 'term_shift':
                self.term_shift = not self.term_shift
            elif act[0] == 'term_enter':
                self.run_terminal_command()
                return
            self.render()

    def touch_xy(self):
        c = self.calibration
        x, y = self.raw_x, self.raw_y
        sx = round(c['a']*x + c['b']*y + c['c'])
        sy = round(c['d']*x + c['e']*y + c['f'])
        return max(0, min(W-1, sx)), max(0, min(H-1, sy))

    def run(self):
        self.render()
        try:
            while True:
                readable, _, _ = select.select([self.touch.fd], [], [], 0.10)
                now = time.monotonic()
                if readable:
                    try:
                        events = self.touch.read()
                    except BlockingIOError:
                        events = []
                    for ev in events:
                        if ev.type == ecodes.EV_ABS:
                            if ev.code == ecodes.ABS_X:
                                self.raw_x = ev.value
                            elif ev.code == ecodes.ABS_Y:
                                self.raw_y = ev.value
                        elif ev.type == ecodes.EV_KEY and ev.code == ecodes.BTN_TOUCH:
                            if ev.value == 1:
                                self.is_pressed = True
                                if self.mode == 'face':
                                    self.hold_since = now
                                self.released_at = None
                            else:
                                self.is_pressed = False
                                if self.ignore_next_release:
                                    # A long hold already switched to the menu.
                                    # Do not interpret lifting the finger as a menu click.
                                    self.ignore_next_release = False
                                    continue
                                if self.mode == 'face':
                                    short_press = (self.hold_since is not None and
                                                   now-self.hold_since < 0.7)
                                    self.hold_since = None
                                    self.released_at = now
                                    if short_press:
                                        self.face_blink_until = now+0.18
                                        self.render()
                                else:
                                    if (self.raw_x is not None and self.raw_y is not None
                                            and now-self.last_release >= 0.16):
                                        sx, sy = self.touch_xy()
                                        for (l,t,r,b), action in list(self.hotspots):
                                            if l <= sx <= r and t <= sy <= b:
                                                self.last_release = now
                                                self.action(action)
                                                break
                if self.mode == 'face':
                    if (self.is_pressed and self.hold_since is not None and
                            now - self.hold_since >= 5.0):
                        self.is_pressed = False
                        self.ignore_next_release = True
                        self.hold_since = self.released_at = None
                        self.mode = 'menu'
                        self.render()
                    elif (not self.is_pressed and self.released_at is not None and
                          now-self.released_at > 0.35):
                        self.hold_since = self.released_at = None
                    elif (self.face_blink_until and
                          now > self.face_blink_until and self.face_state != 'normal'):
                        self.face_state = 'normal'
                        self.render()
                    elif now < self.face_blink_until:
                        self.face_state = 'blink'
        except KeyboardInterrupt:
            pass
        finally:
            self.touch.ungrab()
            self.touch.close()


if __name__ == '__main__':
    Launcher().run()
