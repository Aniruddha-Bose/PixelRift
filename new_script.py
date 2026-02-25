import pygame
import sys
import array
import math
import random
import json
import os

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

desktop_info = pygame.display.Info()
DESKTOP_W, DESKTOP_H = desktop_info.current_w, desktop_info.current_h

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

# Player
PLAYER_W, PLAYER_H = 28, 44
PLAYER_SPEED = 4
JUMP_FORCE   = -13
GRAVITY      = 0.55
PLAYER_COLOR   = (220, 100, 50)
PLAYER_OUTLINE = (140, 55, 15)
GROUND_Y = GROUND_ROW * TILE - PLAYER_H   # y when standing on ground

player_x  = TILE                           # start at left
player_y  = GROUND_Y
player_vy = 0.0                            # vertical velocity


def draw_forest_level():
    # Sky gradient
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    cols = WIDTH // TILE + 1
    total_rows = HEIGHT // TILE + 1

    for row in range(GROUND_ROW, total_rows):
        for col in range(cols):
            x, y = col * TILE, row * TILE
            rng = random.Random(row * 997 + col * 31)  # deterministic per tile

            if row == GROUND_ROW:
                # Full grass tile
                pygame.draw.rect(screen, GRASS_MID, (x, y, TILE, TILE))
                pygame.draw.rect(screen, GRASS_LITE, (x, y, TILE, 5))
                for _ in range(5):
                    pygame.draw.rect(screen, GRASS_DARK,
                        (x + rng.randint(1, TILE-3), y + rng.randint(6, TILE-3), 2, 2))

            elif row == GROUND_ROW + 1:
                # Transition tile: top ~60% grass, bottom ~40% dirt blending in
                split = TILE * 3 // 5
                pygame.draw.rect(screen, GRASS_MID,  (x, y,          TILE, split))
                pygame.draw.rect(screen, DIRT_MID,   (x, y + split,  TILE, TILE - split))
                # Grass roots reaching deeper
                for _ in range(5):
                    gx = x + rng.randint(2, TILE - 4)
                    gh = rng.randint(4, split + 6)
                    pygame.draw.rect(screen, GRASS_DARK, (gx, y, 2, gh))
                # Soil particles in the lower half
                for _ in range(4):
                    shade = DIRT_DARK if rng.random() < 0.5 else DIRT_LITE
                    pygame.draw.rect(screen, shade,
                        (x + rng.randint(1, TILE-3), y + rng.randint(split, TILE-3), 2, 2))

            elif row == GROUND_ROW + 2:
                # Mostly dirt but a few stray grass roots at the very top
                pygame.draw.rect(screen, DIRT_MID, (x, y, TILE, TILE))
                for _ in range(2):
                    gx = x + rng.randint(2, TILE - 4)
                    gh = rng.randint(2, 6)
                    pygame.draw.rect(screen, GRASS_DARK, (gx, y, 2, gh))
                for _ in range(6):
                    shade = DIRT_DARK if rng.random() < 0.5 else DIRT_LITE
                    pygame.draw.rect(screen, shade,
                        (x + rng.randint(1, TILE-3), y + rng.randint(1, TILE-3), 2, 2))

            else:
                # Pure dirt
                pygame.draw.rect(screen, DIRT_MID, (x, y, TILE, TILE))
                for _ in range(6):
                    shade = DIRT_DARK if rng.random() < 0.5 else DIRT_LITE
                    pygame.draw.rect(screen, shade,
                        (x + rng.randint(1, TILE-3), y + rng.randint(1, TILE-3), 2, 2))

    # Player rectangle
    pygame.draw.rect(screen, PLAYER_COLOR,   (player_x, player_y, PLAYER_W, PLAYER_H))
    pygame.draw.rect(screen, PLAYER_OUTLINE, (player_x, player_y, PLAYER_W, PLAYER_H), 3)

SETTINGS_LEFT_W  = WIDTH // 3
SETTINGS_RIGHT_W = WIDTH - SETTINGS_LEFT_W

CATEGORIES   = ["Audio", "Accessibility", "Performance", "Account"]
CAT_Y_START  = 75
CAT_SPACING  = 35

SLIDER_W = 210
SLIDER_H = 8
SLIDER_X = SETTINGS_LEFT_W + 120
SLIDER_Y = 140

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

    # ── LEFT PANEL ────────────────────────────────────────────────────────────
    pixel_text(screen, "Settings", 2, WHITE, SETTINGS_LEFT_W // 2, 15)
    pygame.draw.line(screen, WHITE, (8, 57), (SETTINGS_LEFT_W - 8, 57), 1)

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
        pixel_text(screen, "Volume", 1, WHITE, SETTINGS_LEFT_W + 55, 132)

        # Track
        pygame.draw.rect(screen, DARK_GREY, (SLIDER_X, SLIDER_Y, SLIDER_W, SLIDER_H))
        fill_w = int(master_volume * SLIDER_W)
        if fill_w > 0:
            pygame.draw.rect(screen, GREEN, (SLIDER_X, SLIDER_Y, fill_w, SLIDER_H))
        # Handle
        hx = SLIDER_X + fill_w
        pygame.draw.rect(screen, WHITE, (hx - 5, SLIDER_Y - 7, 10, SLIDER_H + 14))
        # Percentage
        pixel_text(screen, str(int(master_volume * 100)) + "%", 1, WHITE,
                   SLIDER_X + SLIDER_W + 32, 132)


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


# Game states
STATE_HOME           = "home"
STATE_LEVEL_SELECT   = "level_select"
STATE_FOREST         = "forest"
STATE_PAUSED         = "paused"
STATE_SETTINGS       = "settings"
STATE_CREATE_PROFILE = "create_profile"
state = STATE_CREATE_PROFILE if profile_username is None else STATE_HOME

clock = pygame.time.Clock()

username_input       = ""
show_profile_warning = False
settings_category    = "audio"
master_volume        = 1.0
slider_dragging      = False

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
            if state == STATE_CREATE_PROFILE:
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
            if event.key == pygame.K_ESCAPE:
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
            if event.key == pygame.K_SPACE and state == STATE_FOREST and player_y >= GROUND_Y:
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
                    player_x  = TILE
                    player_y  = GROUND_Y
                    player_vy = 0.0
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
            elif state == STATE_SETTINGS:
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
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            slider_dragging = False
        if event.type == pygame.MOUSEMOTION and slider_dragging:
            master_volume = max(0.0, min(1.0,
                (mouse_pos[0] - SLIDER_X) / SLIDER_W))
            click_sound.set_volume(master_volume)

    if state == STATE_FOREST:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_x = max(0, player_x - PLAYER_SPEED)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_x = min(WIDTH - PLAYER_W, player_x + PLAYER_SPEED)

        # Gravity + jump landing
        player_vy += GRAVITY
        player_y  += player_vy
        if player_y >= GROUND_Y:
            player_y  = GROUND_Y
            player_vy = 0.0

    if state == STATE_CREATE_PROFILE:
        confirm_hovered = confirm_btn_rect.collidepoint(mouse_pos)
        draw_create_profile(username_input, confirm_hovered, show_profile_warning)
    elif state == STATE_HOME:
        draw_home(hovered, settings_hovered)
    elif state == STATE_SETTINGS:
        draw_settings(mouse_pos)
    elif state == STATE_LEVEL_SELECT:
        draw_level_select(mouse_pos)
    elif state == STATE_FOREST:
        draw_forest_level()
    elif state == STATE_PAUSED:
        draw_forest_level()
        draw_pause_menu(mouse_pos)

    # Scale render surface to fill the entire display
    dw, dh = display_surf.get_size()
    scaled = pygame.transform.scale(screen, (dw, dh))
    display_surf.blit(scaled, (0, 0))
    pygame.display.flip()
    clock.tick(60)
