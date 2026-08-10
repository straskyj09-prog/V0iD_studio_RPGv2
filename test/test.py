import os
import sys
import pygame

# Initialize Pygame
pygame.init()

# Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Color Palette
GREEN_GRASS = (80, 168, 70)
DARK_GRASS  = (60, 130, 50)
UI_BG       = (25, 20, 35)
UI_BORDER   = (210, 165, 75)
UI_SLOT     = (45, 40, 60)
UI_SELECT   = (255, 220, 100)
TEXT_COLOR  = (240, 240, 240)
HP_RED      = (220, 40, 50)
HP_DARK     = (80, 10, 20)
SWORD_COLOR = (220, 220, 240)
BTN_HOVER   = (60, 50, 80)

# Debug Colors
DBG_PLAYER = (255, 255, 0)   # Yellow
DBG_ENEMY  = (255, 0, 255)   # Magenta
DBG_ATTACK = (255, 0, 0)     # Red
DBG_TEXT   = (0, 255, 255)   # Cyan


# ITEM CLASS
class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type):
        super().__init__()
        self.item_type = item_type
        self.name = item_type.capitalize()
        self.image = self._create_item_surface()
        self.rect = self.image.get_rect(center=(x, y))

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
        return surf


# ENEMY CLASS
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.speed = 1.2
        self.damage = 5
        self.max_hp = 10
        self.hp = 10
        self.image = self._create_fallback_sprite()
        self.rect = self.image.get_rect(center=(x, y))

    def _create_fallback_sprite(self):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (200, 30, 40), (2, 8, 28, 22))
        pygame.draw.ellipse(surf, (240, 80, 90), (6, 11, 20, 14))
        pygame.draw.rect(surf, (255, 255, 255), (8, 14, 4, 6))
        pygame.draw.rect(surf, (255, 255, 255), (20, 14, 4, 6))
        pygame.draw.rect(surf, (0, 0, 0), (10, 16, 2, 4))
        pygame.draw.rect(surf, (0, 0, 0), (20, 16, 2, 4))
        return surf

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()

    def draw_hp_bar(self, screen):
        bar_w, bar_h = 30, 4
        bar_x = self.rect.centerx - bar_w // 2
        bar_y = self.rect.top - 8

        pygame.draw.rect(screen, HP_DARK, (bar_x, bar_y, bar_w, bar_h))
        fill_w = int((self.hp / self.max_hp) * bar_w)
        if fill_w > 0:
            pygame.draw.rect(screen, HP_RED, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), 1)

    def update(self, player_rect, can_move=True):
        if not can_move:
            return
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        dist = (dx**2 + dy**2)**0.5
        if dist != 0:
            self.rect.x += int((dx / dist) * self.speed)
            self.rect.y += int((dy / dist) * self.speed)


# PLAYER CLASS
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.scale = 3
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

    def _load_custom_sprites(self):
        directions = ['down', 'up', 'left', 'right']
        sprites = {d: [] for d in directions}
        
        # PyInstaller path resolution support
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        try:
            for d in directions:
                for i in range(1, 5):
                    file_path = os.path.join(base_path, "sprites", f"walk_{d}_{i}.png")
                    image = pygame.image.load(file_path).convert_alpha()
                    width = image.get_width() * self.scale
                    height = image.get_height() * self.scale
                    scaled_image = pygame.transform.scale(image, (width, height))
                    sprites[d].append(scaled_image)
        except (FileNotFoundError, pygame.error):
            for d in directions:
                for _ in range(4):
                    surf = pygame.Surface((16 * self.scale, 16 * self.scale), pygame.SRCALPHA)
                    pygame.draw.rect(surf, (40, 130, 50), (0, 0, 16 * self.scale, 16 * self.scale))
                    sprites[d].append(surf)
        return sprites

    def attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 12
            self.hit_enemies.clear()

            reach = 30
            if self.direction == 'down':
                self.attack_rect = pygame.Rect(self.rect.left, self.rect.bottom, self.rect.width, reach)
            elif self.direction == 'up':
                self.attack_rect = pygame.Rect(self.rect.left, self.rect.top - reach, self.rect.width, reach)
            elif self.direction == 'left':
                self.attack_rect = pygame.Rect(self.rect.left - reach, self.rect.top, reach, self.rect.height)
            elif self.direction == 'right':
                self.attack_rect = pygame.Rect(self.rect.right, self.rect.top, reach, self.rect.height)

    def take_damage(self, amount):
        if self.invincible_timer == 0:
            self.hp = max(0, self.hp - amount)
            self.invincible_timer = 40

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def update(self, keys, keybinds, can_move=True):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

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

        if keys[keybinds['LEFT']]:
            dx -= self.speed
            self.direction = 'left'
            self.is_moving = True
        elif keys[keybinds['RIGHT']]:
            dx += self.speed
            self.direction = 'right'
            self.is_moving = True

        if keys[keybinds['UP']]:
            dy -= self.speed
            self.direction = 'up'
            self.is_moving = True
        elif keys[keybinds['DOWN']]:
            dy += self.speed
            self.direction = 'down'
            self.is_moving = True

        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x + dx))
        self.rect.y = max(0, min(SCREEN_HEIGHT - self.rect.height, self.rect.y + dy))

        if self.is_moving:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.sprites[self.direction]):
                self.frame_index = 0
        else:
            self.frame_index = 0

        self.image = self.sprites[self.direction][int(self.frame_index)]

    def draw_attack_slash(self, screen):
        if self.is_attacking:
            pygame.draw.rect(screen, SWORD_COLOR, self.attack_rect, border_radius=4)


# INVENTORY & HUD OVERLAY
class InventoryUI:
    def __init__(self, font):
        self.font = font
        self.is_open = False
        self.selected_index = 0
        
        self.width = 360
        self.height = 260
        self.rect = pygame.Rect(
            (SCREEN_WIDTH - self.width) // 2,
            (SCREEN_HEIGHT - self.height) // 2,
            self.width,
            self.height
        )

    def toggle(self):
        self.is_open = not self.is_open
        self.selected_index = 0

    def handle_input(self, event, player, keybinds):
        if not self.is_open:
            return

        cols = 4
        total_items = len(player.inventory)

        if event.type == pygame.KEYDOWN and total_items > 0:
            if event.key == keybinds['RIGHT']:
                self.selected_index = (self.selected_index + 1) % total_items
            elif event.key == keybinds['LEFT']:
                self.selected_index = (self.selected_index - 1) % total_items
            elif event.key == keybinds['DOWN']:
                if self.selected_index + cols < total_items:
                    self.selected_index += cols
            elif event.key == keybinds['UP']:
                if self.selected_index - cols >= 0:
                    self.selected_index -= cols
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                item = player.inventory[self.selected_index]
                if item.item_type == 'sword':
                    player.equipped_item = item
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
        if player.equipped_item:
            screen.blit(player.equipped_item.image, (21, 21))

        hp_x, hp_y, hp_w, hp_h = 65, 20, 170, 16
        pygame.draw.rect(screen, HP_DARK, (hp_x, hp_y, hp_w, hp_h))
        
        current_hp_width = int((player.hp / player.max_hp) * hp_w)
        if current_hp_width > 0:
            pygame.draw.rect(screen, HP_RED, (hp_x, hp_y, current_hp_width, hp_h))
        pygame.draw.rect(screen, UI_BORDER, (hp_x, hp_y, hp_w, hp_h), 2)

        hp_text = self.font.render(f"HP: {player.hp}/{player.max_hp}", True, TEXT_COLOR)
        screen.blit(hp_text, (hp_x + 5, hp_y + 18))

    def draw_menu(self, screen, player, keybinds):
        if not self.is_open:
            inv_k = pygame.key.name(keybinds['INVENTORY']).upper()
            atk_k = pygame.key.name(keybinds['ATTACK']).upper()
            hint = self.font.render(f"[{inv_k}] Inventory  |  [{atk_k}] Attack  |  [ESC] Menu", True, (255, 255, 255))
            screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 30))
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, UI_BG, self.rect)
        pygame.draw.rect(screen, UI_BORDER, self.rect, 4)

        title = self.font.render("— INVENTORY —", True, UI_BORDER)
        screen.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.y + 15))

        start_x = self.rect.x + 35
        start_y = self.rect.y + 60
        slot_size = 50
        padding = 20

        for i in range(8):
            row = i // 4
            col = i % 4
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)

            slot_rect = pygame.Rect(x, y, slot_size, slot_size)
            pygame.draw.rect(screen, UI_SLOT, slot_rect)

            if i == self.selected_index and len(player.inventory) > 0:
                pygame.draw.rect(screen, UI_SELECT, slot_rect, 3)
            else:
                pygame.draw.rect(screen, UI_BORDER, slot_rect, 1)

            if i < len(player.inventory):
                item = player.inventory[i]
                item_rect = item.image.get_rect(center=slot_rect.center)
                screen.blit(item.image, item_rect)

        if len(player.inventory) > 0 and self.selected_index < len(player.inventory):
            curr_item = player.inventory[self.selected_index]
            desc = "Heals +10 HP" if curr_item.item_type == 'potion' else "Press [ENTER/SPACE] to Equip"
            info_text = self.font.render(f"{curr_item.name} ({desc})", True, TEXT_COLOR)
            screen.blit(info_text, (self.rect.centerx - info_text.get_width() // 2, self.rect.bottom - 40))


# MENU MANAGER CLASS
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
        color = BTN_HOVER if is_hovered else UI_BG
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, UI_BORDER, rect, 2, border_radius=8)

        lbl = self.font.render(text, True, TEXT_COLOR)
        screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))
        return rect

    def draw_main_menu(self, screen, mouse_pos):
        screen.fill(UI_BG)
        title = self.big_font.render("ELIAN'S ADVENTURE", True, UI_BORDER)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        btn_w, btn_h = 200, 45
        start_y = 240
        play_rect = self.draw_button(screen, "PLAY", SCREEN_WIDTH // 2 - btn_w // 2, start_y, btn_w, btn_h, pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y, btn_w, btn_h).collidepoint(mouse_pos))
        opts_rect = self.draw_button(screen, "OPTIONS", SCREEN_WIDTH // 2 - btn_w // 2, start_y + 65, btn_w, btn_h, pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + 65, btn_w, btn_h).collidepoint(mouse_pos))
        quit_rect = self.draw_button(screen, "QUIT", SCREEN_WIDTH // 2 - btn_w // 2, start_y + 130, btn_w, btn_h, pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + 130, btn_w, btn_h).collidepoint(mouse_pos))

        return play_rect, opts_rect, quit_rect

    def draw_options_menu(self, screen, mouse_pos):
        screen.fill(UI_BG)
        title = self.big_font.render("OPTIONS", True, UI_BORDER)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        btn_w, btn_h = 280, 40
        y = 130
        rects = {}

        fs_str = "Display: FULLSCREEN" if self.fullscreen else "Display: WINDOWED"
        fs_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, y, btn_w, btn_h)
        self.draw_button(screen, fs_str, fs_rect.x, fs_rect.y, btn_w, btn_h, fs_rect.collidepoint(mouse_pos))
        rects['FULLSCREEN'] = fs_rect

        y += 55
        for action, key_val in self.keybinds.items():
            key_name = pygame.key.name(key_val).upper()
            btn_text = f"Press Key..." if self.rebinding_key == action else f"{action}: [{key_name}]"
            b_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, y, btn_w, btn_h)
            self.draw_button(screen, btn_text, b_rect.x, b_rect.y, btn_w, btn_h, b_rect.collidepoint(mouse_pos))
            rects[action] = b_rect
            y += 48

        back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 60, 200, 40)
        self.draw_button(screen, "BACK", back_rect.x, back_rect.y, 200, 40, back_rect.collidepoint(mouse_pos))
        rects['BACK'] = back_rect

        return rects


# MAIN ENGINE
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Elian's Adventure")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 14, bold=True)
    big_font = pygame.font.SysFont("arial", 36, bold=True)

    menu_sys = MenuSystem(font, big_font)
    state = "MENU"
    
    # State tracking
    debug_mode = False 

    # Game Objects
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    inventory_ui = InventoryUI(font)

    all_sprites = pygame.sprite.Group(player)
    items_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()

    sword_item = Item(250, 300, 'sword')
    items_group.add(sword_item, Item(550, 250, 'potion'), Item(400, 450, 'potion'))
    all_sprites.add(items_group)

    player.inventory.append(sword_item)
    player.equipped_item = sword_item

    enemy = Enemy(150, 150)
    enemies_group.add(enemy)
    all_sprites.add(enemy)

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    play_r, opts_r, quit_r = menu_sys.draw_main_menu(screen, mouse_pos)
                    if play_r.collidepoint(mouse_pos):
                        state = "GAME"
                    elif opts_r.collidepoint(mouse_pos):
                        state = "OPTIONS"
                    elif quit_r.collidepoint(mouse_pos):
                        running = False

            elif state == "OPTIONS":
                if menu_sys.rebinding_key is not None:
                    if event.type == pygame.KEYDOWN:
                        menu_sys.keybinds[menu_sys.rebinding_key] = event.key
                        menu_sys.rebinding_key = None
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        opt_rects = menu_sys.draw_options_menu(screen, mouse_pos)
                        if opt_rects['BACK'].collidepoint(mouse_pos):
                            state = "MENU"
                        elif opt_rects['FULLSCREEN'].collidepoint(mouse_pos):
                            menu_sys.fullscreen = not menu_sys.fullscreen
                            if menu_sys.fullscreen:
                                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                            else:
                                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                        else:
                            for action in menu_sys.keybinds.keys():
                                if opt_rects[action].collidepoint(mouse_pos):
                                    menu_sys.rebinding_key = action

            elif state == "GAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_MINUS:
                        debug_mode = not debug_mode
                        
                    elif event.key == pygame.K_ESCAPE:
                        state = "MENU"
                    elif event.key == menu_sys.keybinds['INVENTORY'] and player.hp > 0:
                        inventory_ui.toggle()
                    elif event.key == menu_sys.keybinds['ATTACK'] and not inventory_ui.is_open and player.hp > 0:
                        player.attack()
                    elif event.key == pygame.K_r and player.hp <= 0:
                        main()
                        return
                    
                    inventory_ui.handle_input(event, player, menu_sys.keybinds)

        # RENDER
        if state == "MENU":
            menu_sys.draw_main_menu(screen, mouse_pos)

        elif state == "OPTIONS":
            menu_sys.draw_options_menu(screen, mouse_pos)

        elif state == "GAME":
            if player.hp > 0:
                player.update(pygame.key.get_pressed(), menu_sys.keybinds, can_move=not inventory_ui.is_open)
                enemies_group.update(player.rect, can_move=not inventory_ui.is_open)

                if not inventory_ui.is_open:
                    picked_items = pygame.sprite.spritecollide(player, items_group, True)
                    for item in picked_items:
                        if item not in player.inventory:
                            player.inventory.append(item)

                    if player.is_attacking:
                        for enemy in enemies_group:
                            if player.attack_rect.colliderect(enemy.rect):
                                if enemy not in player.hit_enemies:
                                    enemy.take_damage(player.sword_damage)
                                    player.hit_enemies.add(enemy)

                    hit_enemies = pygame.sprite.spritecollide(player, enemies_group, False)
                    for e in hit_enemies:
                        player.take_damage(e.damage)

            for y in range(0, SCREEN_HEIGHT, 40):
                for x in range(0, SCREEN_WIDTH, 40):
                    color = GREEN_GRASS if (x // 40 + y // 40) % 2 == 0 else DARK_GRASS
                    pygame.draw.rect(screen, color, (x, y, 40, 40))

            player.draw_attack_slash(screen)
            all_sprites.draw(screen)

            for enemy in enemies_group:
                enemy.draw_hp_bar(screen)

            inventory_ui.draw_hud(screen, player, menu_sys.keybinds)
            
            # DEBUG TOOL OVERLAY
            if debug_mode:
                # Draw Hitboxes
                pygame.draw.rect(screen, DBG_PLAYER, player.rect, 2)
                if player.is_attacking:
                    pygame.draw.rect(screen, DBG_ATTACK, player.attack_rect, 2)
                for enemy in enemies_group:
                    pygame.draw.rect(screen, DBG_ENEMY, enemy.rect, 2)
                for item in items_group:
                    pygame.draw.rect(screen, DBG_TEXT, item.rect, 1)
                
                # Diagnostic Text Panel
                debug_info = [
                    f"DEBUG",
                    f"FPS: {int(clock.get_fps())}",
                    f"Player X/Y: {player.rect.x}, {player.rect.y}",
                    f"Direction: {player.direction}",
                    f"Attacking: {player.is_attacking}",
                    f"Invincible: {player.invincible_timer > 0}",
                    f"Enemies Alive: {len(enemies_group)}",
                    f"Items Loaded: {len(items_group)}"
                ]
                
                # Dark transparent background for text
                overlay_surf = pygame.Surface((180, len(debug_info) * 22 + 10), pygame.SRCALPHA)
                overlay_surf.fill((0, 0, 0, 180))
                screen.blit(overlay_surf, (10, 75))
                
                # Render the text lines
                for i, text in enumerate(debug_info):
                    color = DBG_TEXT if i > 0 else (255, 100, 100)
                    surf = font.render(text, True, color)
                    screen.blit(surf, (15, 80 + i * 22))

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