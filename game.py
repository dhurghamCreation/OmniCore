import json
import math
import os
import random
import asyncio
import struct
import time
from array import array
from collections import deque
from copy import deepcopy
from datetime import datetime

import pygame

APP_VERSION = "3.5.0"
TILE_SIZE = 72
SCREEN_RES = (1280, 800)
FPS = 60

SAVE_FILE = "savegame.json"

THEMES = [
    {
        "name": "Neon Abyss",
        "bg_a": (6, 10, 21),
        "bg_b": (10, 20, 36),
        "wall": (39, 48, 74),
        "player": (39, 241, 255),
        "clone": (255, 83, 214),
        "box": (255, 123, 107),
        "goal": (198, 255, 84),
        "portal": (127, 96, 255),
        "ice": (168, 226, 255),
        "hud": (10, 13, 31),
        "hud_text": (232, 240, 255),
        "sub": (142, 162, 196),
        "accent": (255, 200, 50),
        "danger": (255, 80, 80),
        "success": (80, 255, 120),
    },
    {
        "name": "Solar Pulse",
        "bg_a": (22, 11, 8),
        "bg_b": (45, 16, 10),
        "wall": (84, 45, 31),
        "player": (255, 186, 56),
        "clone": (255, 108, 52),
        "box": (255, 76, 88),
        "goal": (250, 235, 84),
        "portal": (127, 209, 255),
        "ice": (174, 226, 255),
        "hud": (39, 17, 13),
        "hud_text": (255, 238, 223),
        "sub": (214, 166, 141),
        "accent": (255, 220, 100),
        "danger": (255, 60, 60),
        "success": (100, 255, 100),
    },
    {
        "name": "Emerald Circuit",
        "bg_a": (5, 17, 14),
        "bg_b": (7, 33, 24),
        "wall": (33, 67, 54),
        "player": (86, 255, 185),
        "clone": (74, 208, 255),
        "box": (125, 255, 92),
        "goal": (251, 255, 125),
        "portal": (105, 128, 255),
        "ice": (145, 232, 255),
        "hud": (8, 24, 21),
        "hud_text": (226, 255, 242),
        "sub": (132, 183, 163),
        "accent": (255, 230, 80),
        "danger": (255, 70, 70),
        "success": (90, 255, 130),
    },
    {
        "name": "Candy Clash",
        "bg_a": (30, 8, 35),
        "bg_b": (50, 12, 45),
        "wall": (80, 40, 70),
        "player": (255, 130, 220),
        "clone": (130, 255, 200),
        "box": (255, 200, 100),
        "goal": (255, 255, 180),
        "portal": (200, 130, 255),
        "ice": (200, 230, 255),
        "hud": (35, 10, 30),
        "hud_text": (255, 230, 250),
        "sub": (200, 150, 190),
        "accent": (255, 150, 255),
        "danger": (255, 100, 100),
        "success": (150, 255, 150),
    },
    {
        "name": "Ocean Depths",
        "bg_a": (5, 15, 30),
        "bg_b": (8, 25, 45),
        "wall": (25, 55, 80),
        "player": (100, 200, 255),
        "clone": (255, 150, 100),
        "box": (80, 180, 220),
        "goal": (200, 255, 200),
        "portal": (150, 100, 255),
        "ice": (180, 220, 255),
        "hud": (8, 18, 35),
        "hud_text": (200, 230, 255),
        "sub": (120, 160, 200),
        "accent": (255, 220, 100),
        "danger": (255, 80, 80),
        "success": (100, 255, 180),
    },
]


class NeonParticle:
    def __init__(self, x, y, color, speed=(1.0, 4.0), decay=0.025):
        self.x = float(x)
        self.y = float(y)
        angle = random.uniform(0, math.pi * 2)
        velocity = random.uniform(speed[0], speed[1])
        self.vx = math.cos(angle) * velocity
        self.vy = math.sin(angle) * velocity
        self.life = 1.0
        self.decay = decay
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        return self.life > 0

    def draw(self, surface):
        radius = int(2 + self.life * 4)
        if radius <= 0:
            return
        color = tuple(max(0, min(255, int(c * self.life + 20))) for c in self.color)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), radius)


class Star:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(0, SCREEN_RES[0])
        self.y = random.uniform(0, SCREEN_RES[1])
        self.z = random.uniform(0.2, 1.0)
        self.twinkle_speed = random.uniform(1.0, 4.0)
        self.twinkle_offset = random.uniform(0, math.pi * 2)

    def update(self, dt, time_sec):
        self.y += (20 + 40 * self.z) * dt
        if self.y > SCREEN_RES[1]:
            self.y = 0
            self.x = random.uniform(0, SCREEN_RES[0])

    def draw(self, surface, time_sec):
        twinkle = int(60 * math.sin(time_sec * self.twinkle_speed + self.twinkle_offset))
        b = max(50, min(255, int(130 + 125 * self.z + twinkle)))
        pygame.draw.circle(surface, (b, b, b), (int(self.x), int(self.y)), int(1 + self.z * 2))


class FloatingText:
    def __init__(self, x, y, text, color, size=20, lifetime=1.5):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        self.y -= 30 * dt
        return self.age < self.lifetime

    def draw(self, surface, font):
        alpha = max(0, int(255 * (1 - self.age / self.lifetime)))
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (self.x, self.y))


class ConfettiParticle:
    def __init__(self, x, y, color, drift=(0.0, 0.0)):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-5.0, 5.0) + drift[0]
        self.vy = random.uniform(-9.0, -2.0) + drift[1]
        self.spin = random.uniform(-0.3, 0.3)
        self.size = random.randint(4, 8)
        self.life = random.uniform(0.9, 1.8)
        self.age = 0.0
        self.color = color

    def update(self):
        self.age += 1 / FPS
        self.vy += 0.28
        self.x += self.vx
        self.y += self.vy
        self.vx += self.spin
        return self.age < self.life

    def draw(self, surface):
        alpha = max(0, int(255 * (1 - self.age / self.life)))
        color = tuple(max(0, min(255, int(c + alpha * 0.15))) for c in self.color)
        rect = pygame.Rect(int(self.x), int(self.y), self.size, max(2, self.size // 2))
        pygame.draw.rect(surface, color, rect, border_radius=2)


class AIOpponent:
    """Smart AI that actually solves levels with visible movement"""
    def __init__(self, name="CyberBrain", difficulty="medium"):
        self.name = name
        self.difficulty = difficulty
        self.current_level = 0
        self.completed = 0
        self.total_score = 0
        self.move_count = 0
        self.thinking = False
        self.thought_progress = 0.0
        self.last_result = {"rating": "-", "score": 0, "time": 0, "moves": 0}
        self.ai_path = []
        self.ai_path_index = 0
        self.ai_move_timer = 0.0
        self.ai_moving = False
        self.ai_grid_pos = [1, 1]
        self.ai_visual_pos = [float(1), float(1)]
        self.ai_solved = False
        self.ai_time = 0.0
        self.ai_step_delay = {"easy": 0.34, "medium": 0.22, "hard": 0.14, "extreme": 0.08}[difficulty]
        self.think_speed = {"easy": 1.0, "medium": 2.8, "hard": 5.8, "extreme": 9.5}[difficulty]
        self.ai_quality = {"easy": 0.25, "medium": 0.55, "hard": 0.82, "extreme": 0.97}[difficulty]

    def think(self, dt):
        if self.thinking:
            self.thought_progress += dt * self.think_speed
            if self.thought_progress >= 1.0:
                self.thinking = False
                self.thought_progress = 0.0
                return True
        return False

    def start_thinking(self):
        self.thinking = True
        self.thought_progress = 0.0
        self.ai_solved = False
        self.ai_moving = False
        self.ai_path = []
        self.ai_path_index = 0
        self.ai_move_timer = 0.0
        self.ai_time = 0.0

    def generate_path(self, grid, entities, portals, player_start):
        self.ai_path = []
        self.ai_grid_pos = list(player_start)
        self.ai_visual_pos = [float(player_start[0]), float(player_start[1])]
        self.ai_path.append(list(player_start))
        self.ai_path_index = 0
        self.ai_moving = True
        self.ai_solved = False

        goals = []
        boxes = []
        for y, row in enumerate(grid):
            for x, val in enumerate(row):
                if val == 2:
                    goals.append((x, y))
        for e in entities:
            if e["type"] == 3:
                boxes.append(tuple(e["grid"]))

        if not goals or not boxes:
            self.ai_moving = False
            self.ai_solved = True
            return

        blocked = {(x, y) for y, row in enumerate(grid) for x, value in enumerate(row) if value in (1, 13)}
        width = len(grid[0])
        height = len(grid)

        def bfs(start, goal):
            queue = deque([start])
            came_from = {start: None}
            while queue:
                current = queue.popleft()
                if current == goal:
                    break
                cx, cy = current
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if not (0 <= nx < width and 0 <= ny < height):
                        continue
                    if (nx, ny) in blocked or (nx, ny) in came_from:
                        continue
                    came_from[(nx, ny)] = current
                    queue.append((nx, ny))
            if goal not in came_from:
                return []
            path = []
            node = goal
            while node is not None:
                path.append([node[0], node[1]])
                node = came_from[node]
            path.reverse()
            return path

        current = tuple(player_start)
        path = [list(player_start)]
        for goal in goals[:4]:
            goal_path = bfs(current, goal)
            if not goal_path:
                continue
            path.extend(goal_path[1:])
            current = goal
        if len(path) == 1:
            path.extend([[min(width - 2, player_start[0] + 1), player_start[1]]])
        self.ai_path = path
        if len(self.ai_path) > 2 and self.ai_quality < 0.9:
            trimmed = max(3, int(len(self.ai_path) * (0.90 + (1 - self.ai_quality) * 0.05)))
            self.ai_path = self.ai_path[:trimmed]
        self.ai_path_index = 1 if len(self.ai_path) > 1 else 0

    def update_movement(self, dt):
        if not self.ai_moving or self.ai_path_index >= len(self.ai_path):
            if self.ai_moving:
                self.ai_moving = False
                self.ai_solved = True
            return
        
        self.ai_move_timer += dt
        move_speed = self.ai_step_delay
        
        if self.ai_move_timer >= move_speed:
            self.ai_move_timer = 0.0
            if self.ai_path_index < len(self.ai_path):
                target = self.ai_path[self.ai_path_index]
                self.ai_grid_pos = list(target)
                self.ai_path_index += 1
                self.ai_time += move_speed

    def get_visual_pos(self):
        if self.ai_path_index < len(self.ai_path):
            target = self.ai_path[self.ai_path_index]
            lerp = min(1.0, self.ai_move_timer / max(0.01, self.ai_step_delay)) if self.ai_move_timer > 0 else 0
            if self.ai_path_index > 0:
                prev = self.ai_path[self.ai_path_index - 1]
            else:
                prev = self.ai_path[0]
            return (prev[0] + (target[0] - prev[0]) * lerp, 
                    prev[1] + (target[1] - prev[1]) * lerp)
        return (self.ai_grid_pos[0], self.ai_grid_pos[1])


class BrilliantEngine:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        
        self.base_width = 1280
        self.base_height = 800
        self.windowed_size = (self.base_width, self.base_height)
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        global SCREEN_RES
        SCREEN_RES = self.screen.get_size()
        pygame.display.set_caption(f"Omni Core Redux v{APP_VERSION} | Puzzle Battle")
        pygame.display.set_icon(pygame.Surface((32, 32)))
        self.clock = pygame.time.Clock()

        self.running = True
        self.state = "welcome"
        self.previous_state = "welcome"
        self.paused = False
        self.theme_index = 0
        self.theme = THEMES[self.theme_index]
        self.player_name = os.getenv("USERNAME", "Player")[:16]
        self.name_input = self.player_name
        self.pending_mode = "campaign"
        self.menu_mode_index = 0
        self.push_assist = True
        
        self.result_type = None
        self.result_message = ""
        self.result_subtitle = ""
        self.result_timer = 0
        self.level_clear_timer = 0.0
        self.pending_clear_state = None

        self.sfx = {}
        self.music = None
        self.music_menu = None
        self.music_gameplay = None
        self.music_daily = None
        self.music_on = False
        self.music_volume = 0.7
        self.music_type = "menu"

        self.level_idx = 0
        self.selected_level = 0
        self.pending_next_level = 0
        self.move_count = 0
        self.level_move_count = 0
        self.level_start_time = time.time()
        self.game_start_time = time.time()
        self.completed_runs = 0
        self.total_score = 0
        self.combo_streak = 0
        self.max_combo = 0
        self.shake = 0
        self.flash = 0

        self.unlocked_level = 1
        self.challenge_start_index = 0
        self.best_scores = {}
        self.leaderboard = []
        self.leaderboard_tab = "campaign"
        self.game_mode = "campaign"
        self.daily_seed = 0
        self.daily_level_indices = []
        self.daily_idx = 0
        self.daily_history = {}
        self.daily_streak = 0
        self.coins = 0
        self.weekly_badges = []
        self.owned_skins = ["classic"]
        self.box_skin = "classic"
        
        self.store_items = [
            {"id": "diamond", "name": "💎 Diamond Box", "price": 35, "category": "skins", "desc": "Shiny diamond-shaped box"},
            {"id": "rounded", "name": "⚪ Rounded Box", "price": 45, "category": "skins", "desc": "Smooth rounded edges"},
            {"id": "hollow", "name": "◻ Hollow Box", "price": 60, "category": "skins", "desc": "Transparent hollow design"},
            {"id": "glitch", "name": "👾 Glitch Box", "price": 85, "category": "skins", "desc": "Corrupted glitch effect"},
            {"id": "flame", "name": "🔥 Flame Box", "price": 120, "category": "skins", "desc": "Burning with fire"},
            {"id": "crystal", "name": "💠 Crystal Box", "price": 150, "category": "skins", "desc": "Pure crystal transparency"},
            {"id": "neon", "name": "✨ Neon Box", "price": 200, "category": "skins", "desc": "Brilliant neon glow"},
            {"id": "cosmic", "name": "🌌 Cosmic Box", "price": 300, "category": "skins", "desc": "Galaxy swirl pattern"},
            {"id": "extra_rescue", "name": "🛟 Extra Rescue", "price": 50, "category": "powerups", "desc": "+1 rescue charge per level"},
            {"id": "time_freeze", "name": "⏸ Time Freeze", "price": 80, "category": "powerups", "desc": "Pause timer for 10s"},
            {"id": "ghost_vision", "name": "👻 Ghost Vision", "price": 100, "category": "powerups", "desc": "See optimal path hint"},
            {"id": "double_coins", "name": "🪙 Double Coins", "price": 120, "category": "powerups", "desc": "2x coins for 3 levels"},
            {"id": "trail_sparkle", "name": "✨ Sparkle Trail", "price": 70, "category": "cosmetics", "desc": "Sparkly movement trail"},
            {"id": "aura_glow", "name": "🌟 Aura Glow", "price": 90, "category": "cosmetics", "desc": "Radiant player aura"},
            {"id": "rainbow_mode", "name": "🌈 Rainbow Mode", "price": 250, "category": "cosmetics", "desc": "All colors cycling!"},
        ]
        self.store_cursor = 0
        self.store_category = 0
        self.store_categories = ["skins", "powerups", "cosmetics"]
        self.store_category_names = ["🎨 BOX SKINS", "⚡ POWER-UPS", "💫 COSMETICS"]
        self.active_powerups = {}
        self.powerup_timers = {}
        
        self.block_highlight_timer = {}
        self.block_visibility = {}
        self.achievements = {
            "first_win": False, "speed_runner": False, "strategist": False,
            "combo_master": False, "perfectionist": False, "level_25": False,
            "level_50": False, "level_100": False, "level_150": False,
            "level_200": False, "coin_collector": False, "skin_collector": False,
            "ai_beater": False,
        }
        self.last_result = {"rating": "-", "score": 0, "time": 0, "moves": 0, "level": 1}

        self.world_particles = []
        self.result_particles = []
        self.ui_particles = []
        self.floating_texts = []
        self.stars = [Star() for _ in range(90)]
        self.rescue_charges = 1
        self.current_trace = []
        self.ghost_runs = {}
        self.active_ghost = []
        self.ghost_step = 0
        self.ghost_tick = 0.0
        self.toast_text = ""
        self.toast_timer = 0
        self.toast_color = None
        self.transition_phase = None
        self.transition_alpha = 0
        self.transition_target_state = None
        
        self.mouse_down = False
        self.mouse_start_pos = (0, 0)
        self.mouse_current_pos = (0, 0)
        self.last_move_dir = (0, 0)
        self.window_mode = "windowed"
        self.window_controls = {}
        
        self.is_boss_level = False
        self.boss_level_rule = None
        
        self.settings = {
            "music_volume": 0.7, "sfx_volume": 0.8, "typing_sound": True,
            "typing_volume": 0.55, "ui_volume": 0.45,
            "difficulty": "normal", "touch_controls": True, "particle_effects": True,
            "screen_shake": True, "ghost_preview": True,
        }
        self.difficulty_profile = {"timer_rate": 1.0, "rescue_bonus": 0, "auto_fix": True}
        self.settings_cursor = 0
        self.settings_scroll = 0
        self.settings_return_state = "menu"
        
        self.welcome_shown = False
        self.welcome_timer = 0
        self.campaign_intro_active = False
        self.campaign_intro_step = 0
        self.campaign_intro_timer = 0.0
        self.loading_progress = 0.0
        self.is_loading = False
        self.career_started = False
        self.career_progress = {}
        self.total_prizes = 0
        self.level_prizes = {}
        self.last_coin_gain = 0
        self.is_portrait = False

        self.alert_active = False
        self.alert_title = ""
        self.alert_message = ""
        self.alert_tips = []
        self.alert_callback = None

        self.game_submode = "single"
        self.ai_opponent = AIOpponent("CyberBrain", "medium")
        self.ai_level = 0
        self.ai_score = 0
        self.ai_moves = 0
        self.ai_thinking = False
        self.ai_has_completed = False
        self.ai_difficulty_index = 1
        self.ai_difficulties = ["easy", "medium", "hard", "extreme"]
        self.ai_difficulty_names = ["🤖 Easy AI", "🤖 Medium AI", "🤖 Hard AI", "🤖 Extreme AI"]
        self.ai_countdown = 120
        self.ai_countdown_active = False
        self.ai_vs_mode = False
        
        self.multiplayer_turn = 0
        self.multiplayer_names = ["Player 1", "Player 2"]
        self.multiplayer_scores = [0, 0]
        self.multiplayer_levels = [0, 0]
        self.multiplayer_wins = [0, 0]
        self.multiplayer_active_player = 0
        self.multiplayer_states = [None, None]
        self.multiplayer_initial_state = None
        self.multiplayer_finished = [False, False]
        self.multiplayer_finish_times = [None, None]
        self.multiplayer_last_winner = 0
        self.multiplayer_switch_pending = None
        
        self.last_typing_time = 0
        self.typing_sound_cooldown = 0.05
        
        self.level_challenges = {}
        
        self._init_levels()
        self._build_daily_plan()
        self._load_assets()
        self._load_audio()
        self._load_progress()
        self.apply_audio_settings()
        self.load_current_level(reset_run_stats=True)

    def _save_path(self):
        return os.path.join(os.path.dirname(__file__), SAVE_FILE)

    def _build_daily_plan(self):
        day_key = datetime.now().strftime("%Y%m%d")
        self.daily_seed = int(day_key)
        rng = random.Random(self.daily_seed)
        all_levels = list(range(len(self.levels)))
        rng.shuffle(all_levels)
        self.daily_level_indices = all_levels[:20]
        self.daily_idx = 0
        self.daily_display_indices = [(i + 1) for i in self.daily_level_indices]

    def set_state(self, new_state, animated=False):
        if animated:
            self.transition_phase = "out"
            self.transition_alpha = 0
            self.transition_target_state = new_state
            return
        self.previous_state = self.state
        self.state = new_state
        self.sync_music_for_state()

    def open_settings(self, return_state=None):
        self.settings_return_state = return_state or ("playing" if self.state == "playing" else "menu")
        self.set_state("settings", animated=True)

    def close_settings(self):
        target = self.settings_return_state or "menu"
        if target == "playing":
            self.paused = False
            self.set_state("playing", animated=True)
        else:
            self.set_state("menu", animated=True)

    def apply_audio_settings(self):
        music_volume = max(0.0, min(1.0, float(self.settings.get("music_volume", 0.7))))
        sfx_volume = max(0.0, min(1.0, float(self.settings.get("sfx_volume", 0.8))))
        if self.music_menu:
            self.music_menu.set_volume((music_volume * 0.45) if self.music_on else 0.0)
        if self.music_gameplay:
            self.music_gameplay.set_volume((music_volume * 0.70) if self.music_on else 0.0)
        if self.music_daily:
            self.music_daily.set_volume((music_volume * 0.72) if self.music_on else 0.0)
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume

    def sync_music_for_state(self):
        if pygame.mixer.get_init() is None:
            return
        if self.state in ("playing", "campaign_intro"):
            active = self.music_daily if self.game_mode == "daily" else self.music_gameplay
            self.music_type = "gameplay"
        else:
            active = self.music_menu
            self.music_type = "menu"
        if not active:
            return
        if self.music is active and pygame.mixer.get_busy():
            self.apply_audio_settings()
            return
        try:
            pygame.mixer.stop()
            self.music = active
            self.apply_audio_settings()
            if self.music_on:
                self.music.play(-1)
        except pygame.error:
            self.music_on = False

    def update_difficulty_profile(self):
        difficulty = self.settings.get("difficulty", "normal")
        profiles = {
            "easy": {"timer_rate": 0.8, "rescue_bonus": 1, "auto_fix": True},
            "normal": {"timer_rate": 1.0, "rescue_bonus": 0, "auto_fix": True},
            "hard": {"timer_rate": 1.2, "rescue_bonus": 0, "auto_fix": False},
            "expert": {"timer_rate": 1.45, "rescue_bonus": 0, "auto_fix": False},
        }
        self.difficulty_profile = profiles.get(difficulty, profiles["normal"])

    def capture_level_state(self):
        return {
            "grid": [row[:] for row in self.grid],
            "entities": [{"type": e["type"], "grid": e["grid"][:], "visual": e["visual"][:]} for e in self.entities],
            "history": [[{"grid": item["grid"][:], "type": item["type"]} for item in step] for step in self.history],
            "move_count": self.move_count,
            "level_move_count": self.level_move_count,
            "level_start_time": self.level_start_time,
            "current_trace": [p[:] for p in self.current_trace],
            "rescue_charges": self.rescue_charges,
            "combo_streak": self.combo_streak,
        }

    def restore_level_state(self, state):
        if not state:
            return
        self.grid = [row[:] for row in state["grid"]]
        self.entities = [{"type": e["type"], "grid": e["grid"][:], "visual": e["visual"][:]} for e in state["entities"]]
        self.history = [[{"grid": item["grid"][:], "type": item["type"]} for item in step] for step in state["history"]]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.move_count = state.get("move_count", self.move_count)
        self.level_move_count = state.get("level_move_count", self.level_move_count)
        self.level_start_time = state.get("level_start_time", self.level_start_time)
        self.current_trace = [p[:] for p in state.get("current_trace", [])]
        self.rescue_charges = state.get("rescue_charges", self.rescue_charges)
        self.combo_streak = state.get("combo_streak", self.combo_streak)

    def sync_active_multiplayer_state(self):
        if self.game_mode != "multiplayer" or not self.multiplayer_states[self.multiplayer_active_player]:
            return
        self.multiplayer_states[self.multiplayer_active_player] = self.capture_level_state()

    def switch_multiplayer_board(self, idx):
        if self.game_mode != "multiplayer":
            return
        if idx not in (0, 1):
            return
        if idx == self.multiplayer_active_player:
            return
        self.sync_active_multiplayer_state()
        self.multiplayer_active_player = idx
        self.restore_level_state(self.multiplayer_states[idx])
        # Reset the level timer so each player's time is measured from when THEY start playing
        self.level_start_time = time.time()
        self.set_toast(f"{self.multiplayer_names[idx]} controls this board", seconds=1.0)

    def update_transition(self):
        if self.transition_phase == "out":
            self.transition_alpha = min(255, self.transition_alpha + 22)
            if self.transition_alpha >= 255:
                self.previous_state = self.state
                self.state = self.transition_target_state
                self.sync_music_for_state()
                self.transition_phase = "in"
        elif self.transition_phase == "in":
            self.transition_alpha = max(0, self.transition_alpha - 22)
            if self.transition_alpha <= 0:
                self.transition_phase = None
                self.transition_target_state = None

    def draw_transition_overlay(self):
        if self.transition_phase:
            overlay = pygame.Surface(SCREEN_RES, pygame.SRCALPHA)
            overlay.fill((4, 7, 16, self.transition_alpha))
            self.screen.blit(overlay, (0, 0))

    def set_toast(self, text, seconds=1.3, color=None):
        self.toast_text = text
        self.toast_timer = int(seconds * FPS)
        self.toast_color = color or self.theme.get("goal", (198, 255, 84))

    def add_floating_text(self, x, y, text, color, size=20, lifetime=1.5):
        self.floating_texts.append(FloatingText(x, y, text, color, size, lifetime))

    def show_alert(self, title, message, tips=None, callback=None):
        self.alert_active = True
        self.alert_title = title
        self.alert_message = message
        self.alert_tips = tips or []
        self.alert_callback = callback

    def close_alert(self):
        self.alert_active = False
        if self.alert_callback:
            self.alert_callback()
            self.alert_callback = None

    def compute_daily_streak(self):
        streak = 0
        cursor = datetime.now().date()
        while True:
            key = cursor.strftime("%Y-%m-%d")
            day = self.daily_history.get(key)
            if not day or not day.get("completed", False):
                break
            streak += 1
            cursor = cursor.fromordinal(cursor.toordinal() - 1)
        return streak

    def record_daily_completion(self):
        today = datetime.now().strftime("%Y-%m-%d")
        row = self.daily_history.get(today, {"completed": False, "best_score": 0})
        first_complete_today = not row.get("completed", False)
        row["completed"] = True
        row["best_score"] = max(int(row.get("best_score", 0)), int(self.total_score))
        self.daily_history[today] = row
        self.daily_streak = self.compute_daily_streak()
        if first_complete_today:
            bonus = min(7, self.daily_streak) * 180
            self.total_score += bonus
            self.set_toast(f"Daily streak x{self.daily_streak} bonus +{bonus}", seconds=2.0)
        weekly_total = 0
        base_day = datetime.now().date()
        for i in range(7):
            d = base_day.fromordinal(base_day.toordinal() - i).strftime("%Y-%m-%d")
            weekly_total += int(self.daily_history.get(d, {}).get("best_score", 0))
        reward = None
        if weekly_total >= 18000:
            reward = "Mythic Weekly"
        elif weekly_total >= 12000:
            reward = "Elite Weekly"
        elif weekly_total >= 7000:
            reward = "Rising Weekly"
        if reward and reward not in self.weekly_badges:
            self.weekly_badges.append(reward)
            self.coins += 25
            self.set_toast(f"Weekly badge unlocked: {reward} (+25 coins)", seconds=2.2)

    def _load_image(self, path, size=None):
        if not os.path.exists(path):
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.smoothscale(img, size)
            return img
        except pygame.error:
            return None

    def _load_assets(self):
        base = os.path.dirname(__file__)
        font_path = os.path.join(base, "assets", "fonts", "ModernFont.ttf")
        if os.path.exists(font_path):
            try:
                self.font_title = pygame.font.Font(font_path, 62)
                self.font_hud = pygame.font.Font(font_path, 26)
                self.font_text = pygame.font.Font(font_path, 20)
                self.font_tiny = pygame.font.Font(font_path, 16)
                self.font_big = pygame.font.Font(font_path, 42)
                self.font_giant = pygame.font.Font(font_path, 80)
            except (pygame.error, ValueError):
                self.font_title = pygame.font.SysFont("Impact", 62)
                self.font_hud = pygame.font.SysFont("Verdana", 24, bold=True)
                self.font_text = pygame.font.SysFont("Consolas", 20)
                self.font_tiny = pygame.font.SysFont("Consolas", 16)
                self.font_big = pygame.font.SysFont("Impact", 42)
                self.font_giant = pygame.font.SysFont("Impact", 80)
        else:
            self.font_title = pygame.font.SysFont("Impact", 62)
            self.font_hud = pygame.font.SysFont("Verdana", 24, bold=True)
            self.font_text = pygame.font.SysFont("Consolas", 20)
            self.font_tiny = pygame.font.SysFont("Consolas", 16)
            self.font_big = pygame.font.SysFont("Impact", 42)
            self.font_giant = pygame.font.SysFont("Impact", 80)
        gfx = os.path.join(base, "assets", "gfx")
        self.sprite_floor = self._load_image(os.path.join(gfx, "floor_tile.png"), (TILE_SIZE, TILE_SIZE))
        self.sprite_player = self._load_image(os.path.join(gfx, "player_sprite.png"), (TILE_SIZE - 18, TILE_SIZE - 18))
        self.sprite_glow = self._load_image(os.path.join(gfx, "particle_glow.png"), (68, 68))

    def _load_audio(self):
        self.sfx = {}
        sfx_dir = os.path.join(os.path.dirname(__file__), "assets", "sfx")
        if pygame.mixer.get_init() is None:
            self.music = None
            self.music_menu = None
            self.music_gameplay = None
            self.music_daily = None
            self.music_on = False
            return
        sound_files = {
            "move": "move.wav", "undo": "undo.wav", "solve": "solve.wav",
            "click": "move.wav", "coin": "solve.wav", "buy": "solve.wav",
        }
        for key, filename in sound_files.items():
            sound_path = os.path.join(sfx_dir, filename)
            if os.path.exists(sound_path):
                try:
                    self.sfx[key] = pygame.mixer.Sound(sound_path)
                except pygame.error:
                    self.sfx[key] = None
        self.sfx["box_move"] = self.sfx.get("move")
        self.sfx["box_hit"] = self._build_fx_sound([(178, 0.05), (144, 0.08)], volume=0.24)
        self.sfx["ui_click"] = self._build_fx_sound([(980, 0.03), (1320, 0.04)], volume=0.16)
        self.sfx["typing"] = self._build_fx_sound([(680, 0.02), (860, 0.02)], volume=0.10)
        self.sfx["victory"] = self._build_fx_sound([(523, 0.18), (659, 0.18), (784, 0.22), (1046, 0.26)], volume=0.42)
        self.sfx["defeat"] = self._build_fx_sound([(220, 0.22), (196, 0.22), (174, 0.28), (146, 0.32)], volume=0.45)
        self.music_menu = self._build_music_loop("menu")
        self.music_gameplay = self._build_music_loop("gameplay")
        self.music_daily = self._build_music_loop("daily")
        self.music = self.music_menu
        if self.music:
            self.music_on = True
            self.music.set_volume(0.22)
            try:
                self.music.play(-1)
            except pygame.error:
                self.music = None
                self.music_menu = None
                self.music_gameplay = None
                self.music_daily = None
                self.music_on = False

    def _build_music_loop(self, mode="campaign"):
        if pygame.mixer.get_init() is None:
            return None
        sample_rate = 44100
        beat = 0.32
        if mode == "daily":
            melody = [523, 587, 659, 587, 659, 740, 659, 587, 523, 494, 523, 587]
            bass = [131, 131, 147, 147, 165, 165, 147, 147, 131, 123, 131, 147]
            chord = [261, 330, 392, 330]
        elif mode == "gameplay":
            beat = 0.24
            melody = [392, 494, 587, 659, 740, 659, 587, 494, 440, 494, 523, 587, 659, 587, 523, 494]
            bass = [98, 98, 110, 131, 147, 131, 110, 98, 82, 82, 98, 110, 131, 110, 98, 82]
            chord = [196, 247, 294, 330, 392, 330, 294, 247]
        else:
            melody = [330, 392, 440, 392, 349, 392, 440, 494, 440, 392, 349, 330]
            bass = [82, 82, 98, 110, 98, 82, 74, 82, 65, 82, 74, 82]
            chord = [131, 165, 196, 165]
        data = array("h")
        total = int(len(melody) * beat * sample_rate * 2)
        for i in range(total):
            t = i / sample_rate
            idx = int(t / beat) % len(melody)
            cidx = int(t / (beat * 2)) % len(chord)
            m = melody[idx]
            b = bass[idx]
            c = chord[cidx]
            beat_pos = (t % beat) / beat
            env = max(0.0, 1.0 - beat_pos * 0.55)
            lead = math.sin(2 * math.pi * m * t) * 0.45
            lead += math.sin(2 * math.pi * m * 1.5 * t) * 0.15
            lead += math.sin(2 * math.pi * m * 2.0 * t) * 0.12
            bass_layer = math.sin(2 * math.pi * b * t) * 0.40
            bass_layer += math.sin(2 * math.pi * b * 0.5 * t) * 0.10
            pad = math.sin(2 * math.pi * c * t) * 0.18
            pad += math.sin(2 * math.pi * c * 0.25 * t) * 0.12
            vibrato = math.sin(2 * math.pi * 5.0 * t) * 0.02
            value = (lead + bass_layer + pad + vibrato) * env
            sample = max(-32767, min(32767, int(value * 16000)))
            data.append(sample)
            data.append(sample)
        return pygame.mixer.Sound(buffer=struct.pack("<" + "h" * len(data), *data))

    def _build_fx_sound(self, notes, volume=0.5):
        if pygame.mixer.get_init() is None:
            return None
        sample_rate = 44100
        data = array("h")
        for frequency, duration in notes:
            samples = max(1, int(sample_rate * duration))
            for i in range(samples):
                t = i / sample_rate
                envelope = 1.0 - (i / samples) * 0.8
                tone = math.sin(2 * math.pi * frequency * t)
                tone += 0.4 * math.sin(2 * math.pi * frequency * 0.5 * t)
                sample = max(-32767, min(32767, int(tone * envelope * volume * 16000)))
                data.append(sample)
                data.append(sample)
        return pygame.mixer.Sound(buffer=struct.pack("<" + "h" * len(data), *data))

    def get_hud_width(self):
        base = int(max(220, min(360, SCREEN_RES[0] * 0.27)))
        if self.is_portrait:
            return int(max(200, min(300, SCREEN_RES[0] * 0.33)))
        return base

    def resize_window(self, width, height):
        global SCREEN_RES
        width = max(960, int(width))
        height = max(640, int(height))
        self.windowed_size = (width, height)
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        SCREEN_RES = self.screen.get_size()
        self.is_portrait = height > width

    def toggle_window_mode(self):
        global SCREEN_RES
        if self.window_mode == "windowed":
            self.windowed_size = self.screen.get_size()
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            self.window_mode = "fullscreen"
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.window_mode = "windowed"
        SCREEN_RES = self.screen.get_size()
        self.is_portrait = SCREEN_RES[1] > SCREEN_RES[0]

    def spawn_result_fx(self, result_type):
        self.result_particles = []
        w, h = SCREEN_RES
        colors = []
        if result_type == "win":
            colors = [self.theme["goal"], self.theme["player"], (255, 215, 0), (120, 255, 180), (255, 255, 255)]
        else:
            colors = [self.theme["danger"], self.theme["player"], (255, 190, 190), (120, 160, 255)]
        center = (w // 2, h // 2)
        for _ in range(140 if result_type == "win" else 80):
            px = random.randint(max(0, center[0] - 220), min(w - 1, center[0] + 220))
            py = random.randint(max(0, center[1] - 120), min(h - 1, center[1] + 120))
            self.result_particles.append(ConfettiParticle(px, py, random.choice(colors), drift=((px - center[0]) * 0.015, (py - center[1]) * 0.01)))

    def draw_window_controls(self):
        close_rect = pygame.Rect(SCREEN_RES[0] - 42, 12, 30, 26)
        resize_rect = pygame.Rect(SCREEN_RES[0] - 78, 12, 30, 26)
        self.window_controls = {"close": close_rect, "resize": resize_rect}
        pygame.draw.rect(self.screen, (14, 20, 34), close_rect, border_radius=7)
        pygame.draw.rect(self.screen, self.theme["danger"], close_rect, 2, border_radius=7)
        pygame.draw.rect(self.screen, (14, 20, 34), resize_rect, border_radius=7)
        pygame.draw.rect(self.screen, self.theme["player"], resize_rect, 2, border_radius=7)
        close_text = self.font_tiny.render("X", True, self.theme["danger"])
        resize_text = self.font_tiny.render("↔", True, self.theme["player"])
        self.screen.blit(close_text, close_text.get_rect(center=close_rect.center))
        self.screen.blit(resize_text, resize_text.get_rect(center=resize_rect.center))

    def handle_window_button_click(self, pos):
        if self.window_controls.get("close") and self.window_controls["close"].collidepoint(pos):
            self.running = False
            return True
        if self.window_controls.get("resize") and self.window_controls["resize"].collidepoint(pos):
            self.toggle_window_mode()
            return True
        return False

    def _load_progress(self):
        path = self._save_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as fp:
                payload = json.load(fp)
        except (OSError, ValueError):
            return
        self.unlocked_level = max(1, min(len(self.levels), int(payload.get("unlocked_level", 1))))
        self.best_scores = payload.get("best_scores", {})
        self.leaderboard = payload.get("leaderboard", [])
        self.ghost_runs = payload.get("ghost_runs", {})
        self.daily_history = payload.get("daily_history", {})
        self.coins = int(payload.get("coins", 0))
        self.weekly_badges = payload.get("weekly_badges", [])
        owned = payload.get("owned_skins", ["classic"])
        if isinstance(owned, list) and owned:
            self.owned_skins = owned
        self.box_skin = payload.get("box_skin", "classic")
        if self.box_skin not in self.owned_skins:
            self.box_skin = self.owned_skins[0]
        saved_achievements = payload.get("achievements", {})
        for key in self.achievements:
            self.achievements[key] = bool(saved_achievements.get(key, False))
        self.daily_streak = self.compute_daily_streak()
        self.selected_level = min(self.unlocked_level - 1, len(self.levels) - 1)
        saved_settings = payload.get("settings", {})
        if isinstance(saved_settings, dict):
            self.settings.update(saved_settings)
        self.ai_score = int(payload.get("ai_score", 0))
        self.ai_level = int(payload.get("ai_level", 0))
        self.multiplayer_wins = payload.get("multiplayer_wins", [0, 0])
        self.multiplayer_scores = payload.get("multiplayer_scores", [0, 0])

    def _save_progress(self):
        payload = {
            "version": APP_VERSION, "unlocked_level": self.unlocked_level,
            "best_scores": self.best_scores, "leaderboard": self.leaderboard[:12],
            "achievements": self.achievements, "ghost_runs": self.ghost_runs,
            "daily_history": self.daily_history, "coins": self.coins,
            "weekly_badges": self.weekly_badges, "owned_skins": self.owned_skins,
            "box_skin": self.box_skin, "settings": self.settings,
            "ai_score": self.ai_score, "ai_level": self.ai_level,
            "multiplayer_wins": self.multiplayer_wins, "multiplayer_scores": self.multiplayer_scores,
        }
        try:
            with open(self._save_path(), "w", encoding="utf-8") as fp:
                json.dump(payload, fp, indent=2)
        except OSError:
            pass

    def _init_levels(self):
        self.levels = []
        self.level_pars = []
        self.level_challenges = {}
        self.level_names = {}
        
        self.levels.append([
            [1, 1, 1, 1, 1, 1, 1],
            [1, 4, 12, 3, 2, 13, 1],
            [1, 1, 1, 1, 1, 1, 1],
        ])
        self.level_pars.append({"moves": 4, "time": 15})
        self.level_challenges["1"] = "Push the box onto the goal!"
        self.level_names["1"] = "First Steps"
        
        self.levels.append([
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 4, 0, 0, 0, 0, 0, 1],
            [1, 0, 3, 13, 3, 0, 12, 1],
            [1, 0, 0, 2, 0, 2, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
        ])
        self.level_pars.append({"moves": 8, "time": 25})
        self.level_challenges["2"] = "Push both boxes onto the glowing goals!"
        self.level_names["2"] = "Double Duty"
        
        self.levels.append([
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 4, 5, 0, 0, 0, 6, 2, 1],
            [1, 0, 3, 0, 0, 12, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
        ])
        self.level_pars.append({"moves": 7, "time": 25})
        self.level_challenges["3"] = "Push box through portal to reach the goal!"
        self.level_names["3"] = "Portal Hop"
        
        self.levels.append([
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 4, 8, 8, 0, 8, 12, 3, 0, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ])
        self.level_pars.append({"moves": 5, "time": 18})
        self.level_challenges["4"] = "Slide on ice - you can't stop until you hit something!"
        self.level_names["4"] = "Ice Slide"
        
        self.levels.append([
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 4, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 9, 13, 0, 11, 12, 1],
            [1, 0, 0, 0, 3, 0, 0, 2, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
        ])
        self.level_pars.append({"moves": 6, "time": 18})
        self.level_challenges["5"] = "Avoid red traps! Collect rescue pickups!"
        self.level_names["5"] = "Danger Zone"
        
        for i in range(5, 200):
            level_grid, par, challenge, name = self._build_generated_level(i)
            self.levels.append(level_grid)
            self.level_pars.append(par)
            self.level_challenges[str(i+1)] = challenge
            self.level_names[str(i+1)] = name

    def _build_generated_level(self, index):
        rng = random.Random(9100 + index)
        variant = index % 12
        if variant == 0:
            grid = [
                [1,1,1,1,1,1,1,1,1],
                [1,4,0,12,0,3,0,2,1],
                [1,1,0,13,0,0,11,1,1],
                [1,1,1,1,1,1,1,1,1],
            ]
            challenge = "Use the boost lane to push around the barrier!"
            name = f"Boost Run {index+1}"
        elif variant == 1:
            grid = [
                [1,1,1,1,1,1,1,1,1],
                [1,4,0,0,9,0,3,12,1],
                [1,0,13,0,0,0,0,2,1],
                [1,0,0,11,0,0,10,0,1],
                [1,1,1,1,1,1,1,1,1],
            ]
            challenge = "Trap dodging, coin collecting, and a clean finish!"
            name = f"Neon Detour {index+1}"
        elif variant == 2:
            grid = [
                [1,1,1,1,1,1,1,1,1,1],
                [1,4,0,0,5,1,1,0,2,1],
                [1,0,3,0,0,0,0,6,0,1],
                [1,0,0,13,0,12,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1],
            ]
            challenge = "Use the portal pair to break the dead-end!"
            name = f"Portal Split {index+1}"
        elif variant == 3:
            grid = [
                [1,1,1,1,1,1,1,1,1],
                [1,4,8,8,8,0,3,0,2],
                [1,0,13,0,8,0,0,11,1],
                [1,0,0,0,8,12,0,0,1],
                [1,1,1,1,1,1,1,1,1],
            ]
            challenge = "Slide through the ice corridor and time the push!"
            name = f"Ice Channel {index+1}"
        elif variant == 4:
            grid = [
                [1,1,1,1,1,1,1,1,1,1],
                [1,4,0,0,13,0,0,0,2,1],
                [1,0,0,3,0,12,0,10,0,1],
                [1,0,11,0,0,0,9,0,0,1],
                [1,1,1,1,1,1,1,1,1,1],
            ]
            challenge = "Weave between traps and grab the prize route!"
            name = f"Trap Weave {index+1}"
        elif variant == 5:
            grid = [
                [1,1,1,1,1,1,1,1,1],
                [1,4,0,12,0,0,0,2,1],
                [1,0,3,13,3,0,10,0,1],
                [1,0,0,0,0,11,0,0,1],
                [1,1,1,1,1,1,1,1,1],
            ]
            challenge = "Two-box pressure with a reward lane!"
            name = f"Double Drift {index+1}"
        elif variant == 6:
            grid = [
                [1,1,1,1,1,1,1,1,1,1],
                [1,4,0,0,0,13,0,0,2,1],
                [1,0,8,8,0,3,8,12,0,1],
                [1,0,10,8,0,0,8,11,0,1],
                [1,1,1,1,1,1,1,1,1,1],
            ]
            challenge = "Ice, boosts, and a narrow escape path!"
            name = f"Frozen Line {index+1}"
        elif variant == 7:
            grid = [
                [1,1,1,1,1,1,1,1,1],
                [1,4,0,0,0,0,3,0,2],
                [1,0,13,0,9,0,12,0,1],
                [1,0,0,11,0,10,0,0,1],
                [1,1,1,1,1,1,1,1,1],
            ]
            challenge = "A clean route with bonus pickups and one trap!"
            name = f"Circuit {index+1}"
        elif variant == 8:
            # BOSS LEVEL - Teleport Maze
            grid = [
                [1,1,1,1,1,1,1,1,1,1,1],
                [1,4,5,0,0,0,0,0,6,2,1],
                [1,0,0,0,1,1,1,0,0,0,1],
                [1,0,3,0,1,13,1,0,12,0,1],
                [1,0,0,0,1,1,1,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1],
            ]
            challenge = "BOSS: Teleport maze with a trapped box!"
            name = f"Teleport Maze {index+1}"
        elif variant == 9:
            # BOSS LEVEL - Ice Gauntlet
            grid = [
                [1,1,1,1,1,1,1,1,1,1,1],
                [1,4,8,8,8,0,8,8,8,2,1],
                [1,0,0,9,8,0,8,9,0,0,1],
                [1,0,3,0,8,2,8,0,12,3,1],
                [1,0,0,0,0,0,0,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1],
            ]
            challenge = "BOSS: Ice gauntlet with traps on both sides!"
            name = f"Ice Gauntlet {index+1}"
        elif variant == 10:
            # BOSS LEVEL - Double Portal Pressure
            grid = [
                [1,1,1,1,1,1,1,1,1,1,1,1],
                [1,4,5,0,0,0,0,0,0,6,2,1],
                [1,0,0,0,1,1,1,1,0,0,0,1],
                [1,0,3,0,0,0,10,0,0,12,0,1],
                [1,0,0,0,1,1,1,1,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1,1],
            ]
            challenge = "BOSS: Portal puzzle with coin and boost!"
            name = f"Portal Pressure {index+1}"
        else:
            # Classic variant with more open space and multiple elements
            grid = [
                [1,1,1,1,1,1,1,1,1,1],
                [1,4,0,0,12,0,0,0,2,1],
                [1,0,3,0,13,0,11,10,0,1],
                [1,0,0,0,0,9,0,0,0,1],
                [1,0,5,0,0,0,0,6,0,1],
                [1,1,1,1,1,1,1,1,1,1],
            ]
            challenge = "Classic challenge with coins and a portal shortcut!"
            name = f"Classic Run {index+1}"
        par = {"moves": 8 + (index % 5), "time": 20 + (index % 3) * 5}
        return deepcopy(grid), par, challenge, name

    def load_current_level(self, reset_run_stats=False):
        raw = self.levels[self.level_idx]
        self.grid = [row[:] for row in raw]
        self.grid, fixes_applied = self.validate_and_fix_level_boxes(self.grid)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.entities = []
        self.portals = {}
        self.history = []
        self.is_loading = True
        self.loading_progress = 0.0
        for y in range(self.rows):
            for x in range(self.cols):
                val = self.grid[y][x]
                if val in (3, 4, 7):
                    self.entities.append({"type": val, "grid": [x, y], "visual": [float(x), float(y)]})
                    self.grid[y][x] = 0
                elif val == 5:
                    self.portals["A"] = (x, y)
                elif val == 6:
                    self.portals["B"] = (x, y)
                self.loading_progress = (y * self.cols + x) / (self.rows * self.cols)
        self.level_start_time = time.time()
        self.level_move_count = 0
        self.rescue_charges = 1
        if self.game_mode == "daily":
            self.rescue_charges = 2
        if "extra_rescue" in self.owned_skins:
            self.rescue_charges += 1
        self.update_difficulty_profile()
        self.rescue_charges += self.difficulty_profile.get("rescue_bonus", 0)
        if fixes_applied > 0:
            self.rescue_charges += fixes_applied
            self.set_toast(f"Level optimized: {fixes_applied} box(es) repositioned", seconds=3.0)
        player = next((e for e in self.entities if e["type"] == 4), None)
        self.player_start_grid = player["grid"][:] if player else [1, 1]
        self.current_trace = [player["grid"][:]] if player else []
        level_key = str(self.level_idx + 1)
        ghost = self.ghost_runs.get(level_key, {})
        self.active_ghost = ghost.get("path", []) if isinstance(ghost, dict) else []
        self.ghost_step = 0
        self.ghost_tick = 0.0
        if reset_run_stats:
            self.game_start_time = time.time()
            self.move_count = 0
            self.total_score = 0
            self.combo_streak = 0
            self.max_combo = 0
            self.completed_runs = 0
            if self.game_mode == "ai":
                self.ai_countdown_active = True
                self.ai_countdown = 120
                self.ai_opponent.start_thinking()
                self.ai_thinking = True
                self.ai_has_completed = False
        self.is_loading = False
        self.sync_music_for_state()

    def validate_and_fix_level_boxes(self, grid):
        return grid, 0

    def get_color(self, ent_type):
        if ent_type == 4:
            return self.theme["player"]
        if ent_type == 7:
            return self.theme["clone"]
        if ent_type == 3:
            return self.theme["box"]
        return (255, 255, 255)

    def play_sfx(self, key, volume=1.0):
        snd = self.sfx.get(key)
        if not snd:
            return
        snd.set_volume(max(0.0, min(1.0, volume * self.settings.get("sfx_volume", 0.8))))
        try:
            snd.play()
        except pygame.error:
            pass

    def play_typing_sound(self):
        if not self.settings.get("typing_sound", True):
            return
        now = time.time()
        if now - self.last_typing_time < self.typing_sound_cooldown:
            return
        self.last_typing_time = now
        self.play_sfx("typing", float(self.settings.get("typing_volume", 0.55)))

    def play_ui_click(self, volume=0.28):
        self.play_sfx("ui_click", volume * float(self.settings.get("ui_volume", 0.45)))

    def music_status_text(self):
        if not self.music:
            return "UNAVAILABLE"
        return "ON" if self.music_on else "OFF"

    def save_state(self):
        self.history.append([{"grid": e["grid"][:], "type": e["type"]} for e in self.entities])

    def undo(self):
        if not self.history:
            return
        previous = self.history.pop()
        for i, entity in enumerate(self.entities):
            entity["grid"] = previous[i]["grid"][:]
        self.play_sfx("undo", 0.7)
        self.shake = 4
        self.sync_active_multiplayer_state()

    def check_portal(self, x, y):
        if (x, y) == self.portals.get("A"):
            return self.portals["B"]
        if (x, y) == self.portals.get("B"):
            return self.portals["A"]
        return x, y

    def is_walkable(self, x, y):
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return False
        if self.grid[y][x] in (1, 13):
            return False
        return not any(e["grid"] == [x, y] for e in self.entities)

    def is_walkable_except(self, x, y, ignore_entity):
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return False
        if self.grid[y][x] in (1, 13):
            return False
        for entity in self.entities:
            if entity is ignore_entity:
                continue
            if entity["grid"] == [x, y]:
                return False
        return True

    def is_goal_tile(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows and self.grid[y][x] == 2

    def is_blocking_cell(self, x, y):
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return True
        return self.grid[y][x] in (1, 13)

    def is_dead_corner(self, x, y):
        if self.is_goal_tile(x, y):
            return False
        up = self.is_blocking_cell(x, y - 1)
        down = self.is_blocking_cell(x, y + 1)
        left = self.is_blocking_cell(x - 1, y)
        right = self.is_blocking_cell(x + 1, y)
        return (up and left) or (up and right) or (down and left) or (down and right)

    def rescue_cornered_box(self):
        if self.rescue_charges <= 0:
            self.set_toast("No rescue charges left")
            return
        player = next((e for e in self.entities if e["type"] == 4), None)
        stuck_boxes = []
        for box in (e for e in self.entities if e["type"] == 3):
            x, y = box["grid"]
            is_dead = self.is_dead_corner(x, y)
            is_surrounded = all(
                (not (0 <= x+dx < self.cols and 0 <= y+dy < self.rows)) or
                self.grid[y+dy][x+dx] in (1, 13) or
                any(e2["grid"] == [x+dx, y+dy] for e2 in self.entities if e2["type"] == 3)
                for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]
            )
            if is_dead or is_surrounded:
                stuck_boxes.append(box)
        if not stuck_boxes:
            self.set_toast("No stuck boxes.")
            return
        best = None
        best_dist = 10**9
        target_box = None
        for box in stuck_boxes:
            for y in range(self.rows):
                for x in range(self.cols):
                    if not self.is_walkable_except(x, y, box):
                        continue
                    if self.is_dead_corner(x, y):
                        continue
                    dist = abs(box["grid"][0]-x) + abs(box["grid"][1]-y)
                    if player:
                        dist += abs(player["grid"][0]-x) + abs(player["grid"][1]-y)
                    if dist < best_dist:
                        best_dist = dist
                        best = [x, y]
                        target_box = box
        if not best or not target_box:
            self.set_toast("No rescue path")
            return
        target_box["grid"] = best
        self.rescue_charges -= 1

    def slide(self, entity, dx, dy):
        max_steps = 100  # SAFETY: prevent infinite loop on circular ice
        steps = 0
        while steps < max_steps:
            nx = entity["grid"][0] + dx
            ny = entity["grid"][1] + dy
            if self.is_walkable(nx, ny) and self.grid[ny][nx] == 8:
                entity["grid"] = [nx, ny]
                steps += 1
            else:
                break

    def spawn_fx(self, gx, gy, color, count=12):
        origin_x, origin_y = self.grid_origin()
        px = gx * TILE_SIZE + origin_x + TILE_SIZE // 2
        py = gy * TILE_SIZE + origin_y + TILE_SIZE // 2
        for _ in range(count):
            self.world_particles.append(NeonParticle(px, py, color))

    def apply_entity_tile_effects(self, entity):
        x, y = entity["grid"]
        tile = self.grid[y][x]
        if tile == 9 and entity["type"] in (4, 7):
            if entity["type"] == 4:
                entity["grid"] = self.player_start_grid[:]
                self.shake = 12
                self.set_toast("Trap hit: returning to start", color=(255, 80, 80))
            return
        if entity["type"] == 4 and tile == 10:
            self.coins += 1
            self.grid[y][x] = 0
            self.spawn_fx(x, y, (255, 215, 0), 12)
            self.play_sfx("coin", 0.5)
            self.set_toast("+1 coin collected", seconds=0.8, color=self.theme["accent"])
        elif entity["type"] == 4 and tile == 11:
            self.rescue_charges += 1
            self.grid[y][x] = 0
            self.spawn_fx(x, y, self.theme["player"], 14)
        elif entity["type"] == 4 and tile == 12:
            self.total_score += 60
            self.combo_streak += 1
            self.flash = 10
            self.spawn_fx(x, y, self.theme["accent"], 18)
            self.play_sfx("coin", 0.45)
            dx, dy = self.last_move_dir
            if dx or dy:
                nx, ny = x + dx, y + dy
                if self.is_walkable(nx, ny):
                    entity["grid"] = [nx, ny]
                    self.spawn_fx(nx, ny, self.theme["goal"], 12)

    def attempt_move(self, entity, dx, dy):
        entity["last_dir"] = [dx, dy]
        cx, cy = entity["grid"]
        nx, ny = cx + dx, cy + dy
        if not (0 <= nx < self.cols and 0 <= ny < self.rows):
            self.shake = 7
            self.play_sfx("box_hit", 0.35)
            return False
        if self.grid[ny][nx] in (1, 13):
            self.shake = 7
            self.play_sfx("box_hit", 0.35)
            return False
        box = next((e for e in self.entities if e["type"] == 3 and e["grid"] == [nx, ny]), None)
        if box:
            if not self.push_box_chain(box, dx, dy):
                self.shake = 12
                self.play_sfx("box_hit", 0.45)
                return False
            entity["grid"] = [nx, ny]
            bx, by = box["grid"]
            if self.grid[by][bx] == 8:
                self.slide(box, dx, dy)
            self.spawn_fx(bx, by, self.theme["box"], 14)
            self.play_sfx("box_move", 0.5)
            return True
        tx, ty = self.check_portal(nx, ny)
        entity["grid"] = [tx, ty]
        if self.grid[ty][tx] == 8:
            self.slide(entity, dx, dy)
        self.spawn_fx(tx, ty, self.get_color(entity["type"]), 9)
        return True

    def move(self, dx, dy):
        if self.result_type or self.level_clear_timer > 0:
            return
        if self.game_mode == "multiplayer" and self.multiplayer_finished[self.multiplayer_active_player]:
            return
        self.last_move_dir = (dx, dy)
        self.save_state()
        player = next(e for e in self.entities if e["type"] == 4)
        clone = next((e for e in self.entities if e["type"] == 7), None)
        moved_player = self.attempt_move(player, dx, dy)
        moved_clone = self.attempt_move(clone, -dx, -dy) if clone else False
        if not moved_player and not moved_clone:
            if self.history:
                self.history.pop()
            return
        player = next((e for e in self.entities if e["type"] == 4), None)
        if player:
            self.current_trace.append(player["grid"][:])
            self.apply_entity_tile_effects(player)
        if clone:
            self.apply_entity_tile_effects(clone)
        if self.difficulty_profile.get("auto_fix", True):
            self.recover_stuck_boxes()
        self.move_count += 1
        self.level_move_count += 1
        self.play_sfx("move", 0.45)
        self.check_win()
        self.sync_active_multiplayer_state()

    def recover_stuck_boxes(self):
        goals = [(x, y) for y, row in enumerate(self.grid) for x, value in enumerate(row) if value == 2]
        if not goals:
            return
        moved = 0
        for box in [e for e in self.entities if e["type"] == 3]:
            x, y = box["grid"]
            if self.is_goal_tile(x, y) or not self.is_dead_corner(x, y):
                continue
            occupied = {tuple(e["grid"]) for e in self.entities if e is not box}
            best = None
            best_cost = 10**9
            for ty in range(self.rows):
                for tx in range(self.cols):
                    if self.grid[ty][tx] in (1, 13):
                        continue
                    if (tx, ty) in occupied:
                        continue
                    if self.is_dead_corner(tx, ty) and not self.is_goal_tile(tx, ty):
                        continue
                    goal_dist = min(abs(tx - gx) + abs(ty - gy) for gx, gy in goals)
                    move_dist = abs(tx - x) + abs(ty - y)
                    cost = goal_dist * 3 + move_dist
                    if cost < best_cost:
                        best_cost = cost
                        best = [tx, ty]
            if best:
                box["grid"] = best
                moved += 1
                self.spawn_fx(best[0], best[1], self.theme["goal"], 10)
        if moved > 0:
            self.set_toast(f"Auto-unstuck moved {moved} box(es)", seconds=1.2, color=self.theme["accent"])

    def push_box_chain(self, box, dx, dy, seen=None):
        if seen is None:
            seen = set()
        box_id = id(box)
        if box_id in seen:
            return False
        seen.add(box_id)

        x, y = box["grid"]
        candidates = [(x + dx, y + dy)] + self._box_flex_candidates(x, y, dx, dy)
        for nx, ny in candidates:
            if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                continue
            if self.grid[ny][nx] in (1, 13):
                continue
            next_box = next((e for e in self.entities if e["type"] == 3 and e is not box and e["grid"] == [nx, ny]), None)
            if next_box and not self.push_box_chain(next_box, dx, dy, seen):
                continue
            if not self.is_walkable(nx, ny):
                continue
            box["grid"] = [nx, ny]
            return True
        return False

    def _box_flex_candidates(self, x, y, dx, dy):
        if dx == 0 and dy != 0:
            return [(x + 1, y), (x - 1, y), (x + 1, y + dy), (x - 1, y + dy)]
        if dy == 0 and dx != 0:
            return [(x, y + 1), (x, y - 1), (x + dx, y + 1), (x + dx, y - 1)]
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    def level_rating(self, moves, elapsed, par_moves, par_time):
        ratio = max(moves / max(1, par_moves), elapsed / max(1, par_time))
        if ratio <= 0.65:
            return "S"
        if ratio <= 0.80:
            return "A"
        if ratio <= 1.10:
            return "B"
        if ratio <= 1.50:
            return "C"
        return "D"

    def level_score(self, moves, elapsed, par_moves, par_time, rating):
        move_bonus = max(0, (par_moves - moves) * 32)
        time_bonus = max(0, (par_time - elapsed) * 8)
        rating_mult = {"S": 1.5, "A": 1.25, "B": 1.0, "C": 0.8, "D": 0.5}[rating]
        combo_bonus = self.combo_streak * 120
        return int((1000 + move_bonus + time_bonus + combo_bonus) * rating_mult)

    def start_run(self, mode):
        self.game_mode = mode
        self.result_type = None
        self.result_message = ""
        
        if mode == "daily":
            self._build_daily_plan()
            self.daily_idx = 0
            self.level_idx = self.daily_level_indices[self.daily_idx]
        elif mode == "ai":
            self.level_idx = self.selected_level
            self.ai_level = self.level_idx
            diff = self.ai_difficulties[self.ai_difficulty_index]
            self.ai_opponent = AIOpponent("CyberBrain", diff)
            self.ai_opponent.current_level = self.level_idx
            self.ai_vs_mode = True
            self.ai_countdown_active = True
            self.ai_countdown = 120
            self.ai_thinking = True
        elif mode == "multiplayer":
            self.level_idx = self.selected_level
            self.multiplayer_turn = 0
            self.multiplayer_active_player = 0
            self.multiplayer_finished = [False, False]
            self.multiplayer_finish_times = [None, None]
        else:
            if mode == "campaign" and not self.career_started:
                self.level_idx = 0
                self.career_started = True
                self.campaign_intro_active = True
                self.campaign_intro_step = 0
                self.campaign_intro_timer = 0.0
            else:
                self.level_idx = self.selected_level
        
        self.load_current_level(reset_run_stats=True)
        if mode == "multiplayer":
            base_state = self.capture_level_state()
            self.multiplayer_initial_state = deepcopy(base_state)
            self.multiplayer_states = [deepcopy(base_state), deepcopy(base_state)]
            self.restore_level_state(self.multiplayer_states[0])
        self.paused = False
        if self.campaign_intro_active:
            self.set_state("campaign_intro", animated=True)
        else:
            self.set_state("playing", animated=True)

    def update_achievements(self, rating, moves, elapsed, par_moves, par_time):
        level_num = self.level_idx + 1
        self.achievements["first_win"] = True
        if elapsed <= par_time / 2:
            self.achievements["speed_runner"] = True
        if moves <= par_moves:
            self.achievements["strategist"] = True
        if rating == "S":
            self.achievements["perfectionist"] = True
        if self.combo_streak >= 3:
            self.achievements["combo_master"] = True
        if level_num >= 25:
            self.achievements["level_25"] = True
        if level_num >= 50:
            self.achievements["level_50"] = True
        if level_num >= 100:
            self.achievements["level_100"] = True
        if level_num >= 150:
            self.achievements["level_150"] = True
        if level_num >= 200:
            self.achievements["level_200"] = True
        if self.coins >= 100:
            self.achievements["coin_collector"] = True
        if len(self.owned_skins) >= 5:
            self.achievements["skin_collector"] = True
        if self.game_mode == "ai" and self.ai_has_completed and self.total_score > self.ai_score:
            self.achievements["ai_beater"] = True

    def add_leaderboard_entry(self):
        elapsed = int(time.time() - self.game_start_time)
        entry = {
            "name": self.player_name,
            "mode": "Daily" if self.game_mode == "daily" else "Campaign",
            "score": self.total_score,
            "moves": self.move_count,
            "time": elapsed,
            "streak": self.daily_streak,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        self.leaderboard.append(entry)
        self.leaderboard.sort(key=lambda e: (-int(e["score"]), int(e["time"]), int(e["moves"])))
        self.leaderboard = self.leaderboard[:12]

    def show_result_screen(self, result_type, title, subtitle=""):
        self.result_type = result_type
        self.result_message = title
        self.result_subtitle = subtitle
        self.result_timer = 240
        self.spawn_result_fx(result_type)
        if result_type == "win":
            self.play_sfx("victory", 1.0)
            self.set_toast("🏆 YOU WIN!", seconds=3.0, color=(255, 215, 0))
        elif result_type == "lose":
            self.play_sfx("defeat", 1.0)
            self.set_toast("😔 YOU LOST!", seconds=3.0, color=(255, 80, 80))
        else:
            self.play_sfx("solve", 0.9)
            self.set_toast("🤝 IT'S A DRAW!", seconds=3.0, color=(100, 255, 200))

    def check_win(self):
        goals = [(x, y) for y, row in enumerate(self.grid) for x, value in enumerate(row) if value == 2]
        boxes = [tuple(e["grid"]) for e in self.entities if e["type"] == 3]
        if not all(goal in boxes for goal in goals):
            return

        self.play_sfx("solve", 0.9)
        self.flash = 16
        self.shake = 14

        elapsed_raw = time.time() - self.level_start_time
        elapsed = int(elapsed_raw)
        par = self.level_pars[self.level_idx]
        rating = self.level_rating(self.level_move_count, elapsed, par["moves"], par["time"])

        if rating in ("S", "A"):
            self.combo_streak += 1
            self.max_combo = max(self.max_combo, self.combo_streak)
        else:
            self.combo_streak = 0

        score = self.level_score(self.level_move_count, elapsed, par["moves"], par["time"], rating)
        self.total_score += score
        self.completed_runs += 1

        prize_reward = 0
        if rating == "S":
            prize_reward = 50
        elif rating == "A":
            prize_reward = 30
        elif rating == "B":
            prize_reward = 15
        elif rating == "C":
            prize_reward = 5

        self.total_prizes += prize_reward
        coin_gain = max(1, prize_reward // 5)
        self.coins += coin_gain
        self.last_coin_gain = coin_gain
        if coin_gain > 0:
            self.set_toast(f"Level reward +{coin_gain} coin(s)", seconds=1.2, color=self.theme["accent"])
        level_key = str(self.level_idx + 1)
        self.level_prizes[level_key] = prize_reward
        self.best_scores[level_key] = max(score, int(self.best_scores.get(level_key, 0)))
        self.update_achievements(rating, self.level_move_count, elapsed, par["moves"], par["time"])

        self.last_result = {
            "rating": rating, "score": score, "time": elapsed,
            "moves": self.level_move_count, "level": self.level_idx + 1,
            "par_moves": par["moves"], "par_time": par["time"],
        }

        old_ghost = self.ghost_runs.get(level_key, {})
        old_score = int(old_ghost.get("score", -1)) if isinstance(old_ghost, dict) else -1
        if score >= old_score and self.current_trace:
            self.ghost_runs[level_key] = {
                "path": [p[:] for p in self.current_trace],
                "score": score, "moves": self.level_move_count, "time": elapsed,
            }

        self.unlocked_level = max(self.unlocked_level, min(len(self.levels), self.level_idx + 2))

        if self.game_mode == "ai":
            if self.ai_level < self.level_idx:
                self.ai_level = self.level_idx
            self.ai_has_completed = True
            self.ai_countdown_active = False
            self.ai_vs_mode = False
            
            ai_finished = self.ai_opponent.ai_solved
            player_time = self.last_result["time"]
            ai_time = self.ai_opponent.ai_time if ai_finished else self.ai_countdown
            
            if ai_finished and self.last_result["moves"] <= len(self.ai_opponent.ai_path):
                if player_time <= ai_time:
                    self.show_result_screen("win", "🏆 YOU BEAT THE AI!", f"You: {player_time}s | AI: {ai_time:.1f}s")
                else:
                    self.show_result_screen("lose", "😔 AI BEAT YOU!", f"AI: {ai_time:.1f}s | You: {player_time}s")
            elif ai_finished:
                self.show_result_screen("lose", "😔 AI WAS FASTER!", f"AI finished in {ai_time:.1f}s")
            else:
                self.show_result_screen("win", "🏆 YOU WIN! AI STUCK!", "AI couldn't solve it!")
            
            if self.total_score > self.ai_score:
                self.ai_score = self.total_score
            self.ai_thinking = False
            self._save_progress()
            return

        if self.game_mode == "multiplayer":
            idx = self.multiplayer_active_player
            if not self.multiplayer_finished[idx]:
                self.multiplayer_finished[idx] = True
                self.multiplayer_finish_times[idx] = elapsed_raw
                self.multiplayer_scores[idx] += score
                self.multiplayer_wins[idx] += 1
                winner = self.multiplayer_names[idx]
                other_idx = 1 if idx == 0 else 0
                if not self.multiplayer_finished[other_idx]:
                    result_msg = f"🏁 {winner} IS DONE!"
                    result_sub = f"Time: {elapsed_raw:.1f}s  Score: {score} — Now it's {self.multiplayer_names[other_idx]}'s turn!"
                    self.show_result_screen("win", result_msg, result_sub)
                    self.multiplayer_last_winner = idx
                    self.multiplayer_switch_pending = other_idx
                else:
                    t0 = self.multiplayer_finish_times[0]
                    t1 = self.multiplayer_finish_times[1]
                    diff_sec = abs(t0 - t1)
                    if t0 < t1:
                        overall_winner = self.multiplayer_names[0]
                        result_line = f"🏆 {self.multiplayer_names[0]} WINS! (Faster by {diff_sec:.2f}s)"
                        result_line += f"\n{self.multiplayer_names[0]}: {t0:.1f}s | {self.multiplayer_names[1]}: {t1:.1f}s"
                    elif t1 < t0:
                        overall_winner = self.multiplayer_names[1]
                        result_line = f"🏆 {self.multiplayer_names[1]} WINS! (Faster by {diff_sec:.2f}s)"
                        result_line += f"\n{self.multiplayer_names[0]}: {t0:.1f}s | {self.multiplayer_names[1]}: {t1:.1f}s"
                    else:
                        overall_winner = "DRAW"
                        result_line = f"🤝 IT'S A DRAW! Exact same time: {t0:.1f}s"
                        result_line += f"\n{self.multiplayer_names[0]}: {t0:.1f}s | {self.multiplayer_names[1]}: {t1:.1f}s"
                    if overall_winner == "DRAW":
                        self.show_result_screen("draw", "🤝 IT'S A DRAW!", result_line)
                    else:
                        self.show_result_screen("win", overall_winner, result_line)
                self._save_progress()
            return

        if self.game_mode == "daily":
            if self.daily_idx >= len(self.daily_level_indices) - 1:
                self.record_daily_completion()
                self.add_leaderboard_entry()
                self.spawn_result_fx("win")
                self.pending_clear_state = "victory"
            else:
                self.daily_idx += 1
                self.pending_next_level = self.daily_level_indices[self.daily_idx]
                self.pending_clear_state = "post_level"
        else:
            if self.level_idx >= len(self.levels) - 1:
                self.add_leaderboard_entry()
                self.spawn_result_fx("win")
                self.pending_clear_state = "victory"
            else:
                self.pending_next_level = self.level_idx + 1
                self.pending_clear_state = "post_level"

        self.level_clear_timer = 0.35
        self._save_progress()

    def grid_origin(self):
        hud_width = self.get_hud_width()
        panel = self.get_competitor_panel_rect()
        right_reserved = (SCREEN_RES[0] - panel.x + 12) if panel else 0
        available_width = SCREEN_RES[0] - hud_width - right_reserved
        grid_pixel_width = self.cols * TILE_SIZE
        ox = hud_width + max(0, (available_width - grid_pixel_width) // 2)
        oy = max(0, (SCREEN_RES[1] - self.rows * TILE_SIZE) // 2)
        return ox, oy

    def get_competitor_panel_rect(self):
        if self.game_mode not in ("ai", "multiplayer"):
            return None
        panel_w = min(300, SCREEN_RES[0] // 4)
        panel_h = min(290, SCREEN_RES[1] - 180)
        px = SCREEN_RES[0] - panel_w - 16
        py = 88
        return pygame.Rect(px, py, panel_w, panel_h)

    def draw_world(self, dt):
        self.draw_background_fx(dt)

        if self.level_clear_timer > 0:
            self.level_clear_timer = max(0.0, self.level_clear_timer - dt)
            if self.level_clear_timer <= 0 and self.pending_clear_state:
                self.set_state(self.pending_clear_state, animated=True)
                self.pending_clear_state = None
        
        if self.game_mode == "ai" and self.ai_vs_mode:
            if self.ai_thinking:
                if self.ai_opponent.think(dt):
                    self.ai_thinking = False
                    player = next((e for e in self.entities if e["type"] == 4), None)
                    start = player["grid"][:] if player else [1, 1]
                    self.ai_opponent.generate_path(self.grid, self.entities, self.portals, start)
                    self.set_toast("🤖 AI is moving! Finish fast!", seconds=2.0)
            
            if not self.ai_thinking and not self.ai_has_completed and not self.result_type:
                self.ai_opponent.update_movement(dt)
                if self.ai_opponent.ai_solved:
                    self.ai_has_completed = True
        
        if self.game_mode == "ai" and self.ai_countdown_active and not self.result_type:
            self.ai_countdown -= dt * self.difficulty_profile.get("timer_rate", 1.0)
            if self.ai_countdown <= 0:
                self.ai_countdown = 0
                self.ai_countdown_active = False
                if not self.ai_has_completed:
                    self.ai_has_completed = True
                    self.show_result_screen("lose", "⏱ TIME'S UP!", "You ran out of time!")
        
        if self.result_type:
            self.result_timer -= 1
            if self.result_timer <= 0:
                self.result_type = None
                if self.game_mode == "ai":
                    self.ai_vs_mode = False
                    self.pending_next_level = self.level_idx + 1
                    self.set_state("post_level", animated=True)
                elif self.game_mode == "multiplayer":
                    self.pending_next_level = min(len(self.levels) - 1, self.level_idx + 1)
                    self.set_state("post_level", animated=True)
        
        origin_x, origin_y = self.grid_origin()
        self.player_panel_rect = pygame.Rect(origin_x, origin_y, self.cols * TILE_SIZE, self.rows * TILE_SIZE)
        if self.shake > 0 and self.settings.get("screen_shake", True):
            origin_x += random.randint(-self.shake, self.shake)
            origin_y += random.randint(-self.shake, self.shake)
            self.shake -= 1

        pulse_t = time.time()

        for y in range(self.rows):
            for x in range(self.cols):
                px = x * TILE_SIZE + origin_x
                py = y * TILE_SIZE + origin_y
                tile = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
                value = self.grid[y][x]
                if self.sprite_floor:
                    self.screen.blit(self.sprite_floor, tile.topleft)
                else:
                    pygame.draw.rect(self.screen, (20, 31, 49), tile, border_radius=8)
                if value == 1:
                    wall_rect = tile.inflate(-10, -10)
                    pygame.draw.rect(self.screen, self.theme["wall"], wall_rect, border_radius=10)
                elif value == 13:
                    core = tile.inflate(-14, -14)
                    pygame.draw.rect(self.screen, (82, 100, 136), core, border_radius=10)
                    pygame.draw.rect(self.screen, (40, 54, 76), core.inflate(-12, -12), 2, border_radius=8)
                elif value == 8:
                    ice = tile.inflate(-14, -14)
                    pygame.draw.rect(self.screen, (176, 232, 255), ice, border_radius=10)
                    pygame.draw.rect(self.screen, self.theme["ice"], ice, 2, border_radius=8)
                    pygame.draw.line(self.screen, (225, 250, 255), (ice.left + 10, ice.top + 14), (ice.right - 10, ice.bottom - 14), 2)
                elif value == 9:
                    trap = tile.inflate(-16, -16)
                    pygame.draw.rect(self.screen, (84, 18, 32), trap, border_radius=10)
                    pygame.draw.polygon(self.screen, self.theme["danger"], [(px + 18, py + 18), (px + 54, py + 18), (px + 36, py + 52)])
                elif value == 10:
                    coin = tile.inflate(-18, -18)
                    pygame.draw.circle(self.screen, (255, 215, 64), coin.center, coin.w // 3)
                    pygame.draw.circle(self.screen, (255, 245, 180), coin.center, coin.w // 5, 2)
                elif value == 11:
                    vial = tile.inflate(-18, -18)
                    pygame.draw.rect(self.screen, (28, 80, 52), vial, border_radius=8)
                    pygame.draw.rect(self.screen, (120, 255, 170), vial.inflate(-10, -10), border_radius=6)
                    pygame.draw.rect(self.screen, (220, 255, 235), (vial.centerx - 4, vial.top - 6, 8, 12), border_radius=3)
                elif value == 12:
                    boost_rect = tile.inflate(-16, -16)
                    pygame.draw.rect(self.screen, (20, 54, 74), boost_rect, border_radius=10)
                    pygame.draw.polygon(self.screen, self.theme["accent"], [
                        (px + 20, py + 24), (px + 38, py + 12), (px + 38, py + 20),
                        (px + 54, py + 20), (px + 54, py + 28), (px + 38, py + 28),
                        (px + 38, py + 36)
                    ])
                elif value in (5, 6):
                    portal_color = self.theme["portal"] if value == 5 else (155, 236, 255)
                    portal = tile.inflate(-16, -16)
                    pygame.draw.ellipse(self.screen, (30, 24, 70), portal)
                    pygame.draw.ellipse(self.screen, portal_color, portal, 3)
                    pygame.draw.circle(self.screen, portal_color, portal.center, max(3, portal.w // 8))
                elif value == 2:
                    pulse = int(6 + math.sin(pulse_t * 8.0) * 3)
                    goal_rect = pygame.Rect(px+24-pulse, py+24-pulse, 24+pulse*2, 24+pulse*2)
                    pygame.draw.rect(self.screen, self.theme["goal"], goal_rect, 3, border_radius=6)

        for entity in self.entities:
            entity["visual"][0] += (entity["grid"][0] - entity["visual"][0]) * 0.25
            entity["visual"][1] += (entity["grid"][1] - entity["visual"][1]) * 0.25
            ex = int(entity["visual"][0] * TILE_SIZE + origin_x + 9)
            ey = int(entity["visual"][1] * TILE_SIZE + origin_y + 9)
            body = pygame.Rect(ex, ey, TILE_SIZE - 18, TILE_SIZE - 18)
            color = self.get_color(entity["type"])
            if entity["type"] == 4:
                # Player glow effect
                glow_color = self.theme["player"]
                for i in range(3, 0, -1):
                    glow = body.inflate(i*8, i*8)
                    alpha = max(0, 40 - i * 12)
                    glow_surf = pygame.Surface((glow.w, glow.h), pygame.SRCALPHA)
                    glow_surf.fill((glow_color[0], glow_color[1], glow_color[2], alpha))
                    self.screen.blit(glow_surf, glow.topleft)
                pygame.draw.rect(self.screen, color, body, border_radius=8)
                # Inner shine
                shine = body.inflate(-8, -8)
                pygame.draw.rect(self.screen, (min(255,color[0]+60), min(255,color[1]+60), min(255,color[2]+60)), shine, border_radius=6)
            elif entity["type"] == 3:
                skin = self.box_skin if hasattr(self, 'box_skin') else "classic"
                texture = body.inflate(-2, -2)
                if skin == "classic":
                    pygame.draw.rect(self.screen, (63, 42, 24), body, border_radius=10)
                    pygame.draw.rect(self.screen, color, texture, border_radius=8)
                    pygame.draw.rect(self.screen, (255, 236, 160), texture, 2, border_radius=8)
                    pygame.draw.line(self.screen, (255, 245, 210), (texture.left + 6, texture.top + 8), (texture.right - 6, texture.top + 8), 2)
                    pygame.draw.line(self.screen, (115, 72, 36), (texture.left + 8, texture.bottom - 10), (texture.right - 8, texture.bottom - 10), 3)
                    pygame.draw.line(self.screen, (87, 56, 28), (texture.left + 8, texture.centery), (texture.right - 8, texture.centery), 2)
                elif skin == "diamond":
                    cx, cy = texture.center
                    r = texture.w // 2
                    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
                    pygame.draw.polygon(self.screen, (63, 42, 24), [(cx, cy-r-2), (cx+r+2, cy), (cx, cy+r+2), (cx-r-2, cy)])
                    pygame.draw.polygon(self.screen, (100, 200, 255), pts)
                    pygame.draw.polygon(self.screen, (200, 230, 255), pts, 3)
                elif skin == "rounded":
                    pygame.draw.rect(self.screen, (63, 42, 24), body, border_radius=TILE_SIZE)
                    pygame.draw.rect(self.screen, (255, 150, 200), texture, border_radius=TILE_SIZE)
                    pygame.draw.rect(self.screen, (255, 200, 230), texture, 3, border_radius=TILE_SIZE)
                elif skin == "hollow":
                    pygame.draw.rect(self.screen, (63, 42, 24), body, border_radius=6)
                    pygame.draw.rect(self.screen, color, texture, 4, border_radius=6)
                    pygame.draw.rect(self.screen, (200, 200, 255), texture, 2, border_radius=6)
                    pygame.draw.circle(self.screen, (100, 100, 200), texture.center, texture.w // 5, 2)
                elif skin == "glitch":
                    pygame.draw.rect(self.screen, (30, 30, 30), body, border_radius=6)
                    pygame.draw.rect(self.screen, (0, 255, 0), texture, border_radius=6)
                    for _ in range(4):
                        gx = random.randint(texture.left, texture.right - 8)
                        gy = random.randint(texture.top, texture.bottom - 4)
                        gw = random.randint(6, 14)
                        gh = random.randint(2, 4)
                        pygame.draw.rect(self.screen, (0, 200, 0), (gx, gy, gw, gh))
                        pygame.draw.rect(self.screen, (255, 0, 255), (gx+2, gy, max(1,gw-4), gh), 1)
                elif skin == "flame":
                    pygame.draw.rect(self.screen, (80, 20, 10), body, border_radius=8)
                    pygame.draw.rect(self.screen, (255, 100, 0), texture, border_radius=6)
                    pygame.draw.rect(self.screen, (255, 200, 50), texture, 3, border_radius=6)
                    fy = texture.top + random.randint(-3, 3)
                    for i in range(3):
                        fx = texture.left + 6 + i * 10
                        fh = random.randint(4, 12)
                        pygame.draw.rect(self.screen, (255, 255, 100), (fx, fy - fh, 6, fh), border_radius=2)
                elif skin == "crystal":
                    pygame.draw.rect(self.screen, (40, 60, 80), body, border_radius=6)
                    pygame.draw.rect(self.screen, (100, 200, 255), texture, border_radius=6)
                    pygame.draw.rect(self.screen, (200, 240, 255), texture, 2, border_radius=6)
                    pts = [(texture.left+4, texture.top+4), (texture.centerx, texture.top+4), (texture.left+4, texture.centery)]
                    pygame.draw.polygon(self.screen, (255, 255, 255, 80), pts)
                elif skin == "neon":
                    glow_color = (0, 255, 200)
                    for i in range(4, 0, -1):
                        glow = texture.inflate(i*6, i*6)
                        alpha = max(0, 60 - i * 15)
                        glow_surf = pygame.Surface((glow.w, glow.h), pygame.SRCALPHA)
                        glow_surf.fill((glow_color[0], glow_color[1], glow_color[2], alpha))
                        self.screen.blit(glow_surf, glow.topleft)
                    pygame.draw.rect(self.screen, (0, 40, 40), body, border_radius=8)
                    pygame.draw.rect(self.screen, glow_color, texture, 3, border_radius=8)
                elif skin == "cosmic":
                    pygame.draw.rect(self.screen, (10, 10, 40), body, border_radius=8)
                    pygame.draw.rect(self.screen, (40, 20, 80), texture, border_radius=8)
                    for _ in range(6):
                        sx = texture.left + random.randint(2, texture.w - 4)
                        sy = texture.top + random.randint(2, texture.h - 4)
                        pygame.draw.circle(self.screen, (255, 255, 200), (sx, sy), random.randint(1, 3))
                    pygame.draw.rect(self.screen, (150, 100, 255), texture, 2, border_radius=8)
                else:
                    pygame.draw.rect(self.screen, (63, 42, 24), body, border_radius=10)
                    pygame.draw.rect(self.screen, color, texture, border_radius=8)
                    pygame.draw.rect(self.screen, (255, 236, 160), texture, 2, border_radius=8)
            else:
                for i in range(8, 0, -2):
                    pygame.draw.rect(self.screen, color, body.inflate(i*2, i*2), 1, border_radius=8)

        if self.settings.get("particle_effects", True):
            self.world_particles = [p for p in self.world_particles if p.update()]
            for p in self.world_particles:
                p.draw(self.screen)

        self.draw_hud()
        self.draw_music_badge()
        self.draw_toast()

        if self.result_type:
            self.draw_result_overlay()

        if self.paused:
            self.draw_pause_menu()

        if self.ai_thinking and self.game_mode == "ai":
            self._draw_ai_thinking()

        if self.multiplayer_turn == 1 and self.game_mode == "multiplayer":
            self._draw_multiplayer_indicator()

        if self.flash > 0:
            overlay = pygame.Surface(SCREEN_RES, pygame.SRCALPHA)
            overlay.fill((255, 255, 255, min(180, self.flash * 10)))
            self.screen.blit(overlay, (0, 0))
            self.flash -= 1

        if self.level_clear_timer > 0:
            overlay = pygame.Surface(SCREEN_RES, pygame.SRCALPHA)
            overlay.fill((4, 7, 16, 110))
            self.screen.blit(overlay, (0, 0))
            clear_text = self.font_title.render("LEVEL CLEAR!", True, self.theme["goal"])
            self.screen.blit(clear_text, clear_text.get_rect(center=(SCREEN_RES[0] // 2, 90)))

        if self.game_mode in ("ai", "multiplayer"):
            self.draw_competitor_arena()

        if self.settings.get("touch_controls", True):
            self.draw_touch_controls()

    def draw_result_overlay(self):
        overlay = pygame.Surface(SCREEN_RES, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        self.result_particles = [p for p in self.result_particles if p.update()]
        for p in self.result_particles:
            p.draw(self.screen)
        
        panel_w, panel_h = min(640, SCREEN_RES[0] - 120), min(340, SCREEN_RES[1] - 120)
        px = (SCREEN_RES[0] - panel_w) // 2
        py = (SCREEN_RES[1] - panel_h) // 2 - 30
        panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        pulse = 10 + int(6 * math.sin(time.time() * 4.0))
        pygame.draw.rect(self.screen, (8, 14, 28), panel_rect, border_radius=16)
        
        if self.result_type == "win":
            border_color = (80, 255, 120)
            title_color = (255, 215, 0)
        elif self.result_type == "lose":
            border_color = (255, 80, 80)
            title_color = (255, 200, 200)
        else:
            border_color = (100, 255, 200)
            title_color = (200, 255, 220)
        
        pygame.draw.rect(self.screen, border_color, panel_rect.inflate(pulse, pulse), 1, border_radius=20)
        pygame.draw.rect(self.screen, border_color, panel_rect, 3, border_radius=16)
        
        title_font = self.font_big if panel_w < 620 else self.font_title
        title_surf = title_font.render(self.result_message, True, title_color)
        title_rect = title_surf.get_rect(center=(SCREEN_RES[0] // 2, py + 64))
        self.screen.blit(title_surf, title_rect)
        
        if self.result_subtitle:
            sub_surf = self.font_hud.render(self.result_subtitle, True, self.theme["hud_text"])
            sub_rect = sub_surf.get_rect(center=(SCREEN_RES[0] // 2, py + 125))
            self.screen.blit(sub_surf, sub_rect)
        
        cont_surf = self.font_text.render("ENTER/SPACE continue   ESC menu", True, self.theme["sub"])
        cont_rect = cont_surf.get_rect(center=(SCREEN_RES[0] // 2, py + panel_h - 42))
        self.screen.blit(cont_surf, cont_rect)

    def _draw_ai_thinking(self):
        overlay = pygame.Surface(SCREEN_RES, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        ai_box = pygame.Rect(400, 300, 480, 120)
        pygame.draw.rect(self.screen, (8, 14, 28), ai_box, border_radius=12)
        pygame.draw.rect(self.screen, self.theme["player"], ai_box, 2, border_radius=12)
        diff_name = self.ai_difficulty_names[self.ai_difficulty_index]
        ai_label = self.font_hud.render(f"{diff_name} thinking...", True, self.theme["player"])
        ai_rect = ai_label.get_rect(center=(640, 340))
        self.screen.blit(ai_label, ai_rect)
        dots = "." * (int(time.time() * 3) % 4)
        ai_progress = self.font_text.render(f"Calculating optimal path{dots}", True, self.theme["sub"])
        progress_rect = ai_progress.get_rect(center=(640, 380))
        self.screen.blit(ai_progress, progress_rect)
        if hasattr(self.ai_opponent, 'thought_progress'):
            bar_width = 300
            bar_x = 490
            bar_y = 400
            pygame.draw.rect(self.screen, (20, 30, 50), (bar_x, bar_y, bar_width, 8), border_radius=4)
            fill = int(bar_width * self.ai_opponent.thought_progress)
            if fill > 0:
                pygame.draw.rect(self.screen, self.theme["goal"], (bar_x, bar_y, fill, 8), border_radius=4)

    def _draw_multiplayer_indicator(self):
        indicator_text = f"🎮 Controlling: {self.multiplayer_names[self.multiplayer_active_player]}"
        indicator_color = self.theme["player"] if self.multiplayer_active_player == 0 else self.theme["clone"]
        indicator = self.font_text.render(indicator_text, True, indicator_color)
        self.screen.blit(indicator, (SCREEN_RES[0] - 300, SCREEN_RES[1] - 40))
        score_text = f"{self.multiplayer_names[0]}: {self.multiplayer_scores[0]} | {self.multiplayer_names[1]}: {self.multiplayer_scores[1]}"
        score_surf = self.font_tiny.render(score_text, True, self.theme["sub"])
        self.screen.blit(score_surf, (SCREEN_RES[0] - 450, SCREEN_RES[1] - 60))

    def draw_competitor_arena(self):
        panel = self.get_competitor_panel_rect()
        if panel is None:
            return
        self.competition_panel_rect = panel
        pygame.draw.rect(self.screen, (8, 14, 28), panel, border_radius=12)
        border_color = self.theme["danger"] if self.game_mode == "ai" else self.theme["clone"]
        pygame.draw.rect(self.screen, border_color, panel, 2, border_radius=12)

        if self.game_mode == "multiplayer":
            other = 1 if self.multiplayer_active_player == 0 else 0
            title = f"{self.multiplayer_names[other]} Arena"
        else:
            title = "AI Arena"
        self.screen.blit(self.font_text.render(title, True, border_color), (panel.x + 10, panel.y + 8))

        draw_grid = self.grid
        draw_entities = self.entities
        if self.game_mode == "multiplayer" and self.multiplayer_states[1 if self.multiplayer_active_player == 0 else 0]:
            other_state = self.multiplayer_states[1 if self.multiplayer_active_player == 0 else 0]
            draw_grid = other_state["grid"]
            draw_entities = other_state["entities"]

        rows = len(draw_grid)
        cols = len(draw_grid[0]) if rows else 1
        grid_w = cols * 1.0
        grid_h = rows * 1.0
        tile = max(14, min(30, int(min((panel.w - 20) / max(1, grid_w), (panel.h - 42) / max(1, grid_h)))))
        ox = panel.x + (panel.w - cols * tile) // 2
        oy = panel.y + 30 + max(0, (panel.h - 40 - rows * tile) // 2)

        for y in range(rows):
            for x in range(cols):
                cell = pygame.Rect(ox + x * tile, oy + y * tile, tile, tile)
                v = draw_grid[y][x]
                pygame.draw.rect(self.screen, (16, 28, 46), cell, border_radius=4)
                if v == 1:
                    pygame.draw.rect(self.screen, self.theme["wall"], cell.inflate(-4, -4), border_radius=4)
                elif v == 2:
                    pygame.draw.rect(self.screen, self.theme["goal"], cell.inflate(-6, -6), 2, border_radius=3)
                elif v == 13:
                    pygame.draw.rect(self.screen, (82, 100, 136), cell.inflate(-4, -4), border_radius=4)
                elif v == 8:
                    pygame.draw.rect(self.screen, (176, 232, 255), cell.inflate(-5, -5), border_radius=3)
                elif v == 9:
                    pygame.draw.polygon(self.screen, self.theme["danger"], [(cell.centerx, cell.top + 4), (cell.right - 4, cell.bottom - 4), (cell.left + 4, cell.bottom - 4)])
                elif v == 10:
                    pygame.draw.circle(self.screen, (255, 215, 64), cell.center, max(2, tile // 4))
                elif v == 11:
                    pygame.draw.rect(self.screen, (120, 255, 170), cell.inflate(-8, -8), border_radius=3)
                elif v == 12:
                    pygame.draw.polygon(self.screen, self.theme["accent"], [(cell.left + 4, cell.centery), (cell.centerx, cell.top + 4), (cell.centerx, cell.bottom - 4), (cell.right - 4, cell.centery)])
                elif v in (5, 6):
                    pygame.draw.ellipse(self.screen, self.theme["portal"] if v == 5 else (155, 236, 255), cell.inflate(-6, -6), 2)

        for e in draw_entities:
            if e["type"] != 3:
                continue
            ex, ey = e["grid"]
            rect = pygame.Rect(ox + ex * tile + 2, oy + ey * tile + 2, tile - 4, tile - 4)
            pygame.draw.rect(self.screen, self.theme["box"], rect, border_radius=3)

        if self.game_mode == "ai":
            vx, vy = self.ai_opponent.get_visual_pos()
            ai_rect = pygame.Rect(int(ox + vx * tile + 2), int(oy + vy * tile + 2), tile - 4, tile - 4)
            pygame.draw.rect(self.screen, self.theme["danger"], ai_rect, border_radius=3)
            prog = f"{self.ai_opponent.ai_path_index}/{max(1, len(self.ai_opponent.ai_path))}"
            self.screen.blit(self.font_tiny.render(f"Progress {prog}", True, self.theme["sub"]), (panel.x + 10, panel.bottom - 22))
        else:
            marker = pygame.Rect(ox + 2, oy + 2, tile - 4, tile - 4)
            pygame.draw.rect(self.screen, self.theme["clone"], marker, border_radius=3)
            active_name = self.multiplayer_names[self.multiplayer_active_player]
            self.screen.blit(self.font_tiny.render(f"Active: {active_name} (click arenas)", True, self.theme["sub"]), (panel.x + 10, panel.bottom - 22))

    def draw_hud(self):
        hud_width = self.get_hud_width()
        left_panel = pygame.Rect(0, 0, hud_width, SCREEN_RES[1])
        pygame.draw.rect(self.screen, self.theme["hud"], left_panel)
        pygame.draw.line(self.screen, self.theme["player"], (hud_width - 2, 0), (hud_width - 2, SCREEN_RES[1]), 2)
        original_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(8, 8, max(0, hud_width - 16), SCREEN_RES[1] - 16))

        level_time = int(time.time() - self.level_start_time)
        elapsed = int(time.time() - self.game_start_time)
        best_level_score = int(self.best_scores.get(str(self.level_idx + 1), 0))
        level_num = self.level_idx + 1

        self.screen.blit(self.font_title.render("OMNI CORE", True, self.theme["player"]), (18, 20))
        self.screen.blit(self.font_hud.render(f"v{APP_VERSION}", True, self.theme["sub"]), (22, 92))
        level_display = self.font_hud.render(f"Level {level_num}/200", True, self.theme["goal"])
        self.screen.blit(level_display, (22, 162))

        y_base = 215
        stat_items = [
            (f"Moves: {self.move_count}  Lv: {self.level_move_count}", self.theme["hud_text"]),
            (f"Score: {self.total_score}", self.theme["hud_text"]),
            (f"Best: {best_level_score}", self.theme["hud_text"]),
        ]
        
        timer_color = (255, 80, 80) if level_time > 60 else self.theme["goal"]
        self.screen.blit(self.font_tiny.render(f"⏱ {level_time}s  Run: {elapsed}s", True, timer_color), (22, y_base + len(stat_items) * 18 + 2))
        for i, (text, color) in enumerate(stat_items):
            self.screen.blit(self.font_tiny.render(text, True, color), (22, y_base + i * 18))
        
        status_y = y_base + len(stat_items) * 18 + 22
        status_text = f"🪙{self.coins}  Rescue:{self.rescue_charges}  Combo x{self.combo_streak}"
        self.screen.blit(self.font_tiny.render(status_text, True, self.theme["goal"]), (22, status_y))
        
        if self.game_mode == "ai" and self.ai_vs_mode:
            countdown_color = (255, 80, 80) if self.ai_countdown < 30 else self.theme["goal"]
            cd_text = f"⏱ AI Countdown: {int(self.ai_countdown)}s"
            self.screen.blit(self.font_hud.render(cd_text, True, countdown_color), (22, status_y + 22))
            
            if not self.ai_thinking and self.ai_opponent.ai_path:
                progress = f"AI progress: {self.ai_opponent.ai_path_index}/{len(self.ai_opponent.ai_path)}"
                self.screen.blit(self.font_tiny.render(progress, True, self.theme["sub"]), (22, status_y + 50))
        
        challenge_y = status_y + (50 if self.game_mode == "ai" else 24)
        if hasattr(self, 'level_challenges') and str(level_num) in self.level_challenges:
            ch = self.level_challenges[str(level_num)]
            self.screen.blit(self.font_tiny.render(f"🎯 {ch[:36]}", True, self.theme["sub"]), (22, challenge_y))
        
        controls_y = min(challenge_y + 40, SCREEN_RES[1] - 160)
        pygame.draw.line(self.screen, self.theme["player"], (22, controls_y), (hud_width - 10, controls_y), 1)
        control_labels = [
            ("CONTROLS", self.theme["goal"]),
            ("Arrows:Move  Z:Undo  R:Restart", self.theme["sub"]),
            ("K:Rescue  P:Assist  Esc:Pause", self.theme["sub"]),
        ]
        for i, (txt, clr) in enumerate(control_labels):
            self.screen.blit(self.font_tiny.render(txt, True, clr), (22, controls_y + 8 + i * 18))

        hud_store_rect = pygame.Rect(18, SCREEN_RES[1] - 104, min(190, hud_width - 36), 44)
        pygame.draw.rect(self.screen, (20, 35, 54), hud_store_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.theme["accent"], hud_store_rect, 2, border_radius=10)
        hud_store_label = self.font_tiny.render("🏪 STORE  (B)", True, self.theme["accent"])
        self.screen.blit(hud_store_label, hud_store_label.get_rect(center=hud_store_rect.center))
        self.hud_store_rect = hud_store_rect

        self.screen.set_clip(original_clip)

    def draw_touch_controls(self):
        size = 56 if SCREEN_RES[0] >= 900 else 46
        gap = 10
        base_x = SCREEN_RES[0] - (size * 3 + gap * 2) - 22
        base_y = SCREEN_RES[1] - (size * 3 + gap * 2) - 22
        self.touch_controls = {
            "up": pygame.Rect(base_x + size + gap, base_y, size, size),
            "left": pygame.Rect(base_x, base_y + size + gap, size, size),
            "down": pygame.Rect(base_x + size + gap, base_y + size + gap, size, size),
            "right": pygame.Rect(base_x + (size + gap) * 2, base_y + size + gap, size, size),
        }
        for name, rect in self.touch_controls.items():
            pygame.draw.rect(self.screen, (14, 20, 34), rect, border_radius=14)
            pygame.draw.rect(self.screen, self.theme["player"], rect, 2, border_radius=14)
            label = {"up": "↑", "left": "←", "down": "↓", "right": "→"}[name]
            text = self.font_hud.render(label, True, self.theme["hud_text"])
            self.screen.blit(text, text.get_rect(center=rect.center))

    def handle_touch_controls(self, pos):
        if not hasattr(self, "touch_controls"):
            return False
        for name, rect in self.touch_controls.items():
            if rect.collidepoint(pos):
                moves = {"up": (0, -1), "left": (-1, 0), "down": (0, 1), "right": (1, 0)}
                dx, dy = moves[name]
                self.move(dx, dy)
                return True
        return False

    def draw_welcome(self, dt):
        self.draw_background_fx(dt)
        self.welcome_timer += dt
        portrait = SCREEN_RES[1] > SCREEN_RES[0]
        title_font = self.font_big if portrait else self.font_title
        subtitle_font = self.font_text if portrait else self.font_hud
        center_x = SCREEN_RES[0] // 2
        center_y = SCREEN_RES[1] // 2
        title = title_font.render("OMNI CORE", True, self.theme["player"])
        self.screen.blit(title, title.get_rect(center=(center_x, center_y - 40)))
        sub = subtitle_font.render("Puzzle battle recharged for phone and desktop", True, self.theme["goal"])
        self.screen.blit(sub, sub.get_rect(center=(center_x, center_y + 15)))
        if self.welcome_timer > 1.5:
            pulse = int(abs(math.sin(time.time() * 3.0)) * 100)
            c = tuple(min(255, c + pulse) for c in self.theme["player"])
            prompt = self.font_text.render("Press ENTER to continue", True, c)
            self.screen.blit(prompt, prompt.get_rect(center=(center_x, SCREEN_RES[1] - 90)))
            button_w = min(260, SCREEN_RES[0] - 80)
            button_rect = pygame.Rect((SCREEN_RES[0] - button_w) // 2, SCREEN_RES[1] - 156, button_w, 52)
            self.welcome_start_rect = button_rect
            pygame.draw.rect(self.screen, (22, 40, 60), button_rect, border_radius=16)
            pygame.draw.rect(self.screen, self.theme["goal"], button_rect, 2, border_radius=16)
            label = self.font_hud.render("TAP TO START", True, self.theme["goal"])
            self.screen.blit(label, label.get_rect(center=button_rect.center))
        if self.welcome_timer > 8.0:
            self.set_state("menu", animated=True)

    def draw_campaign_intro(self, dt):
        self.draw_background_fx(dt)
        self.campaign_intro_timer += dt
        pane_w = min(820, SCREEN_RES[0] - 40)
        pane_h = min(560, SCREEN_RES[1] - 40)
        pane = pygame.Rect((SCREEN_RES[0] - pane_w) // 2, (SCREEN_RES[1] - pane_h) // 2, pane_w, pane_h)
        pygame.draw.rect(self.screen, (10, 16, 28), pane, border_radius=18)
        pygame.draw.rect(self.screen, self.theme["player"], pane, 2, border_radius=18)
        title = self.font_title.render("WELCOME, PILOT", True, self.theme["goal"])
        self.screen.blit(title, title.get_rect(center=(pane.centerx, pane.y + 68)))
        steps = [
            "1. Move with Arrow Keys or swipe.",
            "2. Push every box onto a glowing goal.",
            "3. Use Z for Undo, R for Restart, K for Rescue.",
            "4. Press Esc to pause, then return or change settings.",
            "5. Clear the board to unlock the next level.",
        ]
        active_step = min(len(steps) - 1, int(self.campaign_intro_timer // 2.0))
        if active_step > self.campaign_intro_step:
            self.campaign_intro_step = active_step
            self.play_ui_click(0.18)
        y = pane.y + 150
        for idx in range(self.campaign_intro_step + 1):
            prefix = "▶ " if idx == self.campaign_intro_step else "  "
            step_text = self.font_text.render(prefix + steps[idx], True, self.theme["hud_text"] if idx == self.campaign_intro_step else self.theme["sub"])
            self.screen.blit(step_text, (pane.x + 34, y))
            y += 46
        button_w = min(320, pane.w - 80)
        button_h = 54
        button_x = pane.centerx - button_w // 2
        button_y = pane.bottom - 92
        self.campaign_intro_button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        pygame.draw.rect(self.screen, (24, 42, 64), self.campaign_intro_button_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.theme["accent"], self.campaign_intro_button_rect, 2, border_radius=16)
        prompt = self.font_hud.render("TAP OR PRESS ENTER", True, self.theme["accent"])
        self.screen.blit(prompt, prompt.get_rect(center=self.campaign_intro_button_rect.center))
        if self.campaign_intro_timer >= 12.0:
            self.campaign_intro_active = False
            self.set_state("playing", animated=True)

    def draw_background_fx(self, dt):
        self.draw_gradient_background()
        phase = time.time()
        for star in self.stars:
            star.update(dt, phase)
            star.draw(self.screen, phase)

    def draw_gradient_background(self):
        top = self.theme["bg_a"]
        bottom = self.theme["bg_b"]
        for y in range(SCREEN_RES[1]):
            t = y / SCREEN_RES[1]
            color = (int(top[0]*(1-t)+bottom[0]*t), int(top[1]*(1-t)+bottom[1]*t), int(top[2]*(1-t)+bottom[2]*t))
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_RES[0], y))

    def draw_music_badge(self):
        status = self.music_status_text()
        colors = {"ON": (80, 230, 120), "OFF": (255, 170, 80), "UNAVAILABLE": (255, 110, 110)}
        color = colors.get(status, (240, 240, 240))
        badge = pygame.Rect(18, SCREEN_RES[1] - 52, 210, 36)
        pygame.draw.rect(self.screen, (12, 16, 30), badge, border_radius=8)
        pygame.draw.rect(self.screen, color, badge, 2, border_radius=8)
        text = self.font_tiny.render(f"Music: {status}", True, color)
        self.screen.blit(text, (badge.x + 14, badge.y + 10))

    def draw_toast(self):
        if self.toast_timer <= 0:
            return
        w, h = 420, 40
        x = (SCREEN_RES[0] - w) // 2
        y = SCREEN_RES[1] - 72
        pane = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (10, 16, 28), pane, border_radius=10)
        border_color = self.toast_color if hasattr(self, 'toast_color') and self.toast_color else self.theme["goal"]
        pygame.draw.rect(self.screen, border_color, pane, 2, border_radius=10)
        msg = self.font_tiny.render(self.toast_text, True, self.theme["hud_text"])
        msg.set_alpha(min(255, self.toast_timer * 2))
        self.screen.blit(msg, (x + 14, y + 12))
        self.toast_timer -= 1

    def draw_pause_menu(self):
        overlay = pygame.Surface(SCREEN_RES, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        box_width, box_height = 500, 350
        box_x = (SCREEN_RES[0] - box_width) // 2
        box_y = (SCREEN_RES[1] - box_height) // 2
        pause_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, (8, 14, 28), pause_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.theme["goal"], pause_rect, 3, border_radius=16)
        title = self.font_title.render("⏸ PAUSED", True, self.theme["goal"])
        title_rect = title.get_rect(center=(SCREEN_RES[0] // 2, box_y + 40))
        self.screen.blit(title, title_rect)
        options = [
            ("Press ESC to Resume", "Resume playing", self.theme["hud_text"]),
            ("Press S for Settings", "Adjust game options", self.theme["sub"]),
            ("Press M for Music", "Toggle music on/off", self.theme["sub"]),
            ("Press Q for Quit", "Return to main menu", self.theme["sub"]),
        ]
        y_offset = box_y + 100
        for i, (cmd, desc, color) in enumerate(options):
            cmd_text = self.font_text.render(cmd, True, self.theme["goal"])
            desc_text = self.font_tiny.render(desc, True, color)
            self.screen.blit(cmd_text, (box_x + 30, y_offset + i * 60))
            self.screen.blit(desc_text, (box_x + 50, y_offset + i * 60 + 25))

    def draw_menu(self, dt):
        self.draw_background_fx(dt)
        portrait = SCREEN_RES[1] > SCREEN_RES[0]
        margin = 24 if portrait else 60
        frame = pygame.Rect(margin, margin, SCREEN_RES[0] - margin * 2, SCREEN_RES[1] - margin * 2 - 20)
        pygame.draw.rect(self.screen, (8, 14, 28), frame, border_radius=18)
        pygame.draw.rect(self.screen, self.theme["player"], frame, 2, border_radius=18)
        
        title_font = self.font_big if portrait else self.font_title
        title = title_font.render("OMNI CORE REDUX", True, self.theme["player"])
        self.screen.blit(title, (frame.x + 24, frame.y + 18))
        subtitle = self.font_hud.render("Premium Edition", True, self.theme["goal"])
        version = self.font_tiny.render(f"v{APP_VERSION}", True, self.theme["sub"])
        self.screen.blit(subtitle, (frame.x + 28, frame.y + 92))
        self.screen.blit(version, (frame.x + 28, frame.y + 122))
        pygame.draw.line(self.screen, self.theme["player"], (frame.x + 18, frame.y + 152), (frame.right - 18, frame.y + 152), 1)

        if portrait:
            left_col_x = frame.x + 24
            left_col_w = frame.w - 48
            stats_x = left_col_x
            stats_y = frame.y + 520
        else:
            left_col_x = frame.x + 24
            left_col_w = 360
            stats_x = frame.x + 420
            stats_y = frame.y + 430
        desc_col_x = left_col_x + left_col_w + (18 if not portrait else 0)
        desc_col_w = max(160, frame.right - desc_col_x - 24) if not portrait else left_col_w

        self.screen.blit(self.font_hud.render("GAME MODE", True, self.theme["hud_text"]), (left_col_x, frame.y + 170))
        modes = [
            ("🎮 Campaign", "campaign", "Play through 200 levels!"),
            ("📅 Daily Challenge", "daily", "New challenges every day!"),
            ("🤖 VS AI", "ai", "Race against CyberBrain AI!"),
            ("👥 Multiplayer", "multiplayer", "Local 2-player hotseat!"),
        ]
        for i, (mode_name, mode_id, mode_desc) in enumerate(modes):
            y = frame.y + 208 + i * (52 if portrait else 48)
            active = self.menu_mode_index == i
            mode_rect = pygame.Rect(left_col_x, y, left_col_w, 40 if portrait else 36)
            pygame.draw.rect(self.screen, (16, 28, 46) if not active else (22, 40, 60), mode_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.theme["goal"] if active else self.theme["sub"], mode_rect, 2 if active else 1, border_radius=8)
            mode_label = self.font_text.render(mode_name, True, self.theme["goal"] if active else self.theme["hud_text"])
            self.screen.blit(mode_label, (mode_rect.x + 10, mode_rect.y + 8))
            desc_rect = pygame.Rect(desc_col_x, y, desc_col_w, 40 if portrait else 36)
            pygame.draw.rect(self.screen, (12, 22, 36), desc_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.theme["sub"], desc_rect, 1, border_radius=8)
            desc_label = self.font_tiny.render(mode_desc, True, self.theme["sub"])
            self.screen.blit(desc_label, (desc_rect.x + 10, desc_rect.y + 10))
        
        if self.menu_mode_index == 2:
            diff_y = frame.y + 208 + 4 * (52 if portrait else 45) + 5
            self.screen.blit(self.font_tiny.render("AI Difficulty:", True, self.theme["sub"]), (left_col_x, diff_y))
            diff_rect = pygame.Rect(left_col_x + 170, diff_y - 3, 180 if not portrait else 150, 25)
            pygame.draw.rect(self.screen, (22, 40, 60), diff_rect, border_radius=6)
            pygame.draw.rect(self.screen, self.theme["player"], diff_rect, 2, border_radius=6)
            diff_name = self.ai_difficulty_names[self.ai_difficulty_index]
            diff_label = self.font_tiny.render(diff_name, True, self.theme["player"])
            self.screen.blit(diff_label, (diff_rect.x + 8, diff_rect.y + 4))
            self.screen.blit(self.font_tiny.render("← → to change", True, self.theme["sub"]), (diff_rect.right + 12, diff_y))

        stat_panel = pygame.Rect(stats_x - 10, stats_y - 12, frame.right - stats_x - 24, 126)
        pygame.draw.rect(self.screen, (10, 16, 28), stat_panel, border_radius=10)
        pygame.draw.rect(self.screen, self.theme["player"], stat_panel, 1, border_radius=10)
        stats_items = [
            (f"🪙 Coins: {self.coins}", self.theme["accent"]),
            (f"🏆 Run Score: {self.total_score}", self.theme["goal"]),
            (f"🎯 Level: {self.selected_level + 1}/{self.unlocked_level}", self.theme["goal"]),
        ]
        if self.game_submode == "ai":
            stats_items.append((f"🤖 AI High Score: {self.ai_score}", self.theme["player"]))
        for i, (text, color) in enumerate(stats_items):
            self.screen.blit(self.font_text.render(text, True, color), (stats_x, stats_y + i * 28))

        menu_store_rect = pygame.Rect(frame.right - 220, frame.bottom - 110, 190, 44)
        pygame.draw.rect(self.screen, (20, 35, 54), menu_store_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.theme["accent"], menu_store_rect, 2, border_radius=10)
        menu_store_label = self.font_text.render("🏪 STORE", True, self.theme["accent"])
        self.screen.blit(menu_store_label, menu_store_label.get_rect(center=menu_store_rect.center))
        self.menu_store_rect = menu_store_rect
        
        controls_y = max(frame.y + 520 if not portrait else stats_y + 170, stats_y + len(stats_items) * 28 + 32)
        self.screen.blit(self.font_hud.render("⌨ CONTROLS", True, self.theme["hud_text"]), (frame.x + 24, controls_y))
        controls = [
            "↑↓: Select mode  |  ← →: Choose level  |  ENTER: Start",
            "L: Leaderboard  |  B: Store  |  T: Theme",
            "S: Settings  |  M: Music  |  Esc: Quit",
        ]
        for i, ctrl in enumerate(controls):
            self.screen.blit(self.font_tiny.render(ctrl, True, self.theme["sub"]), (frame.x + 24, controls_y + 30 + i * 22))

    def draw_post_level(self, dt):
        self.draw_background_fx(dt)
        overlay = pygame.Surface(SCREEN_RES, pygame.SRCALPHA)
        overlay.fill((6, 10, 20, 220))
        self.screen.blit(overlay, (0, 0))
        pane_w = min(860, SCREEN_RES[0] - 60)
        pane_h = min(620, SCREEN_RES[1] - 60)
        pane = pygame.Rect((SCREEN_RES[0] - pane_w) // 2, (SCREEN_RES[1] - pane_h) // 2, pane_w, pane_h)
        pygame.draw.rect(self.screen, (11, 20, 35), pane, border_radius=18)
        pygame.draw.rect(self.screen, self.theme["goal"], pane, 2, border_radius=18)
        rating = self.last_result["rating"]
        stars = "⭐" * {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}.get(rating, 0) + "☆" * (5 - {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}.get(rating, 0))
        header_font = self.font_title if pane_w >= 760 else self.font_big
        header = header_font.render(f"LEVEL {self.last_result['level']} CLEAR", True, self.theme["goal"])
        self.screen.blit(header, header.get_rect(center=(pane.centerx, pane.y + 70)))
        stars_surf = self.font_hud.render(stars, True, (255, 215, 0))
        self.screen.blit(stars_surf, stars_surf.get_rect(center=(pane.centerx, pane.y + 138)))
        
        stats_y = pane.y + 200
        stats = [
            (f"Rating: {rating}", self.theme["player"]),
            (f"Score: {self.last_result['score']}", self.theme["hud_text"]),
            (f"Moves: {self.last_result['moves']} (Par {self.last_result['par_moves']})", self.theme["hud_text"]),
            (f"Time: {self.last_result['time']}s (Par {self.last_result['par_time']}s)", self.theme["hud_text"]),
        ]
        if self.game_mode == "ai" and self.ai_opponent.ai_solved:
            ai_res = self.ai_opponent.last_result
            beat_ai = self.total_score > self.ai_score
            ai_text = f"🤖 AI: {ai_res['rating']} ({int(ai_res['score'])}pts) in {self.ai_opponent.ai_time:.1f}s"
            ai_color = self.theme["goal"] if beat_ai else self.theme["danger"]
            stats.append((ai_text, ai_color))
            result_text = "✅ YOU WON!" if beat_ai else "😔 AI Won This Round"
            stats.append((result_text, self.theme["goal"] if beat_ai else self.theme["sub"]))
        
        for i, (text, color) in enumerate(stats):
            stat_surf = self.font_hud.render(text, True, color)
            self.screen.blit(stat_surf, (pane.x + 36, stats_y + i * 34))
        coin_line = self.font_text.render(f"Coins earned: +{getattr(self, 'last_coin_gain', 0)}  Wallet: {self.coins}", True, self.theme["accent"])
        self.screen.blit(coin_line, (pane.x + 36, stats_y + len(stats) * 34 + 10))

        buttons = [
            ("ENTER / SPACE", "Next", self.theme["goal"]),
            ("ESC", "Menu", self.theme["sub"]),
            ("B", "Store", self.theme["accent"]),
        ]
        base_y = pane.bottom - 104
        for idx, (key_text, label, color) in enumerate(buttons):
            btn = pygame.Rect(pane.x + 36 + idx * 210, base_y, 190, 52)
            pygame.draw.rect(self.screen, (18, 30, 48), btn, border_radius=14)
            pygame.draw.rect(self.screen, color, btn, 2, border_radius=14)
            top = self.font_tiny.render(key_text, True, color)
            bottom = self.font_text.render(label, True, self.theme["hud_text"])
            self.screen.blit(top, top.get_rect(center=(btn.centerx, btn.y + 16)))
            self.screen.blit(bottom, bottom.get_rect(center=(btn.centerx, btn.y + 34)))

    def draw_leaderboard(self, dt):
        self.draw_background_fx(dt)
        portrait = SCREEN_RES[1] > SCREEN_RES[0]
        pane = pygame.Rect(18, 54, SCREEN_RES[0] - 36, SCREEN_RES[1] - 84) if portrait else pygame.Rect(100, 40, SCREEN_RES[0] - 200, SCREEN_RES[1] - 70)
        pygame.draw.rect(self.screen, (11, 20, 35), pane, border_radius=16)
        pygame.draw.rect(self.screen, self.theme["player"], pane, 2, border_radius=16)
        title = (self.font_big if portrait else self.font_title).render("🏆 LEADERBOARD", True, self.theme["player"])
        self.screen.blit(title, (pane.x + 28, pane.y + 18))

        headers = ["#", "Name", "Mode", "Score", "Time", "Moves"]
        hx = [pane.x + 28, pane.x + 90, pane.x + 250, pane.x + 430, pane.x + 560, pane.x + 660]
        for i, head in enumerate(headers):
            self.screen.blit(self.font_tiny.render(head, True, self.theme["goal"]), (hx[i], pane.y + 92))

        if not self.leaderboard:
            msg = self.font_text.render("No entries yet. Finish levels to record scores.", True, self.theme["sub"])
            self.screen.blit(msg, (pane.x + 30, pane.y + 150))
        else:
            max_rows = 10
            for idx, entry in enumerate(self.leaderboard[:max_rows]):
                y = pane.y + 130 + idx * 34
                row = pygame.Rect(pane.x + 20, y - 4, pane.w - 40, 28)
                pygame.draw.rect(self.screen, (14, 24, 40) if idx % 2 == 0 else (12, 20, 34), row, border_radius=6)
                values = [
                    str(idx + 1),
                    str(entry.get("name", "Player"))[:12],
                    str(entry.get("mode", "Campaign"))[:10],
                    str(entry.get("score", 0)),
                    f"{entry.get('time', 0)}s",
                    str(entry.get("moves", 0)),
                ]
                for i, value in enumerate(values):
                    self.screen.blit(self.font_tiny.render(value, True, self.theme["hud_text"]), (hx[i], y))

        footer = self.font_text.render("ESC: Return to menu", True, self.theme["sub"])
        self.screen.blit(footer, (pane.x + 24, pane.bottom - 34))

    def draw_store(self, dt):
        self.draw_background_fx(dt)
        portrait = SCREEN_RES[1] > SCREEN_RES[0]
        pane = pygame.Rect(18, 54, SCREEN_RES[0] - 36, SCREEN_RES[1] - 84) if portrait else pygame.Rect(120, 80, SCREEN_RES[0] - 240, SCREEN_RES[1] - 140)
        pygame.draw.rect(self.screen, (11, 20, 35), pane, border_radius=16)
        pygame.draw.rect(self.screen, self.theme["player"], pane, 2, border_radius=16)
        title = (self.font_big if portrait else self.font_title).render("🏪 SUPERMARKET", True, self.theme["accent"])
        self.screen.blit(title, (pane.x + 28, pane.y + 18))
        self.screen.blit(self.font_hud.render(f"🪙 Coins: {self.coins}", True, self.theme["goal"]), (pane.x + 30, pane.y + 86))

        tab_y = pane.y + 130
        tab_w = (pane.w - 80) // len(self.store_categories)
        for i, cat in enumerate(self.store_categories):
            tab = pygame.Rect(pane.x + 24 + i * (tab_w + 8), tab_y, tab_w, 34)
            active = i == self.store_category
            pygame.draw.rect(self.screen, (20, 35, 54) if active else (13, 24, 40), tab, border_radius=8)
            pygame.draw.rect(self.screen, self.theme["goal"] if active else self.theme["sub"], tab, 2 if active else 1, border_radius=8)
            name = self.store_category_names[i]
            label = self.font_tiny.render(name, True, self.theme["goal"] if active else self.theme["sub"])
            self.screen.blit(label, label.get_rect(center=tab.center))

        items = [it for it in self.store_items if it.get("category") == self.store_categories[self.store_category]]
        if items:
            self.store_cursor = max(0, min(self.store_cursor, len(items) - 1))

        start_y = tab_y + 48
        row_h = 58
        visible_rows = max(1, (pane.bottom - 120 - start_y) // row_h)
        top_index = min(self.store_cursor, max(0, len(items) - visible_rows)) if items else 0
        for idx in range(top_index, min(len(items), top_index + visible_rows)):
            item = items[idx]
            y = start_y + (idx - top_index) * row_h
            row = pygame.Rect(pane.x + 24, y, pane.w - 48, row_h - 8)
            active = idx == self.store_cursor
            pygame.draw.rect(self.screen, (22, 40, 60) if active else (14, 24, 40), row, border_radius=10)
            pygame.draw.rect(self.screen, self.theme["player"] if active else self.theme["sub"], row, 2 if active else 1, border_radius=10)

            owned = item["id"] in self.owned_skins
            equipped = self.box_skin == item["id"]
            status = "EQUIPPED" if equipped else ("OWNED" if owned else f"{item['price']} coins")
            status_color = self.theme["success"] if owned else (self.theme["danger"] if self.coins < item["price"] else self.theme["goal"])

            name = self.font_text.render(item["name"], True, self.theme["hud_text"])
            desc = self.font_tiny.render(item.get("desc", ""), True, self.theme["sub"])
            price = self.font_tiny.render(status, True, status_color)
            self.screen.blit(name, (row.x + 12, row.y + 8))
            self.screen.blit(desc, (row.x + 12, row.y + 30))
            self.screen.blit(price, (row.right - 160, row.y + 20))

        help_text = "↑↓ Select  ←→ Category  ENTER Buy/Equip  ESC Back"
        self.screen.blit(self.font_tiny.render(help_text, True, self.theme["sub"]), (pane.x + 24, pane.bottom - 34))

    def draw_name_entry(self, dt):
        self.draw_background_fx(dt)
        portrait = SCREEN_RES[1] > SCREEN_RES[0]
        pane = pygame.Rect(18, 140, SCREEN_RES[0] - 36, min(360, SCREEN_RES[1] - 180)) if portrait else pygame.Rect(240, 160, SCREEN_RES[0] - 480, SCREEN_RES[1] - 320)
        pygame.draw.rect(self.screen, (11, 20, 35), pane, border_radius=16)
        pygame.draw.rect(self.screen, self.theme["player"], pane, 2, border_radius=16)
        mode_labels = {"campaign": "🎮 Campaign", "daily": "📅 Daily Challenge", "ai": "🤖 VS AI", "multiplayer": "👥 Multiplayer"}
        mode_name = mode_labels.get(self.pending_mode, "Campaign")
        title = (self.font_big if portrait else self.font_title).render("PILOT IDENT", True, self.theme["player"])
        self.screen.blit(title, (pane.x + 30, pane.y + 26))
        self.screen.blit(self.font_hud.render(f"Mode: {mode_name}", True, self.theme["goal"]), (pane.x + 30, pane.y + 96))
        box_w = pane.w - 60
        box = pygame.Rect(pane.x + 30, pane.y + 160, box_w, 52)
        pygame.draw.rect(self.screen, (8, 14, 28), box, border_radius=8)
        pygame.draw.rect(self.screen, self.theme["goal"], box, 2, border_radius=8)
        blink = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else ""
        display_name = (self.name_input or "PLAYER") + blink
        self.screen.blit(self.font_hud.render(display_name, True, self.theme["hud_text"]), (box.x + 16, box.y + 10))

    def draw_settings(self, dt):
        self.draw_background_fx(dt)
        portrait = SCREEN_RES[1] > SCREEN_RES[0]
        pane = pygame.Rect(18, 54, SCREEN_RES[0] - 36, SCREEN_RES[1] - 84) if portrait else pygame.Rect(200, 80, SCREEN_RES[0] - 400, SCREEN_RES[1] - 140)
        pygame.draw.rect(self.screen, (11, 20, 35), pane, border_radius=16)
        pygame.draw.rect(self.screen, self.theme["player"], pane, 2, border_radius=16)
        title = (self.font_big if portrait else self.font_title).render("⚙ SETTINGS", True, self.theme["player"])
        self.screen.blit(title, (pane.x + 28, pane.y + 20))
        close_rect = pygame.Rect(pane.right - 46, pane.y + 18, 28, 28)
        pygame.draw.rect(self.screen, (14, 20, 34), close_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.theme["danger"], close_rect, 2, border_radius=8)
        close_text = self.font_tiny.render("X", True, self.theme["danger"])
        self.screen.blit(close_text, close_text.get_rect(center=close_rect.center))
        self.settings_close_rect = close_rect
        settings_list = [
            ("🎵 Music Volume", f"{int(self.settings['music_volume']*100)}%", "music_volume", "range"),
            ("🔊 Sound Effects", f"{int(self.settings['sfx_volume']*100)}%", "sfx_volume", "range"),
            ("⌨ Typing Volume", f"{int(self.settings.get('typing_volume', 0.55)*100)}%", "typing_volume", "range"),
            ("🖱 Button Volume", f"{int(self.settings.get('ui_volume', 0.45)*100)}%", "ui_volume", "range"),
            ("⌨ Typing Sounds", "ON" if self.settings.get('typing_sound', True) else "OFF", "typing_sound", "toggle"),
            ("🎯 Difficulty", self.settings['difficulty'].upper(), "difficulty", "cycle"),
            ("📱 Touch Controls", "ON" if self.settings['touch_controls'] else "OFF", "touch_controls", "toggle"),
            ("✨ Particle Effects", "ON" if self.settings.get('particle_effects', True) else "OFF", "particle_effects", "toggle"),
            ("💥 Screen Shake", "ON" if self.settings.get('screen_shake', True) else "OFF", "screen_shake", "toggle"),
            ("👻 Ghost Preview", "ON" if self.settings.get('ghost_preview', True) else "OFF", "ghost_preview", "toggle"),
        ]
        row_w = pane.w - 60
        for i, (label, value, key, ctrl_type) in enumerate(settings_list):
            y = pane.y + 100 + i * (52 if portrait else 55)
            row = pygame.Rect(pane.x + 30, y, row_w, 45)
            active = i == self.settings_cursor
            pygame.draw.rect(self.screen, (16, 28, 46) if not active else (22, 40, 60), row, border_radius=8)
            pygame.draw.rect(self.screen, self.theme["goal"] if active else self.theme["sub"], row, 2 if active else 1, border_radius=8)
            self.screen.blit(self.font_text.render(label, True, self.theme["hud_text"]), (row.x + 20, row.y + 12))
            self.screen.blit(self.font_text.render(value, True, self.theme["goal"] if active else self.theme["sub"]), (row.right - 150, row.y + 12))
        self.screen.blit(self.font_tiny.render("ESC: Back", True, self.theme["sub"]), (pane.x + 28, pane.bottom - 34))

    def draw_level_map(self, dt):
        self.draw_background_fx(dt)
        portrait = SCREEN_RES[1] > SCREEN_RES[0]
        pane = pygame.Rect(16, 54, SCREEN_RES[0] - 32, SCREEN_RES[1] - 84) if portrait else pygame.Rect(80, 50, SCREEN_RES[0] - 160, SCREEN_RES[1] - 90)
        pygame.draw.rect(self.screen, (11, 20, 35), pane, border_radius=16)
        pygame.draw.rect(self.screen, self.theme["player"], pane, 2, border_radius=16)
        title = (self.font_big if portrait else self.font_title).render("🗺 LEVEL MAP", True, self.theme["player"])
        self.screen.blit(title, (pane.x + 24, pane.y + 20))
        self.screen.blit(self.font_tiny.render("← → Select  ENTER: Play  ESC: Back", True, self.theme["sub"]), (pane.x + 24, pane.bottom - 30))

    def draw_victory(self, dt):
        self.draw_background_fx(dt)
        self.result_particles = [p for p in self.result_particles if p.update()]
        for p in self.result_particles:
            p.draw(self.screen)
        overlay = pygame.Surface(SCREEN_RES, pygame.SRCALPHA)
        overlay.fill((6, 10, 20, 220))
        self.screen.blit(overlay, (0, 0))
        pane = pygame.Rect(40, 50, SCREEN_RES[0] - 80, SCREEN_RES[1] - 100)
        pygame.draw.rect(self.screen, (11, 20, 35), pane, border_radius=18)
        pygame.draw.rect(self.screen, self.theme["goal"], pane, 2, border_radius=18)
        title = self.font_title.render("🎉 ALL DONE!", True, self.theme["goal"])
        self.screen.blit(title, title.get_rect(center=(pane.centerx, pane.y + 80)))
        footer = self.font_text.render("ENTER menu  L leaderboard  R restart", True, self.theme["sub"])
        self.screen.blit(footer, footer.get_rect(center=(pane.centerx, pane.bottom - 48)))

    def handle_keydown(self, key):
        # FIX #1: Handle K_KP_ENTER (keypad enter) same as K_RETURN
        if key == pygame.K_KP_ENTER:
            key = pygame.K_RETURN

        if self.transition_phase is not None:
            if key == pygame.K_ESCAPE:
                self.transition_phase = None
                self.transition_target_state = None
                self.set_state("menu")
            return

        if key == pygame.K_F11:
            self.toggle_window_mode()
            return
        
        if self.result_type:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.result_type = None
                if self.game_mode == "ai":
                    self.ai_vs_mode = False
                    self.pending_next_level = self.level_idx + 1
                    self.set_state("post_level", animated=True)
                elif self.game_mode == "multiplayer" and self.multiplayer_switch_pending is not None:
                    switch_to = self.multiplayer_switch_pending
                    self.multiplayer_switch_pending = None
                    self.switch_multiplayer_board(switch_to)
                    self.set_toast(f"{self.multiplayer_names[switch_to]}'s turn! Solve the puzzle!", seconds=2.0, color=self.theme["goal"])
                elif self.game_mode == "multiplayer":
                    self.pending_next_level = self.level_idx + 1
                    self.set_state("post_level", animated=True)
            elif key == pygame.K_ESCAPE:
                self.result_type = None
                self.multiplayer_switch_pending = None
                self.set_state("menu", animated=True)
            return

        if self.state in ("name_entry",) and key not in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.play_typing_sound()
        
        if self.alert_active:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                self.close_alert()
            return

        if key == pygame.K_s and self.state == "menu":
            self.play_ui_click(0.24)
            self.open_settings("menu")
            return
        if key == pygame.K_m and self.state == "menu":
            self.play_ui_click(0.24)
            self.set_state("level_map", animated=True)
            return
        if key == pygame.K_ESCAPE and self.state == "playing":
            self.paused = not self.paused
            return
        if key == pygame.K_m:
            self.play_ui_click(0.24)
            self.toggle_music()
            return
        if key == pygame.K_t:
            self.play_ui_click(0.24)
            self.cycle_theme()
            return
        if key == pygame.K_l:
            self.play_ui_click(0.24)
            self.set_state("leaderboard", animated=True)
            return
        if key == pygame.K_b and self.state in ("menu", "playing", "post_level"):
            self.play_ui_click(0.24)
            self.set_state("store", animated=True)
            return

        if self.state == "welcome":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.play_ui_click(0.24)
                self.set_state("menu", animated=True)
                self.welcome_shown = True
            return

        if self.state == "campaign_intro":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.play_ui_click(0.24)
                self.campaign_intro_active = False
                self.set_state("playing", animated=True)
            elif key == pygame.K_ESCAPE:
                self.play_ui_click(0.24)
                self.campaign_intro_active = False
                self.set_state("menu", animated=True)
            return

        if self.state == "settings":
            settings_keys = list(self.settings.keys())
            if key == pygame.K_UP:
                self.settings_cursor = max(0, self.settings_cursor - 1)
                self.play_ui_click(0.18)
            elif key == pygame.K_DOWN:
                self.settings_cursor = min(len(settings_keys) - 1, self.settings_cursor + 1)
                self.play_ui_click(0.18)
            elif key == pygame.K_LEFT:
                skey = settings_keys[self.settings_cursor]
                if skey == "music_volume":
                    self.settings[skey] = max(0.0, self.settings[skey] - 0.1)
                elif skey == "sfx_volume":
                    self.settings[skey] = max(0.0, self.settings[skey] - 0.1)
                elif skey in ("typing_volume", "ui_volume"):
                    self.settings[skey] = max(0.0, self.settings.get(skey, 0.5) - 0.1)
                elif skey == "difficulty":
                    diffs = ["easy", "normal", "hard", "expert"]
                    idx = diffs.index(self.settings[skey])
                    self.settings[skey] = diffs[max(0, idx - 1)]
                    self.update_difficulty_profile()
                else:
                    self.settings[skey] = not self.settings[skey]
                self.play_ui_click(0.22)
                self.play_typing_sound()
                self.apply_audio_settings()
            elif key == pygame.K_RIGHT:
                skey = settings_keys[self.settings_cursor]
                if skey == "music_volume":
                    self.settings[skey] = min(1.0, self.settings[skey] + 0.1)
                elif skey == "sfx_volume":
                    self.settings[skey] = min(1.0, self.settings[skey] + 0.1)
                elif skey in ("typing_volume", "ui_volume"):
                    self.settings[skey] = min(1.0, self.settings.get(skey, 0.5) + 0.1)
                elif skey == "difficulty":
                    diffs = ["easy", "normal", "hard", "expert"]
                    idx = diffs.index(self.settings[skey])
                    self.settings[skey] = diffs[min(3, idx + 1)]
                    self.update_difficulty_profile()
                else:
                    self.settings[skey] = not self.settings[skey]
                self.play_ui_click(0.22)
                self.play_typing_sound()
                self.apply_audio_settings()
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.play_ui_click(0.24)
                self._save_progress()
                self.close_settings()
            elif key == pygame.K_ESCAPE:
                self.play_ui_click(0.24)
                self.close_settings()
            return

        if self.state == "level_map":
            if key == pygame.K_LEFT:
                self.selected_level = max(0, self.selected_level - 1)
                self.play_ui_click(0.18)
            elif key == pygame.K_RIGHT:
                self.selected_level = min(self.unlocked_level - 1, self.selected_level + 1)
                self.play_ui_click(0.18)
            elif key == pygame.K_RETURN:
                self.play_ui_click(0.24)
                self.pending_mode = "campaign"
                self.name_input = self.player_name
                self.set_state("name_entry", animated=True)
            elif key in (pygame.K_ESCAPE, pygame.K_SPACE):
                self.play_ui_click(0.24)
                self.set_state("menu", animated=True)
            return

        if self.state == "leaderboard":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.play_ui_click(0.24)
                self.set_state("menu", animated=True)
            return

        if self.state == "store":
            if key == pygame.K_LEFT:
                self.store_category = max(0, self.store_category - 1)
                self.store_cursor = 0
                self.play_ui_click(0.18)
            elif key == pygame.K_RIGHT:
                self.store_category = min(len(self.store_categories) - 1, self.store_category + 1)
                self.store_cursor = 0
                self.play_ui_click(0.18)
            elif key == pygame.K_UP:
                self.store_cursor = max(0, self.store_cursor - 1)
                self.play_ui_click(0.18)
            elif key == pygame.K_DOWN:
                cats = [i for i in self.store_items if i.get("category") == self.store_categories[self.store_category]]
                self.store_cursor = min(len(cats) - 1, self.store_cursor + 1)
                self.play_ui_click(0.18)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                cats = [i for i in self.store_items if i.get("category") == self.store_categories[self.store_category]]
                if self.store_cursor < len(cats):
                    item = cats[self.store_cursor]
                    if item["id"] in self.owned_skins:
                        self.box_skin = item["id"]
                        self.set_toast(f"Equipped {item['name']}")
                        self.play_ui_click(0.24)
                    elif self.coins >= item["price"]:
                        self.coins -= item["price"]
                        self.owned_skins.append(item["id"])
                        self.box_skin = item["id"]
                        self.set_toast(f"Purchased {item['name']}!")
                        self._save_progress()
                        self.play_ui_click(0.24)
                    else:
                        self.set_toast("Not enough coins!", color=(255, 80, 80))
                        self.play_sfx("box_hit", 0.22)
            elif key == pygame.K_ESCAPE:
                self.play_ui_click(0.24)
                self.set_state("menu", animated=True)
            return

        if self.state == "name_entry":
            if key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
                self.play_ui_click(0.14)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.player_name = (self.name_input.strip() or "Player")[:16]
                if self.pending_mode == "multiplayer":
                    self.multiplayer_names[0] = self.player_name
                    self.multiplayer_names[1] = f"{self.player_name} 2"
                    self.multiplayer_scores = [0, 0]
                self.play_ui_click(0.26)
                self.start_run(self.pending_mode)
            elif key == pygame.K_ESCAPE:
                self.play_ui_click(0.24)
                self.set_state("menu", animated=True)
            return

        if self.state == "menu":
            if key == pygame.K_UP:
                self.menu_mode_index = max(0, self.menu_mode_index - 1)
                self.play_ui_click(0.18)
            elif key == pygame.K_DOWN:
                self.menu_mode_index = min(3, self.menu_mode_index + 1)
                self.play_ui_click(0.18)
            elif key == pygame.K_LEFT:
                if self.menu_mode_index == 2:
                    self.ai_difficulty_index = max(0, self.ai_difficulty_index - 1)
                    self.play_ui_click(0.18)
                else:
                    self.selected_level = max(0, self.selected_level - 1)
                    self.play_ui_click(0.18)
            elif key == pygame.K_RIGHT:
                if self.menu_mode_index == 2:
                    self.ai_difficulty_index = min(3, self.ai_difficulty_index + 1)
                    self.play_ui_click(0.18)
                else:
                    self.selected_level = min(self.unlocked_level - 1, self.selected_level + 1)
                    self.play_ui_click(0.18)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                mode_map = {0: "campaign", 1: "daily", 2: "ai", 3: "multiplayer"}
                self.pending_mode = mode_map.get(self.menu_mode_index, "campaign")
                self.name_input = self.player_name
                tips = [
                    "Arrow Keys: Move",
                    "Z: Undo  R: Restart",
                    "K: Rescue cornered box",
                    "Esc: Pause/Menu",
                ]
                mode_labels = {
                    "campaign": "Conquer all 200 levels!",
                    "daily": "Fresh puzzles every day!",
                    "ai": f"Race against {self.ai_difficulty_names[self.ai_difficulty_index]}!",
                    "multiplayer": "Challenge a friend locally!",
                }
                self.show_alert(
                    f"🎮 {self.pending_mode.title()} Mode",
                    f"{mode_labels.get(self.pending_mode, '')}\nStarting Level: {self.selected_level + 1}\n\nPush boxes to goals!\nBeat the timer! Win prizes!",
                    tips=tips,
                    callback=lambda: self.set_state("name_entry", animated=True)
                )
                self.play_ui_click(0.24)
            return

        if self.state == "post_level":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.play_ui_click(0.24)
                self.level_idx = self.pending_next_level
                if self.game_mode == "ai":
                    self.ai_vs_mode = True
                    self.ai_countdown_active = True
                    self.ai_countdown = 120
                    self.ai_opponent.start_thinking()
                    self.ai_thinking = True
                    self.ai_has_completed = False
                self.load_current_level(reset_run_stats=False)
                if self.game_mode == "multiplayer":
                    base_state = self.capture_level_state()
                    self.multiplayer_initial_state = deepcopy(base_state)
                    self.multiplayer_states = [deepcopy(base_state), deepcopy(base_state)]
                    self.multiplayer_finished = [False, False]
                    self.multiplayer_finish_times = [None, None]
                    self.multiplayer_active_player = 0
                    self.restore_level_state(self.multiplayer_states[0])
                self.set_state("playing", animated=True)
            elif key == pygame.K_ESCAPE:
                self.play_ui_click(0.24)
                self.set_state("menu", animated=True)
            return

        if self.state == "victory":
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.play_ui_click(0.24)
                self.set_state("menu", animated=True)
            return

        if self.paused:
            if key == pygame.K_ESCAPE:
                self.paused = False
            elif key == pygame.K_s:
                self.play_ui_click(0.24)
                self.open_settings("playing")
                self.paused = False
            elif key == pygame.K_m:
                self.toggle_music()
            elif key == pygame.K_q:
                self.paused = False
                self.play_ui_click(0.24)
                self.set_state("menu", animated=True)
            return
        
        # FIX #2: Only process movement keys when in playing state
        if self.state == "playing" and not self.paused:
            if key == pygame.K_ESCAPE:
                self.paused = True
            elif key == pygame.K_UP:
                self.move(0, -1)
            elif key == pygame.K_DOWN:
                self.move(0, 1)
            elif key == pygame.K_LEFT:
                self.move(-1, 0)
            elif key == pygame.K_RIGHT:
                self.move(1, 0)
            elif key == pygame.K_z:
                self.undo()
            elif key == pygame.K_r:
                if self.game_mode == "multiplayer" and self.multiplayer_initial_state:
                    self.multiplayer_states[self.multiplayer_active_player] = deepcopy(self.multiplayer_initial_state)
                    self.restore_level_state(self.multiplayer_states[self.multiplayer_active_player])
                    self.multiplayer_finished[self.multiplayer_active_player] = False
                    self.multiplayer_finish_times[self.multiplayer_active_player] = None
                    self.set_toast(f"{self.multiplayer_names[self.multiplayer_active_player]} restarted")
                else:
                    self.load_current_level(reset_run_stats=False)
            elif key == pygame.K_k:
                self.rescue_cornered_box()
            elif key == pygame.K_p:
                self.push_assist = not self.push_assist
                self.set_toast(f"Push assist {'ON' if self.push_assist else 'OFF'}")

    def handle_textinput(self, text):
        if self.state != "name_entry":
            return
        if not text:
            return
        if text.isprintable() and len(self.name_input) < 16:
            self.name_input += text
            self.play_typing_sound()

    def handle_mouse_drag(self, start_pos, end_pos):
        if not start_pos or not end_pos:
            return
        if not hasattr(self, "player_panel_rect") or not self.player_panel_rect.collidepoint(start_pos):
            return
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        if (dx**2 + dy**2) ** 0.5 < 30:
            return
        if abs(dx) > abs(dy):
            direction = (1, 0) if dx > 0 else (-1, 0)
        else:
            direction = (0, 1) if dy > 0 else (0, -1)
        self.move(direction[0], direction[1])

    def toggle_music(self):
        self.music_on = not self.music_on
        try:
            if self.music_on:
                pygame.mixer.stop()
                self.sync_music_for_state()
                self.set_toast("🎵 Music ON", seconds=0.8)
            else:
                pygame.mixer.stop()
                self.set_toast("🔇 Music OFF", seconds=0.8)
            self.apply_audio_settings()
        except pygame.error:
            self.music_on = False

    def cycle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEMES)
        self.theme = THEMES[self.theme_index]

    async def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            await asyncio.sleep(0)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                elif event.type == pygame.TEXTINPUT:
                    self.handle_textinput(event.text)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.handle_window_button_click(event.pos):
                        self.play_ui_click(0.22)
                        continue
                    if self.state == "welcome" and hasattr(self, "welcome_start_rect") and self.welcome_start_rect.collidepoint(event.pos):
                        self.play_ui_click(0.24)
                        self.set_state("menu", animated=True)
                        self.welcome_shown = True
                        continue
                    if self.state == "settings" and hasattr(self, "settings_close_rect") and self.settings_close_rect.collidepoint(event.pos):
                        self.play_ui_click(0.22)
                        self.close_settings()
                        continue
                    if self.state == "menu" and hasattr(self, "menu_store_rect") and self.menu_store_rect.collidepoint(event.pos):
                        self.play_ui_click(0.22)
                        self.set_state("store", animated=True)
                        continue
                    if self.state == "playing" and hasattr(self, "hud_store_rect") and self.hud_store_rect.collidepoint(event.pos):
                        self.play_ui_click(0.22)
                        self.set_state("store", animated=True)
                        continue
                    if self.state == "campaign_intro" and hasattr(self, "campaign_intro_button_rect") and self.campaign_intro_button_rect.collidepoint(event.pos):
                        self.play_ui_click(0.24)
                        self.campaign_intro_active = False
                        self.set_state("playing", animated=True)
                        continue
                    if self.state == "playing" and not self.alert_active:
                        if self.game_mode == "multiplayer":
                            if hasattr(self, "competition_panel_rect") and self.competition_panel_rect.collidepoint(event.pos):
                                self.play_ui_click(0.22)
                                self.switch_multiplayer_board(1)
                                continue
                            if hasattr(self, "player_panel_rect") and self.player_panel_rect.collidepoint(event.pos):
                                if self.multiplayer_active_player != 0:
                                    self.play_ui_click(0.22)
                                    self.switch_multiplayer_board(0)
                                continue
                        if self.settings.get("touch_controls", True) and self.handle_touch_controls(event.pos):
                            continue
                        if hasattr(self, "player_panel_rect") and self.player_panel_rect.collidepoint(event.pos):
                            self.mouse_down = True
                            self.mouse_start_pos = pygame.mouse.get_pos()
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.state == "playing" and self.mouse_down:
                        self.mouse_down = False
                        self.mouse_current_pos = pygame.mouse.get_pos()
                        self.handle_mouse_drag(self.mouse_start_pos, self.mouse_current_pos)
                elif event.type == pygame.VIDEORESIZE:
                    self.resize_window(event.w, event.h)

            if self.state == "welcome":
                self.draw_welcome(dt)
            elif self.state == "menu":
                self.draw_menu(dt)
            elif self.state == "settings":
                self.draw_settings(dt)
            elif self.state == "level_map":
                self.draw_level_map(dt)
            elif self.state == "campaign_intro":
                self.draw_campaign_intro(dt)
            elif self.state == "playing":
                self.draw_world(dt)
            elif self.state == "post_level":
                self.draw_post_level(dt)
            elif self.state == "leaderboard":
                self.draw_leaderboard(dt)
            elif self.state == "name_entry":
                self.draw_name_entry(dt)
            elif self.state == "store":
                self.draw_store(dt)
            else:
                self.draw_victory(dt)

            self.draw_window_controls()
            self.update_transition()
            self.draw_transition_overlay()
            pygame.display.flip()

        pygame.quit()


async def main():
    await BrilliantEngine().run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
