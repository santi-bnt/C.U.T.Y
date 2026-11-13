#!/usr/bin/env python3
"""C.U.T.Y 3.5in launcher: menu / basic terminal / Wi-Fi / animated face.

Reuses the already-calibrated cuty_wifi_panel.py and ADS7846 framebuffer.
Run on the Raspberry Pi as root. No HDMI, X11, Wayland or Internet needed.
"""
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from evdev import ecodes

# Import the WORKING Wi-Fi panel from the same directory, without rewriting it.
import cuty_wifi_panel as wifi

# The animated face, camera tracking and voice link live in the cuty package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
try:
    from cuty.face.framebuffer import FramebufferWriter, to_rgb565
    from cuty.brain.menu_voice import MenuVoice
    from cuty.face.link import FaceLinkReceiver
    from cuty.face.renderer import Face
    from cuty.vision.camera import camera_mode
    from cuty.vision.face_tracker import FaceTracker
    from cuty.vision.ipc import socket_path_for_user
    FACE_ERROR = ''
except ImportError as error:  # e.g. NumPy missing: keep menus working.
    FACE_ERROR = f'Cara no disponible: {error}'

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

FACE_FPS = max(5.0, min(40.0, float(os.getenv('CUTY_FACE_FPS', '20') or 20)))
FACE_SSAA = {'1': 1, '2': 2, '3': 3}.get(os.getenv('CUTY_FACE_SSAA', '2').strip(), 2)
START_MODE = os.getenv('CUTY_START_MODE', 'menu').strip().lower()

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
        self.face = None
        self.face_writer = None
        self.tracker = None
        self.next_face_frame = 0.0
        self.link = None if FACE_ERROR else FaceLinkReceiver.from_env()
        self.is_pressed = False
        self.hold_since = None
        self.released_at = None
        self.raw_x = self.raw_y = None
        self.last_release = 0
        self.ignore_next_release = False
        self.last_status_check = 0
        self.voice = MenuVoice(Path(__file__).resolve().parents[1], NORM_USER) if not FACE_ERROR else None
        self.voice_error = ''
        self.power_action = None
        self.power_error = ''
        self.power_busy = ''

    def draw_button(self, d, rect, title, action, font=FONT, fill=BLUE):
        x1, y1, x2, y2 = rect
        d.rounded_rectangle(rect, radius=9, fill=fill)
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
        self.draw_button(d, (W-188, 8, W-12, 55), 'Apagar / Reiniciar', ('power_menu',), SMALL)
        options = [
            (70, 'Terminal', 'Comandos y diagnóstico', 'terminal'),
            (151, 'Internet', 'Wi-Fi, IP y conexión', 'internet'),
            (232, 'C.U.T.Y', self.voice_error or 'Toca para conversar', 'face'),
        ]
        for y, title, description, action in options:
            d.rounded_rectangle((12, y, W-12, y+70), radius=12, fill=CARD)
            text(d, (29, y+9), title, LARGE)
            text(d, (30, y+43), description, SMALL, MUTED)
            d.polygon([(W-38,y+24),(W-25,y+35),(W-38,y+46)], fill=GREEN)
            self.hotspots.append(((12, y, W-12, y+70), ('mode', action)))

    def draw_power(self, d):
        text(d, (18, 11), 'Energía', LARGE)
        if self.screen == 'busy':
            text(d, (24, 121), self.power_busy, LARGE, WHITE, W-48)
            text(d, (24, 167), 'Espera a que el sistema termine.', FONT, MUTED, W-48)
            return  # no buttons while a system request is pending
        self.back_button(d)
        if self.screen == 'confirm':
            restarting = self.power_action == 'reboot'
            d.rounded_rectangle((14, 65, W-14, 220), radius=12, fill=CARD)
            text(d, (28, 85), '¿Reiniciar Raspberry?' if restarting else '¿Apagar Raspberry?', LARGE)
            text(d, (28, 131), 'Se cerrarán la voz y la cámara.', FONT, MUTED)
            text(d, (28, 165), 'La Raspberry volverá a arrancar.' if restarting else
                 'Para volver a usarla tendrás que encenderla.', SMALL, MUTED, W-56)
            self.draw_button(d, (16, 242, 230, 306), 'Cancelar', ('power_cancel',))
            self.draw_button(d, (250, 242, W-16, 306), 'Sí, reiniciar' if restarting else
                             'Sí, apagar', ('power_confirm',), fill='#8f293d')
            return
        text(d, (18, 47), 'Selecciona una opción; se pedirá confirmación.', SMALL, MUTED)
        self.draw_button(d, (18, 82, W-18, 151), 'Apagar Raspberry', ('power_request', 'poweroff'))
        self.draw_button(d, (18, 171, W-18, 240), 'Reiniciar Raspberry', ('power_request', 'reboot'))
        if self.power_error:
            text(d, (20, 263), self.power_error, SMALL, RED, W-40)
            text(d, (20, 286), 'Revisa el registro del launcher por SSH.', SMALL, MUTED)

    def execute_power(self):
        """Only a confirmed local touch may queue one normal system shutdown."""
        requested = self.power_action
        if (self.mode != 'power' or self.screen != 'confirm' or
                requested not in ('poweroff', 'reboot')):
            return
        self.power_action = None  # consume before doing anything; repeated touches are ignored
        self.screen = 'busy'
        self.power_busy = 'Reiniciando Raspberry…' if requested == 'reboot' else 'Apagando Raspberry…'
        self.render()
        try:
            self.leave_face()
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            print('C.U.T.Y energía: no se pudo cerrar la sesión:', error, flush=True)
            self.power_error = 'No se pudo cerrar la sesión de C.U.T.Y.'
            self.screen = 'home'
            self.render()
            return
        result = command(['/usr/bin/systemctl', '--no-block', requested], timeout=8)
        if result is None or result.returncode != 0:
            detail = 'Tiempo agotado o systemctl no disponible' if result is None else result.stderr.strip()
            print('C.U.T.Y energía:', detail, flush=True)
            self.power_error = 'No se pudo solicitar el reinicio.' if requested == 'reboot' else 'No se pudo solicitar el apagado.'
            self.screen = 'home'
            self.render()

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

    def draw_face_error(self, d):
        text(d, (18, 120), 'C.U.T.Y', LARGE)
        text(d, (18, 160), FACE_ERROR, SMALL, RED, W-36)
        text(d, (18, 184), 'Instala python3-numpy y reinicia el servicio.', SMALL, MUTED)

    # ----- animated face -------------------------------------------------
    def enter_face(self):
        """Start the animated face; never let a camera problem stop the menu."""
        self.mode, self.screen = 'face', 'home'
        if FACE_ERROR:
            return
        if self.face is None:
            self.face = Face(W, H, ssaa=FACE_SSAA)
        if self.face_writer is None:
            self.face_writer = FramebufferWriter(FB, W, H)
        self.face_writer.invalidate()
        if self.tracker is None and camera_mode() != 'off':
            self.tracker = FaceTracker(
                vision_ipc_path=socket_path_for_user(NORM_USER), vision_user=NORM_USER,
            )
        if self.tracker is not None:
            self.tracker.start()
        self.next_face_frame = 0.0
        if self.voice is not None and os.getenv('CUTY_MENU_VOICE', 'on').lower() not in ('off', '0', 'false'):
            try:
                self.voice_error = ''
                self.voice.start()
            except (OSError, RuntimeError) as error:
                print('C.U.T.Y voz:', error, flush=True)
                self.voice_error = 'Voz no disponible; revisa el registro'
                self.leave_face()
                self.mode, self.screen = 'menu', 'home'

    def leave_face(self):
        if self.voice is not None:
            self.voice.stop()
        if self.tracker is not None:
            self.tracker.stop()
        if self.face is not None:
            self.face.clear_target()
        if self.face_writer is not None:
            self.face_writer.invalidate()

    def check_voice(self):
        """A normal voice exit returns home; a failure also leaves the menu usable."""
        if self.voice is None or self.voice.process is None:
            return False
        code = self.voice.poll()
        if code is None:
            return False
        self.voice_error = '' if code == 0 else 'Error de voz; revisa el registro'
        self.leave_face()
        self.hold_since = self.released_at = None
        self.ignore_next_release = self.is_pressed
        self.mode, self.screen = 'menu', 'home'
        self.render()
        return True

    def apply_link_messages(self):
        """Expressions, mouth level and blinks sent by the voice app."""
        if self.link is None:
            return
        for msg in self.link.poll():
            if self.face is None:
                continue
            if msg.type == 'expression':
                self.face.set_expression(msg.expression, msg.intensity)
            elif msg.type == 'mouth':
                self.face.set_mouth_open(msg.level)
            elif msg.type == 'look' and (self.tracker is None or self.tracker.latest() is None):
                self.face.look_at(msg.x, msg.y)
            elif msg.type == 'blink':
                self.face.blink()

    def draw_face_frame(self, now):
        if self.tracker is not None:
            target = self.tracker.latest()
            if target is not None:
                self.face.look_at(target.x, target.y)
        self.face_writer.write(to_rgb565(self.face.render(now)))

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
        elif self.mode == 'power':
            self.draw_power(d)
        elif self.mode == 'face':
            if not FACE_ERROR:
                self.next_face_frame = 0.0  # drawn by the animation loop
                return
            self.draw_face_error(d)
        render_frame(im)

    def action(self, act):
        if self.mode == 'power' and self.screen == 'busy':
            return
        if act == ('menu',):
            if self.mode == 'face':
                self.leave_face()
            self.mode, self.screen = 'menu', 'home'
            self.power_action = None
            self.value = ''  # never leave passwords displayed
            self.render()
            return
        if act == ('power_menu',) and self.mode == 'menu':
            self.mode, self.screen = 'power', 'home'
            self.power_action = None
            self.power_error = ''
            self.value = ''
            self.render()
            return
        if self.mode == 'power':
            if self.screen == 'busy':
                return
            if act == ('power_cancel',):
                self.power_action = None
                self.screen = 'home'
                self.render()
            elif (isinstance(act, tuple) and len(act) == 2 and act[0] == 'power_request'
                  and self.screen == 'home' and act[1] in ('poweroff', 'reboot')):
                self.power_action = act[1]
                self.power_error = ''
                self.screen = 'confirm'
                self.render()
            elif act == ('power_confirm',):
                self.execute_power()
            return
        if isinstance(act, tuple) and act[0] == 'mode':
            if act[1] == 'face':
                self.enter_face()
            else:
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
        if START_MODE == 'face':
            self.enter_face()
        self.render()
        face_metric_started = time.monotonic()
        face_metric_frames = 0
        face_metric_render = 0.0
        face_metric_late = 0
        try:
            while True:
                watch = [self.touch.fd] + ([self.link.fileno()] if self.link else [])
                timeout = 0.10
                if self.mode == 'face' and not FACE_ERROR:
                    timeout = max(0.0, self.next_face_frame - time.monotonic())
                readable, _, _ = select.select(watch, [], [], timeout)
                now = time.monotonic()
                if self.link is not None and self.link.fileno() in readable:
                    self.apply_link_messages()
                if self.touch.fd in readable:
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
                                    if short_press and self.face is not None:
                                        self.face.blink()
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
                    if self.check_voice():
                        continue
                    if (self.is_pressed and self.hold_since is not None and
                            now - self.hold_since >= 5.0):
                        self.is_pressed = False
                        self.ignore_next_release = True
                        self.hold_since = self.released_at = None
                        self.leave_face()
                        self.mode = 'menu'
                        self.render()
                        continue
                    if (not self.is_pressed and self.released_at is not None and
                            now-self.released_at > 0.35):
                        self.hold_since = self.released_at = None
                    if not FACE_ERROR and now >= self.next_face_frame:
                        render_started = time.monotonic()
                        self.draw_face_frame(now)
                        render_elapsed = time.monotonic() - render_started
                        face_metric_frames += 1
                        face_metric_render += render_elapsed
                        if render_elapsed > 1 / FACE_FPS:
                            face_metric_late += 1
                        self.next_face_frame += 1/FACE_FPS
                        if self.next_face_frame < now:  # ran late: skip, don't burst
                            self.next_face_frame = now + 1/FACE_FPS
                    metric_elapsed = now - face_metric_started
                    if self.mode == 'face' and metric_elapsed >= 5.0:
                        if face_metric_frames:
                            print('[FACE PERF] fps=%.2f render_ms=%.1f late_frames=%d samples=%d' % (
                                face_metric_frames / metric_elapsed,
                                face_metric_render * 1000 / face_metric_frames,
                                face_metric_late, face_metric_frames), flush=True)
                        face_metric_started = now
                        face_metric_frames = 0
                        face_metric_render = 0.0
                        face_metric_late = 0
        except KeyboardInterrupt:
            pass
        finally:
            self.leave_face()
            if self.face_writer is not None:
                self.face_writer.close()
            if self.link is not None:
                self.link.close()
            self.touch.ungrab()
            self.touch.close()


if __name__ == '__main__':
    Launcher().run()
