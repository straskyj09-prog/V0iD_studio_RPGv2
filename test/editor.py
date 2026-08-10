import os
import sys
import json
import pygame

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
FPS = 60

# Colors
GREEN_GRASS = (80, 168, 70)
DARK_GRASS  = (60, 130, 50)
WALL_COLOR  = (70, 70, 85)
WALL_BORDER = (40, 40, 55)
UI_BG       = (25, 20, 35)
UI_BORDER   = (210, 165, 75)
TEXT_COLOR  = (240, 240, 240)

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

def load_maps_from_json():
    json_path = get_resource_path("maps.json")
    if not os.path.exists(json_path):
        default_grid = [[1 if r in (0, 14) or c in (0, 19) else 0 for c in range(20)] for r in range(15)]
        default_maps = {
            "0,0": {
                "grid": default_grid,
                "enemies": [[150, 150]],
                "chests": [[600, 150]],
                "items": [{"x": 250, "y": 300, "type": "sword"}]
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

def run_standalone_editor():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map Editor")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 14, bold=True)

    world_map = load_maps_from_json()
    world_pos = [0, 0]
    editor_tool = 1  # 1:Wall, 2:Grass, 3:Enemy, 4:Chest, 5:Potion, 6:Sword

    def get_current_room():
        coords = tuple(world_pos)
        if coords not in world_map:
            default_grid = [[1 if r in (0, 14) or c in (0, 19) else 0 for c in range(20)] for r in range(15)]
            world_map[coords] = {"grid": default_grid, "enemies": [], "chests": [], "items": []}
        return world_map[coords]

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        room_data = get_current_room()
        grid = room_data["grid"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_maps_to_json(world_map)
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: editor_tool = 1
                elif event.key == pygame.K_2: editor_tool = 2
                elif event.key == pygame.K_3: editor_tool = 3
                elif event.key == pygame.K_4: editor_tool = 4
                elif event.key == pygame.K_5: editor_tool = 5
                elif event.key == pygame.K_6: editor_tool = 6
                elif event.key == pygame.K_s:
                    save_maps_to_json(world_map)
                # Room navigation in editor
                elif event.key == pygame.K_UP: world_pos[1] -= 1
                elif event.key == pygame.K_DOWN: world_pos[1] += 1
                elif event.key == pygame.K_LEFT: world_pos[0] -= 1
                elif event.key == pygame.K_RIGHT: world_pos[0] += 1

            # Click to place/remove objects
            if pygame.mouse.get_pressed()[0]:
                mx, my = mouse_pos
                gc, gr = mx // TILE_SIZE, my // TILE_SIZE
                if 0 <= gc < 20 and 0 <= gr < 15:
                    if editor_tool == 1: grid[gr][gc] = 1
                    elif editor_tool == 2: grid[gr][gc] = 0
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        cx, cy = gc * TILE_SIZE + 20, gr * TILE_SIZE + 20
                        if editor_tool == 3: room_data["enemies"].append([cx, cy])
                        elif editor_tool == 4: room_data["chests"].append([cx, cy])
                        elif editor_tool == 5: room_data["items"].append({"x": cx, "y": cy, "type": "potion"})
                        elif editor_tool == 6: room_data["items"].append({"x": cx, "y": cy, "type": "sword"})

            # Right click removes nearby placed entities
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                mx, my = mouse_pos
                room_data["enemies"] = [e for e in room_data["enemies"] if abs(e[0]-mx) > 20 or abs(e[1]-my) > 20]
                room_data["chests"]  = [c for c in room_data["chests"] if abs(c[0]-mx) > 20 or abs(c[1]-my) > 20]
                room_data["items"]   = [i for i in room_data["items"] if abs(i["x"]-mx) > 20 or abs(i["y"]-my) > 20]

        # Draw Grid & Background
        for r in range(15):
            for c in range(20):
                x, y = c * TILE_SIZE, r * TILE_SIZE
                if grid[r][c] == 0:
                    pygame.draw.rect(screen, GREEN_GRASS if (r+c)%2==0 else DARK_GRASS, (x, y, TILE_SIZE, TILE_SIZE))
                else:
                    pygame.draw.rect(screen, WALL_COLOR, (x, y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(screen, WALL_BORDER, (x, y, TILE_SIZE, TILE_SIZE), 2)

        # Draw Overlay Entities
        for e in room_data["enemies"]: pygame.draw.circle(screen, (255, 0, 0), e, 12)
        for c in room_data["chests"]: pygame.draw.rect(screen, (150, 75, 0), (c[0]-12, c[1]-12, 24, 24))
        for i in room_data["items"]: pygame.draw.circle(screen, (0, 255, 255), (i["x"], i["y"]), 8)

        # Editor UI Header
        tools = {1:"Wall", 2:"Grass", 3:"Enemy", 4:"Chest", 5:"Potion", 6:"Sword"}
        info = f"Room: {world_pos} | Tool: [{editor_tool}] {tools[editor_tool]} | [1-6] Tools | [Arrows] Change Room | [S] Save"
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, 24))
        screen.blit(font.render(info, True, (255, 255, 0)), (10, 4))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run_standalone_editor()