import pygame
import sys
import array
import math
import json
import os
import ctypes

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.key.set_repeat(400, 50)

desktop_info = pygame.display.Info()
DESKTOP_W, DESKTOP_H = desktop_info.current_w, desktop_info.current_h

# Detect monitor refresh rate
import ctypes
import ctypes.wintypes
class DEVMODE(ctypes.Structure):
    _fields_ = [("dmDeviceName", ctypes.wintypes.WCHAR * 32),
                ("dmSpecVersion", ctypes.wintypes.WORD),
                ("dmDriverVersion", ctypes.wintypes.WORD),
                ("dmSize", ctypes.wintypes.WORD),
                ("dmDriverExtra", ctypes.wintypes.WORD),
                ("dmFields", ctypes.wintypes.DWORD),
                ("_union", ctypes.c_byte * 16),
                ("dmColor", ctypes.wintypes.SHORT),
                ("dmDuplex", ctypes.wintypes.SHORT),
                ("dmYResolution", ctypes.wintypes.SHORT),
                ("dmTTOption", ctypes.wintypes.SHORT),
                ("dmCollate", ctypes.wintypes.SHORT),
                ("dmFormName", ctypes.wintypes.WCHAR * 32),
                ("dmLogPixels", ctypes.wintypes.WORD),
                ("dmBitsPerPel", ctypes.wintypes.DWORD),
                ("dmPelsWidth", ctypes.wintypes.DWORD),
                ("dmPelsHeight", ctypes.wintypes.DWORD),
                ("dmDisplayFlags", ctypes.wintypes.DWORD),
                ("dmDisplayFrequency", ctypes.wintypes.DWORD)]
try:
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    ctypes.windll.user32.EnumDisplaySettingsW(None, -1, ctypes.byref(dm))
    MONITOR_HZ = int(dm.dmDisplayFrequency) if dm.dmDisplayFrequency > 0 else 60
except Exception:
    MONITOR_HZ = 60

def make_click_sound():
    sample_rate = 44100
    duration = 0.04
    n = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n):
        envelope = 1.0 - (i / n)          # linear decay
        val = int(32767 * envelope * math.sin(2 * math.pi * 700 * i / sample_rate))
        buf.append(val)   # left channel
        buf.append(val)   # right channel
    return pygame.mixer.Sound(buffer=buf)

click_sound = make_click_sound()

def make_monkey_hit_sound():
    """Short descending pop when a monkey is stomped."""
    sample_rate = 44100
    duration = 0.12
    n = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n):
        t = i / n
        envelope = (1.0 - t) ** 2
        freq = 500 - 300 * t
        val = int(32767 * envelope * math.sin(2 * math.pi * freq * i / sample_rate))
        buf.append(val)
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf)

monkey_hit_sound = make_monkey_hit_sound()

def make_fireball_sound():
    """Short whoosh when fireball is launched."""
    sample_rate = 44100
    duration = 0.15
    n = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n):
        t = i / n
        envelope = (1.0 - t) ** 1.5
        freq = 200 + 400 * t
        val = int(16000 * envelope * math.sin(2 * math.pi * freq * i / sample_rate))
        buf.append(val)
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf)

fireball_sound = make_fireball_sound()

def make_wall_of_fire_sound():
    """Low rumble when wall of fire is placed."""
    sample_rate = 44100
    duration = 0.3
    n = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n):
        t = i / n
        envelope = (1.0 - t) ** 2
        freq = 100 + 150 * t
        val = int(20000 * envelope * math.sin(2 * math.pi * freq * i / sample_rate))
        buf.append(val)
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf)

wall_of_fire_sound = make_wall_of_fire_sound()

# ── Profile ──────────────────────────────────────────────────────────────────
PROFILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile.json")

def load_profile():
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r") as f:
                data = json.load(f)
            return data.get("username", "") or None
        except Exception:
            return None
    return None

def save_profile(username):
    with open(PROFILE_PATH, "w") as f:
        json.dump({"username": username}, f)

# ── Progress persistence ──────────────────────────────────────────────────
PROGRESS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.json")

def load_progress():
    if os.path.exists(PROGRESS_PATH):
        try:
            with open(PROGRESS_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {"total_coins": 0}
    return {"total_coins": 0}

def save_progress(data):
    with open(PROGRESS_PATH, "w") as f:
        json.dump(data, f)

progress = load_progress()
total_coins = progress.get("total_coins", 0)

profile_username = load_profile()  # None on first launch

# ── Settings ─────────────────────────────────────────────────────────────────
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings():
    data = {
        "master_volume": master_volume,
        "vsync_enabled": vsync_enabled,
        "max_fps": max_fps,
        "alloted_ram": alloted_ram,
        "display_mode": display_mode,
    }
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f)

WIDTH, HEIGHT = 800, 600
screen = pygame.Surface((WIDTH, HEIGHT))          # fixed-size render target
_init_saved = load_settings()
_init_display = _init_saved.get("display_mode", "Windowed")
if _init_display == "Fullscreen":
    display_surf = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    is_fullscreen = True
elif _init_display == "Windowed":
    display_surf = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    is_fullscreen = False
else:  # Off
    display_surf = pygame.display.set_mode((WIDTH, HEIGHT))
    is_fullscreen = False
pygame.display.set_caption("Pixelrift")
if _init_display == "Windowed":
    hwnd = pygame.display.get_wm_info()["window"]
    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE

# Colors
GREY = (180, 180, 180)
DARK_GREY = (120, 120, 120)
GREEN = (100, 185, 60)
DARK_GREEN = (70, 140, 40)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GREEN = (120, 220, 100)
RED         = (210, 60,  60)
DARK_RED    = (160, 40,  40)

# Small pixel font — rendered small then scaled up for chunky pixel look
pixel_font_small = pygame.font.SysFont("Courier New", 16, bold=True)

# Button dimensions
BTN_W, BTN_H = 220, 70
btn_rect          = pygame.Rect(WIDTH // 2 - BTN_W // 2, HEIGHT // 2 - BTN_H // 2, BTN_W, BTN_H)
settings_btn_rect = pygame.Rect(WIDTH // 2 - BTN_W // 2, HEIGHT // 2 + BTN_H // 2 + 15, BTN_W, BTN_H)

def pixel_round_rect_points(rect, step=8):
    """Returns octagon points that simulate pixel-art stepped rounded corners."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    s = step
    return [
        (x + s, y),
        (x + w - s, y),
        (x + w, y + s),
        (x + w, y + h - s),
        (x + w - s, y + h),
        (x + s, y + h),
        (x, y + h - s),
        (x, y + s),
    ]

def draw_pixel_button(surface, rect, text, hovered):
    """Pixel-art style button. Use this style for all future UI buttons/icons."""
    color = DARK_GREEN if hovered else GREEN
    pts = pixel_round_rect_points(rect, step=8)

    # Fill
    pygame.draw.polygon(surface, color, pts)

    # Border — draw each edge individually for crisp pixel corners
    border = 4
    for i in range(len(pts)):
        pygame.draw.line(surface, BLACK, pts[i], pts[(i + 1) % len(pts)], border)

    # Render text with no antialiasing, then scale 2x for blocky pixel look
    label_raw = pixel_font_small.render(text, False, BLACK)
    w, h = label_raw.get_size()
    label = pygame.transform.scale(label_raw, (w * 2, h * 2))

    lx = rect.centerx - label.get_width() // 2
    ly = rect.centery - label.get_height() // 2
    surface.blit(label, (lx, ly))

def draw_red_button(surface, rect, text, hovered):
    color = DARK_RED if hovered else RED
    pts = pixel_round_rect_points(rect, step=8)
    pygame.draw.polygon(surface, color, pts)
    border = 4
    for i in range(len(pts)):
        pygame.draw.line(surface, BLACK, pts[i], pts[(i + 1) % len(pts)], border)
    label_raw = pixel_font_small.render(text, False, BLACK)
    w, h = label_raw.get_size()
    label = pygame.transform.scale(label_raw, (w * 2, h * 2))
    surface.blit(label, (rect.centerx - label.get_width() // 2,
                          rect.centery - label.get_height() // 2))

# Hand-drawn pixel art characters for the PIXELRIFT logo (5 wide x 7 tall grid)
PIXEL_CHARS = {
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
}

def make_logo():
    """Draws each letter as a white pixel pattern inside its own black square cell."""
    PS = 7          # pixels per grid cell
    PAD = 6         # padding inside each black box
    GAP = 3         # gap between boxes
    ROWS, COLS = 7, 5
    cell_w = COLS * PS + PAD * 2
    cell_h = ROWS * PS + PAD * 2
    text = "PIXELRIFT"
    total_w = len(text) * cell_w + (len(text) - 1) * GAP
    surf = pygame.Surface((total_w, cell_h), pygame.SRCALPHA)

    for i, ch in enumerate(text):
        x = i * (cell_w + GAP)
        # Black cell background
        pygame.draw.rect(surf, BLACK, (x, 0, cell_w, cell_h))
        pattern = PIXEL_CHARS.get(ch, [])
        for row_i, row in enumerate(pattern):
            for col_i, cell in enumerate(row):
                if cell == '#':
                    pygame.draw.rect(surf, WHITE, (
                        x + PAD + col_i * PS,
                        PAD + row_i * PS,
                        PS, PS
                    ))
    return surf

logo_surf = make_logo()

def draw_home(hovered, settings_hovered):
    # Grey placeholder background
    screen.fill(GREY)

    # Placeholder label (plain, no frills)
    ph_raw = pixel_font_small.render("[Background Image]", False, DARK_GREY)
    ph_text = pygame.transform.scale(ph_raw, (ph_raw.get_width() * 2, ph_raw.get_height() * 2))
    screen.blit(ph_text, (WIDTH // 2 - ph_text.get_width() // 2, HEIGHT // 4))

    # PIXELRIFT logo — top center
    screen.blit(logo_surf, (WIDTH // 2 - logo_surf.get_width() // 2, 40))

    draw_pixel_button(screen, btn_rect, "Play", hovered)
    draw_pixel_button(screen, settings_btn_rect, "Settings", settings_hovered)

    # Total coins — top-left corner
    coin_raw = pixel_font_small.render("Coins: " + str(total_coins), False, (240, 220, 50))
    coin_surf = pygame.transform.scale(coin_raw, (coin_raw.get_width() * 2, coin_raw.get_height() * 2))
    screen.blit(coin_surf, (12, 12))

    # Username — bottom-right corner
    if profile_username:
        raw = pixel_font_small.render(profile_username, False, DARK_GREY)
        name_surf = pygame.transform.scale(raw, (raw.get_width() * 2, raw.get_height() * 2))
        screen.blit(name_surf, (WIDTH - name_surf.get_width() - 12, HEIGHT - name_surf.get_height() - 10))

# Levels list and index
levels = ["Forest", "Desert", "Polar"]
level_index = 0

CARD_W, CARD_H = 300, 300
card_rect = pygame.Rect(WIDTH // 2 - CARD_W // 2, 130, CARD_W, CARD_H)

# Back (X) button — top left of level select screen
CROSS_SIZE = 45
cross_btn_rect = pygame.Rect(20, 20, CROSS_SIZE, CROSS_SIZE)

# Arrow buttons — vertically centered with the card
ARROW_W, ARROW_H = 55, 55
arrow_cy = card_rect.centery
left_arrow_rect  = pygame.Rect(card_rect.left - 80,  arrow_cy - ARROW_H // 2, ARROW_W, ARROW_H)
right_arrow_rect = pygame.Rect(card_rect.right + 25, arrow_cy - ARROW_H // 2, ARROW_W, ARROW_H)

# Pause button (top-left during gameplay)
PAUSE_BTN_SIZE = 36
pause_btn_rect = pygame.Rect(10, 10, PAUSE_BTN_SIZE, PAUSE_BTN_SIZE)

# Pause menu
PAUSE_BOX_W, PAUSE_BOX_H = 340, 270
pause_box_rect    = pygame.Rect(WIDTH // 2 - PAUSE_BOX_W // 2, HEIGHT // 2 - PAUSE_BOX_H // 2,
                                PAUSE_BOX_W, PAUSE_BOX_H)
pause_resume_rect = pygame.Rect(WIDTH // 2 - BTN_W // 2, pause_box_rect.y + 100, BTN_W, BTN_H)
pause_exit_rect   = pygame.Rect(WIDTH // 2 - BTN_W // 2, pause_box_rect.y + 185, BTN_W, BTN_H)

# Death screen buttons
DEATH_BTN_W = 280
death_retry_rect  = pygame.Rect(WIDTH // 2 - DEATH_BTN_W // 2, HEIGHT // 2 - 20, DEATH_BTN_W, BTN_H)
death_exit_rect   = pygame.Rect(WIDTH // 2 - DEATH_BTN_W // 2, HEIGHT // 2 + 70, DEATH_BTN_W, BTN_H)

# Win screen buttons
WIN_BTN_W = 280
win_retry_rect = pygame.Rect(WIDTH // 2 - WIN_BTN_W // 2, HEIGHT // 2 + 40, WIN_BTN_W, BTN_H)
win_exit_rect  = pygame.Rect(WIDTH // 2 - WIN_BTN_W // 2, HEIGHT // 2 + 130, WIN_BTN_W, BTN_H)

# Ability HUD buttons — bottom-right corner
ABILITY_BTN_SIZE = 56
ABILITY_BTN_GAP  = 10
ABILITY_BTN_Y    = HEIGHT - ABILITY_BTN_SIZE - 12
ability_fireball_rect = pygame.Rect(
    WIDTH - 2 * ABILITY_BTN_SIZE - ABILITY_BTN_GAP - 12,
    ABILITY_BTN_Y,
    ABILITY_BTN_SIZE, ABILITY_BTN_SIZE)
ability_wallfire_rect = pygame.Rect(
    WIDTH - ABILITY_BTN_SIZE - 12,
    ABILITY_BTN_Y,
    ABILITY_BTN_SIZE, ABILITY_BTN_SIZE)

# Level data
level_data = {
    "Forest": {"difficulty": "Easy", "status": "Not Started", "time": "--:--"},
    "Desert": {"difficulty": "Easy", "status": "Not Started", "time": "--:--"},
    "Polar":  {"difficulty": "Easy", "status": "Not Started", "time": "--:--"},
}

def pixel_text(surface, text, scale, color, cx, y):
    """Helper: render pixel text centered at cx, starting at y. Returns bottom y."""
    raw = pixel_font_small.render(text, False, color)
    surf = pygame.transform.scale(raw, (raw.get_width() * scale, raw.get_height() * scale))
    surface.blit(surf, (cx - surf.get_width() // 2, y))
    return y + surf.get_height()

def draw_cross_button(surface, rect, hovered):
    """Pixel-art X (close) button."""
    color = (180, 50, 50) if hovered else (220, 70, 70)
    pts = pixel_round_rect_points(rect, step=6)
    pygame.draw.polygon(surface, color, pts)
    for i in range(len(pts)):
        pygame.draw.line(surface, BLACK, pts[i], pts[(i + 1) % len(pts)], 4)

    # Draw X using two thick pixel lines
    m = 10  # margin from edge
    pygame.draw.line(surface, BLACK, (rect.x + m, rect.y + m), (rect.right - m, rect.bottom - m), 4)
    pygame.draw.line(surface, BLACK, (rect.right - m, rect.y + m), (rect.x + m, rect.bottom - m), 4)

def draw_arrow_button(surface, rect, direction, hovered):
    """Pixel-art arrow button. direction: 'left' or 'right'."""
    color = DARK_GREEN if hovered else GREEN
    pts = pixel_round_rect_points(rect, step=6)
    pygame.draw.polygon(surface, color, pts)
    for i in range(len(pts)):
        pygame.draw.line(surface, BLACK, pts[i], pts[(i + 1) % len(pts)], 4)

    # Draw pixel triangle arrow
    cx, cy = rect.centerx, rect.centery
    size = 10
    if direction == "left":
        tri = [(cx + size, cy - size), (cx + size, cy + size), (cx - size, cy)]
    else:
        tri = [(cx - size, cy - size), (cx - size, cy + size), (cx + size, cy)]
    pygame.draw.polygon(surface, BLACK, tri)

def draw_level_card(surface, rect, label):
    """Pixel-art level card: icon → name → difficulty → stats."""
    pts = pixel_round_rect_points(rect, step=6)
    pygame.draw.polygon(surface, DARK_GREY, pts)
    for i in range(len(pts)):
        pygame.draw.line(surface, BLACK, pts[i], pts[(i + 1) % len(pts)], 4)

    cx = rect.centerx
    padding = 14

    # Icon placeholder
    icon_w, icon_h = rect.width - padding * 2, 140
    icon_rect = pygame.Rect(rect.x + padding, rect.y + padding, icon_w, icon_h)
    pygame.draw.rect(surface, GREY, icon_rect)
    pygame.draw.rect(surface, BLACK, icon_rect, 3)
    pixel_text(surface, "[icon]", 1, BLACK, cx, icon_rect.centery - 8)

    # Name — 2x
    y = icon_rect.bottom + 10
    y = pixel_text(surface, label, 2, BLACK, cx, y) + 4

    # Difficulty — 1x, light green
    difficulty = level_data.get(label, {}).get("difficulty", "Easy")
    y = pixel_text(surface, difficulty, 1, LIGHT_GREEN, cx, y) + 16

    # Status — 1x
    status = level_data.get(label, {}).get("status", "Not Started")
    y = pixel_text(surface, status, 1, BLACK, cx, y) + 4

    # Time — 1x
    time_str = level_data.get(label, {}).get("time", "--:--")
    pixel_text(surface, time_str, 1, BLACK, cx, y)

def draw_level_select(mouse_pos):
    screen.fill(GREY)

    # "Select Level" heading
    heading_raw = pixel_font_small.render("Select Level", False, BLACK)
    heading = pygame.transform.scale(heading_raw, (heading_raw.get_width() * 3, heading_raw.get_height() * 3))
    screen.blit(heading, (WIDTH // 2 - heading.get_width() // 2, 40))

    draw_level_card(screen, card_rect, levels[level_index])

    draw_arrow_button(screen, left_arrow_rect,  "left",  left_arrow_rect.collidepoint(mouse_pos))
    draw_arrow_button(screen, right_arrow_rect, "right", right_arrow_rect.collidepoint(mouse_pos))
    draw_cross_button(screen, cross_btn_rect, cross_btn_rect.collidepoint(mouse_pos))


# ── Profile creation screen ───────────────────────────────────────────────────
INPUT_MAX = 20
INPUT_BOX_W, INPUT_BOX_H = 320, 52
input_box_rect   = pygame.Rect(WIDTH // 2 - INPUT_BOX_W // 2, 230, INPUT_BOX_W, INPUT_BOX_H)
confirm_btn_rect = pygame.Rect(WIDTH // 2 - BTN_W // 2, 310, BTN_W, BTN_H)

def draw_create_profile(username_input, confirm_hovered, show_warning):
    screen.fill(GREY)

    # Logo
    screen.blit(logo_surf, (WIDTH // 2 - logo_surf.get_width() // 2, 40))

    # Heading
    pixel_text(screen, "Create Profile", 2, BLACK, WIDTH // 2, 140)
    pixel_text(screen, "Enter a username:", 1, DARK_GREY, WIDTH // 2, 195)

    # Input box
    pygame.draw.rect(screen, WHITE, input_box_rect)
    pygame.draw.rect(screen, BLACK, input_box_rect, 3)

    if username_input:
        raw = pixel_font_small.render(username_input, False, BLACK)
        txt = pygame.transform.scale(raw, (raw.get_width() * 2, raw.get_height() * 2))
        ty = input_box_rect.centery - txt.get_height() // 2
        screen.blit(txt, (input_box_rect.x + 10, ty))
    else:
        raw = pixel_font_small.render("type here...", False, DARK_GREY)
        txt = pygame.transform.scale(raw, (raw.get_width() * 2, raw.get_height() * 2))
        ty = input_box_rect.centery - txt.get_height() // 2
        screen.blit(txt, (input_box_rect.x + 10, ty))

    # Warning
    if show_warning:
        pixel_text(screen, "Username cannot be empty!", 1, (200, 60, 60),
                   WIDTH // 2, input_box_rect.bottom + 6)

    draw_pixel_button(screen, confirm_btn_rect, "Confirm", confirm_hovered)


# Forest level tile colours
SKY_TOP    = (80,  140, 230)
SKY_BOT    = (160, 210, 255)
GRASS_DARK = (55,  130, 30)
GRASS_MID  = (75,  160, 40)
GRASS_LITE = (100, 185, 55)
DIRT_DARK  = (100, 68,  40)
DIRT_MID   = (120, 85,  52)
DIRT_LITE  = (140, 102, 62)

TILE = 32
GROUND_ROW = (HEIGHT // TILE) - 4  # tile row where grass starts

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
grass_tile = pygame.transform.scale(
    pygame.image.load(os.path.join(ASSETS_DIR, "grass.png")), (TILE, TILE))
grass_dirt_tile = pygame.transform.scale(
    pygame.image.load(os.path.join(ASSETS_DIR, "grass_to_dirt_transition.png")), (TILE, TILE))
dirt_tile = pygame.transform.scale(
    pygame.image.load(os.path.join(ASSETS_DIR, "dirt.png")), (TILE, TILE))

_spike_raw = pygame.image.load(os.path.join(ASSETS_DIR, "spikes.png")).convert_alpha()

# Background tree sprites
_leaves_raw = pygame.image.load(os.path.join(ASSETS_DIR, "leaves.png")).convert_alpha()
_wood_raw   = pygame.image.load(os.path.join(ASSETS_DIR, "wood.png")).convert_alpha()

COIN_SIZE = 20
_coin_raw = pygame.image.load(os.path.join(ASSETS_DIR, "coin.png")).convert_alpha()
_coin_raw = pygame.transform.scale(_coin_raw, (COIN_SIZE, COIN_SIZE))
_coin_raw.set_colorkey((255, 255, 255))  # remove white pixels
coin_img = _coin_raw

# Fireball sprite
FIREBALL_SIZE = 24
_fireball_raw = pygame.image.load(os.path.join(ASSETS_DIR, "fireball.png")).convert_alpha()
fireball_img = pygame.transform.scale(_fireball_raw, (FIREBALL_SIZE, FIREBALL_SIZE))
fireball_img.set_colorkey((255, 255, 255))
fireball_img_left = pygame.transform.flip(fireball_img, True, False)
ABILITY_ICON_SIZE = 38
fireball_icon = pygame.transform.scale(_fireball_raw, (ABILITY_ICON_SIZE, ABILITY_ICON_SIZE))
fireball_icon.set_colorkey((255, 255, 255))

# Player
PLAYER_W, PLAYER_H = 28, 44
PLAYER_SPEED = 2              # sprint speed (pixels/frame)
WALK_SPEED   = 1.07           # walk speed (~2 tiles/sec at 60fps)
JUMP_FORCE   = -13
GRAVITY      = 0.55
PLAYER_COLOR   = (220, 100, 50)
PLAYER_OUTLINE = (140, 55, 15)
GROUND_Y = GROUND_ROW * TILE - PLAYER_H   # y when standing on ground

player_x  = TILE                           # start at left
player_y  = GROUND_Y
player_vy = 0.0                            # vertical velocity
player_dead = False
player_on_ground = False                   # True when standing on ground or platform
player_health = 100                        # health percentage (0-100)
player_energy = 100.0                     # energy percentage (0-100)
player_sprinting = False
camera_x  = 0                              # horizontal scroll offset
player_facing = 1                          # 1 = right, -1 = left

# ── Fireball ability ──────────────────────────────────────────────────────
FIREBALL_SPEED     = 6
FIREBALL_DAMAGE    = 2
FIREBALL_COOLDOWN  = 7.5            # seconds
fireball_cooldown_remaining = 0.0
fireballs = []

# ── Wall of Fire ability ─────────────────────────────────────────────────
WALL_FIRE_WIDTH    = 5 * TILE       # 160px
WALL_FIRE_HEIGHT   = 2 * TILE       # 64px
WALL_FIRE_OFFSET   = 5 * TILE       # placed 5 tiles right of player
WALL_FIRE_DURATION = 3.0            # seconds
WALL_FIRE_COOLDOWN = 10.0           # seconds
WALL_FIRE_DAMAGE   = 2
WALL_FIRE_COLOR    = (255, 100, 20)
WALL_FIRE_COLOR2   = (255, 180, 40)
wall_fire_cooldown_remaining = 0.0
wall_of_fire = None                 # None or {"x", "y", "timer"} dict

# ── Enemy dimensions (needed before level data load) ─────────────────────
MONKEY_W, MONKEY_H = 24, 36
GORILLA_W, GORILLA_H = 32, 44
BOSS_W = 3 * TILE
BOSS_H = 6 * TILE

# ── Load forest level data from JSON ─────────────────────────────────────
FOREST_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels", "forest.json")
FINISH_COLOR = (240, 220, 50)  # yellow

def _make_faded(surface, alpha):
    s = surface.copy()
    s.set_alpha(alpha)
    return s

def load_forest_data():
    """Load forest level layout from forest.json and build all derived data."""
    global LEVEL_WIDTH, PLATFORMS, platform_rects, GAP_COLS, PIT_COLS
    global SPIKE_W, SPIKE_H, spike_img, spikes
    global FINISH_X, FINISH_W, FINISH_H, FINISH_Y
    global MONKEY_SPAWN_POSITIONS, GORILLA_SPAWNS
    global BOSS_ARENA_LEFT, BOSS_ARENA_RIGHT, BOSS_SPEED, BOSS_MAX_HP, BOSS_TURN_MARGIN, BOSS_SPAWN_OFFSET
    global _bg_foliage_front, _bg_foliage_far
    global _wood_tile, _leaves_1x1, _wood_tile_far, _leaves_1x1_far

    with open(FOREST_JSON_PATH, "r") as f:
        data = json.load(f)

    # Level dimensions
    LEVEL_WIDTH = data["level_width_tiles"] * TILE

    # Platforms
    PLATFORMS = [tuple(p) for p in data["platforms"]]
    platform_rects = []
    for pcol, pw, poff in PLATFORMS:
        px = pcol * TILE
        py = (GROUND_ROW - poff) * TILE
        platform_rects.append(pygame.Rect(px, py, pw * TILE, TILE))

    # Gaps and pits
    GAP_COLS = [tuple(g) for g in data["gap_cols"]]
    PIT_COLS = [tuple(p) for p in data["pit_cols"]]

    # Spikes
    SPIKE_W, SPIKE_H = data["spike_size"]
    spike_img = pygame.transform.scale(_spike_raw, (SPIKE_W, SPIKE_H))
    spikes = []
    for gap_start, gap_end in GAP_COLS:
        gap_pixel_x = gap_start * TILE
        gap_pixel_w = (gap_end - gap_start + 1) * TILE
        num = max(1, gap_pixel_w // (SPIKE_W + 4))
        total_w = num * SPIKE_W
        margin = (gap_pixel_w - total_w) // 2
        for i in range(num):
            spikes.append(pygame.Rect(gap_pixel_x + margin + i * SPIKE_W,
                                      GROUND_ROW * TILE - SPIKE_H, SPIKE_W, SPIKE_H))
    for pit_start, pit_end in PIT_COLS:
        pit_pixel_x = pit_start * TILE
        pit_pixel_w = (pit_end - pit_start + 1) * TILE
        num = max(1, pit_pixel_w // (SPIKE_W + 4))
        total_w = num * SPIKE_W
        margin = (pit_pixel_w - total_w) // 2
        for i in range(num):
            spikes.append(pygame.Rect(pit_pixel_x + margin + i * SPIKE_W,
                                      (GROUND_ROW + 3) * TILE - SPIKE_H, SPIKE_W, SPIKE_H))

    # Finish zone
    fin = data["finish"]
    FINISH_W = fin["width_tiles"] * TILE
    FINISH_H = fin["height_tiles"] * TILE
    FINISH_X = LEVEL_WIDTH - fin["offset_from_right_tiles"] * TILE
    FINISH_Y = GROUND_ROW * TILE - FINISH_H

    # Monkey spawn positions
    MONKEY_SPAWN_POSITIONS = []
    for entry in data["monkeys"]:
        col, y_ref = entry[0], entry[1]
        mx = col * TILE
        if y_ref == "ground":
            my = GROUND_ROW * TILE - MONKEY_H
        else:
            my = (GROUND_ROW - y_ref) * TILE - MONKEY_H
        MONKEY_SPAWN_POSITIONS.append((mx, my))

    # Gorilla spawns
    GORILLA_SPAWNS = []
    for entry in data["gorillas"]:
        col, patrol_tiles, y_ref = entry[0], entry[1], entry[2]
        gx = col * TILE
        if y_ref == "ground":
            gy = GROUND_ROW * TILE - GORILLA_H
        else:
            gy = (GROUND_ROW - y_ref) * TILE - GORILLA_H
        GORILLA_SPAWNS.append((gx, patrol_tiles, gy))

    # Boss
    boss_data = data["boss"]
    BOSS_ARENA_LEFT = boss_data["arena_left_col"] * TILE
    BOSS_ARENA_RIGHT = LEVEL_WIDTH - BOSS_W
    BOSS_SPEED = boss_data["speed_tiles_per_sec"] * TILE / 60.0
    BOSS_MAX_HP = boss_data["hp"]
    BOSS_TURN_MARGIN = boss_data["turn_margin_tiles"] * TILE
    BOSS_SPAWN_OFFSET = boss_data["spawn_offset_tiles"] * TILE

    # Foliage
    front_alpha = data.get("foliage_front_alpha", 170)
    far_alpha = data.get("foliage_far_alpha", 90)
    _bg_foliage_front = [{"x": e[0] * TILE, "trunk_h": e[1], "canopy_w": e[2], "canopy_h": e[3]}
                         for e in data.get("foliage_front", [])]
    _bg_foliage_far = [{"x": e[0] * TILE, "trunk_h": e[1], "canopy_w": e[2], "canopy_h": e[3]}
                       for e in data.get("foliage_far", [])]
    _wood_tile = _make_faded(pygame.transform.scale(_wood_raw, (TILE, TILE)), front_alpha)
    _leaves_1x1 = _make_faded(pygame.transform.scale(_leaves_raw, (TILE, TILE)), front_alpha)
    _wood_tile_far = _make_faded(pygame.transform.scale(_wood_raw, (TILE, TILE)), far_alpha)
    _leaves_1x1_far = _make_faded(pygame.transform.scale(_leaves_raw, (TILE, TILE)), far_alpha)

load_forest_data()

# ── Coins ─────────────────────────────────────────────────────────────────
# Place coins in the air between platform jumps
def generate_coins():
    coins = []
    for i in range(len(PLATFORMS) - 1):
        col1, w1, off1 = PLATFORMS[i]
        col2, w2, off2 = PLATFORMS[i + 1]
        # Gap between end of platform i and start of platform i+1
        gap_start_x = (col1 + w1) * TILE
        gap_end_x = col2 * TILE
        if gap_end_x - gap_start_x < 2 * TILE:
            continue  # skip if platforms are too close
        mid_x = (gap_start_x + gap_end_x) // 2
        higher_off = max(off1, off2)
        cy = (GROUND_ROW - higher_off) * TILE - TILE - 20
        coins.append({"x": mid_x - COIN_SIZE // 2 - 16, "y": cy, "collected": False})
    return coins

coins = generate_coins()
coins[-1]["x"] += 20  # shift last coin (high plat → monkeys plat) right

# ── Monkey enemies ────────────────────────────────────────────────────────
MONKEY_COLOR   = (200, 50, 50)
MONKEY_OUTLINE = (120, 20, 20)

BANANA_RADIUS = 5
BANANA_COLOR  = (255, 220, 50)
BANANA_SPEED  = 3
BANANA_THROW_INTERVAL = 180

def init_monkeys():
    monkeys = []
    for mx, my in MONKEY_SPAWN_POSITIONS:
        monkeys.append({
            "x": mx, "y": my, "alive": True,
            "throw_timer": BANANA_THROW_INTERVAL,
        })
    return monkeys

monkeys = init_monkeys()
bananas = []

# ── Gorilla enemies ──────────────────────────────────────────────────────
GORILLA_COLOR   = (30, 30, 30)
GORILLA_OUTLINE = (80, 80, 80)
GORILLA_SPEED   = 1.5
GORILLA_MAX_HP  = 3

def init_gorillas():
    gorillas = []
    for gx, patrol_tiles, gy in GORILLA_SPAWNS:
        gorillas.append({
            "x": float(gx),
            "y": gy,
            "patrol_left": gx,
            "patrol_right": gx + patrol_tiles * TILE - GORILLA_W,
            "vx": GORILLA_SPEED,
            "hp": GORILLA_MAX_HP,
            "hit": False,  # True after first stomp (shows health bar)
            "alive": True,
        })
    return gorillas

gorillas = init_gorillas()

# ── Great Ape Boss ────────────────────────────────────────────────────────
BOSS_COLOR = (120, 70, 30)
BOSS_OUTLINE = (80, 45, 15)

def init_boss():
    return {
        "x": float(BOSS_ARENA_LEFT + BOSS_SPAWN_OFFSET),
        "y": GROUND_ROW * TILE - BOSS_H,
        "vx": BOSS_SPEED,
        "hp": BOSS_MAX_HP,
        "hit": False,
        "alive": True,
    }

boss = init_boss()


def draw_forest_level(mouse_pos=(0, 0)):
    cx = camera_x  # local alias

    # Sky gradient (not scrolled)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Background foliage — two layers for depth
    ground_px = GROUND_ROW * TILE
    # Far layer first (most faded, appears furthest away)
    for tree in _bg_foliage_far:
        tx = int(tree["x"] - cx)
        canopy_total_w = tree["canopy_w"] * TILE
        if tx + canopy_total_w < -TILE or tx - canopy_total_w > WIDTH + TILE:
            continue
        trunk_base_y = ground_px
        for t_row in range(tree["trunk_h"]):
            screen.blit(_wood_tile_far, (tx, trunk_base_y - (t_row + 1) * TILE))
        canopy_bottom = trunk_base_y - tree["trunk_h"] * TILE
        canopy_left = tx + TILE // 2 - (tree["canopy_w"] * TILE) // 2
        for cr in range(tree["canopy_h"]):
            for cc in range(tree["canopy_w"]):
                screen.blit(_leaves_1x1_far, (canopy_left + cc * TILE, canopy_bottom - (cr + 1) * TILE))
    # Front layer (less faded, appears closer)
    for tree in _bg_foliage_front:
        tx = int(tree["x"] - cx)
        canopy_total_w = tree["canopy_w"] * TILE
        if tx + canopy_total_w < -TILE or tx - canopy_total_w > WIDTH + TILE:
            continue
        trunk_base_y = ground_px
        for t_row in range(tree["trunk_h"]):
            screen.blit(_wood_tile, (tx, trunk_base_y - (t_row + 1) * TILE))
        canopy_bottom = trunk_base_y - tree["trunk_h"] * TILE
        canopy_left = tx + TILE // 2 - (tree["canopy_w"] * TILE) // 2
        for cr in range(tree["canopy_h"]):
            for cc in range(tree["canopy_w"]):
                screen.blit(_leaves_1x1, (canopy_left + cc * TILE, canopy_bottom - (cr + 1) * TILE))

    # Figure out which tile columns are visible
    first_col = int(max(0, cx // TILE))
    last_col = int((cx + WIDTH) // TILE + 1)
    total_cols = LEVEL_WIDTH // TILE

    # Ground tiles — full level width, only draw visible
    # Extend rows enough to always cover the screen bottom
    ground_rows_needed = (HEIGHT // TILE) + 2
    for row in range(GROUND_ROW, GROUND_ROW + ground_rows_needed):
        for col in range(first_col, min(last_col, total_cols)):
            world_x = col * TILE
            sx = world_x - cx
            y = row * TILE            # Check if this column is a sunken pit
            in_pit = False
            for pit_s, pit_e in PIT_COLS:
                if pit_s <= col <= pit_e:
                    in_pit = True
                    break
            if in_pit:
                # Only draw bottom 2 dirt rows
                if row >= GROUND_ROW + 3:
                    screen.blit(dirt_tile, (sx, y))
                continue
            # Check if this column is under a platform
            under_platform = False
            for prect in platform_rects:
                if prect.x <= world_x < prect.right:
                    under_platform = True
                    break
            if under_platform:
                screen.blit(dirt_tile, (sx, y))
            elif row <= GROUND_ROW + 1:
                screen.blit(grass_tile, (sx, y))
            elif row == GROUND_ROW + 2:
                screen.blit(grass_dirt_tile, (sx, y))
            else:
                screen.blit(dirt_tile, (sx, y))

    # Platforms — grass on top, transition below, then dirt down to ground
    for prect in platform_rects:
        for i in range(prect.width // TILE):
            tx = prect.x + i * TILE - cx
            screen.blit(grass_tile, (tx, prect.y))
            screen.blit(grass_dirt_tile, (tx, prect.y + TILE))
            for fill_y in range(prect.y + 2 * TILE, GROUND_ROW * TILE, TILE):
                screen.blit(dirt_tile, (tx, fill_y))

    # Spikes
    for sp in spikes:
        screen.blit(spike_img, (sp.x - cx, sp.y))

    # Finish zone
    fz_sx = int(FINISH_X - cx)
    if -FINISH_W < fz_sx < WIDTH:
        fz_surf = pygame.Surface((FINISH_W, FINISH_H), pygame.SRCALPHA)
        pulse = int(180 + 50 * math.sin(pygame.time.get_ticks() * 0.005))
        fz_surf.fill((*FINISH_COLOR, min(255, pulse)))
        screen.blit(fz_surf, (fz_sx, FINISH_Y))
        pygame.draw.rect(screen, BLACK, (fz_sx, FINISH_Y, FINISH_W, FINISH_H), 2)

    # Coins
    for coin in coins:
        if not coin["collected"]:
            screen.blit(coin_img, (coin["x"] - cx, coin["y"]))

    # Player rectangle
    pygame.draw.rect(screen, PLAYER_COLOR,   (player_x - cx, player_y, PLAYER_W, PLAYER_H))
    pygame.draw.rect(screen, PLAYER_OUTLINE, (player_x - cx, player_y, PLAYER_W, PLAYER_H), 3)

    # Monkeys
    for monkey in monkeys:
        if not monkey["alive"]:
            continue
        mx = monkey["x"] - cx
        my = monkey["y"]
        pygame.draw.rect(screen, MONKEY_COLOR,   (mx, my, MONKEY_W, MONKEY_H))
        pygame.draw.rect(screen, MONKEY_OUTLINE, (mx, my, MONKEY_W, MONKEY_H), 3)

    # Bananas
    for banana in bananas:
        bx = int(banana["x"] - cx)
        by = int(banana["y"])
        pygame.draw.circle(screen, BANANA_COLOR, (bx, by), BANANA_RADIUS)
        pygame.draw.circle(screen, BLACK, (bx, by), BANANA_RADIUS, 1)

    # Fireballs
    for fb in fireballs:
        fbx = int(fb["x"] - cx)
        fby = int(fb["y"])
        if fb["vx"] >= 0:
            screen.blit(fireball_img, (fbx, fby))
        else:
            screen.blit(fireball_img_left, (fbx, fby))

    # Gorillas
    for gorilla in gorillas:
        if not gorilla["alive"]:
            continue
        gx = int(gorilla["x"] - cx)
        gy = int(gorilla["y"])
        pygame.draw.rect(screen, GORILLA_COLOR,   (gx, gy, GORILLA_W, GORILLA_H))
        pygame.draw.rect(screen, GORILLA_OUTLINE, (gx, gy, GORILLA_W, GORILLA_H), 3)
        # Health bar above head (only after first hit)
        if gorilla["hit"] and gorilla["hp"] > 0:
            ghb_w = GORILLA_W
            ghb_h = 4
            ghb_x = gx
            ghb_y = gy - 8
            fill = int(ghb_w * gorilla["hp"] / GORILLA_MAX_HP)
            pygame.draw.rect(screen, DARK_GREY, (ghb_x, ghb_y, ghb_w, ghb_h))
            pygame.draw.rect(screen, (220, 50, 50), (ghb_x, ghb_y, fill, ghb_h))
            pygame.draw.rect(screen, BLACK, (ghb_x, ghb_y, ghb_w, ghb_h), 1)

    # Wall of Fire
    if wall_of_fire is not None:
        wf_sx = int(wall_of_fire["x"] - cx)
        wf_sy = int(wall_of_fire["y"])
        wf_alpha = int(180 + 40 * math.sin(pygame.time.get_ticks() * 0.01))
        wf_surf = pygame.Surface((WALL_FIRE_WIDTH, WALL_FIRE_HEIGHT), pygame.SRCALPHA)
        wf_surf.fill((*WALL_FIRE_COLOR, min(255, wf_alpha)))
        inner_margin = 8
        pygame.draw.rect(wf_surf, (*WALL_FIRE_COLOR2, min(255, max(0, wf_alpha - 30))),
                         (inner_margin, inner_margin,
                          WALL_FIRE_WIDTH - 2 * inner_margin,
                          WALL_FIRE_HEIGHT - 2 * inner_margin))
        screen.blit(wf_surf, (wf_sx, wf_sy))
        pygame.draw.rect(screen, BLACK, (wf_sx, wf_sy, WALL_FIRE_WIDTH, WALL_FIRE_HEIGHT), 2)

    # Great Ape Boss
    if boss["alive"]:
        bx = int(boss["x"] - cx)
        by = int(boss["y"])
        pygame.draw.rect(screen, BOSS_COLOR,   (bx, by, BOSS_W, BOSS_H))
        pygame.draw.rect(screen, BOSS_OUTLINE, (bx, by, BOSS_W, BOSS_H), 3)
        # Health bar above head (only after first hit)
        if boss["hit"] and boss["hp"] > 0:
            bhb_w = BOSS_W
            bhb_h = 6
            bhb_x = bx
            bhb_y = by - 10
            fill = int(bhb_w * boss["hp"] / BOSS_MAX_HP)
            pygame.draw.rect(screen, DARK_GREY, (bhb_x, bhb_y, bhb_w, bhb_h))
            pygame.draw.rect(screen, (220, 50, 50), (bhb_x, bhb_y, fill, bhb_h))
            pygame.draw.rect(screen, BLACK, (bhb_x, bhb_y, bhb_w, bhb_h), 1)

    # HUD — top right: player icon + unified status box
    HUD_PAD = 6
    HUD_Y = 6
    ICON_W, ICON_H = 16, 24
    HB_W, HB_H = 100, 12
    ROW_GAP = 6
    YELLOW = (230, 210, 40)
    hp_label = pixel_font_small.render("Health:", False, WHITE)
    hp_pct = pixel_font_small.render(str(max(0, player_health)) + "%", False, WHITE)
    en_label = pixel_font_small.render("Energy:", False, WHITE)
    en_pct = pixel_font_small.render(str(int(player_energy)) + "%", False, WHITE)
    coins_collected = sum(1 for c in coins if c["collected"])
    coin_label = pixel_font_small.render("Coins: " + str(coins_collected), False, WHITE)
    label_w = max(hp_label.get_width(), en_label.get_width())
    row_h = max(hp_label.get_height(), HB_H)
    box_w = HUD_PAD + label_w + 6 + HB_W + 6 + max(hp_pct.get_width(), en_pct.get_width()) + HUD_PAD
    box_h = HUD_PAD + row_h + ROW_GAP + row_h + ROW_GAP + row_h + HUD_PAD
    box_x = WIDTH - box_w - ICON_W - HUD_PAD * 2 - 8
    # Player icon
    icon_x = box_x - ICON_W - HUD_PAD
    icon_y = HUD_Y + (box_h - ICON_H) // 2
    pygame.draw.rect(screen, PLAYER_COLOR, (icon_x, icon_y, ICON_W, ICON_H))
    pygame.draw.rect(screen, PLAYER_OUTLINE, (icon_x, icon_y, ICON_W, ICON_H), 2)
    # Black box
    pygame.draw.rect(screen, BLACK, (box_x, HUD_Y, box_w, box_h))
    pygame.draw.rect(screen, WHITE, (box_x, HUD_Y, box_w, box_h), 1)
    # Health row
    row1_y = HUD_Y + HUD_PAD
    lx = box_x + HUD_PAD
    screen.blit(hp_label, (lx, row1_y + row_h // 2 - hp_label.get_height() // 2))
    bar_x = lx + label_w + 6
    bar_y = row1_y + row_h // 2 - HB_H // 2
    fill_w = int(HB_W * max(0, player_health) / 100)
    pygame.draw.rect(screen, DARK_GREY, (bar_x, bar_y, HB_W, HB_H))
    if fill_w > 0:
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, fill_w, HB_H))
    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, HB_W, HB_H), 1)
    screen.blit(hp_pct, (bar_x + HB_W + 6, row1_y + row_h // 2 - hp_pct.get_height() // 2))
    # Energy row
    row2_y = row1_y + row_h + ROW_GAP
    screen.blit(en_label, (lx, row2_y + row_h // 2 - en_label.get_height() // 2))
    ebar_y = row2_y + row_h // 2 - HB_H // 2
    efill_w = int(HB_W * max(0, player_energy) / 100)
    pygame.draw.rect(screen, DARK_GREY, (bar_x, ebar_y, HB_W, HB_H))
    if efill_w > 0:
        pygame.draw.rect(screen, YELLOW, (bar_x, ebar_y, efill_w, HB_H))
    pygame.draw.rect(screen, WHITE, (bar_x, ebar_y, HB_W, HB_H), 1)
    screen.blit(en_pct, (bar_x + HB_W + 6, row2_y + row_h // 2 - en_pct.get_height() // 2))
    # Coins row
    row3_y = row2_y + row_h + ROW_GAP
    screen.blit(coin_label, (lx, row3_y + row_h // 2 - coin_label.get_height() // 2))

    # Pause button — top left
    pb_hovered = pause_btn_rect.collidepoint(mouse_pos)
    pb_color = DARK_GREEN if pb_hovered else GREEN
    pts = pixel_round_rect_points(pause_btn_rect, step=6)
    pygame.draw.polygon(screen, pb_color, pts)
    for i in range(len(pts)):
        pygame.draw.line(screen, BLACK, pts[i], pts[(i + 1) % len(pts)], 3)
    # Two vertical bars for pause icon
    bar_w, bar_h = 6, 16
    bx = pause_btn_rect.x
    by = pause_btn_rect.y
    bsz = PAUSE_BTN_SIZE
    pygame.draw.rect(screen, BLACK, (bx + bsz // 2 - bar_w - 2, by + (bsz - bar_h) // 2, bar_w, bar_h))
    pygame.draw.rect(screen, BLACK, (bx + bsz // 2 + 2, by + (bsz - bar_h) // 2, bar_w, bar_h))

    # Ability HUD buttons — bottom-right
    # Fireball button
    fb_pts = pixel_round_rect_points(ability_fireball_rect, step=6)
    pygame.draw.polygon(screen, GREEN, fb_pts)
    for i in range(len(fb_pts)):
        pygame.draw.line(screen, BLACK, fb_pts[i], fb_pts[(i + 1) % len(fb_pts)], 3)
    icon_x = ability_fireball_rect.centerx - ABILITY_ICON_SIZE // 2
    icon_y = ability_fireball_rect.centery - ABILITY_ICON_SIZE // 2
    screen.blit(fireball_icon, (icon_x, icon_y))
    # Fireball cooldown overlay
    if fireball_cooldown_remaining > 0:
        cd_frac = fireball_cooldown_remaining / FIREBALL_COOLDOWN
        overlay_h = int(ABILITY_BTN_SIZE * cd_frac)
        if overlay_h > 0:
            cd_surf = pygame.Surface((ABILITY_BTN_SIZE, overlay_h), pygame.SRCALPHA)
            cd_surf.fill((0, 0, 0, 153))
            screen.blit(cd_surf, (ability_fireball_rect.x, ability_fireball_rect.y))

    # Wall of Fire button (blank for now)
    wf_pts = pixel_round_rect_points(ability_wallfire_rect, step=6)
    pygame.draw.polygon(screen, GREEN, wf_pts)
    for i in range(len(wf_pts)):
        pygame.draw.line(screen, BLACK, wf_pts[i], wf_pts[(i + 1) % len(wf_pts)], 3)
    # Wall of Fire cooldown overlay
    if wall_fire_cooldown_remaining > 0:
        cd_frac = wall_fire_cooldown_remaining / WALL_FIRE_COOLDOWN
        overlay_h = int(ABILITY_BTN_SIZE * cd_frac)
        if overlay_h > 0:
            cd_surf = pygame.Surface((ABILITY_BTN_SIZE, overlay_h), pygame.SRCALPHA)
            cd_surf.fill((0, 0, 0, 153))
            screen.blit(cd_surf, (ability_wallfire_rect.x, ability_wallfire_rect.y))

SETTINGS_LEFT_W  = 300
SETTINGS_RIGHT_W = WIDTH - SETTINGS_LEFT_W

CATEGORIES   = ["Audio", "Accessibility", "Performance", "Account"]
CAT_Y_START  = 128
CAT_SPACING  = 35

SLIDER_W = 210
SLIDER_H = 8
SLIDER_X = SETTINGS_LEFT_W + 120
SLIDER_Y = 90

# Username change modal
MODAL_W, MODAL_H     = 390, 330
modal_rect           = pygame.Rect(WIDTH // 2 - 195, HEIGHT // 2 - 165, MODAL_W, MODAL_H)
MODAL_INPUT_W        = 330
modal_input_rect     = pygame.Rect(WIDTH // 2 - MODAL_INPUT_W // 2, modal_rect.y + 150, MODAL_INPUT_W, 40)
MODAL_BTN_W, MODAL_BTN_H = 145, 55
modal_confirm_rect   = pygame.Rect(modal_rect.right - MODAL_BTN_W - 15,
                                   modal_rect.bottom - MODAL_BTN_H - 15, MODAL_BTN_W, MODAL_BTN_H)
modal_cancel_rect    = pygame.Rect(modal_rect.left + 15,
                                   modal_rect.bottom - MODAL_BTN_H - 15, MODAL_BTN_W, MODAL_BTN_H)

# Accessibility — display mode toggle
DISPLAY_TOGGLE_X = SETTINGS_LEFT_W + 160
DISPLAY_TOGGLE_Y = 84
DISPLAY_TOGGLE_W = 120
DISPLAY_TOGGLE_H = 26
display_toggle_rect = pygame.Rect(DISPLAY_TOGGLE_X, DISPLAY_TOGGLE_Y, DISPLAY_TOGGLE_W, DISPLAY_TOGGLE_H)

# Account settings username box
username_box_rect = pygame.Rect(SETTINGS_LEFT_W + 145, 82, 180, 28)

# Delete account button — bottom of account panel
DEL_BTN_W, DEL_BTN_H = 300, 55
delete_account_btn_rect = pygame.Rect(
    SETTINGS_LEFT_W + (WIDTH - SETTINGS_LEFT_W) // 2 - DEL_BTN_W // 2,
    HEIGHT - DEL_BTN_H - 30, DEL_BTN_W, DEL_BTN_H)

# Delete account confirmation modal
DEL_MODAL_W, DEL_MODAL_H = 520, 240
del_modal_rect = pygame.Rect(WIDTH // 2 - DEL_MODAL_W // 2, HEIGHT // 2 - DEL_MODAL_H // 2,
                              DEL_MODAL_W, DEL_MODAL_H)
del_no_rect  = pygame.Rect(del_modal_rect.x + 25,
                            del_modal_rect.bottom - MODAL_BTN_H - 20, MODAL_BTN_W, MODAL_BTN_H)
del_yes_rect = pygame.Rect(del_modal_rect.right - MODAL_BTN_W - 25,
                            del_modal_rect.bottom - MODAL_BTN_H - 20, MODAL_BTN_W, MODAL_BTN_H)

# Performance settings VSync toggle box
vsync_box_rect = pygame.Rect(SETTINGS_LEFT_W + 120, 82, 52, 28)

# Performance settings Max FPS slider (same dimensions as volume slider, one row below VSync)
FPS_SLIDER_X = SLIDER_X
FPS_SLIDER_Y = 130
FPS_MIN = 10
FPS_MAX = 1000

# Performance settings Alloted RAM slider
RAM_SLIDER_X = SETTINGS_LEFT_W + 180
RAM_SLIDER_Y = 170
RAM_MIN = 1
class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
_memstat = _MEMORYSTATUSEX()
_memstat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(_memstat))
RAM_MAX = max(1, round(_memstat.ullTotalPhys / (1024 ** 3)))

def draw_settings(mouse_pos):
    screen.fill(GREY)

    # Left panel — 85% opacity black
    left_panel = pygame.Surface((SETTINGS_LEFT_W, HEIGHT), pygame.SRCALPHA)
    left_panel.fill((0, 0, 0, 216))
    screen.blit(left_panel, (0, 0))

    # Right panel — 60% opacity black
    right_panel = pygame.Surface((SETTINGS_RIGHT_W, HEIGHT), pygame.SRCALPHA)
    right_panel.fill((0, 0, 0, 153))
    screen.blit(right_panel, (SETTINGS_LEFT_W, 0))

    # Divider line — fully opaque white
    pygame.draw.line(screen, WHITE, (SETTINGS_LEFT_W, 0), (SETTINGS_LEFT_W, HEIGHT), 2)

    # Close button — top left
    draw_cross_button(screen, cross_btn_rect, cross_btn_rect.collidepoint(mouse_pos))

    # ── LEFT PANEL ────────────────────────────────────────────────────────────
    pixel_text(screen, "Settings", 2, WHITE, SETTINGS_LEFT_W // 2, 73)
    pygame.draw.line(screen, WHITE, (8, 113), (SETTINGS_LEFT_W - 8, 113), 1)

    for i, cat in enumerate(CATEGORIES):
        cat_y = CAT_Y_START + i * CAT_SPACING
        is_selected = settings_category == cat.lower()
        if is_selected:
            hl = pygame.Surface((SETTINGS_LEFT_W, 28), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 45))
            screen.blit(hl, (0, cat_y - 5))
        color = LIGHT_GREEN if is_selected else WHITE
        pixel_text(screen, cat, 1, color, SETTINGS_LEFT_W // 2, cat_y)

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────
    rcx = SETTINGS_LEFT_W + SETTINGS_RIGHT_W // 2

    if settings_category == "audio":
        pixel_text(screen, "Audio Settings", 2, WHITE, rcx, 15)
        pygame.draw.line(screen, WHITE,
                         (SETTINGS_LEFT_W + 12, 57), (WIDTH - 12, 57), 1)

        # Volume row
        pixel_text(screen, "Volume", 1, WHITE, SETTINGS_LEFT_W + 55, 86)

        # Track
        pygame.draw.rect(screen, DARK_GREY, (SLIDER_X, SLIDER_Y, SLIDER_W, SLIDER_H))
        fill_w = int(master_volume * SLIDER_W)
        if fill_w > 0:
            pygame.draw.rect(screen, GREEN, (SLIDER_X, SLIDER_Y, fill_w, SLIDER_H))
        pygame.draw.rect(screen, BLACK, (SLIDER_X, SLIDER_Y, SLIDER_W, SLIDER_H), 2)
        # Handle
        hx = SLIDER_X + fill_w
        pygame.draw.rect(screen, WHITE, (hx - 5, SLIDER_Y - 7, 10, SLIDER_H + 14))
        pygame.draw.rect(screen, BLACK, (hx - 5, SLIDER_Y - 7, 10, SLIDER_H + 14), 2)
        # Percentage
        pixel_text(screen, str(int(master_volume * 100)) + "%", 1, WHITE,
                   SLIDER_X + SLIDER_W + 32, 86)

    elif settings_category == "accessibility":
        pixel_text(screen, "Accessibility Settings", 2, WHITE, rcx, 15)
        pygame.draw.line(screen, WHITE,
                         (SETTINGS_LEFT_W + 12, 57), (WIDTH - 12, 57), 1)

        # Display mode row
        pixel_text(screen, "Display", 1, WHITE, SETTINGS_LEFT_W + 55, 86)
        pygame.draw.rect(screen, BLACK, display_toggle_rect)
        pygame.draw.rect(screen, WHITE, display_toggle_rect, 2)
        raw = pixel_font_small.render(display_mode, False, WHITE)
        tx = display_toggle_rect.centerx - raw.get_width() // 2
        ty = display_toggle_rect.centery - raw.get_height() // 2
        screen.blit(raw, (tx, ty))

    elif settings_category == "performance":
        pixel_text(screen, "Performance Settings", 2, WHITE, rcx, 15)
        pygame.draw.line(screen, WHITE,
                         (SETTINGS_LEFT_W + 12, 57), (WIDTH - 12, 57), 1)

        # VSync row
        pixel_text(screen, "VSync", 1, WHITE, SETTINGS_LEFT_W + 50, 86)
        pygame.draw.rect(screen, BLACK, vsync_box_rect)
        pygame.draw.rect(screen, WHITE, vsync_box_rect, 2)
        label = "On" if vsync_enabled else "Off"
        raw = pixel_font_small.render(label, False, WHITE)
        tx = vsync_box_rect.centerx - raw.get_width() // 2
        ty = vsync_box_rect.centery - raw.get_height() // 2
        screen.blit(raw, (tx, ty))

        # Max FPS row
        pixel_text(screen, "Max FPS", 1, WHITE, SETTINGS_LEFT_W + 62, 126)
        fps_t = (max_fps - FPS_MIN) / (FPS_MAX - FPS_MIN)
        pygame.draw.rect(screen, DARK_GREY, (FPS_SLIDER_X, FPS_SLIDER_Y, SLIDER_W, SLIDER_H))
        fill_w = int(fps_t * SLIDER_W)
        if fill_w > 0:
            pygame.draw.rect(screen, GREEN, (FPS_SLIDER_X, FPS_SLIDER_Y, fill_w, SLIDER_H))
        pygame.draw.rect(screen, BLACK, (FPS_SLIDER_X, FPS_SLIDER_Y, SLIDER_W, SLIDER_H), 2)
        hx = FPS_SLIDER_X + fill_w
        pygame.draw.rect(screen, WHITE, (hx - 5, FPS_SLIDER_Y - 7, 10, SLIDER_H + 14))
        pygame.draw.rect(screen, BLACK, (hx - 5, FPS_SLIDER_Y - 7, 10, SLIDER_H + 14), 2)
        pixel_text(screen, str(max_fps), 1, WHITE,
                   FPS_SLIDER_X + SLIDER_W + 32, 126)

        # Alloted RAM row
        pixel_text(screen, "Alloted RAM", 1, WHITE, SETTINGS_LEFT_W + 80, 166)
        ram_t = (alloted_ram - RAM_MIN) / max(1, RAM_MAX - RAM_MIN)
        pygame.draw.rect(screen, DARK_GREY, (RAM_SLIDER_X, RAM_SLIDER_Y, SLIDER_W, SLIDER_H))
        fill_w = int(ram_t * SLIDER_W)
        if fill_w > 0:
            pygame.draw.rect(screen, GREEN, (RAM_SLIDER_X, RAM_SLIDER_Y, fill_w, SLIDER_H))
        pygame.draw.rect(screen, BLACK, (RAM_SLIDER_X, RAM_SLIDER_Y, SLIDER_W, SLIDER_H), 2)
        hx = RAM_SLIDER_X + fill_w
        pygame.draw.rect(screen, WHITE, (hx - 5, RAM_SLIDER_Y - 7, 10, SLIDER_H + 14))
        pygame.draw.rect(screen, BLACK, (hx - 5, RAM_SLIDER_Y - 7, 10, SLIDER_H + 14), 2)
        pixel_text(screen, str(alloted_ram) + " GB", 1, WHITE,
                   RAM_SLIDER_X + SLIDER_W + 32, 166)

    elif settings_category == "account":
        pixel_text(screen, "Account Settings", 2, WHITE, rcx, 15)
        pygame.draw.line(screen, WHITE,
                         (SETTINGS_LEFT_W + 12, 57), (WIDTH - 12, 57), 1)

        # Username row
        pixel_text(screen, "Username", 1, WHITE, SETTINGS_LEFT_W + 68, 86)
        pygame.draw.rect(screen, BLACK, username_box_rect)
        pygame.draw.rect(screen, WHITE, username_box_rect, 2)
        if profile_username:
            raw = pixel_font_small.render(profile_username, False, WHITE)
            ty = username_box_rect.centery - raw.get_height() // 2
            screen.blit(raw, (username_box_rect.x + 6, ty))

        # Delete account button
        draw_red_button(screen, delete_account_btn_rect, "Delete Account",
                        delete_account_btn_rect.collidepoint(mouse_pos))


def draw_delete_account_modal(mouse_pos):
    # Full-screen dim
    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    screen.blit(dim, (0, 0))

    # Modal box
    pygame.draw.rect(screen, (25, 25, 25), del_modal_rect)
    pygame.draw.rect(screen, WHITE, del_modal_rect, 2)

    # Heading
    pixel_text(screen, "Are you sure you want", 2, WHITE,
               WIDTH // 2, del_modal_rect.y + 20)
    pixel_text(screen, "to delete your account?", 2, WHITE,
               WIDTH // 2, del_modal_rect.y + 55)

    # Warning sub-text
    pixel_text(screen, "All your progress will be lost!", 1, RED,
               WIDTH // 2, del_modal_rect.y + 100)

    # No (green/safe) on left, Yes (red/danger) on right
    draw_pixel_button(screen, del_no_rect, "No",
                      del_no_rect.collidepoint(mouse_pos))
    draw_red_button(screen, del_yes_rect, "Yes",
                    del_yes_rect.collidepoint(mouse_pos))


def draw_username_modal(mouse_pos):
    # Full-screen dim
    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    screen.blit(dim, (0, 0))

    # Modal box
    pygame.draw.rect(screen, (25, 25, 25), modal_rect)
    pygame.draw.rect(screen, WHITE, modal_rect, 2)

    # Current username
    pixel_text(screen, "Current username", 1, DARK_GREY, WIDTH // 2, modal_rect.y + 14)
    if profile_username:
        pixel_text(screen, profile_username, 2, WHITE, WIDTH // 2, modal_rect.y + 36)

    pygame.draw.line(screen, WHITE,
                     (modal_rect.x + 10, modal_rect.y + 75),
                     (modal_rect.right - 10, modal_rect.y + 75), 1)

    # Change username heading
    pixel_text(screen, "Change Username", 2, WHITE, WIDTH // 2, modal_rect.y + 85)

    # Input box
    pygame.draw.rect(screen, BLACK, modal_input_rect)
    pygame.draw.rect(screen, WHITE, modal_input_rect, 2)
    if username_modal_input:
        raw = pixel_font_small.render(username_modal_input, False, WHITE)
    else:
        raw = pixel_font_small.render("type here...", False, DARK_GREY)
    screen.blit(raw, (modal_input_rect.x + 6,
                      modal_input_rect.centery - raw.get_height() // 2))

    # Confirm (green) and Cancel (red) buttons
    draw_pixel_button(screen, modal_confirm_rect, "Confirm",
                      modal_confirm_rect.collidepoint(mouse_pos))
    draw_red_button(screen, modal_cancel_rect, "Cancel",
                    modal_cancel_rect.collidepoint(mouse_pos))


def draw_pause_menu(mouse_pos):
    # Semi-transparent black box
    overlay = pygame.Surface((PAUSE_BOX_W, PAUSE_BOX_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, pause_box_rect.topleft)

    # "Paused" heading — white, top center of box
    pixel_text(screen, "Paused", 3, WHITE, WIDTH // 2, pause_box_rect.y + 22)

    # Buttons
    draw_pixel_button(screen, pause_resume_rect, "Resume",
                      pause_resume_rect.collidepoint(mouse_pos))
    draw_pixel_button(screen, pause_exit_rect, "Exit Level",
                      pause_exit_rect.collidepoint(mouse_pos))


def draw_death_screen(mouse_pos):
    # Full-screen semi-transparent red overlay (60% opacity)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((255, 0, 0, 153))
    screen.blit(overlay, (0, 0))

    # "You Died!" heading
    pixel_text(screen, "You Died!", 3, WHITE, WIDTH // 2, 80)

    # Buttons
    draw_pixel_button(screen, death_retry_rect, "Try Again",
                      death_retry_rect.collidepoint(mouse_pos))
    draw_red_button(screen, death_exit_rect, "Level Select",
                    death_exit_rect.collidepoint(mouse_pos))


def draw_win_screen(mouse_pos):
    # Full-screen semi-transparent black overlay (60% opacity)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 153))
    screen.blit(overlay, (0, 0))

    # "Level Completed!" heading
    pixel_text(screen, "Level Completed!", 3, FINISH_COLOR, WIDTH // 2, 60)

    # Coin breakdown
    coins_collected = sum(1 for c in coins if c["collected"])
    y = pixel_text(screen, "Bonus: +100 coins", 2, WHITE, WIDTH // 2, 140)
    y = pixel_text(screen, "Collected: +" + str(coins_collected) + " coins", 2, WHITE, WIDTH // 2, y + 8)
    pixel_text(screen, "Total: +" + str(win_coins) + " coins", 2, GREEN, WIDTH // 2, y + 8)

    # Buttons
    draw_pixel_button(screen, win_retry_rect, "Play Again",
                      win_retry_rect.collidepoint(mouse_pos))
    draw_pixel_button(screen, win_exit_rect, "Level Select",
                      win_exit_rect.collidepoint(mouse_pos))


# Game states
STATE_HOME           = "home"
STATE_LEVEL_SELECT   = "level_select"
STATE_FOREST         = "forest"
STATE_PAUSED         = "paused"
STATE_SETTINGS       = "settings"
STATE_CREATE_PROFILE = "create_profile"
STATE_DEAD           = "dead"
STATE_WIN            = "win"
state = STATE_CREATE_PROFILE if profile_username is None else STATE_HOME
win_coins = 0  # coins earned on level completion (shown on win screen)

clock = pygame.time.Clock()

username_input       = ""
show_profile_warning = False
settings_category    = "audio"
_saved               = load_settings()
master_volume        = _saved.get("master_volume", 1.0)
vsync_enabled        = _saved.get("vsync_enabled", False)
max_fps              = _saved.get("max_fps", 120)
alloted_ram          = max(RAM_MIN, min(RAM_MAX, _saved.get("alloted_ram", 2)))
DISPLAY_MODES        = ["Off", "Windowed", "Fullscreen"]
display_mode         = _saved.get("display_mode", "Windowed")
click_sound.set_volume(master_volume)
monkey_hit_sound.set_volume(master_volume)
slider_dragging      = False
fps_slider_dragging  = False
ram_slider_dragging  = False
show_username_modal  = False
show_delete_modal    = False
username_modal_input = ""


def map_mouse(raw, disp_w, disp_h):
    """Map display-space mouse coords to 800x600 render-space coords."""
    rx = raw[0] * WIDTH  // max(disp_w, 1)
    ry = raw[1] * HEIGHT // max(disp_h, 1)
    return (rx, ry)


while True:
    dw, dh = display_surf.get_size()
    mouse_pos = map_mouse(pygame.mouse.get_pos(), dw, dh)
    hovered          = btn_rect.collidepoint(mouse_pos)          and state == STATE_HOME
    settings_hovered = settings_btn_rect.collidepoint(mouse_pos) and state == STATE_HOME

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.VIDEORESIZE and not is_fullscreen:
            display_surf = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                # Reset to normal window first
                display_surf = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                hwnd = pygame.display.get_wm_info()["window"]
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    display_mode = "Fullscreen"
                    display_surf = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    display_mode = "Windowed"
                    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                save_settings()
            if show_delete_modal:
                if event.key == pygame.K_ESCAPE:
                    show_delete_modal = False
            elif show_username_modal:
                if event.key == pygame.K_RETURN:
                    if username_modal_input.strip():
                        profile_username = username_modal_input.strip()
                        save_profile(profile_username)
                        click_sound.play()
                    show_username_modal = False
                    username_modal_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    username_modal_input = username_modal_input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    show_username_modal = False
                    username_modal_input = ""
                elif len(username_modal_input) < INPUT_MAX and event.unicode.isprintable():
                    username_modal_input += event.unicode
            elif state == STATE_CREATE_PROFILE:
                if event.key == pygame.K_RETURN:
                    if username_input.strip():
                        profile_username = username_input.strip()
                        save_profile(profile_username)
                        click_sound.play()
                        state = STATE_HOME
                        show_profile_warning = False
                    else:
                        show_profile_warning = True
                elif event.key == pygame.K_BACKSPACE:
                    username_input = username_input[:-1]
                    show_profile_warning = False
                elif len(username_input) < INPUT_MAX and event.unicode.isprintable():
                    username_input += event.unicode
                    show_profile_warning = False
            if event.key == pygame.K_ESCAPE and not show_username_modal and not show_delete_modal:
                if state == STATE_SETTINGS:
                    click_sound.play()
                    state = STATE_HOME
                elif state == STATE_LEVEL_SELECT:
                    click_sound.play()
                    state = STATE_HOME
                elif state == STATE_FOREST:
                    click_sound.play()
                    state = STATE_PAUSED
                elif state == STATE_PAUSED:
                    click_sound.play()
                    state = STATE_FOREST
            if event.key == pygame.K_SPACE and state == STATE_FOREST and player_on_ground:
                player_vy = JUMP_FORCE
            if event.key == pygame.K_r and state == STATE_FOREST and not player_dead:
                if fireball_cooldown_remaining <= 0:
                    fb_x = player_x + (PLAYER_W if player_facing > 0 else -FIREBALL_SIZE)
                    fb_y = player_y + PLAYER_H // 2 - FIREBALL_SIZE // 2
                    fireballs.append({"x": float(fb_x), "y": float(fb_y),
                                      "vx": FIREBALL_SPEED * player_facing})
                    fireball_cooldown_remaining = FIREBALL_COOLDOWN
                    fireball_sound.set_volume(master_volume)
                    fireball_sound.play()
            if event.key == pygame.K_c and state == STATE_FOREST and not player_dead:
                if wall_fire_cooldown_remaining <= 0:
                    if player_x >= BOSS_ARENA_LEFT - 2 * TILE:
                        wf_x = min(player_x + WALL_FIRE_OFFSET,
                                   LEVEL_WIDTH - WALL_FIRE_WIDTH)
                        wf_y = GROUND_ROW * TILE - WALL_FIRE_HEIGHT
                        wall_of_fire = {"x": wf_x, "y": wf_y,
                                        "timer": WALL_FIRE_DURATION}
                        wall_fire_cooldown_remaining = WALL_FIRE_COOLDOWN
                        wall_of_fire_sound.set_volume(master_volume)
                        wall_of_fire_sound.play()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == STATE_CREATE_PROFILE:
                if confirm_btn_rect.collidepoint(mouse_pos):
                    if username_input.strip():
                        profile_username = username_input.strip()
                        save_profile(profile_username)
                        click_sound.play()
                        state = STATE_HOME
                        show_profile_warning = False
                    else:
                        show_profile_warning = True
            elif state == STATE_HOME and hovered:
                click_sound.play()
                state = STATE_LEVEL_SELECT
            elif state == STATE_HOME and settings_hovered:
                click_sound.play()
                state = STATE_SETTINGS
            elif state == STATE_LEVEL_SELECT:
                if cross_btn_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    state = STATE_HOME
                elif card_rect.collidepoint(mouse_pos) and levels[level_index] == "Forest":
                    click_sound.play()
                    player_x      = TILE
                    player_y      = GROUND_Y
                    player_vy     = 0.0
                    player_health = 100
                    player_energy = 100.0
                    camera_x      = 0
                    monkeys       = init_monkeys()
                    gorillas      = init_gorillas()
                    boss          = init_boss()
                    coins         = generate_coins()
                    bananas       = []
                    fireballs     = []
                    wall_of_fire  = None
                    fireball_cooldown_remaining  = 0.0
                    wall_fire_cooldown_remaining = 0.0
                    player_facing = 1
                    state = STATE_FOREST
                elif left_arrow_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    level_index = (level_index - 1) % len(levels)
                elif right_arrow_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    level_index = (level_index + 1) % len(levels)
            elif state == STATE_FOREST:
                if pause_btn_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    state = STATE_PAUSED
            elif state == STATE_PAUSED:
                if pause_resume_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    state = STATE_FOREST
                elif pause_exit_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    state = STATE_LEVEL_SELECT
            elif state == STATE_DEAD:
                if death_retry_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    player_x         = TILE
                    player_y         = GROUND_Y
                    player_vy        = 0.0
                    player_dead      = False
                    player_on_ground = True
                    player_health    = 100
                    player_energy    = 100.0
                    camera_x         = 0
                    monkeys          = init_monkeys()
                    gorillas         = init_gorillas()
                    boss             = init_boss()
                    coins            = generate_coins()
                    bananas          = []
                    fireballs        = []
                    wall_of_fire     = None
                    fireball_cooldown_remaining  = 0.0
                    wall_fire_cooldown_remaining = 0.0
                    player_facing    = 1
                    state = STATE_FOREST
                elif death_exit_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    player_dead = False
                    monkeys     = init_monkeys()
                    gorillas    = init_gorillas()
                    boss        = init_boss()
                    coins       = generate_coins()
                    bananas     = []
                    fireballs   = []
                    wall_of_fire = None
                    fireball_cooldown_remaining  = 0.0
                    wall_fire_cooldown_remaining = 0.0
                    player_facing = 1
                    state = STATE_LEVEL_SELECT
            elif state == STATE_WIN:
                if win_retry_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    player_x         = TILE
                    player_y         = GROUND_Y
                    player_vy        = 0.0
                    player_dead      = False
                    player_on_ground = True
                    player_health    = 100
                    player_energy    = 100.0
                    camera_x         = 0
                    monkeys          = init_monkeys()
                    gorillas         = init_gorillas()
                    boss             = init_boss()
                    coins            = generate_coins()
                    bananas          = []
                    fireballs        = []
                    wall_of_fire     = None
                    fireball_cooldown_remaining  = 0.0
                    wall_fire_cooldown_remaining = 0.0
                    player_facing    = 1
                    state = STATE_FOREST
                elif win_exit_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    monkeys     = init_monkeys()
                    gorillas    = init_gorillas()
                    boss        = init_boss()
                    coins       = generate_coins()
                    bananas     = []
                    fireballs   = []
                    wall_of_fire = None
                    fireball_cooldown_remaining  = 0.0
                    wall_fire_cooldown_remaining = 0.0
                    player_facing = 1
                    state = STATE_LEVEL_SELECT
            elif state == STATE_SETTINGS:
                if show_delete_modal:
                    if del_no_rect.collidepoint(mouse_pos):
                        click_sound.play()
                        show_delete_modal = False
                    elif del_yes_rect.collidepoint(mouse_pos):
                        click_sound.play()
                        if os.path.exists(PROFILE_PATH):
                            os.remove(PROFILE_PATH)
                        if os.path.exists(SETTINGS_PATH):
                            os.remove(SETTINGS_PATH)
                        if os.path.exists(PROGRESS_PATH):
                            os.remove(PROGRESS_PATH)
                        total_coins = 0
                        progress = {"total_coins": 0}
                        profile_username = None
                        username_input = ""
                        show_delete_modal = False
                        state = STATE_CREATE_PROFILE
                elif show_username_modal:
                    if modal_confirm_rect.collidepoint(mouse_pos):
                        if username_modal_input.strip():
                            profile_username = username_modal_input.strip()
                            save_profile(profile_username)
                            click_sound.play()
                        show_username_modal = False
                        username_modal_input = ""
                    elif modal_cancel_rect.collidepoint(mouse_pos):
                        click_sound.play()
                        show_username_modal = False
                        username_modal_input = ""
                else:
                    if cross_btn_rect.collidepoint(mouse_pos):
                        click_sound.play()
                        state = STATE_HOME
                    for i, cat in enumerate(CATEGORIES):
                        cat_y = CAT_Y_START + i * CAT_SPACING
                        if pygame.Rect(0, cat_y - 5, SETTINGS_LEFT_W, 28).collidepoint(mouse_pos):
                            click_sound.play()
                            settings_category = cat.lower()
                            break
                    if settings_category == "accessibility":
                        if display_toggle_rect.collidepoint(mouse_pos):
                            click_sound.play()
                            idx = DISPLAY_MODES.index(display_mode)
                            display_mode = DISPLAY_MODES[(idx + 1) % len(DISPLAY_MODES)]
                            # Always reset to a normal window first
                            display_surf = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                            hwnd = pygame.display.get_wm_info()["window"]
                            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                            if display_mode == "Fullscreen":
                                is_fullscreen = True
                                display_surf = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            elif display_mode == "Windowed":
                                is_fullscreen = False
                                ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                            else:  # Off
                                is_fullscreen = False
                                display_surf = pygame.display.set_mode((WIDTH, HEIGHT))
                            save_settings()
                    elif settings_category == "audio":
                        hit = pygame.Rect(SLIDER_X - 5, SLIDER_Y - 10, SLIDER_W + 10, SLIDER_H + 20)
                        if hit.collidepoint(mouse_pos):
                            slider_dragging = True
                            master_volume = max(0.0, min(1.0,
                                (mouse_pos[0] - SLIDER_X) / SLIDER_W))
                            click_sound.set_volume(master_volume)
                            monkey_hit_sound.set_volume(master_volume)
                    elif settings_category == "performance":
                        if vsync_box_rect.collidepoint(mouse_pos):
                            click_sound.play()
                            vsync_enabled = not vsync_enabled
                            save_settings()
                        fps_hit = pygame.Rect(FPS_SLIDER_X - 5, FPS_SLIDER_Y - 10, SLIDER_W + 10, SLIDER_H + 20)
                        if fps_hit.collidepoint(mouse_pos):
                            fps_slider_dragging = True
                            t = max(0.0, min(1.0, (mouse_pos[0] - FPS_SLIDER_X) / SLIDER_W))
                            max_fps = max(FPS_MIN, min(FPS_MAX, round((FPS_MIN + t * (FPS_MAX - FPS_MIN)) / 10) * 10))
                        ram_hit = pygame.Rect(RAM_SLIDER_X - 5, RAM_SLIDER_Y - 10, SLIDER_W + 10, SLIDER_H + 20)
                        if ram_hit.collidepoint(mouse_pos):
                            ram_slider_dragging = True
                            t = max(0.0, min(1.0, (mouse_pos[0] - RAM_SLIDER_X) / SLIDER_W))
                            alloted_ram = max(RAM_MIN, min(RAM_MAX, round(RAM_MIN + t * (RAM_MAX - RAM_MIN))))
                    elif settings_category == "account":
                        if delete_account_btn_rect.collidepoint(mouse_pos):
                            click_sound.play()
                            show_delete_modal = True
                        elif username_box_rect.collidepoint(mouse_pos):
                            show_username_modal = True
                            username_modal_input = ""
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if slider_dragging or fps_slider_dragging or ram_slider_dragging:
                save_settings()
            slider_dragging = False
            fps_slider_dragging = False
            ram_slider_dragging = False
        if event.type == pygame.MOUSEMOTION and not show_username_modal:
            if slider_dragging:
                master_volume = max(0.0, min(1.0,
                    (mouse_pos[0] - SLIDER_X) / SLIDER_W))
                click_sound.set_volume(master_volume)
                monkey_hit_sound.set_volume(master_volume)
            if fps_slider_dragging:
                t = max(0.0, min(1.0, (mouse_pos[0] - FPS_SLIDER_X) / SLIDER_W))
                max_fps = max(FPS_MIN, min(FPS_MAX, round((FPS_MIN + t * (FPS_MAX - FPS_MIN)) / 10) * 10))
            if ram_slider_dragging:
                t = max(0.0, min(1.0, (mouse_pos[0] - RAM_SLIDER_X) / SLIDER_W))
                alloted_ram = max(RAM_MIN, min(RAM_MAX, round(RAM_MIN + t * (RAM_MAX - RAM_MIN))))

    if state == STATE_FOREST and not player_dead:
        keys = pygame.key.get_pressed()
        moving = keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]
        player_sprinting = moving and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and player_energy > 0
        speed = PLAYER_SPEED if player_sprinting else WALK_SPEED
        # Energy: deplete while sprinting, refill while not sprinting
        current_fps = max(1, clock.get_fps()) if clock.get_fps() > 0 else 60
        energy_rate = 100.0 / (1.5 * current_fps)  # 1% per 1.5s
        if player_sprinting:
            player_energy = max(0.0, player_energy - energy_rate)
        else:
            player_energy = min(100.0, player_energy + energy_rate)
        # Ability cooldowns
        dt = 1.0 / current_fps
        if fireball_cooldown_remaining > 0:
            fireball_cooldown_remaining = max(0.0, fireball_cooldown_remaining - dt)
        if wall_fire_cooldown_remaining > 0:
            wall_fire_cooldown_remaining = max(0.0, wall_fire_cooldown_remaining - dt)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_x = max(0, player_x - speed)
            player_facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_x = min(LEVEL_WIDTH - PLAYER_W, player_x + speed)
            player_facing = 1

        # Update camera to follow player (keep player roughly centered)
        camera_x = max(0, min(player_x - WIDTH // 3, LEVEL_WIDTH - WIDTH))
        # Horizontal collision with platform walls (only when player is below platform top)
        pr = pygame.Rect(player_x, player_y, PLAYER_W, PLAYER_H)
        for prect in platform_rects:
            wall = pygame.Rect(prect.x, prect.y, prect.width, GROUND_ROW * TILE - prect.y)
            if pr.colliderect(wall) and player_y + PLAYER_H > prect.y + 4:
                from_left = pr.right - wall.left
                from_right = wall.right - pr.left
                if from_left < from_right:
                    player_x = wall.left - PLAYER_W
                else:
                    player_x = wall.right
                pr.x = player_x

        # Gravity + jump landing
        player_vy += GRAVITY
        player_y  += player_vy

        player_on_ground = False
        player_rect = pygame.Rect(player_x, player_y, PLAYER_W, PLAYER_H)

        # Ground collision (skip if player is over a pit)
        player_col = (player_x + PLAYER_W // 2) // TILE
        in_pit = False
        for pit_s, pit_e in PIT_COLS:
            if pit_s <= player_col <= pit_e:
                in_pit = True
                break
        if not in_pit and player_y >= GROUND_Y:
            player_y  = GROUND_Y
            player_vy = 0.0
            player_on_ground = True

        # Platform collision (only when falling)
        if player_vy >= 0:
            for prect in platform_rects:
                feet_y = player_y + PLAYER_H
                prev_feet_y = feet_y - player_vy
                if (player_x + PLAYER_W > prect.x and player_x < prect.right
                        and prev_feet_y <= prect.y and feet_y >= prect.y):
                    player_y  = prect.y - PLAYER_H
                    player_vy = 0.0
                    player_on_ground = True
                    break

        # Coin collection
        player_rect = pygame.Rect(player_x, player_y, PLAYER_W, PLAYER_H)
        for coin in coins:
            if not coin["collected"]:
                coin_rect = pygame.Rect(coin["x"], coin["y"], COIN_SIZE, COIN_SIZE)
                if player_rect.colliderect(coin_rect):
                    coin["collected"] = True
                    click_sound.play()

        # Spike collision
        player_rect = pygame.Rect(player_x, player_y, PLAYER_W, PLAYER_H)
        for sp in spikes:
            if player_rect.colliderect(sp):
                player_health = 0
                player_dead = True
                state = STATE_DEAD
                break

        # Monkey AI & collision
        player_rect = pygame.Rect(player_x, player_y, PLAYER_W, PLAYER_H)
        for monkey in monkeys:
            if not monkey["alive"]:
                continue
            monkey_rect = pygame.Rect(monkey["x"], monkey["y"], MONKEY_W, MONKEY_H)

            # Stomp detection: player falling onto monkey from above
            stomped = False
            if player_vy >= 0:
                feet_y = player_y + PLAYER_H
                prev_feet_y = feet_y - player_vy
                if (player_x + PLAYER_W > monkey["x"]
                        and player_x < monkey["x"] + MONKEY_W
                        and prev_feet_y <= monkey["y"]
                        and feet_y >= monkey["y"]):
                    monkey["alive"] = False
                    coins.append({"x": monkey["x"] + MONKEY_W // 2 - COIN_SIZE // 2,
                                  "y": monkey["y"], "collected": False})
                    monkey_hit_sound.set_volume(master_volume)
                    monkey_hit_sound.play()
                    player_vy = JUMP_FORCE * 0.7
                    player_y = monkey["y"] - PLAYER_H
                    stomped = True

            # Side/bottom collision does 50 damage and bounces player back
            if not stomped and player_rect.colliderect(monkey_rect):
                player_health -= 50
                # Bounce player away from monkey horizontally
                if player_x + PLAYER_W // 2 < monkey["x"] + MONKEY_W // 2:
                    player_x = monkey["x"] - PLAYER_W - 40
                else:
                    player_x = monkey["x"] + MONKEY_W + 40
                player_vy = JUMP_FORCE * 0.5
                if player_health <= 0:
                    player_health = 0
                    player_dead = True
                    state = STATE_DEAD
                break

            # Throw banana toward player's current position
            monkey["throw_timer"] -= 1
            if monkey["throw_timer"] <= 0:
                monkey["throw_timer"] = BANANA_THROW_INTERVAL
                bx = float(monkey["x"] + MONKEY_W // 2)
                by = float(monkey["y"] + MONKEY_H // 3)
                dx = player_x + PLAYER_W // 2 - bx
                dy = player_y + PLAYER_H // 2 - by
                dist = max(1, math.sqrt(dx * dx + dy * dy))
                bananas.append({
                    "x": bx, "y": by,
                    "vx": BANANA_SPEED * dx / dist,
                    "vy": BANANA_SPEED * dy / dist,
                })

        # Banana movement & collision
        for banana in bananas[:]:
            banana["x"] += banana["vx"]
            banana["y"] += banana["vy"]
            if (banana["x"] < -BANANA_RADIUS or banana["x"] > LEVEL_WIDTH + BANANA_RADIUS
                    or banana["y"] < -BANANA_RADIUS or banana["y"] > HEIGHT + BANANA_RADIUS):
                bananas.remove(banana)
                continue
            # Remove banana if it hits a platform wall
            banana_rect = pygame.Rect(
                banana["x"] - BANANA_RADIUS, banana["y"] - BANANA_RADIUS,
                BANANA_RADIUS * 2, BANANA_RADIUS * 2)
            hit_wall = False
            for prect in platform_rects:
                wall = pygame.Rect(prect.x, prect.y, prect.width, GROUND_ROW * TILE - prect.y)
                if banana_rect.colliderect(wall):
                    hit_wall = True
                    break
            if hit_wall:
                bananas.remove(banana)
                continue
            if player_rect.colliderect(banana_rect):
                player_health -= 10
                bananas.remove(banana)
                if player_health <= 0:
                    player_health = 0
                    player_dead = True
                    state = STATE_DEAD
                break

        # Gorilla AI & collision
        player_rect = pygame.Rect(player_x, player_y, PLAYER_W, PLAYER_H)
        for gorilla in gorillas:
            if not gorilla["alive"]:
                continue
            # Patrol movement
            gorilla["x"] += gorilla["vx"]
            if gorilla["x"] <= gorilla["patrol_left"]:
                gorilla["x"] = gorilla["patrol_left"]
                gorilla["vx"] = GORILLA_SPEED
            elif gorilla["x"] >= gorilla["patrol_right"]:
                gorilla["x"] = gorilla["patrol_right"]
                gorilla["vx"] = -GORILLA_SPEED
            gorilla_rect = pygame.Rect(gorilla["x"], gorilla["y"], GORILLA_W, GORILLA_H)
            # Stomp detection: player falling onto gorilla from above
            stomped = False
            if player_vy >= 0:
                feet_y = player_y + PLAYER_H
                prev_feet_y = feet_y - player_vy
                if (player_x + PLAYER_W > gorilla["x"]
                        and player_x < gorilla["x"] + GORILLA_W
                        and prev_feet_y <= gorilla["y"]
                        and feet_y >= gorilla["y"]):
                    gorilla["hp"] -= 1
                    gorilla["hit"] = True
                    player_vy = JUMP_FORCE * 0.6
                    player_y = gorilla["y"] - PLAYER_H
                    stomped = True
                    if gorilla["hp"] <= 0:
                        gorilla["alive"] = False
                        for ci in range(5):
                            coins.append({"x": gorilla["x"] + ci * (COIN_SIZE + 4),
                                          "y": gorilla["y"], "collected": False})
                        monkey_hit_sound.play()
            # Side/bottom collision — one-shot kill
            if not stomped and player_rect.colliderect(gorilla_rect):
                player_health = 0
                player_dead = True
                state = STATE_DEAD
                break

        # Great Ape Boss AI & collision
        if boss["alive"]:
            boss["x"] += boss["vx"]
            if boss["x"] <= BOSS_ARENA_LEFT + BOSS_TURN_MARGIN:
                boss["x"] = BOSS_ARENA_LEFT + BOSS_TURN_MARGIN
                boss["vx"] = BOSS_SPEED
            elif boss["x"] >= BOSS_ARENA_RIGHT - BOSS_TURN_MARGIN:
                boss["x"] = BOSS_ARENA_RIGHT - BOSS_TURN_MARGIN
                boss["vx"] = -BOSS_SPEED
            boss_rect = pygame.Rect(boss["x"], boss["y"], BOSS_W, BOSS_H)
            # Stomp detection: player falling onto boss from above
            boss_stomped = False
            if player_vy >= 0:
                feet_y = player_y + PLAYER_H
                prev_feet_y = feet_y - player_vy
                if (player_x + PLAYER_W > boss["x"]
                        and player_x < boss["x"] + BOSS_W
                        and prev_feet_y <= boss["y"]
                        and feet_y >= boss["y"]):
                    player_vy = JUMP_FORCE * 0.6
                    player_y = boss["y"] - PLAYER_H
                    boss_stomped = True
                    boss["hp"] -= 1
                    boss["hit"] = True
                    monkey_hit_sound.play()
                    if boss["hp"] <= 0:
                        boss["alive"] = False
            # Side/bottom collision — one-shot kill
            if not boss_stomped and player_rect.colliderect(boss_rect):
                player_health = 0
                player_dead = True
                state = STATE_DEAD

        # Fireball movement & collision
        for fb in fireballs[:]:
            fb["x"] += fb["vx"]
            if fb["x"] < -FIREBALL_SIZE or fb["x"] > LEVEL_WIDTH + FIREBALL_SIZE:
                fireballs.remove(fb)
                continue
            fb_rect = pygame.Rect(fb["x"], fb["y"], FIREBALL_SIZE, FIREBALL_SIZE)
            hit = False
            # vs monkeys
            for monkey in monkeys:
                if not monkey["alive"]:
                    continue
                if fb_rect.colliderect(pygame.Rect(monkey["x"], monkey["y"], MONKEY_W, MONKEY_H)):
                    monkey["alive"] = False
                    coins.append({"x": monkey["x"] + MONKEY_W // 2 - COIN_SIZE // 2,
                                  "y": monkey["y"], "collected": False})
                    monkey_hit_sound.play()
                    hit = True
                    break
            if hit:
                fireballs.remove(fb)
                continue
            # vs gorillas
            for gorilla in gorillas:
                if not gorilla["alive"]:
                    continue
                if fb_rect.colliderect(pygame.Rect(gorilla["x"], gorilla["y"], GORILLA_W, GORILLA_H)):
                    gorilla["hp"] -= FIREBALL_DAMAGE
                    gorilla["hit"] = True
                    if gorilla["hp"] <= 0:
                        gorilla["alive"] = False
                        for ci in range(5):
                            coins.append({"x": gorilla["x"] + ci * (COIN_SIZE + 4),
                                          "y": gorilla["y"], "collected": False})
                    monkey_hit_sound.play()
                    hit = True
                    break
            if hit:
                fireballs.remove(fb)
                continue
            # vs boss
            if boss["alive"]:
                if fb_rect.colliderect(pygame.Rect(boss["x"], boss["y"], BOSS_W, BOSS_H)):
                    boss["hp"] -= FIREBALL_DAMAGE
                    boss["hit"] = True
                    if boss["hp"] <= 0:
                        boss["alive"] = False
                    monkey_hit_sound.play()
                    fireballs.remove(fb)
                    continue
            # vs platforms
            for prect in platform_rects:
                wall = pygame.Rect(prect.x, prect.y, prect.width, GROUND_ROW * TILE - prect.y)
                if fb_rect.colliderect(wall):
                    hit = True
                    break
            if hit:
                fireballs.remove(fb)

        # Wall of Fire timer & collision
        if wall_of_fire is not None:
            wall_of_fire["timer"] -= dt
            if wall_of_fire["timer"] <= 0:
                wall_of_fire = None
            else:
                wf_rect = pygame.Rect(wall_of_fire["x"], wall_of_fire["y"],
                                      WALL_FIRE_WIDTH, WALL_FIRE_HEIGHT)
                if "hit_ids" not in wall_of_fire:
                    wall_of_fire["hit_ids"] = set()
                # vs boss
                if boss["alive"] and id(boss) not in wall_of_fire["hit_ids"]:
                    if wf_rect.colliderect(pygame.Rect(boss["x"], boss["y"], BOSS_W, BOSS_H)):
                        wall_of_fire["hit_ids"].add(id(boss))
                        boss["hp"] -= 5
                        boss["hit"] = True
                        if boss["hp"] <= 0:
                            boss["alive"] = False
                        monkey_hit_sound.play()
                # vs gorillas
                for gorilla in gorillas:
                    if not gorilla["alive"] or id(gorilla) in wall_of_fire["hit_ids"]:
                        continue
                    if wf_rect.colliderect(pygame.Rect(gorilla["x"], gorilla["y"], GORILLA_W, GORILLA_H)):
                        wall_of_fire["hit_ids"].add(id(gorilla))
                        gorilla["hp"] -= WALL_FIRE_DAMAGE
                        gorilla["hit"] = True
                        if gorilla["hp"] <= 0:
                            gorilla["alive"] = False
                            for ci in range(5):
                                coins.append({"x": gorilla["x"] + ci * (COIN_SIZE + 4),
                                              "y": gorilla["y"], "collected": False})
                        monkey_hit_sound.play()
                # vs monkeys
                for monkey in monkeys:
                    if not monkey["alive"] or id(monkey) in wall_of_fire["hit_ids"]:
                        continue
                    if wf_rect.colliderect(pygame.Rect(monkey["x"], monkey["y"], MONKEY_W, MONKEY_H)):
                        wall_of_fire["hit_ids"].add(id(monkey))
                        monkey["alive"] = False
                        coins.append({"x": monkey["x"] + MONKEY_W // 2 - COIN_SIZE // 2,
                                      "y": monkey["y"], "collected": False})
                        monkey_hit_sound.play()

        # Finish zone — level complete
        finish_rect = pygame.Rect(FINISH_X, FINISH_Y, FINISH_W, FINISH_H)
        if player_rect.colliderect(finish_rect):
            coins_collected = sum(1 for c in coins if c["collected"])
            win_coins = 100 + coins_collected
            total_coins += win_coins
            progress["total_coins"] = total_coins
            save_progress(progress)
            click_sound.play()
            state = STATE_WIN

        # Fall off screen death
        if player_y > HEIGHT:
            player_dead = True
            state = STATE_DEAD

    if state == STATE_CREATE_PROFILE:
        confirm_hovered = confirm_btn_rect.collidepoint(mouse_pos)
        draw_create_profile(username_input, confirm_hovered, show_profile_warning)
    elif state == STATE_HOME:
        draw_home(hovered, settings_hovered)
    elif state == STATE_SETTINGS:
        draw_settings(mouse_pos)
        if show_delete_modal:
            draw_delete_account_modal(mouse_pos)
        elif show_username_modal:
            draw_username_modal(mouse_pos)
    elif state == STATE_LEVEL_SELECT:
        draw_level_select(mouse_pos)
    elif state == STATE_FOREST:
        draw_forest_level(mouse_pos)
    elif state == STATE_PAUSED:
        draw_forest_level(mouse_pos)
        draw_pause_menu(mouse_pos)
    elif state == STATE_DEAD:
        draw_forest_level(mouse_pos)
        draw_death_screen(mouse_pos)
    elif state == STATE_WIN:
        draw_forest_level(mouse_pos)
        draw_win_screen(mouse_pos)

    # Scale render surface to fill the entire display
    dw, dh = display_surf.get_size()
    scaled = pygame.transform.scale(screen, (dw, dh))
    display_surf.blit(scaled, (0, 0))
    pygame.display.flip()
    clock.tick(MONITOR_HZ if vsync_enabled else max_fps)
