import pygame
import sys
import os  # NOWOŚĆ: Potrzebne do czytania zmiennych systemowych
from dotenv import load_dotenv  # NOWOŚĆ: Ładowanie pliku .env
from google import genai
from google.genai import types

# --- ŁADOWANIE ZMIENNYCH ŚRODOWISKOWYCH ---
load_dotenv()  # Ta funkcja szuka pliku .env i wczytuje z niego dane

# Pobieramy klucz bezpośrednio z pamięci systemu
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None
if GEMINI_API_KEY != "TUTAJ_WKLEJ_SWÓJ_KLUCZ_API":
    client = genai.Client(api_key=GEMINI_API_KEY)

# Inicjalizacja Pygame
pygame.init()

# Panoramiczny format wirtualny (16:9)
VIRTUAL_WIDTH = 1280
VIRTUAL_HEIGHT = 720

screen = pygame.display.set_mode((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Gra modyfikowana przez Gemini 2.5 API - Zasady i Limity")
clock = pygame.time.Clock()

# --- CZCIONKI ---
font = pygame.font.SysFont(None, 28)
input_font = pygame.font.SysFont(None, 36)

# --- SYSTEM PROMPTÓW / MODÓW ---
is_typing = False
user_prompt = ""
status_message = "1 prompt na level! TAB = Prompt. U = Cofnij. R = Reset. ESC = Wyjście."
player_backup = None
ai_behavior_code = "" 
has_prompted_this_level = False # Śledzenie użycia promptu na aktualnym poziomie

# --- SZCZEGÓŁOWE POZIOMY (40 kolumn x 22 wiersze, kafelki 32x32) ---
LEVELS = [
    # POZIOM 1
    [
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X                                  E   X",
        "X                             XXXXXXXXXX",
        "X                                      X",
        "X                     XXXX             X",
        "X                                      X",
        "X             XXXX                     X",
        "X                                      X",
        "X         XXXX                         X",
        "X                                      X",
        "X    S                                 X",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    ],
    # POZIOM 2
    [
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "X                                      X",
        "X  S                                   X",
        "XXXXXXX                                X",
        "X      X       XXXXXXXXXX              X",
        "X      X       X        X              X",
        "X      XXXXXXXXX        X     XXXX     X",
        "X                       X              X",
        "X                       X              X",
        "X             XXXXXXXXXXX              X",
        "X             X                        X",
        "X    XXXX     X         XXXXXXXXX      X",
        "X             X         X       X      X",
        "X             X    X    X   E   X      X",
        "X       XXXXXXX    X    X   XXXXX      X",
        "X                  X    X              X",
        "X                  X    XXXXXXXXX      X",
        "X         XXXXXXXXXX                   X",
        "X                                      X",
        "X                                      X",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXX           X",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXX           X",
    ],
    # POZIOM 3
    [
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X                                      X",
        "X   S                                  X",
        "XXXXXX                                 X",
        "X    X      XXXX                       X",
        "X    X                                 X",
        "X    XXXXXXXXXX      XXXX              X",
        "X                                      X",
        "X                 XXXXXXXX             X",
        "X                                      X",
        "X            XXXX           XXXX       X",
        "X                                      X",
        "X       XXXX           XXXX            X",
        "X                                      X",
        "X  XXXX                                X",
        "X                                    E X",
        "XXXX      XXXXXX   XXXXXXXX    XXXXXXXXX",
        "XXXX      XXXXXX   XXXXXXXX    XXXXXXXXX",
        "XXXX      XXXXXX   XXXXXXXX    XXXXXXXXX",
    ]
]

current_level_idx = 0

class Level:
    def __init__(self, layout):
        self.layout = layout
        self.tile_size = 32 
        self.walls = []
        self.start_pos = (100, 100)
        self.end_rect = None
        self.build()

    def build(self):
        self.walls = []
        self.end_rect = None
        for row_idx, row in enumerate(self.layout):
            for col_idx, cell in enumerate(row):
                y_pos = VIRTUAL_HEIGHT - (len(self.layout) - row_idx) * self.tile_size
                x_pos = col_idx * self.tile_size
                
                if x_pos >= VIRTUAL_WIDTH or y_pos >= VIRTUAL_HEIGHT:
                    continue
                    
                if cell == "X":
                    rect = pygame.Rect(x_pos, y_pos, self.tile_size, self.tile_size)
                    self.walls.append(rect)
                elif cell == "S":
                    self.start_pos = (x_pos + 4, y_pos + self.tile_size - 24)
                elif cell == "E":
                    self.end_rect = pygame.Rect(x_pos + 4, y_pos + 4, self.tile_size - 8, self.tile_size - 8)

    def draw(self, surface):
        for wall in self.walls:
            pygame.draw.rect(surface, (68, 68, 68), wall)
        if self.end_rect:
            pygame.draw.rect(surface, (46, 204, 113), self.end_rect)

class Player:
    def __init__(self, start_pos):
        self.x = start_pos[0]
        self.y = start_pos[1]
        self.size = 24 
        self.vx = 0
        self.vy = 0
        self.speed = 6 
        self.gravity = 0.5
        self.jump_force = -12 
        self.is_grounded = False
        self.jump_count = 0
        self.max_jumps = 1
        self.color = (0, 255, 204)

    def reset_position(self, start_pos):
        self.x = start_pos[0]
        self.y = start_pos[1]
        self.vx = 0
        self.vy = 0

    def reset_stats(self):
        """Przywraca bazowe, fabryczne ustawienia postaci przy zmianie poziomu"""
        self.size = 24
        self.speed = 6
        self.gravity = 0.5
        self.jump_force = -12
        self.max_jumps = 1
        self.color = (0, 255, 204)

def update_logic(p, keys):
    if keys[pygame.K_LEFT]: p.vx = -p.speed
    elif keys[pygame.K_RIGHT]: p.vx = p.speed
    else: p.vx = 0
    
    if keys[pygame.K_UP]:
        if p.is_grounded:
            p.vy = p.jump_force
            p.is_grounded = False
            p.jump_count = 1
            pygame.time.delay(150) 
        elif p.jump_count < p.max_jumps:
            p.vy = p.jump_force
            p.jump_count += 1
            pygame.time.delay(150)

# --- SYSTEM PROMPT DLA GEMINI 2.5 ---
system_instruction = """
Jesteś kreatywnym programistą modów do gry platformowej 2D w Pygame. Twym zadaniem jest dopisanie dodatkowej logiki zachowania gracza na podstawie jego prośby.
Musisz zwrócić TYLKO I WYŁĄCZNIE czysty kod w Pythonie, który zostanie wykonany wewnątrz pętli gry. Bez komentarzy i bez formatowania markdown.

Do dyspozycji masz obiekt gracza 'p' z polami:
p.x, p.y, p.vx, p.vy, p.speed (domyślnie 6), p.gravity (0.5), p.jump_force (-12), p.is_grounded, p.size (24), p.color = (R, G, B).

Napisz czysty kod wykonawczy. Dbaj o poprawne wcięcia (4 spacje).
"""

# Inicjalizacja poziomu i gracza
level = Level(LEVELS[current_level_idx])
player = Player(level.start_pos)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
            elif event.key == pygame.K_TAB:
                # Blokujemy włączenie pisania, jeśli gracz już raz użył promptu na tym poziomie
                if has_prompted_this_level and not is_typing:
                    status_message = "❌ Wykorzystałeś już swój 1 prompt na tym poziomie!"
                else:
                    is_typing = not is_typing
                    if is_typing:
                        status_message = "PISZESZ MOD DLA AI... Wciśnij ENTER aby zatwierdzić."
                    else:
                        status_message = "Anulowano. TAB = Wpisz prompt."
            
            # Resetowanie pozycji i promptu klawiszem R
            elif event.key == pygame.K_r and not is_typing:
                player.reset_position(level.start_pos)
                
                # === NOWOŚĆ: Resetujemy też stan AI na tym poziomie ===
                ai_behavior_code = ""  # Wyłączamy aktualny mod
                has_prompted_this_level = False  # Odblokowujemy możliwość wpisania promptu
                
                # Jeśli robiliśmy backup na tym poziomie, przywracamy fabryczne statystyki
                if player_backup is not None:
                    player.speed = player_backup["speed"]
                    player.gravity = player_backup["gravity"]
                    player.jump_force = player_backup["jump_force"]
                    player.max_jumps = player_backup["max_jumps"]
                    player.size = player_backup["size"]
                    player.color = player_backup["color"]
                    player_backup = None
                else:
                    player.reset_stats() # Jeśli nie było backupu, dajemy bazowe staty
                    
                status_message = "🔄 Poziom zresetowany! Prompt jest znowu aktywny."
                    
            elif event.key == pygame.K_u and not is_typing:
                if player_backup is not None:
                    player.speed = player_backup["speed"]
                    player.gravity = player_backup["gravity"]
                    player.jump_force = player_backup["jump_force"]
                    player.max_jumps = player_backup["max_jumps"]
                    player.size = player_backup["size"]
                    player.color = player_backup["color"]
                    ai_behavior_code = "" 
                    has_prompted_this_level = False # Cofnięcie modu przywraca możliwość wpisania nowego promptu
                    status_message = "↩️ Cofnięto modyfikacje AI! Możesz wpisać nowy prompt."
                    player_backup = None
                else:
                    status_message = "ℹ️ Brak modów do cofnięcia."
                    
            elif is_typing:
                if event.key == pygame.K_RETURN:
                    if user_prompt.strip() == "": continue
                    if not client:
                        status_message = "BŁĄD: Brak klucza API Gemini!"; is_typing = False; continue
                        
                    status_message = f"🤖 Gemini 2.5 generuje mod: '{user_prompt}'..."
                    
                    # Ekran ładowania
                    screen.fill((34, 34, 34)); level.draw(screen)
                    pygame.draw.rect(screen, player.color, (player.x, player.y, player.size, player.size))
                    screen.blit(font.render(status_message, True, (255, 255, 0)), (20, 20)); pygame.display.flip()
                    
                    try:
                        player_backup = {
                            "speed": player.speed, "gravity": player.gravity, "jump_force": player.jump_force,
                            "max_jumps": player.max_jumps, "size": player.size, "color": player.color
                        }
                        response = client.models.generate_content(
                            model='gemini-2.5-flash', contents=user_prompt,
                            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
                        )
                        ai_behavior_code = response.text.strip().replace("```python", "").replace("```", "").strip()
                        has_prompted_this_level = True # ZUŻYTO PROMPT NA TYM POZIOMIE
                        status_message = "✅ Mod aktywny! Limit tego poziomu wyczerpany."
                    except Exception as e:
                        status_message = f"❌ Błąd: {str(e)[:40]}"
                    
                    user_prompt = ""; is_typing = False
                    
                elif event.key == pygame.K_BACKSPACE:
                    user_prompt = user_prompt[:-1]
                else:
                    user_prompt += event.unicode

    # --- FIZYKA GRY ---
    if not is_typing:
        keys = pygame.key.get_pressed()
        update_logic(player, keys)

        if ai_behavior_code:
            try: exec(ai_behavior_code, {}, {"p": player})
            except Exception: pass

        # Ruch X i kolizje
        player.x += player.vx
        player_rect = pygame.Rect(player.x, player.y, player.size, player.size)
        for wall in level.walls:
            if player_rect.colliderect(wall):
                if player.vx > 0: player.x = wall.left - player.size
                if player.vx < 0: player.x = wall.right

        if player.x < 0: player.x = 0
        if player.x > VIRTUAL_WIDTH - player.size: player.x = VIRTUAL_WIDTH - player.size

        # Ruch Y i kolizje
        player.y += player.vy
        player.vy += player.gravity
        player_rect = pygame.Rect(player.x, player.y, player.size, player.size)
        player.is_grounded = False
        
        for wall in level.walls:
            if player_rect.colliderect(wall):
                if player.vy > 0: 
                    player.y = wall.top - player.size
                    player.vy = 0
                    player.is_grounded = True
                    player.jump_count = 0
                elif player.vy < 0: 
                    player.y = wall.bottom
                    player.vy = 0

        # Przepaść (śmierć)
        if player.y > VIRTUAL_HEIGHT:
            player.reset_position(level.start_pos)
            status_message = "💀 Przepaść! Reset pozycji."

        # Kolizja z metą
        player_rect = pygame.Rect(player.x, player.y, player.size, player.size)
        if level.end_rect and player_rect.colliderect(level.end_rect):
            current_level_idx += 1
            
            # === NOWOŚĆ: CZYSZCZENIE MODÓW I PARAMETRÓW PRZY ZMIANIE LEVELU ===
            player.reset_stats()      # Wszystko wraca do normy
            ai_behavior_code = ""     # Wyłączamy aktywny kod AI
            has_prompted_this_level = False # Resetujemy limit promptu dla nowego poziomu
            player_backup = None
            
            if current_level_idx < len(LEVELS):
                level = Level(LEVELS[current_level_idx])
                player.reset_position(level.start_pos)
                status_message = f"🎉 Załadowano Poziom {current_level_idx + 1}! Prompt odblokowany."
            else:
                status_message = "🏆 UKOŃCZYŁEŚ CAŁĄ GRĘ! Gratulacje!"
                current_level_idx = 0
                level = Level(LEVELS[current_level_idx])
                player.reset_position(level.start_pos)

    # --- RENDEROWANIE ---
    screen.fill((34, 34, 34)) 
    level.draw(screen)      
    
    # Gracz
    pygame.draw.rect(screen, player.color, (player.x, player.y, player.size, player.size))

    # UI Statusu
    status_color = (255, 255, 0) if is_typing else (255, 255, 255)
    lvl_info = f"[Poziom {current_level_idx + 1}/{len(LEVELS)}] "
    status_text = font.render(lvl_info + status_message, True, status_color)
    screen.blit(status_text, (20, 20))

    # Ramka promptu
    if is_typing:
        box_width, box_height = 800, 60
        box_x = (VIRTUAL_WIDTH - box_width) // 2
        box_y = 100
        pygame.draw.rect(screen, (20, 20, 20), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (0, 255, 204), (box_x, box_y, box_width, box_height), 2)
        prompt_surf = input_font.render(user_prompt + "_", True, (255, 255, 255))
        screen.blit(prompt_surf, (box_x + 20, box_y + 15))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()