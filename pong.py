import pygame
import numpy as np
import math
import random
import socket
import threading
import os
import time

# Inicialização do Pygame e do mixer (estéreo)
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Dimensões da tela e criação da janela
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong 1972 - Ultimate")
clock = pygame.time.Clock()

# Fontes e temas
font_large = pygame.font.SysFont("Arial", 60)
font_medium = pygame.font.SysFont("Arial", 40)
font_small = pygame.font.SysFont("Arial", 30)

themes = {
    "Classic": {
         "background": (0, 0, 0),
         "paddle": (255, 255, 255),
         "ball": (255, 255, 255),
         "obstacle": (200, 200, 200),
         "particle": (255, 255, 255),
         "text": (255, 255, 255)
    },
    "Dark": {
         "background": (20, 20, 20),
         "paddle": (180, 180, 180),
         "ball": (180, 180, 180),
         "obstacle": (100, 100, 100),
         "particle": (180, 180, 180),
         "text": (180, 180, 180)
    },
    "Neon": {
         "background": (10, 10, 30),
         "paddle": (57, 255, 20),
         "ball": (255, 20, 147),
         "obstacle": (0, 255, 255),
         "particle": (255, 255, 0),
         "text": (255, 20, 147)
    }
}
current_theme = "Classic"
current_theme_color = themes[current_theme]

# Controles padrão e modo mobile
controls = {
    "left_up": pygame.K_w,
    "left_down": pygame.K_s,
    "right_up": pygame.K_UP,
    "right_down": pygame.K_DOWN
}
mobile_mode = False

# Função de fade para transições suaves
def fade(screen, color=(0, 0, 0), duration=1.0):
    fade_surface = pygame.Surface((WIDTH, HEIGHT))
    fade_surface.fill(color)
    steps = int(duration * 60)
    for alpha in range(255, -1, -max(1, 255 // steps)):
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)

# Função para simular compartilhamento em redes sociais
def share_on_social_media(score_left, score_right):
    print(f"Compartilhado no Twitter: Placar {score_left}:{score_right}")

# Função para gerar som em estéreo
def generate_sound(frequency, duration=0.1, volume=0.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * math.pi * frequency * t) * volume
    stereo_wave = np.column_stack((wave, wave))
    stereo_wave = np.int16(stereo_wave * 32767)
    return pygame.sndarray.make_sound(stereo_wave)

# Sons para colisões e pontuações
paddle_beep = generate_sound(440, 0.1, 0.5)
wall_beep   = generate_sound(330, 0.1, 0.5)
score_beep  = generate_sound(550, 0.1, 0.5)

# --- Sistema de Partículas com Pooling ---
class Particle:
    def __init__(self, pos, color):
        self.reset(pos, color)
    def reset(self, pos, color):
        self.pos = np.array(pos, dtype=float)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 200)
        self.vel = np.array([math.cos(angle) * speed, math.sin(angle) * speed], dtype=float)
        self.lifetime = random.uniform(0.5, 1.0)
        self.age = 0
        self.size = random.randint(2, 5)
        self.color = color
    def update(self, dt):
        self.age += dt
        self.pos += self.vel * dt
    def draw(self, surface):
        if self.age < self.lifetime:
            alpha = max(0, int(255 * (1 - self.age / self.lifetime)))
            s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            s.fill((*self.color, alpha))
            surface.blit(s, (int(self.pos[0]), int(self.pos[1])))

class ParticlePool:
    def __init__(self, max_particles=500):
        self.pool = [Particle((0, 0), current_theme_color["particle"]) for _ in range(max_particles)]
        self.index = 0
        self.max_particles = max_particles
    def spawn(self, pos, num=20):
        for _ in range(num):
            self.pool[self.index].reset(pos, current_theme_color["particle"])
            self.index = (self.index + 1) % self.max_particles
    def update(self, dt):
        for p in self.pool:
            p.update(dt)
    def draw(self, surface):
        for p in self.pool:
            if p.age < p.lifetime:
                p.draw(surface)

particle_pool = ParticlePool()

# --- Classes de Jogo ---
class Paddle:
    def __init__(self, x, y, width, height, speed):
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = speed
    def move(self, dy):
        self.rect.y += dy
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
    def draw(self, surface, theme):
        shadow = self.rect.copy()
        shadow.x += 5; shadow.y += 5
        pygame.draw.rect(surface, (50, 50, 50), shadow)
        pygame.draw.rect(surface, theme["paddle"], self.rect)

class Ball:
    def __init__(self, x, y, radius, speed):
        self.radius = radius
        self.init_speed = speed
        self.speed = speed
        self.pos = np.array([x, y], dtype=float)
        self.spin = 0  # Efeito de rotação (spin)
        self.reset_direction()
    def reset_direction(self):
        angle = random.uniform(-math.pi/4, math.pi/4)
        direction = random.choice([-1, 1])
        self.vel = np.array([direction * self.speed * math.cos(angle),
                             self.speed * math.sin(angle)], dtype=float)
    def update(self, dt):
        self.vel[1] += self.spin * dt
        self.pos += self.vel * dt
        self.spin *= 0.98  # Decaimento do spin
        self.speed *= 0.999  # Atrito leve
        if self.pos[1] - self.radius <= 0 or self.pos[1] + self.radius >= HEIGHT:
            self.vel[1] = -self.vel[1]
            particle_pool.spawn(self.pos, 15)
            wall_beep.play()
    def draw(self, surface, theme):
        shadow_pos = (int(self.pos[0] + 5), int(self.pos[1] + 5))
        pygame.draw.circle(surface, (50, 50, 50), shadow_pos, self.radius)
        for i in range(3, 0, -1):
            alpha = max(0, 50 * i)
            glow_surface = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*theme["ball"], alpha), (self.radius * 2, self.radius * 2), self.radius + i * 2)
            surface.blit(glow_surface, (int(self.pos[0] - self.radius * 2), int(self.pos[1] - self.radius * 2)))
        pygame.draw.circle(surface, theme["ball"], (int(self.pos[0]), int(self.pos[1])), self.radius)
    def reset(self):
        self.pos = np.array([WIDTH / 2, HEIGHT / 2], dtype=float)
        self.speed *= 1.05
        self.reset_direction()

class PowerUp:
    def __init__(self, type, rect):
        self.type = type  # "enlarge", "shrink", "speed" ou "slow"
        self.rect = rect
        self.active = True
    def draw(self, surface, theme):
        if self.type == "enlarge":
            color = (0, 255, 0)
        elif self.type == "shrink":
            color = (255, 0, 0)
        elif self.type == "speed":
            color = (0, 0, 255)
        elif self.type == "slow":
            color = (255, 255, 0)
        pygame.draw.ellipse(surface, color, self.rect)

class Obstacle:
    def __init__(self, rect):
        self.rect = rect
    def draw(self, surface, theme):
        pygame.draw.rect(surface, theme["obstacle"], self.rect)

# Classe para gravação e replay
class ReplayRecorder:
    def __init__(self):
        self.records = []
        self.recording = True
    def record(self, state):
        if self.recording:
            self.records.append(state)
    def reset(self):
        self.records = []
    # Agora o método play recebe também o objeto game
    def play(self, surface, game, theme):
        for state in self.records:
            ball_pos, ball_vel, lp_y, rp_y, score_left, score_right = state
            ball.pos = np.array(ball_pos)
            left_paddle.rect.y = int(lp_y)
            right_paddle.rect.y = int(rp_y)
            game.draw(surface)
            pygame.display.flip()
            pygame.time.delay(50)

replay_recorder = ReplayRecorder()

class Game:
    def __init__(self, mode, difficulty, gamemode, theme_name):
        self.mode = mode  # "single" ou "multiplayer"
        self.difficulty = difficulty  # "Easy", "Medium", "Hard"
        self.gamemode = gamemode  # "Classic", "Time Attack", "Survival", "Tournament"
        self.theme = themes[theme_name]
        self.powerups = []
        self.obstacles = []
        self.last_hitter = None  # "left" ou "right"
        self.tournament_target = 5
        self.reset()
        self.powerup_timer = 0
        self.obstacle_timer = 0
        self.game_timer = 0
        self.stats = {"games": 0, "left_points": 0, "right_points": 0}
        self.paused = False
        self.volume = 0.5
        pygame.mixer.music.set_volume(self.volume)
        self.recording = True
    def reset(self):
        global left_paddle, right_paddle, ball
        paddle_width, paddle_height = 10, 100
        paddle_speed = 300
        left_paddle = Paddle(20, (HEIGHT - paddle_height) // 2, paddle_width, paddle_height, paddle_speed)
        right_paddle = Paddle(WIDTH - 20 - paddle_width, (HEIGHT - paddle_height) // 2, paddle_width, paddle_height, paddle_speed)
        ball = Ball(WIDTH / 2, HEIGHT / 2, 10, 300)
        self.score_left = 0
        self.score_right = 0
        self.game_timer = 0
        self.powerups.clear()
        self.obstacles.clear()
        self.last_hitter = None
        replay_recorder.reset()
    def update(self, dt):
        if not self.paused:
            if self.gamemode in ["Time Attack", "Tournament"]:
                self.game_timer += dt
            self.powerup_timer += dt
            if self.powerup_timer > 10:
                self.spawn_powerup()
                self.powerup_timer = 0
            if self.gamemode == "Survival":
                self.obstacle_timer += dt
                if self.obstacle_timer > 15:
                    self.spawn_obstacle()
                    self.obstacle_timer = 0
            # Controle da raquete esquerda
            if mobile_mode:
                mx, my = pygame.mouse.get_pos()
                left_paddle.rect.centery = my
            else:
                keys = pygame.key.get_pressed()
                if keys[controls["left_up"]]:
                    left_paddle.move(-left_paddle.speed * dt)
                if keys[controls["left_down"]]:
                    left_paddle.move(left_paddle.speed * dt)
            # Controle da raquete direita
            if self.mode == "multiplayer":
                if mobile_mode:
                    mx, my = pygame.mouse.get_pos()
                    if mx > WIDTH / 2:
                        right_paddle.rect.centery = my
                else:
                    if keys[controls["right_up"]]:
                        right_paddle.move(-right_paddle.speed * dt)
                    if keys[controls["right_down"]]:
                        right_paddle.move(right_paddle.speed * dt)
            else:
                # IA adaptativa
                base_error = 10
                score_diff = self.score_left - self.score_right
                error_margin = max(0, base_error - score_diff)
                ai_speed = 300 + 50 * abs(score_diff)
                if ball.pos[1] < right_paddle.rect.centery - error_margin:
                    right_paddle.move(-ai_speed * dt)
                elif ball.pos[1] > right_paddle.rect.centery + error_margin:
                    right_paddle.move(ai_speed * dt)
            ball.update(dt)
            ball_rect = pygame.Rect(int(ball.pos[0] - ball.radius), int(ball.pos[1] - ball.radius),
                                    ball.radius * 2, ball.radius * 2)
            if ball_rect.colliderect(left_paddle.rect) and ball.vel[0] < 0:
                self.handle_paddle_collision(left_paddle)
            if ball_rect.colliderect(right_paddle.rect) and ball.vel[0] > 0:
                self.handle_paddle_collision(right_paddle)
            for obs in self.obstacles:
                if ball_rect.colliderect(obs.rect):
                    ball.vel[0] = -ball.vel[0]
                    particle_pool.spawn(ball.pos, 10)
                    wall_beep.play()
            for pu in self.powerups:
                if pu.active and ball_rect.colliderect(pu.rect):
                    self.apply_powerup(pu)
                    pu.active = False
                    particle_pool.spawn(ball.pos, 15)
                    paddle_beep.play()
            if ball.pos[0] - ball.radius < 0:
                self.score_right += 1
                self.stats["right_points"] += 1
                score_beep.play()
                ball.reset()
            if ball.pos[0] + ball.radius > WIDTH:
                self.score_left += 1
                self.stats["left_points"] += 1
                score_beep.play()
                ball.reset()
            if self.gamemode == "Tournament":
                if self.score_left >= self.tournament_target or self.score_right >= self.tournament_target:
                    self.paused = True
            # Grava estado para replay
            if self.recording:
                state = (tuple(ball.pos), tuple(ball.vel), left_paddle.rect.y, right_paddle.rect.y,
                         self.score_left, self.score_right)
                replay_recorder.record(state)
        particle_pool.update(dt)
    def handle_paddle_collision(self, paddle):
        relative_intersect = ball.pos[1] - paddle.rect.centery
        normalized = relative_intersect / (paddle.rect.height / 2)
        max_angle = math.radians(75)
        angle = normalized * max_angle
        speed = math.hypot(ball.vel[0], ball.vel[1])
        if paddle == left_paddle:
            ball.vel[0] = speed * math.cos(angle)
            ball.vel[1] = speed * math.sin(angle)
            if ball.vel[0] < 0:
                ball.vel[0] = -ball.vel[0]
            self.last_hitter = "left"
            ball.spin = normalized * 50
        else:
            ball.vel[0] = -speed * math.cos(angle)
            ball.vel[1] = speed * math.sin(angle)
            if ball.vel[0] > 0:
                ball.vel[0] = -ball.vel[0]
            self.last_hitter = "right"
            ball.spin = -normalized * 50
        particle_pool.spawn(ball.pos, 20)
        paddle_beep.play()
    def spawn_powerup(self):
        types = ["enlarge", "shrink", "speed", "slow"]
        pu_type = random.choice(types)
        size = 20
        x = random.randint(WIDTH // 4, 3 * WIDTH // 4)
        y = random.randint(HEIGHT // 4, 3 * HEIGHT // 4)
        rect = pygame.Rect(x, y, size, size)
        self.powerups.append(PowerUp(pu_type, rect))
    def spawn_obstacle(self):
        w_obs = 20; h_obs = 100
        x = WIDTH // 2 - w_obs // 2
        y = random.randint(HEIGHT // 4, 3 * HEIGHT // 4 - h_obs)
        rect = pygame.Rect(x, y, w_obs, h_obs)
        self.obstacles.append(Obstacle(rect))
    def apply_powerup(self, pu):
        if pu.type == "enlarge":
            if self.last_hitter == "left":
                left_paddle.rect.height = min(HEIGHT, left_paddle.rect.height + 20)
            elif self.last_hitter == "right":
                right_paddle.rect.height = min(HEIGHT, right_paddle.rect.height + 20)
        elif pu.type == "shrink":
            if self.last_hitter == "left":
                right_paddle.rect.height = max(20, right_paddle.rect.height - 20)
            elif self.last_hitter == "right":
                left_paddle.rect.height = max(20, left_paddle.rect.height - 20)
        elif pu.type == "speed":
            ball.speed *= 1.2
            ball.reset_direction()
        elif pu.type == "slow":
            ball.speed *= 0.8
            ball.reset_direction()
    def draw(self, surface):
        surface.fill(self.theme["background"])
        for obs in self.obstacles:
            obs.draw(surface, self.theme)
        for pu in self.powerups:
            if pu.active:
                pu.draw(surface, self.theme)
        left_paddle.draw(surface, self.theme)
        right_paddle.draw(surface, self.theme)
        ball.draw(surface, self.theme)
        particle_pool.draw(surface)
        score_text = font_medium.render(f"{self.score_left}   :   {self.score_right}", True, self.theme["text"])
        surface.blit(score_text, ((WIDTH - score_text.get_width()) // 2, 20))
        if self.gamemode in ["Time Attack", "Tournament"]:
            timer_text = font_small.render(f"Tempo: {int(self.game_timer)}s", True, self.theme["text"])
            surface.blit(timer_text, (WIDTH - timer_text.get_width() - 20, 20))

# --- Modo Online com Interpolação e Tratamento de Erros ---
class OnlineGame(Game):
    def __init__(self, is_host, ip_address, port, difficulty, gamemode, theme_name):
        super().__init__("online", difficulty, gamemode, theme_name)
        self.is_host = is_host
        self.ip_address = ip_address
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(0.1)
        self.running_network = True
        if self.is_host:
            self.sock.bind(('', self.port))
            self.sock.listen(1)
            print("Aguardando conexão de um cliente...")
            try:
                self.conn, addr = self.sock.accept()
                print("Conectado com", addr)
            except Exception as e:
                print("Erro ao aceitar conexão:", e)
        else:
            try:
                self.sock.connect((self.ip_address, self.port))
                self.conn = self.sock
            except Exception as e:
                print("Erro ao conectar:", e)
        self.current_state = None
        self.interp_factor = 0.1
        self.network_thread = threading.Thread(target=self.network_loop, daemon=True)
        self.network_thread.start()
    def network_loop(self):
        while self.running_network:
            try:
                if self.is_host:
                    state = f"{ball.pos[0]},{ball.pos[1]},{ball.vel[0]},{ball.vel[1]},{left_paddle.rect.y},{right_paddle.rect.y},{self.score_left},{self.score_right}"
                    self.conn.sendall(state.encode())
                    data = self.conn.recv(1024).decode()
                    if data == "UP":
                        right_paddle.move(-right_paddle.speed * 0.016)
                    elif data == "DOWN":
                        right_paddle.move(right_paddle.speed * 0.016)
                else:
                    data = self.conn.recv(1024).decode()
                    vals = data.split(',')
                    if len(vals) == 8:
                        new_state = tuple(map(float, vals))
                        if self.current_state is None:
                            self.current_state = new_state
                        else:
                            self.current_state = tuple(
                                self.current_state[i] + self.interp_factor * (new_state[i] - self.current_state[i])
                                for i in range(8)
                            )
                        ball.pos[0], ball.pos[1], ball.vel[0], ball.vel[1], lp_y, rp_y, s_left, s_right = self.current_state
                        left_paddle.rect.y = int(lp_y)
                        right_paddle.rect.y = int(rp_y)
                        self.score_left = int(s_left)
                        self.score_right = int(s_right)
                        keys = pygame.key.get_pressed()
                        if keys[controls["right_up"]]:
                            self.conn.sendall("UP".encode())
                        elif keys[controls["right_down"]]:
                            self.conn.sendall("DOWN".encode())
                        else:
                            self.conn.sendall("NONE".encode())
            except Exception as e:
                print("Erro na rede:", e)
            time.sleep(0.016)
    def stop_network(self):
        self.running_network = False
        try:
            self.conn.close()
            self.sock.close()
        except:
            pass

# --- Menus e Telas ---
class SettingsMenu:
    def __init__(self):
        self.options = ["Left Up", "Left Down", "Right Up", "Right Down", "Toggle Mobile Mode", "Custom Music", "Back"]
        self.selected = 0
        self.changing = False
    def draw(self, surface):
        surface.fill(current_theme_color["background"])
        title = font_large.render("Configurações", True, current_theme_color["text"])
        surface.blit(title, ((WIDTH - title.get_width()) // 2, 50))
        for i, option in enumerate(self.options):
            text_str = option
            if option in ["Left Up", "Left Down", "Right Up", "Right Down"]:
                key_name = pygame.key.name(controls[option.lower().replace(" ", "_")])
                text_str += f": {key_name}"
            elif option == "Toggle Mobile Mode":
                text_str += f": {'On' if mobile_mode else 'Off'}"
            elif option == "Custom Music":
                text_str += ": (Selecione arquivo)"
            if i == self.selected:
                text = font_medium.render("> " + text_str, True, current_theme_color["text"])
            else:
                text = font_medium.render("  " + text_str, True, current_theme_color["text"])
            surface.blit(text, (100, 150 + i * 50))
    def handle_event(self, event):
        global mobile_mode, controls
        if event.type == pygame.KEYDOWN:
            if self.changing:
                key = event.key
                opt = self.options[self.selected]
                if opt in ["Left Up", "Left Down", "Right Up", "Right Down"]:
                    controls[opt.lower().replace(" ", "_")] = key
                    self.changing = False
            else:
                if event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    opt = self.options[self.selected]
                    if opt in ["Left Up", "Left Down", "Right Up", "Right Down"]:
                        self.changing = True
                    elif opt == "Toggle Mobile Mode":
                        mobile_mode = not mobile_mode
                    elif opt == "Custom Music":
                        filename = input("Digite o nome do arquivo de música: ").strip()
                        if os.path.exists(filename):
                            try:
                                pygame.mixer.music.load(filename)
                                pygame.mixer.music.play(-1)
                            except Exception as e:
                                print("Erro ao carregar música:", e)
                    elif opt == "Back":
                        return "Back"
        return None

class Menu:
    def __init__(self):
        self.options = ["Singleplayer", "Local Multiplayer", "Online Multiplayer", "Tournament", "Replay", "Settings", "Stats", "Exit"]
        self.selected = 0
        self.difficulty_options = ["Easy", "Medium", "Hard"]
        self.selected_difficulty = 1
        self.gamemode_options = ["Classic", "Time Attack", "Survival", "Tournament"]
        self.selected_gamemode = 0
        self.theme_options = list(themes.keys())
        self.selected_theme = 0
    def draw(self, surface):
        theme = themes[self.theme_options[self.selected_theme]]
        surface.fill(theme["background"])
        title = font_large.render("Pong 1972 - Menu", True, theme["text"])
        surface.blit(title, ((WIDTH - title.get_width()) // 2, 50))
        for i, option in enumerate(self.options):
            color = theme["text"]
            if i == self.selected:
                text = font_medium.render("> " + option, True, color)
            else:
                text = font_medium.render("  " + option, True, color)
            surface.blit(text, (100, 150 + i * 50))
        diff_text = font_small.render("Dificuldade: " + self.difficulty_options[self.selected_difficulty], True, theme["text"])
        surface.blit(diff_text, (500, 150))
        mode_text = font_small.render("Modo: " + self.gamemode_options[self.selected_gamemode], True, theme["text"])
        surface.blit(mode_text, (500, 200))
        theme_text = font_small.render("Tema: " + self.theme_options[self.selected_theme], True, theme["text"])
        surface.blit(theme_text, (500, 250))
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_LEFT:
                self.selected_difficulty = (self.selected_difficulty - 1) % len(self.difficulty_options)
            elif event.key == pygame.K_RIGHT:
                self.selected_difficulty = (self.selected_difficulty + 1) % len(self.difficulty_options)
            elif event.key == pygame.K_a:
                self.selected_gamemode = (self.selected_gamemode - 1) % len(self.gamemode_options)
            elif event.key == pygame.K_d:
                self.selected_gamemode = (self.selected_gamemode + 1) % len(self.gamemode_options)
            elif event.key == pygame.K_z:
                self.selected_theme = (self.selected_theme - 1) % len(self.theme_options)
            elif event.key == pygame.K_c:
                self.selected_theme = (self.selected_theme + 1) % len(self.theme_options)
            elif event.key == pygame.K_RETURN:
                return self.options[self.selected]
        return None

class StatsScreen:
    def __init__(self, stats):
        self.stats = stats
        self.rankings = self.load_rankings()
    def load_rankings(self):
        if os.path.exists("rankings.txt"):
            with open("rankings.txt", "r") as f:
                data = f.read().splitlines()
            rankings = [line.split(":") for line in data]
            return {r[0]: int(r[1]) for r in rankings if len(r) == 2}
        return {}
    def save_rankings(self):
        with open("rankings.txt", "w") as f:
            for k, v in self.rankings.items():
                f.write(f"{k}:{v}\n")
    def update_rankings(self, mode, score):
        if mode in self.rankings:
            if score > self.rankings[mode]:
                self.rankings[mode] = score
        else:
            self.rankings[mode] = score
        self.save_rankings()
    def draw(self, surface, theme):
        surface.fill(theme["background"])
        title = font_large.render("Estatísticas", True, theme["text"])
        surface.blit(title, ((WIDTH - title.get_width()) // 2, 50))
        games_text = font_medium.render("Jogos: " + str(self.stats["games"]), True, theme["text"])
        surface.blit(games_text, (100, 150))
        left_text = font_medium.render("Pontos Esquerda: " + str(self.stats["left_points"]), True, theme["text"])
        surface.blit(left_text, (100, 200))
        right_text = font_medium.render("Pontos Direita: " + str(self.stats["right_points"]), True, theme["text"])
        surface.blit(right_text, (100, 250))
        ranking_text = font_medium.render("Ranking:", True, theme["text"])
        surface.blit(ranking_text, (100, 300))
        y_offset = 350
        for mode, score in self.rankings.items():
            r_text = font_small.render(f"{mode}: {score}", True, theme["text"])
            surface.blit(r_text, (120, y_offset))
            y_offset += 30
        instruct = font_small.render("Pressione ESC, ENTER ou R para voltar ao menu", True, theme["text"])
        surface.blit(instruct, ((WIDTH - instruct.get_width()) // 2, HEIGHT - 100))

# --- Função Principal ---
def main():
    global current_theme, current_theme_color
    running = True
    state = "menu"  # estados: "menu", "playing", "playing_online", "stats", "settings", "replay"
    menu = Menu()
    settings_menu = SettingsMenu()
    game = None
    stats_screen = None
    online_game = None

    # Carrega música de fundo (arquivo "background.mp3")
    if os.path.exists("background.mp3"):
        pygame.mixer.music.load("background.mp3")
        pygame.mixer.music.play(-1)
    else:
        print("Arquivo 'background.mp3' não encontrado.")

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if state == "menu":
                result = menu.handle_event(event)
                if result == "Exit":
                    running = False
                elif result == "Singleplayer":
                    current_theme = menu.theme_options[menu.selected_theme]
                    current_theme_color = themes[current_theme]
                    game = Game("single", menu.difficulty_options[menu.selected_difficulty],
                                menu.gamemode_options[menu.selected_gamemode], current_theme)
                    state = "playing"
                    fade(screen)
                elif result == "Local Multiplayer":
                    current_theme = menu.theme_options[menu.selected_theme]
                    current_theme_color = themes[current_theme]
                    game = Game("multiplayer", menu.difficulty_options[menu.selected_difficulty],
                                menu.gamemode_options[menu.selected_gamemode], current_theme)
                    state = "playing"
                    fade(screen)
                elif result == "Online Multiplayer":
                    current_theme = menu.theme_options[menu.selected_theme]
                    current_theme_color = themes[current_theme]
                    print("Hospedar (H) ou conectar (C)?")
                    choice = input("Digite H ou C: ").strip().upper()
                    is_host = (choice == "H")
                    ip_address = "localhost"
                    if not is_host:
                        ip_address = input("Digite o IP do host: ").strip()
                    online_game = OnlineGame(is_host, ip_address, 12345,
                                             menu.difficulty_options[menu.selected_difficulty],
                                             menu.gamemode_options[menu.selected_gamemode],
                                             current_theme)
                    state = "playing_online"
                    fade(screen)
                elif result == "Tournament":
                    current_theme = menu.theme_options[menu.selected_theme]
                    current_theme_color = themes[current_theme]
                    game = Game("single", menu.difficulty_options[menu.selected_difficulty],
                                "Tournament", current_theme)
                    state = "playing"
                    fade(screen)
                elif result == "Replay":
                    state = "replay"
                    fade(screen)
                elif result == "Settings":
                    state = "settings"
                    fade(screen)
                elif result == "Stats":
                    stats_screen = StatsScreen(game.stats if game else {"games": 0, "left_points": 0, "right_points": 0})
                    state = "stats"
                    fade(screen)
            elif state == "settings":
                res = settings_menu.handle_event(event)
                if res == "Back":
                    state = "menu"
                    fade(screen)
            elif state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        game.paused = not game.paused
                    if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        game.volume = max(0, game.volume - 0.1)
                        pygame.mixer.music.set_volume(game.volume)
                    if event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                        game.volume = min(1, game.volume + 0.1)
                        pygame.mixer.music.set_volume(game.volume)
                    if event.key == pygame.K_t:
                        share_on_social_media(game.score_left, game.score_right)
                    if event.key == pygame.K_r:
                        game.recording = False
                        state = "replay"
                        fade(screen)
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"
                        game.stats["games"] += 1
                        fade(screen)
            elif state == "playing_online":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"
                        if online_game:
                            online_game.stop_network()
                        fade(screen)
            elif state == "stats":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_r):
                        state = "menu"
                        fade(screen)
            elif state == "replay":
                if event.type == pygame.KEYDOWN:
                    # Agora, pressionar ESC, ENTER ou R sai do modo replay
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_r):
                        state = "menu"
                        fade(screen)
        if state == "menu":
            menu.draw(screen)
        elif state == "settings":
            settings_menu.draw(screen)
        elif state == "stats":
            theme = themes[menu.theme_options[menu.selected_theme]]
            stats_screen.draw(screen, theme)
        elif state == "playing":
            game.update(dt)
            game.draw(screen)
            if game.paused:
                pause_text = font_large.render("PAUSA", True, game.theme["text"])
                screen.blit(pause_text, ((WIDTH - pause_text.get_width()) // 2, HEIGHT // 2))
        elif state == "playing_online":
            online_game.update(dt)
            online_game.draw(screen)
        elif state == "replay":
            replay_recorder.play(screen, game, themes[menu.theme_options[menu.selected_theme]])
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
