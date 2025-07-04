import pygame
import sys
import math
from enum import Enum
import random
import os


# Inicialização do Pygame
pygame.init()
pygame.mixer.init()

# Constantes do jogo
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 50
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
FPS = 60

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)

# Estados do jogo
class GameState(Enum):
    MENU = 0
    PLAYING = 1
    LEVEL_COMPLETE = 2
    GAME_OVER = 3

# Tipos de carga
class ChargeType(Enum):
    POSITIVE = 1
    NEGATIVE = -1
    DIPOLE = 0  # Dipolo tem ambas as cargas

# Tipos de power-up
class PowerUpType(Enum):
    FIELD_STRENGTH = 1
    EXTRA_CHARGE = 2
    EXTRA_LIFE = 3

# Configuração da tela
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("EletroBlast")
clock = pygame.time.Clock()

# Carregar recursos
def load_image(name, scale=1):
    try:
        image = pygame.image.load(name)
        if scale != 1:
            size = image.get_size()
            image = pygame.transform.scale(image, (int(size[0] * scale), int(size[1] * scale)))
        return image
    except:
        # Fallback se a imagem não carregar
        surf = pygame.Surface((100, 100))
        surf.fill(PURPLE)
        return surf

def load_sound(name):
    try:
        return pygame.mixer.Sound(name)
    except:
        # Fallback silencioso se o áudio não carregar
        return pygame.mixer.Sound(buffer=bytearray(0))

# Carregar imagens e sons
menu_image = load_image("menu_background.png")  # Substitua pelo seu arquivo
menu_image = pygame.transform.scale(menu_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

menu_music = load_sound("menu_music.mp3")  # Substitua pelo seu arquivo
game_music = load_sound("game_music.mp3")  # Substitua pelo seu arquivo
charge_sound = load_sound("charge.mp3")  # Substitua pelo seu arquivo

# Classes do jogo
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.max_charges = 1  # Começa colocando apenas 1 campo por vez
        self.placed_charges = []
        self.field_strength = 1.0  # Intensidade do campo
        self.field_radius = 2  # Raio do campo em células
        self.score = 0
        self.lives = 3
        self.invincible = 0
        self.message = ""
        self.message_timer = 0
    
    def move(self, dx, dy, grid):
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Verifica se a nova posição está dentro dos limites e não é uma parede
        if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and 
            grid[new_y][new_x] != 'W'):
            self.x = new_x
            self.y = new_y
            
    def place_charge(self, charge_type):
        if len(self.placed_charges) < self.max_charges:
            self.placed_charges.append({
                'x': self.x,
                'y': self.y,
                'type': charge_type,
                'timer': 180,
                'active': False,
                'activation_timer': 0
            })
            return True
        return False
    
    def update(self):
        # Atualiza temporizador de invencibilidade
        if self.invincible > 0:
            self.invincible -= 1
            
        # Atualiza mensagem
        if self.message_timer > 0:
            self.message_timer -= 1
            
        # Atualiza cargas colocadas
        for charge in self.placed_charges[:]:
            charge['timer'] -= 1
            
            # Ativa automaticamente após 3 segundos
            if charge['timer'] <= 0 and not charge['active']:
                charge['active'] = True
                charge_sound.play()  # Tocar som ao colocar carga
                charge['activation_timer'] = 60  # Campo fica ativo por 1 segundo
            
            # Desativa após o tempo de ativação
            if charge['active']:
                charge['activation_timer'] -= 1
                if charge['activation_timer'] <= 0:
                    self.placed_charges.remove(charge)
    
    def show_message(self, message):
        self.message = message
        self.message_timer = 60  # Mostra por 1 segundo
    
    def draw(self, screen):
        # Desenha o jogador (verde e neutro)
        pygame.draw.circle(screen, GREEN, 
                         (self.x * GRID_SIZE + GRID_SIZE//2, self.y * GRID_SIZE + GRID_SIZE//2), 
                         GRID_SIZE//2 - 5)
        
        # Desenha cargas colocadas
        for charge in self.placed_charges:
            color = RED if charge['type'] == ChargeType.POSITIVE else BLUE
            alpha = 128 if not charge['active'] else 255
            s = pygame.Surface((GRID_SIZE-10, GRID_SIZE-10), pygame.SRCALPHA)
            s.fill((color[0], color[1], color[2], alpha))
            screen.blit(s, (charge['x'] * GRID_SIZE + 5, charge['y'] * GRID_SIZE + 5))
            
            # Desenha símbolo da carga
            charge_symbol = '+' if charge['type'] == ChargeType.POSITIVE else '-'
            font = pygame.font.SysFont(None, 30)
            text = font.render(charge_symbol, True, WHITE if charge['active'] else (200, 200, 200))
            screen.blit(text, (charge['x'] * GRID_SIZE + GRID_SIZE//2 - 5, 
                              charge['y'] * GRID_SIZE + GRID_SIZE//2 - 10))
            
            # Se estiver ativa, desenha o campo elétrico
            if charge['active']:
                radius = int(GRID_SIZE * self.field_radius)
                alpha = max(0, min(255, charge['activation_timer'] * 4))
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (color[0], color[1], color[2], alpha//3), 
                                 (radius, radius), radius)
                screen.blit(s, (charge['x'] * GRID_SIZE + GRID_SIZE//2 - radius, 
                                  charge['y'] * GRID_SIZE + GRID_SIZE//2 - radius))
        
        # Desenha mensagem se houver
        if self.message_timer > 0:
            font = pygame.font.SysFont(None, 36)
            text = font.render(self.message, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
            screen.blit(text, text_rect)

class Enemy:
    def __init__(self, x, y, charge_type=ChargeType.POSITIVE):
        self.x = x
        self.y = y
        self.charge = charge_type
        self.health = 100
        self.stunned = 0
        self.move_counter = 0
        
    def update(self, player, grid):
        if self.stunned > 0:
            self.stunned -= 1
            return
            
        self.move_counter += 1
        if self.move_counter < 30:  # Move a cada 0.5 segundos
            return
        self.move_counter = 0
        
        # Movimento aleatório
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        direction = random.choice(directions)
        
        new_x = self.x + direction[0]
        new_y = self.y + direction[1]
        
        # Verifica colisão com paredes
        if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and 
            grid[new_y][new_x] != 'W'):
            self.x = new_x
            self.y = new_y
            
        # Verifica interação com campos elétricos ativos
        for charge in [c for c in player.placed_charges if c['active']]:
            dx = self.x - charge['x']
            dy = self.y - charge['y']
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Verifica se está no raio do campo e sem paredes no caminho
            if distance <= player.field_radius and not self.has_wall_between(charge['x'], charge['y'], grid):
                # Dipolo tem comportamento especial
                if self.charge == ChargeType.DIPOLE:
                    if charge['type'] == ChargeType.POSITIVE:
                        # Parte negativa do dipolo é atraída
                        self.charge = ChargeType.POSITIVE  # Transforma em carga positiva
                    else:
                        # Parte positiva do dipolo é atraída
                        self.charge = ChargeType.NEGATIVE  # Transforma em carga negativa
                    continue
                
                # Cargas normais
                if self.charge != charge['type']:
                    # Atração - inimigo é eliminado
                    self.health = 0
                else:
                    # Repulsão - inimigo é empurrado
                    force_dir = (int(dx / max(1, abs(dx))), int(dy / max(1, abs(dy))))
                    new_x = self.x + force_dir[0]
                    new_y = self.y + force_dir[1]
                    
                    if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and 
                        grid[new_y][new_x] != 'W'):
                        self.x = new_x
                        self.y = new_y
    
    def has_wall_between(self, x1, y1, grid):
        # Bresenham's line algorithm para verificar paredes no caminho
        dx = abs(self.x - x1)
        dy = abs(self.y - y1)
        x, y = x1, y1
        sx = -1 if x1 > self.x else 1
        sy = -1 if y1 > self.y else 1
        err = dx - dy
        
        while x != self.x or y != self.y:
            if grid[y][x] == 'W':
                return True
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        return False
    
    def draw(self, screen):
        if self.charge == ChargeType.DIPOLE:
            # Desenha dipolo (roxo)
            pygame.draw.circle(screen, PURPLE, 
                             (self.x * GRID_SIZE + GRID_SIZE//2, self.y * GRID_SIZE + GRID_SIZE//2), 
                             GRID_SIZE//2 - 5)
            
            # Desenha ambas as cargas
            font = pygame.font.SysFont(None, 30)
            text_pos = font.render('+', True, WHITE)
            text_neg = font.render('-', True, WHITE)
            screen.blit(text_pos, (self.x * GRID_SIZE + GRID_SIZE//2 - 15, self.y * GRID_SIZE + GRID_SIZE//2 - 10))
            screen.blit(text_neg, (self.x * GRID_SIZE + GRID_SIZE//2 + 5, self.y * GRID_SIZE + GRID_SIZE//2 - 10))
        else:
            # Desenha carga normal
            color = RED if self.charge == ChargeType.POSITIVE else BLUE
            pygame.draw.circle(screen, color, 
                             (self.x * GRID_SIZE + GRID_SIZE//2, self.y * GRID_SIZE + GRID_SIZE//2), 
                             GRID_SIZE//2 - 5)
            
            # Desenha símbolo da carga
            charge_symbol = '+' if self.charge == ChargeType.POSITIVE else '-'
            font = pygame.font.SysFont(None, 30)
            text = font.render(charge_symbol, True, WHITE)
            screen.blit(text, (self.x * GRID_SIZE + GRID_SIZE//2 - 5, 
                              self.y * GRID_SIZE + GRID_SIZE//2 - 10))

class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type
        self.active = True
        
    def apply(self, player):
        if self.type == PowerUpType.FIELD_STRENGTH:
            player.field_strength += 0.5
            player.field_radius += 0.5
            return "Intensidade do Campo +"
        elif self.type == PowerUpType.EXTRA_CHARGE:
            player.max_charges += 1
            return "Carga Extra +"
        else:  # EXTRA_LIFE
            player.lives += 1
            return "Vida Extra +"
        
    def draw(self, screen):
        if not self.active:
            return
            
        if self.type == PowerUpType.FIELD_STRENGTH:
            color = YELLOW
            symbol = 'r+'
        elif self.type == PowerUpType.EXTRA_CHARGE:
            color = ORANGE
            symbol = 'E+'
        else:  # EXTRA_LIFE
            color = PINK
            symbol = '+1'
            
        pygame.draw.rect(screen, color, 
                        (self.x * GRID_SIZE + 5, self.y * GRID_SIZE + 5, 
                         GRID_SIZE - 10, GRID_SIZE - 10))
        
        font = pygame.font.SysFont(None, 30)
        text = font.render(symbol, True, BLACK)
        screen.blit(text, (self.x * GRID_SIZE + GRID_SIZE//2 - 10, 
                          self.y * GRID_SIZE + GRID_SIZE//2 - 10))

# Função para criar um nível
def create_level(level_num):
    grid = [[' ' for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    enemies = []
    powerups = []
    
    # Parede externa
    for x in range(GRID_WIDTH):
        grid[0][x] = 'W'
        grid[GRID_HEIGHT-1][x] = 'W'
    for y in range(GRID_HEIGHT):
        grid[y][0] = 'W'
        grid[y][GRID_WIDTH-1] = 'W'
    
    # Adiciona algumas paredes internas
    for _ in range(5 + level_num):
        x = random.randint(1, GRID_WIDTH-2)
        y = random.randint(1, GRID_HEIGHT-2)
        grid[y][x] = 'W'
    
    # Adiciona inimigos
    for _ in range(2 + level_num * 2):
        x = random.randint(1, GRID_WIDTH-2)
        y = random.randint(1, GRID_HEIGHT-2)
        if grid[y][x] == ' ':
            # 50% chance de carga positiva, 30% negativa, 20% dipolo
            charge_type = random.choices(
                [ChargeType.POSITIVE, ChargeType.NEGATIVE, ChargeType.DIPOLE],
                weights=[5, 3, 2]
            )[0]
            enemies.append(Enemy(x, y, charge_type))
    
    # Adiciona power-ups (apenas um de campo ou carga extra, e raramente vida extra)
    powerup_types = []
    
    # Escolhe entre intensidade de campo ou carga extra
    main_powerup = random.choice([PowerUpType.FIELD_STRENGTH, PowerUpType.EXTRA_CHARGE])
    powerup_types.append(main_powerup)
    
    # 20% chance de aparecer uma vida extra
    if random.random() < 0.2:
        powerup_types.append(PowerUpType.EXTRA_LIFE)
    
    for powerup_type in powerup_types:
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            x = random.randint(1, GRID_WIDTH-2)
            y = random.randint(1, GRID_HEIGHT-2)
            if grid[y][x] == ' ':
                powerups.append(PowerUp(x, y, powerup_type))
                placed = True
            attempts += 1
    
    # Posição inicial do jogador
    player_x, player_y = 1, 1
    while grid[player_y][player_x] != ' ':
        player_x += 1
        if player_x >= GRID_WIDTH-1:
            player_x = 1
            player_y += 1
    
    return grid, player_x, player_y, enemies, powerups

# Função para desenhar o grid
def draw_grid(grid):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(screen, WHITE, rect, 1)
            
            if grid[y][x] == 'W':  # Parede
                pygame.draw.rect(screen, GRAY, rect)

# Função para mostrar HUD
def draw_hud(player, level):
    font = pygame.font.SysFont(None, 36)
    
    # Pontuação
    score_text = font.render(f"Pontos: {player.score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    
    # Vidas
    lives_text = font.render(f"Vidas: {player.lives}", True, WHITE)
    screen.blit(lives_text, (10, 50))
    
    # Nível
    level_text = font.render(f"Nível: {level}", True, WHITE)
    screen.blit(level_text, (10, 90))
    
    # Cargas disponíveis
    charges_text = font.render(
        f"Cargas: {player.max_charges - len(player.placed_charges)}/{player.max_charges}", 
        True, WHITE)
    screen.blit(charges_text, (SCREEN_WIDTH - 200, 10))
    
    # Força do campo
    strength_text = font.render(f"Raio: {player.field_radius:.1f}", True, WHITE)
    screen.blit(strength_text, (SCREEN_WIDTH - 200, 50))

# Função para criar menu
def show_menu():
    menu_music.play(-1)  # Tocar em loop
    blink_timer = 0
    waiting = True
    
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Desenhar menu
        screen.blit(menu_image, (0, 0))
        
        # Texto piscante
        blink_timer += 1
        if blink_timer < 30:
            font = pygame.font.SysFont(None, 72)
            text = font.render("Pressione ENTER", True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
            screen.blit(text, text_rect)
        elif blink_timer > 60:
            blink_timer = 0
        
        pygame.display.flip()
        clock.tick(FPS)
    
    menu_music.stop()
    return GameState.PLAYING

# Função para mostrar nível completo
def show_level_complete(level, score):
    game_music.stop()
    blink_timer = 0
    waiting = True
    
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        screen.fill(BLACK)
        font = pygame.font.SysFont(None, 72)
        title = font.render(f"Fase {level} Completa!", True, GREEN)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//2 - 50))
        
        font = pygame.font.SysFont(None, 48)
        points = font.render(f"Pontuação: {score}", True, WHITE)
        screen.blit(points, (SCREEN_WIDTH//2 - points.get_width()//2, SCREEN_HEIGHT//2 + 20))
        
        # Texto piscante
        blink_timer += 1
        if blink_timer < 30:
            text = font.render("Pressione ENTER para continuar", True, YELLOW)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
            screen.blit(text, text_rect)
        elif blink_timer > 60:
            blink_timer = 0
        
        pygame.display.flip()
        clock.tick(FPS)
    
    game_music.play(-1)  # Retomar música do jogo
    return GameState.PLAYING

# Função para mostrar game over
def show_game_over(score):
    game_music.stop()
    blink_timer = 0
    waiting = True
    
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        screen.fill(BLACK)
        font = pygame.font.SysFont(None, 72)
        title = font.render("GAME OVER", True, RED)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//2 - 50))
        
        font = pygame.font.SysFont(None, 48)
        points = font.render(f"Pontuação Final: {score}", True, WHITE)
        screen.blit(points, (SCREEN_WIDTH//2 - points.get_width()//2, SCREEN_HEIGHT//2 + 20))
        
        # Texto piscante
        blink_timer += 1
        if blink_timer < 30:
            text = font.render("Pressione ENTER para recomeçar", True, YELLOW)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
            screen.blit(text, text_rect)
        elif blink_timer > 60:
            blink_timer = 0
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return GameState.MENU

"""
# Estado do jogo
current_level = 1
grid, player_x, player_y, enemies, powerups = create_level(current_level)
player = Player(player_x, player_y)
game_over = False
level_complete = False
paused = False

# Loop principal do jogo
running = True
while running:
    # Processamento de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
            
            if not paused and not game_over and not level_complete:
                # Movimento do jogador
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    player.move(-1, 0, grid)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    player.move(1, 0, grid)
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    player.move(0, -1, grid)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    player.move(0, 1, grid)
                
                # Colocar carga positiva/negativa
                elif event.key == pygame.K_p:
                    player.place_charge(ChargeType.POSITIVE)
                elif event.key == pygame.K_n:
                    player.place_charge(ChargeType.NEGATIVE)
            
            # Reiniciar nível ou avançar
            elif level_complete and event.key == pygame.K_RETURN:
                current_level += 1
                grid, player_x, player_y, enemies, powerups = create_level(current_level)
                player.x = player_x
                player.y = player_y
                player.placed_charges = []
                level_complete = False
            
            elif game_over and event.key == pygame.K_RETURN:
                current_level = 1
                grid, player_x, player_y, enemies, powerups = create_level(current_level)
                player = Player(player_x, player_y)
                game_over = False
    
    if paused:
        # Mostrar tela de pausa
        screen.fill(BLACK)
        show_message("PAUSADO - Pressione ESC para continuar", 0)
        pygame.display.flip()
        clock.tick(FPS)
        continue
    elif game_over:
        # Mostrar tela de game over
        show_game_over(player.score)
        clock.tick(FPS)
        continue
    elif level_complete:
        # Mostrar tela de nível completo
        screen.fill(BLACK)
        show_message(f"NÍVEL {current_level} COMPLETO! - Pressione ENTER para o próximo nível", 0)
        pygame.display.flip()
        clock.tick(FPS)
        continue
    
    # Atualização do jogo
    player.update()
    
    # Atualiza inimigos
    for enemy in enemies[:]:
        enemy.update(player.placed_charges, grid)
        
        # Verifica se inimigo morreu
        if enemy.health <= 0:
            player.score += 100 if enemy.charge != ChargeType.DIPOLE else 150
            enemies.remove(enemy)
        
        # Verifica colisão com jogador (jogador neutro morre em contato)
        if (enemy.x == player.x and enemy.y == player.y and player.invincible == 0):
            player.lives -= 1
            player.invincible = 60  # 1 segundo de invencibilidade
            if player.lives <= 0:
                game_over = True
    
    # Verifica power-ups
    for powerup in powerups[:]:
        if powerup.active and powerup.x == player.x and powerup.y == player.y:
            powerup.active = False
            message = powerup.apply(player)
            player.show_message(message + "1")
            player.score += 50
            powerups.remove(powerup)
    
    # Verifica se completou o nível (eliminou todos os inimigos)
    if len(enemies) == 0:
        player.score += 500 * current_level
        level_complete = True
    
    # Renderização
    screen.fill(BLACK)
    
    # Desenha grid
    draw_grid(grid)
    
    # Desenha power-ups
    for powerup in powerups:
        powerup.draw(screen)
    
    # Desenha inimigos
    for enemy in enemies:
        enemy.draw(screen)
    
    # Desenha jogador
    player.draw(screen)
    
    # Desenha HUD
    draw_hud(player, current_level)
    
    # Se jogador estiver invencível, pisca
    if player.invincible > 0 and player.invincible % 10 < 5:
        s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        s.fill((255, 255, 255, 128))
        screen.blit(s, (player.x * GRID_SIZE, player.y * GRID_SIZE))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
"""

def main():
    # Estado inicial do jogo
    game_state = GameState.MENU
    current_level = 1
    player = None
    grid, enemies, powerups = [], [], []
    
    # Loop principal do jogo
    running = True
    while running:
        # 1. Estado: MENU
        if game_state == GameState.MENU:
            # Mostra o menu e espera input
            game_state = show_menu()
            
            # Prepara novo jogo
            current_level = 1
            grid, player_x, player_y, enemies, powerups = create_level(current_level)
            player = Player(player_x, player_y)
            game_music.play(-1)  # Inicia música do jogo em loop
        
        # 2. Estado: JOGO EM ANDAMENTO
        elif game_state == GameState.PLAYING:
            # Processa eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_state = GameState.MENU
                        game_music.stop()
                    
                    # Movimento e ações do jogador
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        player.move(-1, 0, grid)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        player.move(1, 0, grid)
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        player.move(0, -1, grid)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        player.move(0, 1, grid)
                    elif event.key == pygame.K_p:
                        player.place_charge(ChargeType.POSITIVE)
                    elif event.key == pygame.K_n:
                        player.place_charge(ChargeType.NEGATIVE)
            
            # Atualiza lógica do jogo
            player.update()
            
            # Atualiza inimigos
            for enemy in enemies[:]:
                enemy.update(player, grid)
                if enemy.health <= 0:
                    player.score += 100 if enemy.charge != ChargeType.DIPOLE else 150
                    enemies.remove(enemy)
                
                # Verifica colisão com jogador
                if (enemy.x == player.x and enemy.y == player.y and player.invincible == 0):
                    player.lives -= 1
                    player.invincible = 60
                    if player.lives <= 0:
                        game_state = GameState.GAME_OVER
            
            # Verifica power-ups
            for powerup in powerups[:]:
                if powerup.active and powerup.x == player.x and powerup.y == player.y:
                    powerup.active = False
                    message = powerup.apply(player)
                    player.show_message(message + "1")
                    player.score += 50
                    powerups.remove(powerup)
            
            # Verifica se completou o nível
            if len(enemies) == 0:
                player.score += 500 * current_level
                game_state = GameState.LEVEL_COMPLETE
            
            # Renderização
            screen.fill(BLACK)
            draw_grid(grid)
            for powerup in powerups:
                powerup.draw(screen)
            for enemy in enemies:
                enemy.draw(screen)
            player.draw(screen)
            draw_hud(player, current_level)
            
            pygame.display.flip()
            clock.tick(FPS)
        
        # 3. Estado: NÍVEL COMPLETO
        elif game_state == GameState.LEVEL_COMPLETE:
            # Mostra tela de nível completo
            game_state = show_level_complete(current_level, player.score)
            
            # Prepara próxima fase
            current_level += 1
            grid, player_x, player_y, enemies, powerups = create_level(current_level)
            player.x = player_x
            player.y = player_y
            player.placed_charges = []
        
        # 4. Estado: GAME OVER
        elif game_state == GameState.GAME_OVER:
            # Mostra tela de game over
            game_state = show_game_over(player.score)
            
            # Volta para o menu (o loop recomeça)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()