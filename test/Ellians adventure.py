import os
import sys
import json
import random
import pygame

# Initialize Pygame
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
FPS = 60

SPRITE_SIZE = (48, 48)

# Color Palette
GREEN_GRASS = (80, 168, 70)
DARK_GRASS  = (60, 130, 50)
WALL_COLOR  = (70, 70, 85)
WALL_BORDER = (40, 40, 55)
UI_BG       = (25, 20, 35)
UI_BORDER   = (210, 165, 75)
UI_SLOT     = (45, 40, 60)
UI_SELECT   = (255, 220, 100)
TEXT_COLOR  = (240, 240, 240)
HP_RED      = (220, 40, 50)
HP_DARK     = (80, 10, 20)
SWORD_COLOR = (220, 220, 240)
BTN_HOVER   = (60, 50, 80)

DBG_PLAYER = (255, 255, 0)
DBG_ENEMY  = (255, 0, 255)
DBG_ATTACK = (255, 0, 0)
DBG_TEXT   = (0, 255, 255)
DBG_WALL   = (255, 128, 0)


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def load_maps_from_json():
    json_path = get_resource_path("maps.json")
    if not os.path.exists(json_path):
        default_grid = [
            [1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,1,1,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1],
            [1,0,0,1,1,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ]
        default_maps = {
            "0,0": {
                "grid": default_grid,
                "enemies": [[150, 150]],
                "chests": [[600, 150]],
                "items": [{"x": 250, "y": 300, "type": "sword"}, {"x": 550, "y": 250, "type": "potion"}]
            }
        }
        with open(json_path, 'w') as f:
            json.dump(default_maps, f, indent=2)

    with open(json_path, 'r') as f:
        raw_data = json.load(f)
        
    world_map = {}
    for key, data in raw_data.items():
        coords = tuple(map(int, key.split(',')))
        if isinstance(data, list):
            world_map[coords] = {"grid": data, "enemies": [], "chests": [], "items": []}
        else:
            world_map[coords] = data
    return world_map


def save_maps_to_json(world_map):
    json_path = get_resource_path("maps.json")
    out_data = {f"{c[0]},{c[1]}": data for c, data in world_map.items()}
    with open(json_path, 'w') as f:
        json.dump(out_data, f, indent=2)


class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type):
        super().__init__()
        self.item_type = item_type
        self.name = item_type.capitalize()
        self.image = self._create_item_surface()
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 20, 20)
        self.hitbox.center = self.rect.center

    def _create_item_surface(self):
        surf = pygame.Surface((28, 28), pygame.SRCALPHA)
        if self.item_type == 'sword':
            pygame.draw.rect(surf, (210, 210, 230), (12, 3, 4, 15))
            pygame.draw.rect(surf, (210, 165, 75), (7, 17, 14, 3))
            pygame.draw.rect(surf, (110, 55, 25), (12, 20, 4, 6))
        elif self.item_type == 'potion':
            pygame.draw.rect(surf, (160, 105, 55), (12, 3, 4, 3))
            pygame.draw.rect(surf, (230, 45, 65), (8, 6, 12, 18))
            pygame.draw.rect(surf, (255, 190, 200), (10, 9, 3, 5))
        elif self.item_type == 'gold':
            pygame.draw.circle(surf, (255, 215, 0), (14, 14), 10)
            pygame.draw.circle(surf, (218, 165, 32), (14, 14), 10, 2)
        return surf


class Chest(pygame.sprite.Sprite):
    def __init__(self, x, y, is_open=False):
        super().__init__()
        self.is_open = is_open
        self.image = self._create_chest_surface()
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 32, 32)
        self.hitbox.center = self.rect.center

    def _create_chest_surface(self):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        if not self.is_open:
            pygame.draw.rect(surf, (139, 69, 19), (2, 6, 28, 22), border_radius=3)
            pygame.draw.rect(surf, (210, 165, 75), (2, 6, 28, 22), 2, border_radius=3)
            pygame.draw.rect(surf, (210, 165, 75), (14, 14, 4, 6))
        else:
            pygame.draw.rect(surf, (100, 50, 15), (2, 12, 28, 16), border_radius=2)
            pygame.draw.rect(surf, (210, 165, 75), (2, 4, 28, 8), border_radius=2)
        return surf

    def open_chest(self):
        if not self.is_open:
            self.is_open = True
            self.image = self._create_chest_surface()
            roll = random.random()
            if roll < 0.50: return Item(self.rect.centerx, self.rect.centery + 10, 'potion')
            elif roll < 0.80: return Item(self.rect.centerx, self.rect.centery + 10, 'gold')
            else: return Item(self.rect.centerx, self.rect.centery + 10, 'sword')
        return None


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.speed = 1.2
        self.damage = 5
        self.max_hp = 10
        self.hp = 10
        self.image = self._load_enemy_sprite()
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 30, 30)
        self.hitbox.center = self.rect.center

    def _load_enemy_sprite(self):
        enemy_path = get_resource_path(os.path.join("sprites", "enemy.png"))
        if os.path.exists(enemy_path):
            try:
                raw_img = pygame.image.load(enemy_path).convert_alpha()
                return pygame.transform.smoothscale(raw_img, SPRITE_SIZE)
            except pygame.error:
                pass
        
        # Fallback sprite with full details (red body + yellow eye + dark center)
        surf = pygame.Surface(SPRITE_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (200, 30, 40), (4, 8, SPRITE_SIZE[0] - 8, SPRITE_SIZE[1] - 12))
        pygame.draw.circle(surf, (255, 230, 50), (SPRITE_SIZE[0] // 2, SPRITE_SIZE[1] // 2 - 2), 7)
        pygame.draw.circle(surf, (20, 20, 20), (SPRITE_SIZE[0] // 2, SPRITE_SIZE[1] // 2 - 2), 3)
        return surf

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0: self.kill()

    def draw_hp_bar(self, screen):
        bar_w, bar_h = 30, 4
        bar_x = self.hitbox.centerx - bar_w // 2
        bar_y = self.hitbox.top - 8
        pygame.draw.rect(screen, HP_DARK, (bar_x, bar_y, bar_w, bar_h))
        fill_w = int((self.hp / self.max_hp) * bar_w)
        if fill_w > 0: pygame.draw.rect(screen, HP_RED, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), 1)

    def update(self, player_hitbox, can_move=True):
        if not can_move: return
        dx = player_hitbox.centerx - self.hitbox.centerx
        dy = player_hitbox.centery - self.hitbox.centery
        dist = (dx**2 + dy**2)**0.5
        if dist != 0:
            self.hitbox.x += int((dx / dist) * self.speed)
            self.hitbox.y += int((dy / dist) * self.speed)
        self.rect.center = self.hitbox.center


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.speed = 3
        self.max_hp = 100
        self.hp = 100
        self.invincible_timer = 0
        self.is_attacking = False
        self.attack_timer = 0
        self.sword_damage = 3
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.hit_enemies = set()
        self.direction = 'down'
        self.frame_index = 0
        self.animation_speed = 0.15
        self.is_moving = False
        self.inventory = []
        self.equipped_item = None
        self.sprites = self._load_custom_sprites()
        self.image = self.sprites[self.direction][0]
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 24, 28)
        self.hitbox.center = self.rect.center

    def _load_custom_sprites(self):
        directions = ['down', 'up', 'left', 'right']
        sprites = {d: [] for d in directions}
        try:
            for d in directions:
                for i in range(1, 5):
                    file_path = get_resource_path(os.path.join("sprites", f"walk_{d}_{i}.png"))
                    img = pygame.image.load(file_path).convert_alpha()
                    sprites[d].append(pygame.transform.smoothscale(img, SPRITE_SIZE))
        except (FileNotFoundError, pygame.error):
            for d in directions:
                for _ in range(4):
                    surf = pygame.Surface(SPRITE_SIZE, pygame.SRCALPHA)
                    pygame.draw.rect(surf, (40, 130, 50), (0, 0, *SPRITE_SIZE))
                    sprites[d].append(surf)
        return sprites

    def attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 12
            self.hit_enemies.clear()
            reach = 30
            if self.direction == 'down': self.attack_rect = pygame.Rect(self.hitbox.left, self.hitbox.bottom, self.hitbox.width, reach)
            elif self.direction == 'up': self.attack_rect = pygame.Rect(self.hitbox.left, self.hitbox.top - reach, self.hitbox.width, reach)
            elif self.direction == 'left': self.attack_rect = pygame.Rect(self.hitbox.left - reach, self.hitbox.top, reach, self.hitbox.height)
            elif self.direction == 'right': self.attack_rect = pygame.Rect(self.hitbox.right, self.hitbox.top, reach, self.hitbox.height)

    def take_damage(self, amount):
        if self.invincible_timer == 0:
            self.hp = max(0, self.hp - amount)
            self.invincible_timer = 40

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def update(self, keys, keybinds, wall_rects, can_move=True):
        if self.invincible_timer > 0: self.invincible_timer -= 1
        if self.is_attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.hit_enemies.clear()

        if not can_move:
            self.is_moving = False
            self.image = self.sprites[self.direction][0]
            return

        dx, dy = 0, 0
        self.is_moving = False

        if keys[keybinds['LEFT']]: dx -= self.speed; self.direction = 'left'; self.is_moving = True
        elif keys[keybinds['RIGHT']]: dx += self.speed; self.direction = 'right'; self.is_moving = True
        if keys[keybinds['UP']]: dy -= self.speed; self.direction = 'up'; self.is_moving = True
        elif keys[keybinds['DOWN']]: dy += self.speed; self.direction = 'down'; self.is_moving = True

        self.hitbox.x += dx
        for wall in wall_rects:
            if self.hitbox.colliderect(wall):
                if dx > 0: self.hitbox.right = wall.left
                if dx < 0: self.hitbox.left = wall.right

        self.hitbox.y += dy
        for wall in wall_rects:
            if self.hitbox.colliderect(wall):
                if dy > 0: self.hitbox.bottom = wall.top
                if dy < 0: self.hitbox.top = wall.bottom

        self.rect.center = self.hitbox.center
        if self.is_moving:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.sprites[self.direction]): self.frame_index = 0
        else: self.frame_index = 0
        self.image = self.sprites[self.direction][int(self.frame_index)]

    def draw_attack_slash(self, screen):
        if self.is_attacking:
            pygame.draw.rect(screen, SWORD_COLOR, self.attack_rect, border_radius=4)


class InventoryUI:
    def __init__(self, font):
        self.font = font
        self.is_open = False
        self.selected_index = 0
        self.width, self.height = 360, 260
        self.rect = pygame.Rect((SCREEN_WIDTH - self.width) // 2, (SCREEN_HEIGHT - self.height) // 2, self.width, self.height)

    def toggle(self):
        self.is_open = not self.is_open
        self.selected_index = 0

    def handle_input(self, event, player, keybinds):
        if not self.is_open: return
        total_items = len(player.inventory)
        if event.type == pygame.KEYDOWN and total_items > 0:
            if event.key == keybinds['RIGHT']: self.selected_index = (self.selected_index + 1) % total_items
            elif event.key == keybinds['LEFT']: self.selected_index = (self.selected_index - 1) % total_items
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                item = player.inventory[self.selected_index]
                if item.item_type == 'sword': player.equipped_item = item
                elif item.item_type == 'potion':
                    player.heal(10)
                    player.inventory.pop(self.selected_index)
                    if self.selected_index >= len(player.inventory):
                        self.selected_index = max(0, len(player.inventory) - 1)

    def draw_hud(self, screen, player, keybinds):
        pygame.draw.rect(screen, UI_BG, (10, 10, 240, 50))
        pygame.draw.rect(screen, UI_BORDER, (10, 10, 240, 50), 2)
        pygame.draw.rect(screen, UI_SLOT, (16, 16, 38, 38))
        pygame.draw.rect(screen, UI_BORDER, (16, 16, 38, 38), 1)
        if player.equipped_item: screen.blit(player.equipped_item.image, (21, 21))

        hp_x, hp_y, hp_w, hp_h = 65, 20, 170, 16
        pygame.draw.rect(screen, HP_DARK, (hp_x, hp_y, hp_w, hp_h))
        cur_w = int((player.hp / player.max_hp) * hp_w)
        if cur_w > 0: pygame.draw.rect(screen, HP_RED, (hp_x, hp_y, cur_w, hp_h))
        pygame.draw.rect(screen, UI_BORDER, (hp_x, hp_y, hp_w, hp_h), 2)

        hp_text = self.font.render(f"HP: {player.hp}/{player.max_hp}", True, TEXT_COLOR)
        screen.blit(hp_text, (hp_x + 5, hp_y + 18))

    def draw_menu(self, screen, player, keybinds):
        if not self.is_open:
            inv_k = pygame.key.name(keybinds['INVENTORY']).upper()
            atk_k = pygame.key.name(keybinds['ATTACK']).upper()
            hint = self.font.render(f"[{inv_k}] Inventory | [{atk_k}] Attack | [E] Editor | [ESC] Menu", True, (255, 255, 255))
            screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 30))
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, UI_BG, self.rect)
        pygame.draw.rect(screen, UI_BORDER, self.rect, 4)

        title = self.font.render("— INVENTORY —", True, UI_BORDER)
        screen.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.y + 15))

        # Render 12 Grid Slots
        cols, rows = 4, 3
        slot_size = 48
        gap = 12
        grid_w = cols * slot_size + (cols - 1) * gap
        start_x = self.rect.centerx - grid_w // 2
        start_y = self.rect.y + 50

        for idx in range(12):
            c = idx % cols
            r = idx // cols
            sx = start_x + c * (slot_size + gap)
            sy = start_y + r * (slot_size + gap)
            slot_rect = pygame.Rect(sx, sy, slot_size, slot_size)

            pygame.draw.rect(screen, UI_SLOT, slot_rect)
            is_selected = (idx == self.selected_index and len(player.inventory) > 0)
            pygame.draw.rect(screen, UI_SELECT if is_selected else UI_BORDER, slot_rect, 2 if not is_selected else 3)

            # Draw Item inside slot if present
            if idx < len(player.inventory):
                itm = player.inventory[idx]
                img_x = sx + (slot_size - itm.image.get_width()) // 2
                img_y = sy + (slot_size - itm.image.get_height()) // 2
                screen.blit(itm.image, (img_x, img_y))

        # Show selected item description at the bottom
        if len(player.inventory) > 0 and self.selected_index < len(player.inventory):
            cur = player.inventory[self.selected_index]
            desc = f"{cur.name} (Press ENTER to Use/Equip)"
            desc_txt = self.font.render(desc, True, TEXT_COLOR)
            screen.blit(desc_txt, (self.rect.centerx - desc_txt.get_width() // 2, self.rect.bottom - 28))
        else:
            empty_txt = self.font.render("Inventory is Empty", True, (150, 150, 160))
            screen.blit(empty_txt, (self.rect.centerx - empty_txt.get_width() // 2, self.rect.bottom - 28))


class MenuSystem:
    def __init__(self, font, big_font):
        self.font = font
        self.big_font = big_font
        self.rebinding_key = None
        self.fullscreen = False
        self.keybinds = {
            'UP': pygame.K_w,
            'DOWN': pygame.K_s,
            'LEFT': pygame.K_a,
            'RIGHT': pygame.K_d,
            'ATTACK': pygame.K_SPACE,
            'INVENTORY': pygame.K_i
        }

    def draw_button(self, screen, text, x, y, w, h, is_hovered):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, BTN_HOVER if is_hovered else UI_BG, rect, border_radius=8)
        pygame.draw.rect(screen, UI_BORDER, rect, 2, border_radius=8)
        lbl = self.font.render(text, True, TEXT_COLOR)
        screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))
        return rect

    def draw_main_menu(self, screen, mouse_pos):
        screen.fill(UI_BG)
        title = self.big_font.render("ELIAN'S ADVENTURE", True, UI_BORDER)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        btn_w, btn_h = 200, 45
        play_r = self.draw_button(screen, "PLAY", SCREEN_WIDTH // 2 - btn_w // 2, 230, btn_w, btn_h, pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, 230, btn_w, btn_h).collidepoint(mouse_pos))
        opts_r = self.draw_button(screen, "OPTIONS", SCREEN_WIDTH // 2 - btn_w // 2, 295, btn_w, btn_h, pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, 295, btn_w, btn_h).collidepoint(mouse_pos))
        quit_r = self.draw_button(screen, "QUIT", SCREEN_WIDTH // 2 - btn_w // 2, 360, btn_w, btn_h, pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, 360, btn_w, btn_h).collidepoint(mouse_pos))
        return play_r, opts_r, quit_r

    def draw_options_menu(self, screen, mouse_pos):
        screen.fill(UI_BG)
        title = self.big_font.render("OPTIONS", True, UI_BORDER)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        btn_w, btn_h = 280, 40
        y = 110
        rects = {}

        fs_str = "Display: FULLSCREEN" if self.fullscreen else "Display: WINDOWED"
        fs_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, y, btn_w, btn_h)
        self.draw_button(screen, fs_str, fs_rect.x, fs_rect.y, btn_w, btn_h, fs_rect.collidepoint(mouse_pos))
        rects['FULLSCREEN'] = fs_rect

        y += 50
        for action, key_val in self.keybinds.items():
            key_name = pygame.key.name(key_val).upper()
            btn_text = f"Press Key..." if self.rebinding_key == action else f"{action}: [{key_name}]"
            b_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, y, btn_w, btn_h)
            self.draw_button(screen, btn_text, b_rect.x, b_rect.y, btn_w, btn_h, b_rect.collidepoint(mouse_pos))
            rects[action] = b_rect
            y += 45

        back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 55, 200, 40)
        self.draw_button(screen, "BACK", back_rect.x, back_rect.y, 200, 40, back_rect.collidepoint(mouse_pos))
        rects['BACK'] = back_rect

        return rects


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Elian's Adventure")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 14, bold=True)
    big_font = pygame.font.SysFont("arial", 36, bold=True)

    world_map = load_maps_from_json()
    world_pos = [0, 0]

    menu_sys = MenuSystem(font, big_font)
    state = "MENU"
    debug_mode = False 
    editor_mode = False
    editor_tool = 1

    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    inventory_ui = InventoryUI(font)

    items_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()
    chests_group = pygame.sprite.Group()

    def load_room_objects(coords):
        items_group.empty()
        enemies_group.empty()
        chests_group.empty()

        if coords not in world_map:
            default_grid = [[1 if r in (0, 14) or c in (0, 19) else 0 for c in range(20)] for r in range(15)]
            world_map[coords] = {"grid": default_grid, "enemies": [], "chests": [], "items": []}

        room_data = world_map[coords]

        for e in room_data.get("enemies", []):
            enemies_group.add(Enemy(e[0], e[1]))
        for c in room_data.get("chests", []):
            chests_group.add(Chest(c[0], c[1]))
        for itm in room_data.get("items", []):
            items_group.add(Item(itm["x"], itm["y"], itm["type"]))

    def save_current_room_state():
        room_data = world_map[tuple(world_pos)]
        room_data["enemies"] = [[e.rect.centerx, e.rect.centery] for e in enemies_group]
        room_data["chests"] = [[c.rect.centerx, c.rect.centery] for c in chests_group]
        room_data["items"] = [{"x": i.rect.centerx, "y": i.rect.centery, "type": i.item_type} for i in items_group]

    load_room_objects(tuple(world_pos))

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_current_room_state()
                save_maps_to_json(world_map)
                running = False

            if state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    play_r, opts_r, quit_r = menu_sys.draw_main_menu(screen, mouse_pos)
                    if play_r.collidepoint(mouse_pos): state = "GAME"
                    elif opts_r.collidepoint(mouse_pos): state = "OPTIONS"
                    elif quit_r.collidepoint(mouse_pos): running = False

            elif state == "OPTIONS":
                if menu_sys.rebinding_key is not None:
                    if event.type == pygame.KEYDOWN:
                        menu_sys.keybinds[menu_sys.rebinding_key] = event.key
                        menu_sys.rebinding_key = None
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        opt_rects = menu_sys.draw_options_menu(screen, mouse_pos)
                        if opt_rects['BACK'].collidepoint(mouse_pos): state = "MENU"
                        elif opt_rects['FULLSCREEN'].collidepoint(mouse_pos):
                            menu_sys.fullscreen = not menu_sys.fullscreen
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN if menu_sys.fullscreen else 0)
                        else:
                            for action in menu_sys.keybinds.keys():
                                if opt_rects[action].collidepoint(mouse_pos):
                                    menu_sys.rebinding_key = action

            elif state == "GAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_MINUS: debug_mode = not debug_mode
                    elif event.key == pygame.K_e: editor_mode = not editor_mode
                    elif event.key == pygame.K_ESCAPE: state = "MENU"
                    elif event.key == menu_sys.keybinds['INVENTORY'] and player.hp > 0: inventory_ui.toggle()
                    elif event.key == menu_sys.keybinds['ATTACK'] and not inventory_ui.is_open and player.hp > 0: player.attack()
                    elif event.key == pygame.K_r and player.hp <= 0: main(); return
                    
                    if editor_mode:
                        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                            editor_tool = int(event.unicode)
                        elif event.key == pygame.K_s:
                            save_current_room_state()
                            save_maps_to_json(world_map)

                inventory_ui.handle_input(event, player, menu_sys.keybinds)

                if editor_mode and pygame.mouse.get_pressed()[0]:
                    mx, my = mouse_pos
                    gc, gr = mx // TILE_SIZE, my // TILE_SIZE
                    cur_room = world_map[tuple(world_pos)]

                    if 0 <= gc < 20 and 0 <= gr < 15:
                        if editor_tool == 1: cur_room["grid"][gr][gc] = 1
                        elif editor_tool == 2: cur_room["grid"][gr][gc] = 0
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            cx, cy = gc * TILE_SIZE + 20, gr * TILE_SIZE + 20
                            if editor_tool == 3: enemies_group.add(Enemy(cx, cy))
                            elif editor_tool == 4: chests_group.add(Chest(cx, cy))
                            elif editor_tool == 5: items_group.add(Item(cx, cy, "potion"))
                            elif editor_tool == 6: items_group.add(Item(cx, cy, "sword"))

                if editor_mode and event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    m_rect = pygame.Rect(mouse_pos[0]-5, mouse_pos[1]-5, 10, 10)
                    for e in list(enemies_group):
                        if e.rect.colliderect(m_rect): e.kill()
                    for c in list(chests_group):
                        if c.rect.colliderect(m_rect): c.kill()
                    for i in list(items_group):
                        if i.rect.colliderect(m_rect): i.kill()

        # Render Loop
        if state == "MENU":
            menu_sys.draw_main_menu(screen, mouse_pos)

        elif state == "OPTIONS":
            menu_sys.draw_options_menu(screen, mouse_pos)

        elif state == "GAME":
            room_data = world_map.get(tuple(world_pos))
            current_grid = room_data["grid"]
            wall_rects = []

            for row_idx, row in enumerate(current_grid):
                for col_idx, tile in enumerate(row):
                    if tile == 1:
                        wall_rects.append(pygame.Rect(col_idx * TILE_SIZE, row_idx * TILE_SIZE, TILE_SIZE, TILE_SIZE))

            if player.hp > 0:
                player.update(pygame.key.get_pressed(), menu_sys.keybinds, wall_rects, can_move=(not inventory_ui.is_open and not editor_mode))
                if not editor_mode:
                    enemies_group.update(player.hitbox, can_move=not inventory_ui.is_open)

                # Screen change/Room system
                old_coords = tuple(world_pos)
                if player.hitbox.top < 0: world_pos[1] -= 1; player.hitbox.bottom = SCREEN_HEIGHT - 10
                elif player.hitbox.bottom > SCREEN_HEIGHT: world_pos[1] += 1; player.hitbox.top = 10
                elif player.hitbox.left < 0: world_pos[0] -= 1; player.hitbox.right = SCREEN_WIDTH - 10
                elif player.hitbox.right > SCREEN_WIDTH: world_pos[0] += 1; player.hitbox.left = 10

                if tuple(world_pos) != old_coords:
                    world_map[old_coords]["enemies"] = [[e.rect.centerx, e.rect.centery] for e in enemies_group]
                    world_map[old_coords]["chests"] = [[c.rect.centerx, c.rect.centery] for c in chests_group]
                    world_map[old_coords]["items"] = [{"x": i.rect.centerx, "y": i.rect.centery, "type": i.item_type} for i in items_group]
                    load_room_objects(tuple(world_pos))

                if not inventory_ui.is_open and not editor_mode:
                    for item in list(items_group):
                        if player.hitbox.colliderect(item.hitbox):
                            player.inventory.append(item)
                            item.kill()

                    for chest in chests_group:
                        if not chest.is_open:
                            if (player.is_attacking and player.attack_rect.colliderect(chest.hitbox)) or player.hitbox.colliderect(chest.hitbox):
                                dropped_item = chest.open_chest()
                                if dropped_item: items_group.add(dropped_item)

                    if player.is_attacking:
                        for enemy in enemies_group:
                            if player.attack_rect.colliderect(enemy.hitbox):
                                if enemy not in player.hit_enemies:
                                    enemy.take_damage(player.sword_damage)
                                    player.hit_enemies.add(enemy)

                    for enemy in enemies_group:
                        if player.hitbox.colliderect(enemy.hitbox):
                            player.take_damage(enemy.damage)

            # Draw Map
            for row_idx, row in enumerate(current_grid):
                for col_idx, tile in enumerate(row):
                    x, y = col_idx * TILE_SIZE, row_idx * TILE_SIZE
                    if tile == 0: pygame.draw.rect(screen, GREEN_GRASS if (col_idx + row_idx) % 2 == 0 else DARK_GRASS, (x, y, TILE_SIZE, TILE_SIZE))
                    elif tile == 1:
                        pygame.draw.rect(screen, WALL_COLOR, (x, y, TILE_SIZE, TILE_SIZE))
                        pygame.draw.rect(screen, WALL_BORDER, (x, y, TILE_SIZE, TILE_SIZE), 2)

            player.draw_attack_slash(screen)
            items_group.draw(screen)
            chests_group.draw(screen)
            enemies_group.draw(screen)
            screen.blit(player.image, player.rect)

            for enemy in enemies_group: enemy.draw_hp_bar(screen)
            inventory_ui.draw_hud(screen, player, menu_sys.keybinds)

            if editor_mode:
                tools = {1: "Wall", 2: "Grass", 3: "Enemy", 4: "Chest", 5: "Potion", 6: "Sword"}
                ed_lbl = font.render(f"EDITOR MODE | Tool: [{editor_tool}] {tools[editor_tool]} | [1-6] Select | [S] Save | [Right Click] Remove", True, (255, 255, 0))
                pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, 24))
                screen.blit(ed_lbl, (10, 4))

            if debug_mode:
                pygame.draw.rect(screen, DBG_PLAYER, player.hitbox, 2)
                if player.is_attacking: pygame.draw.rect(screen, DBG_ATTACK, player.attack_rect, 2)
                for enemy in enemies_group: pygame.draw.rect(screen, DBG_ENEMY, enemy.hitbox, 2)
                for item in items_group: pygame.draw.rect(screen, DBG_TEXT, item.hitbox, 1)
                for chest in chests_group: pygame.draw.rect(screen, (255, 255, 255), chest.hitbox, 1)

            inventory_ui.draw_menu(screen, player, menu_sys.keybinds)

            if player.hp <= 0:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                go_text = big_font.render("GAME OVER", True, (230, 40, 50))
                rst_text = font.render("Press [R] to Restart", True, (255, 255, 255))
                screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, 240))
                screen.blit(rst_text, (SCREEN_WIDTH // 2 - rst_text.get_width() // 2, 300))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()