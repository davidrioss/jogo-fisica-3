import pygame
import sys
import math
from enum import Enum
import random

pygame.init()

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
LIGHT_BLUE = (173, 216, 230)

# Tipos de carga
class ChargeType(Enum):
    POSITIVE = 1
    NEGATIVE = -1

# Configuração da tela
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("EletroBlast")
clock = pygame.time.Clock()

# Carregar imagens (substitua por suas próprias imagens)
try:
    player_img = pygame.Surface((GRID_SIZE-10, GRID_SIZE-10))
    player_img.fill(BLUE)
    
    enemy_img = pygame.Surface((GRID_SIZE-10, GRID_SIZE-10))
    enemy_img.fill(RED)
    
    charge_img = {
        ChargeType.POSITIVE: pygame.Surface((GRID_SIZE-10, GRID_SIZE-10)),
        ChargeType.NEGATIVE: pygame.Surface((GRID_SIZE-10, GRID_SIZE-10))
    }
    charge_img[ChargeType.POSITIVE].fill(RED)
    charge_img[ChargeType.NEGATIVE].fill(BLUE)
    
    wall_img = pygame.Surface((GRID_SIZE, GRID_SIZE))
    wall_img.fill(GRAY)
    
    conductor_img = pygame.Surface((GRID_SIZE, GRID_SIZE))
    conductor_img.fill(YELLOW)
    
    dielectric_img = pygame.Surface((GRID_SIZE, GRID_SIZE))
    dielectric_img.fill(PURPLE)
    
    powerup_img = pygame.Surface((GRID_SIZE-10, GRID_SIZE-10))
    powerup_img.fill(GREEN)
except:
    print("Erro ao carregar imagens. Usando superfícies simples.")

# Classes do jogo
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.charge = ChargeType.POSITIVE  # Começa com carga positiva
        self.max_charges = 3
        self.placed_charges = []
        self.field_strength = 1.0
        self.score = 0
        self.lives = 3
        self.invincible = 0
        
    def move(self, dx, dy, grid):
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Verifica se a nova posição está dentro dos limites e não é uma parede
        if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and 
            grid[new_y][new_x] != 'W' and grid[new_y][new_x] != 'C' and grid[new_y][new_x] != 'D'):
            self.x = new_x
            self.y = new_y
            
    def place_charge(self, charge_type):
        if len(self.placed_charges) < self.max_charges:
            self.placed_charges.append({
                'x': self.x,
                'y': self.y,
                'type': charge_type,
                'active': False,
                'timer': 0
            })
            return True
        return False
    
    def activate_charges(self):
        for charge in self.placed_charges:
            charge['active'] = True
            charge['timer'] = 60  # 1 segundo a 60 FPS
    
    def update(self):
        # Atualiza temporizador de invencibilidade
        if self.invincible > 0:
            self.invincible -= 1
            
        # Atualiza cargas ativas
        for charge in self.placed_charges[:]:
            if charge['active']:
                charge['timer'] -= 1
                if charge['timer'] <= 0:
                    self.placed_charges.remove(charge)
    
    def draw(self, screen):
        # Desenha o jogador
        color = BLUE if self.charge == ChargeType.POSITIVE else RED
        pygame.draw.circle(screen, color, 
                         (self.x * GRID_SIZE + GRID_SIZE//2, self.y * GRID_SIZE + GRID_SIZE//2), 
                         GRID_SIZE//2 - 5)
        
        # Desenha ícone de carga
        charge_symbol = '+' if self.charge == ChargeType.POSITIVE else '-'
        font = pygame.font.SysFont(None, 30)
        text = font.render(charge_symbol, True, WHITE)
        screen.blit(text, (self.x * GRID_SIZE + GRID_SIZE//2 - 5, self.y * GRID_SIZE + GRID_SIZE//2 - 10))
        
        # Desenha cargas colocadas
        for charge in self.placed_charges:
            color = RED if charge['type'] == ChargeType.POSITIVE else BLUE
            alpha = 255 if charge['active'] else 128
            s = pygame.Surface((GRID_SIZE-10, GRID_SIZE-10), pygame.SRCALPHA)
            s.fill((color[0], color[1], color[2], alpha))
            screen.blit(s, (charge['x'] * GRID_SIZE + 5, charge['y'] * GRID_SIZE + 5))
            
            # Desenha símbolo da carga
            charge_symbol = '+' if charge['type'] == ChargeType.POSITIVE else '-'
            text = font.render(charge_symbol, True, WHITE if charge['active'] else (200, 200, 200))
            screen.blit(text, (charge['x'] * GRID_SIZE + GRID_SIZE//2 - 5, 
                              charge['y'] * GRID_SIZE + GRID_SIZE//2 - 10))
            
            # Se estiver ativa, desenha o campo elétrico
            if charge['active']:
                radius = int(GRID_SIZE * 2 * self.field_strength)
                alpha = max(0, min(255, charge['timer'] * 2))
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (color[0], color[1], color[2], alpha//3), 
                                 (radius, radius), radius)
                screen.blit(s, (charge['x'] * GRID_SIZE + GRID_SIZE//2 - radius, 
                              charge['y'] * GRID_SIZE + GRID_SIZE//2 - radius))

class Enemy:
    def __init__(self, x, y, charge_type=ChargeType.POSITIVE):
        self.x = x
        self.y = y
        self.charge = charge_type
        self.health = 100
        self.stunned = 0
        
    def update(self, player_charges, grid):
        if self.stunned > 0:
            self.stunned -= 1
            return
            
        # Inimigo simples: move-se aleatoriamente
        direction = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0), (0, 0)])
        new_x = self.x + direction[0]
        new_y = self.y + direction[1]
        
        # Verifica colisão com paredes e outros obstáculos
        if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and 
            grid[new_y][new_x] != 'W' and grid[new_y][new_x] != 'C' and grid[new_y][new_x] != 'D'):
            self.x = new_x
            self.y = new_y
            
        # Verifica interação com campos elétricos
        for charge in player_charges:
            if charge['active']:
                dx = self.x - charge['x']
                dy = self.y - charge['y']
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 2 * player.field_strength:  # Dentro do campo
                    # Força elétrica: atrair ou repelir
                    force_multiplier = 1 if charge['type'] != self.charge else -1
                    force_multiplier *= player.field_strength / max(1, distance)
                    
                    # Aplica força
                    new_x = self.x + int(force_multiplier * dx / max(1, abs(dx)))
                    new_y = self.y + int(force_multiplier * dy / max(1, abs(dy)))
                    
                    # Verifica se pode mover
                    if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and 
                        grid[new_y][new_x] != 'W' and grid[new_y][new_x] != 'C' and grid[new_y][new_x] != 'D'):
                        self.x = new_x
                        self.y = new_y
                    
                    # Dano se for repelido contra parede
                    if (grid[self.y][self.x] == 'W' and force_multiplier < 0):
                        self.health -= 20
                        self.stunned = 30
                        
    def draw(self, screen):
        color = RED if self.charge == ChargeType.POSITIVE else BLUE
        alpha = 128 if self.stunned > 0 else 255
        s = pygame.Surface((GRID_SIZE-10, GRID_SIZE-10), pygame.SRCALPHA)
        s.fill((color[0], color[1], color[2], alpha))
        screen.blit(s, (self.x * GRID_SIZE + 5, self.y * GRID_SIZE + 5))
        
        # Desenha símbolo da carga
        charge_symbol = '+' if self.charge == ChargeType.POSITIVE else '-'
        font = pygame.font.SysFont(None, 30)
        text_color = (255, 255, 255, alpha) if self.stunned > 0 else WHITE
        text = font.render(charge_symbol, True, text_color)
        screen.blit(text, (self.x * GRID_SIZE + GRID_SIZE//2 - 5, 
                          self.y * GRID_SIZE + GRID_SIZE//2 - 10))

class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type  # 'charge', 'strength', 'shield'
        self.active = True
        
    def draw(self, screen):
        if not self.active:
            return
            
        if self.type == 'charge':
            color = GREEN
        elif self.type == 'strength':
            color = YELLOW
        else:  # shield
            color = LIGHT_BLUE
            
        pygame.draw.rect(screen, color, 
                        (self.x * GRID_SIZE + 5, self.y * GRID_SIZE + 5, 
                         GRID_SIZE - 10, GRID_SIZE - 10))
        
        # Desenha símbolo
        font = pygame.font.SysFont(None, 30)
        if self.type == 'charge':
            symbol = 'C+'
        elif self.type == 'strength':
            symbol = 'S+'
        else:
            symbol = '🛡'
            
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
    for _ in range(10 + level_num * 2):
        x = random.randint(1, GRID_WIDTH-2)
        y = random.randint(1, GRID_HEIGHT-2)
        grid[y][x] = 'W'
    
    # Adiciona condutores
    for _ in range(3 + level_num):
        x = random.randint(1, GRID_WIDTH-2)
        y = random.randint(1, GRID_HEIGHT-2)
        if grid[y][x] == ' ':
            grid[y][x] = 'C'
    
    # Adiciona dielétricos
    for _ in range(2 + level_num):
        x = random.randint(1, GRID_WIDTH-2)
        y = random.randint(1, GRID_HEIGHT-2)
        if grid[y][x] == ' ':
            grid[y][x] = 'D'
    
    # Adiciona inimigos
    for _ in range(3 + level_num):
        x = random.randint(1, GRID_WIDTH-2)
        y = random.randint(1, GRID_HEIGHT-2)
        if grid[y][x] == ' ':
            charge = random.choice([ChargeType.POSITIVE, ChargeType.NEGATIVE])
            enemies.append(Enemy(x, y, charge))
    
    # Adiciona power-ups
    for _ in range(2):
        x = random.randint(1, GRID_WIDTH-2)
        y = random.randint(1, GRID_HEIGHT-2)
        if grid[y][x] == ' ':
            powerups.append(PowerUp(x, y, random.choice(['charge', 'strength', 'shield'])))
    
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
            elif grid[y][x] == 'C':  # Condutor
                pygame.draw.rect(screen, YELLOW, rect)
            elif grid[y][x] == 'D':  # Dielétrico
                pygame.draw.rect(screen, PURPLE, rect)

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
    strength_text = font.render(f"Força: {player.field_strength:.1f}", True, WHITE)
    screen.blit(strength_text, (SCREEN_WIDTH - 200, 50))
    
    # Carga atual
    charge_text = font.render(
        f"Carga: {'+' if player.charge == ChargeType.POSITIVE else '-'}", 
        True, WHITE)
    screen.blit(charge_text, (SCREEN_WIDTH - 200, 90))

# Função para mostrar mensagem
def show_message(message, duration=2000):
    font = pygame.font.SysFont(None, 48)
    text = font.render(message, True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    
    # Fundo semi-transparente
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))
    screen.blit(s, (0, 0))
    
    screen.blit(text, text_rect)
    pygame.display.flip()
    pygame.time.delay(duration)

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
                elif event.key == pygame.K_q:
                    player.place_charge(ChargeType.POSITIVE)
                elif event.key == pygame.K_e:
                    player.place_charge(ChargeType.NEGATIVE)
                
                # Ativar cargas
                elif event.key == pygame.K_SPACE:
                    player.activate_charges()
                
                # Mudar carga do jogador
                elif event.key == pygame.K_c:
                    player.charge = ChargeType.POSITIVE if player.charge == ChargeType.NEGATIVE else ChargeType.NEGATIVE
            
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
    
    if paused or game_over or level_complete:
        # Mostrar tela de pausa/game over/nível completo
        screen.fill(BLACK)
        
        if paused:
            show_message("PAUSADO - Pressione ESC para continuar", 0)
        elif game_over:
            show_message("GAME OVER - Pressione ENTER para recomeçar", 0)
        elif level_complete:
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
            player.score += 100
            enemies.remove(enemy)
        
        # Verifica colisão com jogador
        if (enemy.x == player.x and enemy.y == player.y and player.invincible == 0):
            player.lives -= 1
            player.invincible = 60  # 1 segundo de invencibilidade
            if player.lives <= 0:
                game_over = True
    
    # Verifica power-ups
    for powerup in powerups[:]:
        if powerup.active and powerup.x == player.x and powerup.y == player.y:
            powerup.active = False
            player.score += 50
            
            if powerup.type == 'charge':
                player.max_charges += 1
                show_message("+1 Carga Máxima!")
            elif powerup.type == 'strength':
                player.field_strength += 0.5
                show_message("+0.5 Força de Campo!")
            elif powerup.type == 'shield':
                player.lives = min(5, player.lives + 1)
                show_message("+1 Vida!")
            
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