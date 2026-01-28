import math, random
from dataclasses import dataclass
from typing import Optional, Tuple, List
import pygame
import pygame.gfxdraw

# ---------------------- CONFIG ----------------------
WIDTH, HEIGHT = 900, 650
FONT_SMALL, FONT_BIG = 24, 44

OVEN_TARGET_TEMP = 350
OVEN_TARGET_TIME = 20.0

PAN_TARGET = (0.52, 0.68)
PAN_FILL_RATE = 90.0
PAN_UNFILL_RATE = 120.0

EGG_TAPS_TO_CRACK = 3

# ---------------------- COLORS ----------------------
BG_TOP = (22, 18, 45)
BG_BOT = (68, 35, 96)
WHITE = (245, 245, 250)
BLACK = (10, 10, 14)
GREY = (70, 70, 85)
GOLD = (255, 220, 120)
TEAL = (120, 200, 180)

# egg pieces
SHELL = (252, 247, 236)
SHELL_EDGE = (220, 205, 190)
YOLK = (255, 210, 70)

# UI palette for frosting colors
PALETTE = [
    (255, 99, 132),   # strawberry
    (255, 159, 64),   # orange
    (255, 205, 86),   # lemon
    (75, 192, 192),   # mint
    (54, 162, 235),   # blue
    (153, 102, 255),  # grape
    (255, 255, 255),  # white
    (0, 0, 0),        # choc drizzle
    (255, 105, 180),  # hot pink
]

# ---- Cake palettes (prebake batter vs baked crumb) ----
BASE_ICING = (252, 244, 220)
VANILLA_TOP_HILITE = (255, 252, 240)
VANILLA_TOP_EDGE   = (235, 220, 190)
SIDE_SHADE_LIGHT   = (245, 232, 204)
SIDE_SHADE_DARK    = (225, 202, 165)
OUTLINE            = (210, 190, 170)

PALETTE_PREBAKE = {
    "BASE": (250, 246, 232),
    "TOP_HI": (255, 253, 244),
    "TOP_EDGE": (236, 224, 198),
    "SIDE_L": (246, 236, 210),
    "SIDE_D": (228, 206, 172),
    "OUT": (212, 192, 172),
}
PALETTE_BAKED = {
    "BASE": (248, 229, 185),  # sand/crumb
    "TOP_HI": (252, 235, 200),
    "TOP_EDGE": (220, 185, 140),
    "SIDE_L": (235, 205, 170),
    "SIDE_D": (205, 170, 125),
    "OUT": (190, 160, 130),
}

def set_cake_palette(mode: str):
    global BASE_ICING, VANILLA_TOP_HILITE, VANILLA_TOP_EDGE, SIDE_SHADE_LIGHT, SIDE_SHADE_DARK, OUTLINE
    p = PALETTE_PREBAKE if mode == 'prebake' else PALETTE_BAKED
    BASE_ICING = p["BASE"]
    VANILLA_TOP_HILITE = p["TOP_HI"]
    VANILLA_TOP_EDGE = p["TOP_EDGE"]
    SIDE_SHADE_LIGHT = p["SIDE_L"]
    SIDE_SHADE_DARK = p["SIDE_D"]
    OUTLINE = p["OUT"]

# ---------------------- UTIL ----------------------
def clamp(a, lo, hi): return max(lo, min(hi, a))
def lerp(a, b, t): return a + (b - a) * t
def ease_out_cubic(t): return 1 - (1 - t) ** 3

def _blend(c1, c2, t):
    return tuple(int(c1[i]*(1-t) + c2[i]*t) for i in range(3))

def _vertical_gradient(surf, rect, top_col, bot_col):
    h = max(1, rect.height)
    for i in range(h):
        tt = i / h
        col = _blend(top_col, bot_col, tt)
        pygame.draw.line(surf, col, (rect.x, rect.y+i), (rect.right, rect.y+i))

def _alpha_ellipse_local(surface, color_rgba, rect, width=0):
    """Alpha ellipse with a small temp surface just as big as rect."""
    tmp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.ellipse(tmp, color_rgba, tmp.get_rect(), width)
    surface.blit(tmp, rect.topleft)

def _ellipse_ring_local(surf, rect, inner_alpha=50, outer_alpha=0, width=10, col=(0, 0, 0)):
    """Alpha-correct ring using local temp ellipse that shrinks each step."""
    for i in range(width):
        t = i / max(1, width-1)
        a = int(inner_alpha * (1 - t) + outer_alpha * t)
        rr = rect.inflate(-2 * i, -int(2 * i * rect.height / rect.width))
        if rr.width <= 0 or rr.height <= 0: break
        _alpha_ellipse_local(surf, (*col, a), rr, 1)

def _soft_ellipse_shadow(surf, rect, alpha=70):
    sh = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, alpha), sh.get_rect())
    surf.blit(sh, rect.topleft)

# Anti-aliased dot for smooth strokes
def aa_dot(surf, x, y, r, col):
    xi, yi, rr = int(x), int(y), int(r)
    pygame.gfxdraw.filled_circle(surf, xi, yi, rr, col)
    pygame.gfxdraw.aacircle(surf, xi, yi, rr, col)

# Catmull–Rom smoothing utilities
def catmull_rom(points: List[Tuple[float,float]], samples=8) -> List[Tuple[float,float]]:
    if len(points) < 4:
        return points[:]
    out=[]
    for i in range(1, len(points)-2):
        p0,p1,p2,p3 = points[i-1], points[i], points[i+1], points[i+2]
        for s in range(samples):
            t=s/samples; t2=t*t; t3=t2*t
            x=0.5*((2*p1[0])+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y=0.5*((2*p1[1])+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            out.append((x,y))
    # include the last point
    out.append(points[-1])
    return out

# helpers to mirror the tier drawing math
def tier_height(r: int) -> int:
    return int(max(28, r * 0.48))

def tier_ry(r: int) -> int:
    return int(r * 0.18)

# ---------------------- TIER ----------------------
@dataclass
class Tier:
    center: Tuple[int, int]
    r: int            # horizontal radius (x)
    h: int            # vertical side height
    ry: int           # vertical radius of the top ellipse (y)
    top_surf: pygame.Surface
    side_surf: pygame.Surface

    def top_rect(self) -> pygame.Rect:
        cx, cy = self.center
        return pygame.Rect(cx - self.r, cy - self.ry, self.r*2, self.ry*2)

    def side_rect(self) -> pygame.Rect:
        cx, cy = self.center
        return pygame.Rect(cx - self.r, cy, self.r*2, self.h)

    def inside_top(self, x, y) -> bool:
        cx, cy = self.center
        dx, dy = (x - cx), (y - cy)
        return (dx*dx)/(self.r*self.r) + (dy*dy)/(self.ry*self.ry) <= 1.0

    def inside_side(self, x, y) -> bool:
        return self.side_rect().collidepoint(x, y)

    def draw_base(self, screen):
        cx, cy = self.center
        r, ry, h = self.r, self.ry, self.h

        # shadow
        shadow_rect = pygame.Rect(cx - int(r*1.1), cy + h - int(ry*0.3), int(r*2.2), int(ry*1.0))
        _soft_ellipse_shadow(screen, shadow_rect, alpha=60)

        # cylindrical side
        side_rect = self.side_rect()
        _vertical_gradient(screen, side_rect, SIDE_SHADE_LIGHT, SIDE_SHADE_DARK)

        # subtle ledge under top (alpha-correct, local)
        ledge = pygame.Rect(cx - r, cy + int(ry*0.2), r*2, int(ry*1.4))
        _alpha_ellipse_local(screen, (0, 0, 0, 35), ledge, 1)

        # bottom rim
        bottom = pygame.Rect(cx - r, cy + h - ry, r*2, ry*2)
        pygame.draw.ellipse(screen, SIDE_SHADE_DARK, bottom, 2)

        # top ellipse — flat look
        top = self.top_rect()
        pygame.draw.ellipse(screen, VANILLA_TOP_HILITE, top)
        _ellipse_ring_local(screen, top, inner_alpha=45, outer_alpha=0, width=10, col=(0,0,0))
        pygame.draw.ellipse(screen, OUTLINE, top, 2)

# ---------------------- GAME ----------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Bake & Decorate — cozy cakes (AA + smoothing)")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, FONT_SMALL)
        self.big = pygame.font.SysFont(None, FONT_BIG, bold=True)

        # state & background time
        self.state = 'EGGS'
        self.t = 0.0
        set_cake_palette('prebake')

        # ---- Eggs
        self.egg_taps = 0
        self.egg_center = (WIDTH//2, 220)
        self.left_pos = [self.egg_center[0]-70, self.egg_center[1]-90]
        self.right_pos = [self.egg_center[0], self.egg_center[1]-90]
        self.dragging_side: Optional[str] = None
        self.drag_offset = (0, 0)

        self.yolk_dropped = False
        self.yolk_y = 0.0
        self.yolk_v = 0.0
        self.egg_done = False     # only one drop total

        # ---- Ingredients (after egg)
        self.ingredients = [
            {"name":"vanilla", "color":(235,220,190), "needed":1.0, "added":0.0},
            {"name":"flour",   "color":(245,240,230), "needed":1.0, "added":0.0},
            {"name":"water",   "color":(190,210,255), "needed":1.0, "added":0.0},
            {"name":"oil",     "color":(240,230,140), "needed":1.0, "added":0.0},
        ]
        self.pouring_idx: Optional[int] = None  # which container you're holding on

        # ---- Mix
        self.mix_progress = 0.0  # hold mouse in bowl to stir

        # ---- Pans
        self.pans = []
        pcx = WIDTH//2
        self.pans.append({"center": (pcx-200, 430), "r": 60, "cap": 100.0, "fill": 0.0})
        self.pans.append({"center": (pcx,      430), "r": 70, "cap": 120.0, "fill": 0.0})
        self.pans.append({"center": (pcx+200, 430), "r": 60, "cap": 100.0, "fill": 0.0})
        self.score_pans = 0.0

        # ---- Oven
        self.oven_temp = 350
        self.oven_timer = 0.0
        self.oven_running = False
        self.score_bake = 0.0

        # ---- Tiers (auto-stacked)
        r1, r2, r3 = 220, 160, 110
        self.tiers: List[Tier] = []
        self.build_stack(r1, r2, r3)

        # ---- Base layer cache
        self.base_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.needs_base_rebuild = True

        # ---- Decorate
        self.sel_tier = 2
        self.sel_region = 'top'  # 'top' or 'side'
        self.brush_color = PALETTE[0]
        self.brush_size = 14
        self.tool = 'brush'
        self.last_pos: Optional[Tuple[int, int]] = None

        # stroke smoothing
        self.stroke_points: List[Tuple[float,float]] = []
        self.stroke_snapshot: Optional[pygame.Surface] = None

        # ---- History (Undo/Redo)
        self.history: List[Tuple[int, pygame.Surface, pygame.Surface]] = []
        self.redo: List[Tuple[int, pygame.Surface, pygame.Surface]] = []

        # ---- Toast (for save notifications)
        self.toast_text = ""
        self.toast_timer = 0.0

    # ---- Build/stack tiers so they touch cleanly ----
    def build_stack(self, r1, r2, r3):
        self.tiers.clear()
        # compute heights and ry
        h1, h2, h3 = tier_height(r1), tier_height(r2), tier_height(r3)
        ry1, ry2, ry3 = tier_ry(r1), tier_ry(r2), tier_ry(r3)
        overlap = 6  # small extra sink

        # place bottom so its bottom sits above the floor
        bottom_y = HEIGHT - 70 - h1
        mid_y = bottom_y - h2 + overlap
        top_y = mid_y - h3 + overlap

        cx = WIDTH//2
        for r, h, ry, cy in [(r1,h1,ry1,bottom_y),
                             (r2,h2,ry2,mid_y),
                             (r3,h3,ry3,top_y)]:
            top_surf  = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            side_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            self.tiers.append(Tier((cx, cy), r, h, ry, top_surf, side_surf))

    # --------- Base rebuild ---------
    def rebuild_base_layer(self):
        self.base_layer.fill((0,0,0,0))
        for tier in self.tiers:
            tier.draw_base(self.base_layer)
        self.needs_base_rebuild = False

    # --------- BG & Titles ---------
    def draw_bg(self, t):
        for i in range(HEIGHT):
            k = i / HEIGHT
            col = _blend(BG_TOP, BG_BOT, k)
            pygame.draw.line(self.screen, col, (0, i), (WIDTH, i))
        # few twinkles
        random.seed(0)
        for _ in range(120):
            x = random.randint(0, WIDTH-1)
            y = random.randint(0, HEIGHT-1)
            self.screen.set_at((x, y), (255, 255, 255))
        # toast
        if self.toast_timer > 0:
            self.toast_timer -= 1/60
            s = self.font.render(self.toast_text, True, GOLD)
            box = pygame.Rect(WIDTH//2 - s.get_width()//2 - 10, 8, s.get_width()+20, s.get_height()+8)
            pygame.draw.rect(self.screen, (30,30,50), box, border_radius=8)
            pygame.draw.rect(self.screen, WHITE, box, 2, border_radius=8)
            self.screen.blit(s, (box.x+10, box.y+4))

    def draw_title(self, text, size=32):
        f = pygame.font.SysFont(None, size, bold=True)
        s = f.render(text, True, WHITE)
        self.screen.blit(s, (WIDTH//2 - s.get_width()//2, 14))

    # ---------------- EGGS ----------------
    def reset_egg_positions(self):
        cx, cy = self.egg_center
        self.left_pos = [cx-70, cy-90]
        self.right_pos = [cx, cy-90]

    def start_yolk_drop(self, bowl):
        if self.yolk_dropped:  # only once
            return
        self.yolk_dropped = True
        self.yolk_y = 310
        self.yolk_v = 0.0
        self.egg_done = False

    def update_yolk(self, dt, bowl):
        if not self.yolk_dropped or self.egg_done:
            return
        g = 900.0
        self.yolk_v += g * dt
        self.yolk_y += self.yolk_v * dt
        if self.yolk_y >= bowl.centery - 8:  # hit the bowl once
            self.yolk_y = bowl.centery - 8
            self.egg_done = True

    def draw_egg_step(self, dt):
        self.draw_title("Crack the egg: tap 3× then drag shells apart", 28)
        # bowl
        bowl = pygame.Rect(WIDTH//2-140, 300, 280, 140)
        pygame.draw.ellipse(self.screen, (230,230,255), bowl)
        pygame.draw.ellipse(self.screen, WHITE, bowl, 3)

        cx, cy = self.egg_center
        if self.egg_taps < EGG_TAPS_TO_CRACK:
            whole_rect = pygame.Rect(cx-70, cy-90, 140, 180)
            pygame.draw.ellipse(self.screen, SHELL, whole_rect)
            pygame.draw.ellipse(self.screen, SHELL_EDGE, whole_rect, 3)
            tap = self.font.render(f"Taps: {self.egg_taps}/{EGG_TAPS_TO_CRACK}", True, WHITE)
            self.screen.blit(tap, (WIDTH//2 - tap.get_width()//2, 260))
        else:
            # halves (draggable)
            L = pygame.Rect(int(self.left_pos[0]), int(self.left_pos[1]), 70, 180)
            R = pygame.Rect(int(self.right_pos[0]), int(self.right_pos[1]), 70, 180)
            pygame.draw.ellipse(self.screen, SHELL, L); pygame.draw.ellipse(self.screen, SHELL_EDGE, L, 2)
            pygame.draw.ellipse(self.screen, SHELL, R); pygame.draw.ellipse(self.screen, SHELL_EDGE, R, 2)

            # yolk logic (one-time drop)
            dist = (R.x - L.x)
            if dist > 200 and not self.yolk_dropped:
                self.start_yolk_drop(bowl)
            self.update_yolk(dt, bowl)
            if self.yolk_dropped:
                pygame.draw.circle(self.screen, YOLK, (bowl.centerx, int(self.yolk_y)), 22)

            info = self.font.render("Pull the shells apart until the yolk drops!", True, WHITE)
            self.screen.blit(info, (WIDTH//2 - info.get_width()//2, 260))

            if self.egg_done:
                nxt = self.font.render("Great! Press Enter", True, GOLD)
                self.screen.blit(nxt, (WIDTH//2 - nxt.get_width()//2, 290))

    # ---------------- MEASURE (add ingredients) ----------------
    def draw_measure(self, dt):
        self.draw_title("Add ingredients: click & hold each container to pour. Enter when all full.", 24)
        # bowl
        bowl = pygame.Rect(WIDTH//2-160, 340, 320, 160)
        pygame.draw.ellipse(self.screen, (230,230,255), bowl)
        pygame.draw.ellipse(self.screen, WHITE, bowl, 3)

        # containers
        start_x = 80
        y = 130
        w = 90; h = 110; gap = 30
        mouse = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed(3)[0]

        all_full = True
        for i, ing in enumerate(self.ingredients):
            rect = pygame.Rect(start_x + i*(w+gap), y, w, h)
            pygame.draw.rect(self.screen, (60,60,80), rect, border_radius=10)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=10)
            # fill gauge on container
            bar = rect.inflate(-20, -20)
            fill = clamp(ing["added"]/ing["needed"], 0.0, 1.0)
            filled_h = int(bar.height * fill)
            if filled_h > 0:
                pygame.draw.rect(self.screen, ing["color"], pygame.Rect(bar.x, bar.bottom - filled_h, bar.width, filled_h), border_radius=6)
            name = self.font.render(ing["name"].capitalize(), True, WHITE)
            self.screen.blit(name, (rect.centerx - name.get_width()//2, rect.bottom + 6))

            if rect.collidepoint(mouse) and pressed and fill < 1.0:
                # pour into bowl
                ing["added"] += 0.8 * dt  # pour rate
                # stream
                sx = rect.centerx
                pygame.draw.line(self.screen, ing["color"], (sx, rect.bottom), (bowl.centerx, bowl.centery-20), 4)

            if fill < 1.0:
                all_full = False

        if all_full:
            txt = self.font.render("All set — Enter to Mix", True, GOLD)
            self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 310))

    # ---------------- MIX ----------------
    def draw_mix_step(self, dt):
        self.draw_title("Mix: click & hold inside the bowl to stir. Enter when smooth.", 24)
        bowl = pygame.Rect(WIDTH//2-180, 340, 360, 180)
        pygame.draw.ellipse(self.screen, (235,235,255), bowl)
        pygame.draw.ellipse(self.screen, WHITE, bowl, 3)

        mx, my = pygame.mouse.get_pos()
        if bowl.collidepoint(mx, my) and pygame.mouse.get_pressed(3)[0]:
            self.mix_progress = clamp(self.mix_progress + 0.6*dt, 0, 1)
            # swirl trail
            for i in range(50):
                t = (self.t*2 + i*0.07) % 1.0
                a = t * math.tau
                r = 120 * (1 - t*0.85)
                x = bowl.centerx + math.cos(a)*r*0.9
                y = bowl.centery + math.sin(a)*r*0.45
                self.screen.set_at((int(x), int(y)), (255,230,240))

        prog = self.font.render(f"Progress: {int(self.mix_progress*100)}%", True, WHITE)
        self.screen.blit(prog, (WIDTH//2 - prog.get_width()//2, 310))
        if self.mix_progress >= 1.0:
            txt = self.font.render("Looks perfect — Enter!", True, GOLD)
            self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 290))

    # ---------------- PANS ----------------
    def compute_pans_score(self):
        lows, highs = PAN_TARGET
        rng = max(1e-6, highs - lows)
        total = 0.0
        for p in self.pans:
            frac = p["fill"]/p["cap"]
            if lows <= frac <= highs:
                total += 1.0
            else:
                d = (lows - frac)/rng if frac < lows else (frac - highs)/rng
                total += max(0.0, 1.0 - d)
        self.score_pans = total / len(self.pans)

    def draw_pans(self, dt):
        self.draw_title("Pans: Left=pour, Right=scoop. Fill to the teal band, then Enter.", 24)
        lows, highs = PAN_TARGET
        for p in self.pans:
            cx, cy = p["center"]; r = p["r"]
            # pan look
            pygame.draw.circle(self.screen, (90, 90, 110), p["center"], r)
            pygame.draw.circle(self.screen, WHITE, p["center"], r, 3)
            # target band
            rr_low = int(r * (0.15 + 0.7*lows))
            rr_high = int(r * (0.15 + 0.7*highs))
            pygame.draw.circle(self.screen, TEAL, p["center"], rr_low, 2)
            pygame.draw.circle(self.screen, TEAL, p["center"], rr_high, 2)
            # fill (inner disk)
            frac = clamp(p["fill"]/p["cap"], 0.0, 1.0)
            rr_fill = int(r * (0.15 + 0.7*frac))
            if rr_fill > 0:
                pygame.draw.circle(self.screen, (235,210,255), p["center"], rr_fill)
                pygame.draw.circle(self.screen, (210,180,240), p["center"], rr_fill, 2)
            # check mark
            ok = lows <= frac <= highs
            if ok:
                pygame.draw.circle(self.screen, (90,200,140), (cx + r-24, cy - r+24), 12)
                pygame.draw.circle(self.screen, WHITE, (cx + r-24, cy - r+24), 12, 2)
                pygame.draw.line(self.screen, WHITE, (cx + r-30, cy - r+22), (cx + r-24, cy - r+28), 2)
                pygame.draw.line(self.screen, WHITE, (cx + r-24, cy - r+28), (cx + r-16, cy - r+18), 2)

        # pour/scoop
        pressed = pygame.mouse.get_pressed(3)
        if pressed[0] or pressed[2]:
            mx, my = pygame.mouse.get_pos()
            for p in self.pans:
                cx, cy = p["center"]; r = p["r"]
                if (mx-cx)**2 + (my-cy)**2 <= r*r:
                    if pressed[0]:
                        p["fill"] = min(p["cap"], p["fill"] + PAN_FILL_RATE*dt)
                    else:
                        p["fill"] = max(0.0, p["fill"] - PAN_UNFILL_RATE*dt)

        # live score readout
        self.compute_pans_score()
        score = self.font.render(f"Pan accuracy: {int(self.score_pans*100)}%", True, GOLD)
        self.screen.blit(score, (WIDTH//2 - score.get_width()//2, 62))

        tip = self.font.render("Enter continues", True, WHITE)
        self.screen.blit(tip, (WIDTH//2 - tip.get_width()//2, 90))

    # ---------------- OVEN ----------------
    def draw_oven(self, dt):
        self.draw_title("Oven: ←/→ temp • ↑/↓ time • Space start/stop • Enter take out", 24)

        oven = pygame.Rect(WIDTH//2 - 240, 210, 480, 320)
        pygame.draw.rect(self.screen, (55, 55, 70), oven, border_radius=16)
        pygame.draw.rect(self.screen, WHITE, oven, 2, border_radius=16)

        # slider
        slider = pygame.Rect(oven.x + 30, oven.y + 40, oven.width - 60, 10)
        pygame.draw.rect(self.screen, GREY, slider, border_radius=5)
        t = clamp((self.oven_temp - 250) / 200, 0.0, 1.0)
        knob_x = int(slider.x + t * slider.width)
        pygame.draw.circle(self.screen, GOLD, (knob_x, slider.y + 5), 10)
        lab = self.font.render(f"Temp: {self.oven_temp}°F", True, WHITE)
        self.screen.blit(lab, (slider.x, slider.y - 26))

        # timer display
        timer_box = pygame.Rect(oven.x + 160, oven.y + 90, 160, 60)
        pygame.draw.rect(self.screen, (40, 40, 60), timer_box, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, timer_box, 2, border_radius=10)
        tim = self.big.render(f"{self.oven_timer:0.1f}s", True, WHITE)
        self.screen.blit(tim, (timer_box.centerx - tim.get_width() // 2,
                               timer_box.centery - tim.get_height() // 2))

        if self.oven_running:
            self.oven_timer += dt

        done = self.font.render("Enter to take out cake", True, GOLD)
        self.screen.blit(done, (WIDTH//2 - done.get_width()//2, oven.bottom + 48))

    # ---------------- STACK ----------------
    def draw_stack(self, dt):
        self.draw_title("Stacked! Press Enter to Decorate", 30)
        if self.needs_base_rebuild: self.rebuild_base_layer()
        self.screen.blit(self.base_layer, (0, 0))

    # ---------------- DECORATE ----------------
    def get_tier_region_at(self, pos):
        """Returns (tier_index, 'top'|'side') or (None, None)."""
        x, y = pos
        for idx in range(len(self.tiers)-1, -1, -1):
            t = self.tiers[idx]
            if t.inside_top(x, y): return idx, 'top'
            if t.inside_side(x, y): return idx, 'side'
        return None, None

    def clip_brush_radius_top(self, tier: Tier, x: float, y: float, r: int) -> int:
        cx, cy = tier.center
        dx, dy = (x - cx), (y - cy)
        rx, ry = tier.r, tier.ry
        if dx == 0 and dy == 0:
            margin = min(rx, ry)
        else:
            denom = (dx*dx)/(rx*rx) + (dy*dy)/(ry*ry)
            if denom <= 0: return 0
            s = 1.0 / math.sqrt(denom)
            D = math.hypot(dx, dy)
            boundary = s * D
            margin = boundary - D
        if margin <= 0: return 0
        return int(min(r, margin))

    def clip_brush_radius_side(self, tier: Tier, x: float, y: float, r: int) -> int:
        rect = tier.side_rect()
        if not rect.collidepoint(x, y): return 0
        dleft   = x - rect.left
        dright  = rect.right - x
        dtop    = y - rect.top
        dbottom = rect.bottom - y
        margin = min(dleft, dright, dtop, dbottom)
        if margin <= 0: return 0
        return int(min(r, margin))

    def paint_circle(self, surf, x, y, r, col):
        aa_dot(surf, x, y, r, col)

    def draw_line(self, surf, p0, p1, r, col, tier=None, region=None):
        x0, y0 = p0; x1, y1 = p1
        dist = max(1, int(math.hypot(x1-x0, y1-y0)))
        step = max(1, int(r * 0.6))
        for i in range(0, dist + 1, step):
            t = i / max(1, dist)
            x = x0 + (x1-x0) * t
            y = y0 + (y1-y0) * t
            rr = r
            if tier is not None and region is not None:
                if region == 'top':
                    rr = self.clip_brush_radius_top(tier, x, y, r)
                else:
                    rr = self.clip_brush_radius_side(tier, x, y, r)
            if rr > 0:
                aa_dot(surf, x, y, rr, col)

    def sprinkle_burst(self, surf, x, y):
        for _ in range(22):
            ang = random.random() * math.tau
            d = random.uniform(0, self.brush_size*1.4)
            sx = x + math.cos(ang) * d
            sy = y + math.sin(ang) * d
            col = random.choice(PALETTE[:6])
            pygame.gfxdraw.filled_circle(surf, int(sx), int(sy), random.randint(2, 4), col)

    def draw_dec_ui(self):
        y = HEIGHT - 64
        self.screen.blit(self.font.render("Colors (1-9)", True, WHITE), (30, y-34))
        for i, col in enumerate(PALETTE):
            x = 30 + i*42
            pygame.draw.circle(self.screen, col, (x, y), 16)
            if col == self.brush_color:
                pygame.draw.circle(self.screen, WHITE, (x, y), 18, 2)
        tips = f"Tool:{self.tool.upper()}  Size:{self.brush_size}  Tier:{self.sel_tier+1} {self.sel_region.upper()}  B/E/F/S • [/] size • Ctrl+Z/Y undo/redo • Alt Eyedropper • Ctrl+S Save • Enter done"
        self.screen.blit(self.font.render(tips, True, WHITE), (30, y+14))

    def draw_decorate(self, dt):
        self.draw_title("Decorate: click a tier (top or side) to select; paint stays inside.", 26)
        # bases (cached)
        if self.needs_base_rebuild: self.rebuild_base_layer()
        self.screen.blit(self.base_layer, (0, 0))

        # frosting layers
        for tier in self.tiers:
            self.screen.blit(tier.side_surf, (0,0))
            self.screen.blit(tier.top_surf, (0,0))

        # selection glow
        sel = self.tiers[self.sel_tier]
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        if self.sel_region == 'top':
            rect = sel.top_rect().inflate(12, 12)
            pygame.draw.ellipse(glow, (255,245,170,80), rect)
            pygame.draw.ellipse(glow, (255,245,170,140), rect, 3)
        else:
            rect = sel.side_rect().inflate(12, 12)
            pygame.draw.rect(glow, (255,245,170,60), rect, border_radius=8)
            pygame.draw.rect(glow, (255,245,170,140), rect, 3, border_radius=8)
        self.screen.blit(glow, (0,0))

        self.draw_dec_ui()

        # brush ghost (edge-aware, AA)
        mx, my = pygame.mouse.get_pos()
        tier = self.tiers[self.sel_tier]
        r_preview = (self.clip_brush_radius_top(tier, mx, my, self.brush_size)
                     if self.sel_region == 'top'
                     else self.clip_brush_radius_side(tier, mx, my, self.brush_size))
        if r_preview > 0:
            ghost = pygame.Surface((2*r_preview+4, 2*r_preview+4), pygame.SRCALPHA)
            gx, gy = r_preview+2, r_preview+2
            # fill
            col = self.brush_color if self.tool != 'eraser' else BASE_ICING
            pygame.gfxdraw.filled_circle(ghost, gx, gy, r_preview, (*col, 60))
            pygame.gfxdraw.aacircle(ghost, gx, gy, r_preview, (255,255,255,140))
            self.screen.blit(ghost, (mx-gx, my-gy))

    # ---------------- RESULTS ----------------
    def draw_results(self, dt):
        self.draw_title("YUM! Press Esc to quit.", 34)
        if self.needs_base_rebuild: self.rebuild_base_layer()
        self.screen.blit(self.base_layer, (0, 0))
        for tier in self.tiers:
            self.screen.blit(tier.side_surf, (0,0))
            self.screen.blit(tier.top_surf, (0,0))

    # ---------------- APPLY TOOL ----------------
    def apply_tool(self, pos, start=False):
        x, y = pos
        tier = self.tiers[self.sel_tier]
        if self.sel_region == 'top':
            surf = tier.top_surf
            limit = self.clip_brush_radius_top(tier, x, y, self.brush_size)
        else:
            surf = tier.side_surf
            limit = self.clip_brush_radius_side(tier, x, y, self.brush_size)

        if start and limit <= 0 and self.tool != 'fill':
            return

        if self.tool == 'brush':
            if self.last_pos is None:
                if limit > 0: self.paint_circle(surf, x, y, limit, self.brush_color)
            else:
                self.draw_line(surf, self.last_pos, (x,y), self.brush_size, self.brush_color, tier, self.sel_region)
            self.last_pos = (x, y)
        elif self.tool == 'eraser':
            if self.last_pos is None:
                if limit > 0: self.paint_circle(surf, x, y, limit, BASE_ICING)
            else:
                self.draw_line(surf, self.last_pos, (x,y), self.brush_size, BASE_ICING, tier, self.sel_region)
            self.last_pos = (x, y)
        elif self.tool == 'fill':
            # fill entire region
            if start:
                if self.sel_region == 'top':
                    pygame.draw.ellipse(surf, self.brush_color, tier.top_rect())
                else:
                    pygame.draw.rect(surf, self.brush_color, tier.side_rect())
        elif self.tool == 'sprinkles':
            if start: self.sprinkle_burst(surf, x, y)

    # ------------ Stroke smoothing (called on mouse-up) ------------
    def redraw_smoothed_stroke(self):
        if not self.stroke_points or self.stroke_snapshot is None:
            return
        # restore before beautifying
        tier = self.tiers[self.sel_tier]
        surf = tier.top_surf if self.sel_region == 'top' else tier.side_surf
        surf.blit(self.stroke_snapshot, (0,0))

        # build smoothed path
        pts = self.stroke_points
        # Add virtual endpoints for Catmull if needed
        if len(pts) >= 2:
            pts = [pts[0]] + pts + [pts[-1]]
        smooth = catmull_rom(pts, samples=10)

        # draw AA dots along smoothed path with edge-aware clipping
        color = self.brush_color if self.tool == 'brush' else BASE_ICING
        r = self.brush_size
        step = max(1, int(r * 0.5))
        for i in range(0, len(smooth)-1):
            x, y = smooth[i]
            if self.sel_region == 'top':
                rr = self.clip_brush_radius_top(tier, x, y, r)
            else:
                rr = self.clip_brush_radius_side(tier, x, y, r)
            if rr > 0:
                aa_dot(surf, x, y, rr, color)

    # ---------------- Export PNG ----------------
    def export_png(self, path="cake.png"):
        out = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        if self.needs_base_rebuild: self.rebuild_base_layer()
        out.blit(self.base_layer, (0,0))
        for t in self.tiers:
            out.blit(t.side_surf, (0,0))
            out.blit(t.top_surf, (0,0))
        try:
            pygame.image.save(out, path)
            self.toast_text = f"Saved {path}"
        except Exception as ex:
            self.toast_text = f"Save failed: {ex}"
        self.toast_timer = 2.0

    # ---------------- LOOP ----------------
    def run(self):
        running = True
        prev_secs = pygame.time.get_ticks() / 1000.0

        while running:
            now_secs = pygame.time.get_ticks() / 1000.0
            dt = min(0.05, now_secs - prev_secs)
            prev_secs = now_secs
            self.t += dt

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: running = False

                    # global save (decorate/results)
                    if (e.key == pygame.K_s) and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        if self.state in ('DECORATE','RESULTS'):
                            self.export_png("cake.png")

                    if self.state == 'EGGS':
                        if e.key == pygame.K_RETURN and self.egg_done:
                            self.state = 'MEASURE'

                    elif self.state == 'MEASURE':
                        if e.key == pygame.K_RETURN and all(ing["added"] >= ing["needed"] for ing in self.ingredients):
                            self.state = 'MIX'

                    elif self.state == 'MIX':
                        if e.key == pygame.K_RETURN and self.mix_progress >= 1.0:
                            self.state = 'PANS'

                    elif self.state == 'PANS':
                        if e.key == pygame.K_RETURN:
                            self.compute_pans_score()
                            self.state = 'OVEN'

                    elif self.state == 'OVEN':
                        if e.key == pygame.K_SPACE:
                            self.oven_running = not self.oven_running
                        elif e.key == pygame.K_LEFT:
                            self.oven_temp = max(250, self.oven_temp-5)
                        elif e.key == pygame.K_RIGHT:
                            self.oven_temp = min(450, self.oven_temp+5)
                        elif e.key == pygame.K_UP:
                            self.oven_timer = min(99.9, self.oven_timer + 1)
                        elif e.key == pygame.K_DOWN:
                            self.oven_timer = max(0.0, self.oven_timer - 1)
                        elif e.key == pygame.K_RETURN:
                            temp_score = max(0, 1 - abs(self.oven_temp-OVEN_TARGET_TEMP)/75)
                            time_score = max(0, 1 - abs(self.oven_timer-OVEN_TARGET_TIME)/4)
                            self.score_bake = (temp_score*0.5 + time_score*0.5)
                            set_cake_palette('baked')
                            self.needs_base_rebuild = True  # palette changed; rebuild base visuals
                            self.state = 'STACK'

                    elif self.state == 'STACK':
                        if e.key == pygame.K_RETURN:
                            self.state = 'DECORATE'

                    elif self.state == 'DECORATE':
                        if e.key == pygame.K_RETURN:
                            self.state = 'RESULTS'
                        elif e.key == pygame.K_b: self.tool = 'brush'
                        elif e.key == pygame.K_e: self.tool = 'eraser'
                        elif e.key == pygame.K_f: self.tool = 'fill'
                        elif e.key == pygame.K_s: self.tool = 'sprinkles'
                        elif e.key == pygame.K_LEFTBRACKET:
                            self.brush_size = max(2, self.brush_size - 1)
                        elif e.key == pygame.K_RIGHTBRACKET:
                            self.brush_size = min(64, self.brush_size + 1)
                        elif e.unicode in '123456789':
                            idx = int(e.unicode) - 1
                            if 0 <= idx < len(PALETTE): self.brush_color = PALETTE[idx]
                        # Undo/Redo
                        elif (e.key == pygame.K_z) and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            if self.history:
                                idx, top_snap, side_snap = self.history.pop()
                                cur = self.tiers[idx]
                                self.redo.append((idx, cur.top_surf.copy(), cur.side_surf.copy()))
                                cur.top_surf.blit(top_snap, (0,0))
                                cur.side_surf.blit(side_snap, (0,0))
                        elif (e.key == pygame.K_y) and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            if self.redo:
                                idx, top_snap, side_snap = self.redo.pop()
                                cur = self.tiers[idx]
                                self.history.append((idx, cur.top_surf.copy(), cur.side_surf.copy()))
                                cur.top_surf.blit(top_snap, (0,0))
                                cur.side_surf.blit(side_snap, (0,0))

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3):
                    if self.state == 'EGGS':
                        mx, my = e.pos
                        cx, cy = self.egg_center
                        if self.egg_taps < EGG_TAPS_TO_CRACK:
                            whole_rect = pygame.Rect(cx-70, cy-90, 140, 180)
                            if whole_rect.collidepoint(mx, my):
                                self.egg_taps += 1
                                if self.egg_taps >= EGG_TAPS_TO_CRACK:
                                    self.reset_egg_positions()
                        else:
                            lrect = pygame.Rect(self.left_pos[0], self.left_pos[1], 70, 180)
                            rrect = pygame.Rect(self.right_pos[0], self.right_pos[1], 70, 180)
                            if lrect.collidepoint(mx, my):
                                self.dragging_side = 'left'
                                self.drag_offset = (mx - self.left_pos[0], my - self.left_pos[1])
                            elif rrect.collidepoint(mx, my):
                                self.dragging_side = 'right'
                                self.drag_offset = (mx - self.right_pos[0], my - self.right_pos[1])

                    elif self.state == 'DECORATE':
                        # Eyedropper if Alt held: pick from selected layer
                        if pygame.key.get_mods() & pygame.KMOD_ALT:
                            idx, reg = self.get_tier_region_at(e.pos)
                            if idx is not None:
                                self.sel_tier, self.sel_region = idx, reg
                                t = self.tiers[idx]
                                surf = t.top_surf if reg == 'top' else t.side_surf
                                x, y = e.pos
                                col = surf.get_at((int(x), int(y)))
                                self.brush_color = (col[0], col[1], col[2])
                            continue

                        idx, reg = self.get_tier_region_at(e.pos)
                        if idx is not None:
                            self.sel_tier = idx
                            self.sel_region = reg
                            # snapshot this tier’s paint layers for Undo
                            t = self.tiers[self.sel_tier]
                            self.history.append((self.sel_tier, t.top_surf.copy(), t.side_surf.copy()))
                            if len(self.history) > 40: self.history.pop(0)
                            self.redo.clear()

                            # stroke smoothing setup
                            self.stroke_points = [e.pos]
                            self.stroke_snapshot = (t.top_surf.copy() if reg == 'top' else t.side_surf.copy())

                            self.last_pos = e.pos
                            # temporarily swap to eraser if right-click
                            tool_backup = self.tool
                            if e.button == 3: self.tool = 'eraser'
                            self.apply_tool(e.pos, start=True)
                            self.tool = tool_backup

                elif e.type == pygame.MOUSEBUTTONUP and e.button in (1, 3):
                    # apply smoothing pass on stroke end (only for brush/eraser)
                    if self.state == 'DECORATE' and self.tool in ('brush','eraser'):
                        self.redraw_smoothed_stroke()
                    self.last_pos = None
                    self.dragging_side = None
                    self.pouring_idx = None
                    self.stroke_points.clear()
                    self.stroke_snapshot = None

                elif e.type == pygame.MOUSEMOTION:
                    if self.state == 'DECORATE' and (e.buttons[0] or e.buttons[2]):
                        tool_backup = self.tool
                        if e.buttons[2]: self.tool = 'eraser'  # right-drag = erase
                        self.apply_tool(e.pos)
                        self.tool = tool_backup
                        # record for smoothing
                        self.stroke_points.append(e.pos)
                    elif self.state == 'EGGS' and self.dragging_side:
                        mx, my = e.pos
                        if self.dragging_side == 'left':
                            self.left_pos[0] = min(mx - self.drag_offset[0], self.egg_center[0] - 10)
                            self.left_pos[1] = my - self.drag_offset[1]
                        else:
                            self.right_pos[0] = max(mx - self.drag_offset[0], self.egg_center[0] + 10)
                            self.right_pos[1] = my - self.drag_offset[1]

            # -------- DRAW --------
            self.draw_bg(self.t)
            if   self.state == 'EGGS':      self.draw_egg_step(dt)
            elif self.state == 'MEASURE':   self.draw_measure(dt)
            elif self.state == 'MIX':       self.draw_mix_step(dt)
            elif self.state == 'PANS':      self.draw_pans(dt)
            elif self.state == 'OVEN':      self.draw_oven(dt)
            elif self.state == 'STACK':     self.draw_stack(dt)
            elif self.state == 'DECORATE':  self.draw_decorate(dt)
            elif self.state == 'RESULTS':   self.draw_results(dt)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.display.quit()
        pygame.quit()

# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    Game().run()
