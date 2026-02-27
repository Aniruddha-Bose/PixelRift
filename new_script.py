import pygame
import sys
import array
import math
import json
import os

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
    }
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f)

WIDTH, HEIGHT = 800, 600
screen = pygame.Surface((WIDTH, HEIGHT))          # fixed-size render target
display_surf = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Pixelrift")
is_fullscreen = False

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

# Player
PLAYER_W, PLAYER_H = 28, 44
PLAYER_SPEED = 2
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
camera_x  = 0                              # horizontal scroll offset

# How far the level extends to the right (in pixels)
LEVEL_WIDTH = 40 * TILE

# Platforms: (start_col, width_in_tiles, height_offset from GROUND_ROW going up)
PLATFORMS = [
    (8, 4, 2),    # platform 1: cols 8-11
    (14, 4, 4),   # platform 2: cols 14-17
    (20, 4, 6),   # platform 3: cols 20-23
]

# Build platform rects in pixel coords (top surface for collision)
platform_rects = []
for pcol, pw, poff in PLATFORMS:
    px = pcol * TILE
    py = (GROUND_ROW - poff) * TILE
    platform_rects.append(pygame.Rect(px, py, pw * TILE, TILE))

# Spike gaps sit directly between adjacent platforms (2 cols each)
# Gap 1: cols 12-13, Gap 2: cols 18-19
GAP_COLS = [(12, 13), (18, 19)]

# Spikes: 3 per gap, narrow
SPIKE_W = 16
SPIKE_H = 20
spikes = []
for gap_start, gap_end in GAP_COLS:
    gap_pixel_x = gap_start * TILE
    gap_pixel_w = (gap_end - gap_start + 1) * TILE
    total_spikes_w = 3 * SPIKE_W
    margin = (gap_pixel_w - total_spikes_w) // 2
    for i in range(3):
        sx = gap_pixel_x + margin + i * SPIKE_W
        sy = GROUND_ROW * TILE - SPIKE_H
        spikes.append(pygame.Rect(sx, sy, SPIKE_W, SPIKE_H))

# ── Monkey enemies ────────────────────────────────────────────────────────
MONKEY_W, MONKEY_H = 24, 36
MONKEY_COLOR   = (200, 50, 50)
MONKEY_OUTLINE = (120, 20, 20)
MONKEY_Y = GROUND_ROW * TILE - MONKEY_H

BANANA_RADIUS = 5
BANANA_COLOR  = (255, 220, 50)
BANANA_SPEED  = 3
BANANA_THROW_INTERVAL = 180

MONKEY_SPAWN_POSITIONS = [27 * TILE]

def init_monkeys():
    monkeys = []
    for mx in MONKEY_SPAWN_POSITIONS:
        monkeys.append({
            "x": mx, "y": MONKEY_Y, "alive": True,
            "throw_timer": BANANA_THROW_INTERVAL,
        })
    return monkeys

monkeys = init_monkeys()
bananas = []


def draw_forest_level():
    cx = camera_x  # local alias

    # Sky gradient (not scrolled)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Figure out which tile columns are visible
    first_col = max(0, cx // TILE)
    last_col = (cx + WIDTH) // TILE + 1
    total_cols = LEVEL_WIDTH // TILE

    # Ground tiles — full level width, only draw visible
    for row in range(GROUND_ROW, GROUND_ROW + 5):
        for col in range(first_col, min(last_col, total_cols)):
            world_x = col * TILE
            sx = world_x - cx
            y = row * TILE
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

    # Spikes — white with black outline and light grey blend
    for sp in spikes:
        tip   = (sp.x + sp.width // 2 - cx, sp.y)
        left  = (sp.x - cx, sp.y + sp.height)
        right = (sp.x + sp.width - cx, sp.y + sp.height)
        # White fill
        pygame.draw.polygon(screen, WHITE, [tip, left, right])
        # Light grey inner border for pixel blending
        pygame.draw.polygon(screen, DARK_GREY, [tip, left, right], 2)
        # Black outline
        pygame.draw.polygon(screen, BLACK, [tip, left, right], 1)

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

    # Health bar — top right
    HB_W, HB_H = 140, 16
    hb_x = WIDTH - HB_W - 50
    hb_y = 12
    fill_w = int(HB_W * max(0, player_health) / 100)
    pygame.draw.rect(screen, DARK_GREY, (hb_x, hb_y, HB_W, HB_H))
    if fill_w > 0:
        pygame.draw.rect(screen, GREEN, (hb_x, hb_y, fill_w, HB_H))
    pygame.draw.rect(screen, BLACK, (hb_x, hb_y, HB_W, HB_H), 2)
    hp_raw = pixel_font_small.render(str(max(0, player_health)) + "%", False, WHITE)
    screen.blit(hp_raw, (hb_x + HB_W + 6, hb_y + HB_H // 2 - hp_raw.get_height() // 2))

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


# Game states
STATE_HOME           = "home"
STATE_LEVEL_SELECT   = "level_select"
STATE_FOREST         = "forest"
STATE_PAUSED         = "paused"
STATE_SETTINGS       = "settings"
STATE_CREATE_PROFILE = "create_profile"
STATE_DEAD           = "dead"
state = STATE_CREATE_PROFILE if profile_username is None else STATE_HOME

clock = pygame.time.Clock()

username_input       = ""
show_profile_warning = False
settings_category    = "audio"
_saved               = load_settings()
master_volume        = _saved.get("master_volume", 1.0)
vsync_enabled        = _saved.get("vsync_enabled", False)
max_fps              = _saved.get("max_fps", 120)
alloted_ram          = max(RAM_MIN, min(RAM_MAX, _saved.get("alloted_ram", 2)))
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
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    display_surf = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    display_surf = pygame.display.set_mode(
                        (WIDTH, HEIGHT), pygame.RESIZABLE)
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
                    camera_x      = 0
                    monkeys       = init_monkeys()
                    bananas       = []
                    state = STATE_FOREST
                elif left_arrow_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    level_index = (level_index - 1) % len(levels)
                elif right_arrow_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    level_index = (level_index + 1) % len(levels)
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
                    camera_x         = 0
                    monkeys          = init_monkeys()
                    bananas          = []
                    state = STATE_FOREST
                elif death_exit_rect.collidepoint(mouse_pos):
                    click_sound.play()
                    player_dead = False
                    monkeys     = init_monkeys()
                    bananas     = []
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
                    if settings_category == "audio":
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
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_x = max(0, player_x - PLAYER_SPEED)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_x = min(LEVEL_WIDTH - PLAYER_W, player_x + PLAYER_SPEED)

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

        # Ground collision
        if player_y >= GROUND_Y:
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
                player_health -= 5
                bananas.remove(banana)
                if player_health <= 0:
                    player_health = 0
                    player_dead = True
                    state = STATE_DEAD
                break

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
        draw_forest_level()
    elif state == STATE_PAUSED:
        draw_forest_level()
        draw_pause_menu(mouse_pos)
    elif state == STATE_DEAD:
        draw_forest_level()
        draw_death_screen(mouse_pos)

    # Scale render surface to fill the entire display
    dw, dh = display_surf.get_size()
    scaled = pygame.transform.scale(screen, (dw, dh))
    display_surf.blit(scaled, (0, 0))
    pygame.display.flip()
    clock.tick(MONITOR_HZ if vsync_enabled else max_fps)
