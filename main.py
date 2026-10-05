"""Jogo de foguete: simulação com passo fixo, câmera e interface em tela cheia."""
import math
import random

# pyrefly: ignore [missing-import]
import pygame

from physics import DT, FPS, FUEL_MASS
from rocket import Rocket

WORLD_HEIGHT = 3000.0  # metros visíveis na tela, antes do deslocamento da câmera
GROUND_FRACTION = 0.08  # fração da tela ocupada pelo solo
TEXT = (232, 239, 250)
MUTED = (157, 179, 206)
ACCENT = (82, 219, 198)


class Game:
    """Score em passos de simulação; o recorde dura enquanto o jogo estiver aberto."""

    def __init__(self):
        self.best = 0.0
        self.restart()

    @property
    def elapsed(self):
        return self.frames * DT

    def restart(self):
        self.rocket = Rocket()
        self.frames = 0

    def update(self, thrusting=False, turn=0):
        if self.rocket.alive:
            # Atualização com passo fixo Δt = 1/60 s
            self.rocket.update(DT, thrusting, turn)
            self.frames += 1
            self.best = max(self.best, self.elapsed)


class Renderer:
    """Desenho em pixels, separado das posições e forças em unidades SI."""

    def __init__(self, screen):
        self.screen = screen
        self.sw, self.sh = screen.get_size()
        self.ground_y = int(self.sh * (1 - GROUND_FRACTION))
        self.scale = self.ground_y / WORLD_HEIGHT  # pixels por metro
        self.ui = min(self.sw / 1280, self.sh / 720)
        self.font = pygame.font.SysFont("Segoe UI", max(14, int(20 * self.ui)))
        self.small = pygame.font.SysFont("Segoe UI", max(12, int(16 * self.ui)))
        self.title = pygame.font.SysFont("Segoe UI", max(24, int(38 * self.ui)), bold=True)
        self.background = pygame.Surface(screen.get_size())
        # O fundo é pré-calculado; sua decoração não interfere na física.
        for y in range(self.sh):
            t = y / max(1, self.sh - 1)
            color = (int(8 + 9 * t), int(15 + 16 * t), int(33 + 23 * t))
            pygame.draw.line(self.background, color, (0, y), (self.sw, y))
        rng = random.Random(42)
        for _ in range(150):
            x, y = rng.randrange(self.sw), rng.randrange(self.sh)
            shade = rng.randrange(90, 190)
            pygame.draw.circle(self.background, (shade, shade, min(255, shade + 30)), (x, y), 1)

    def label(self, text, x, y, color=TEXT, font=None, centered=False):
        surface = (font or self.font).render(text, True, color)
        self.screen.blit(surface, (x - surface.get_width() // 2 if centered else x, y))

    def panel(self, rect):
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, (12, 23, 42, 230), layer.get_rect(), border_radius=12)
        self.screen.blit(layer, rect)
        pygame.draw.rect(self.screen, (55, 78, 105), rect, 1, border_radius=12)

    def draw_world(self, rocket):
        # A câmera acompanha x e sobe quando necessário, sem alterar o movimento.
        camera_x = rocket.x
        camera_y = max(0.0, rocket.y - WORLD_HEIGHT * 0.85)

        def to_screen(x, y):
            return int(self.sw / 2 + (x - camera_x) * self.scale), int(self.ground_y - (y - camera_y) * self.scale)

        self.screen.blit(self.background, (0, 0))
        ground_y = to_screen(0, 0)[1]
        if ground_y < self.sh:
            pygame.draw.rect(self.screen, (39, 65, 65), (0, ground_y, self.sw, self.sh - ground_y))
            pygame.draw.line(self.screen, (106, 163, 143), (0, ground_y), (self.sw, ground_y), 3)
            # Marcas de posição tornam o movimento horizontal visível.
            left_m = camera_x - self.sw / (2 * self.scale)
            right_m = camera_x + self.sw / (2 * self.scale)
            for x in range(math.floor(left_m / 500) * 500, math.ceil(right_m / 500) * 500 + 1, 500):
                sx, sy = to_screen(x, 0)
                pygame.draw.line(self.screen, MUTED, (sx, sy), (sx, sy + 10), 2)
                self.label(f"{x} m", sx, sy - self.small.get_height() - 8, MUTED, self.small, centered=True)
            sx, sy = to_screen(0, 0)
            pygame.draw.rect(self.screen, (113, 130, 144), (sx - 45, sy, 90, 8))

        # Desenho
        px, py = to_screen(rocket.x, rocket.y)  # (px, py) = centro de massa
        h, w = max(40, int(54 * self.ui)), max(12, int(18 * self.ui))
        # O sprite tem tamanho ilustrativo; a colisão usa y=0 no centro de massa.
        if not rocket.alive:
            py = ground_y - h // 2
        ca, sa = math.cos(rocket.angle), math.sin(rocket.angle)

        def rot(lx, ly):
            # ponto local (x direita, y para o nariz) girado em torno do CM
            return (px + lx * ca + ly * sa, py - (-lx * sa + ly * ca))

        def polygon(color, points):
            pygame.draw.polygon(self.screen, color, [rot(x, y) for x, y in points])

        if rocket.thrusting:
            flicker = pygame.time.get_ticks() // 40 % 6  # apenas animação visual
            polygon((255, 136, 59), [(-w * .4, -h * .4), (w * .4, -h * .4), (0, -h * .95 - flicker)])
            polygon((255, 230, 130), [(-w * .2, -h * .4), (w * .2, -h * .4), (0, -h * .75)])
        polygon((99, 158, 179), [(-w / 2, -h * .1), (-w, -h * .45), (-w / 2, -h * .4)])
        polygon((99, 158, 179), [(w / 2, -h * .1), (w, -h * .45), (w / 2, -h * .4)])
        polygon((223, 231, 239), [(-w / 2, h * .25), (w / 2, h * .25), (w / 2, -h * .4), (-w / 2, -h * .4)])
        polygon((82, 219, 198), [(0, h / 2), (w / 2, h * .25), (-w / 2, h * .25)])
        polygon((71, 93, 120), [(-w * .4, -h * .4), (w * .4, -h * .4), (w * .3, -h * .48), (-w * .3, -h * .48)])
        pygame.draw.circle(self.screen, (45, 83, 117), rot(0, h * .1), max(3, w // 4))
        if camera_y > 0:
            self.label("Solo abaixo da câmera", self.sw // 2, self.sh - int(85 * self.ui), MUTED, self.small, centered=True)

    def draw(self, game):
        rocket = game.rocket
        self.draw_world(rocket)
        margin = int(22 * self.ui)
        row = max(22, int(29 * self.ui))
        width = max(245, int(310 * self.ui))
        self.panel(pygame.Rect(margin, margin, width, row * 11 + margin))
        x, y = margin * 2, margin * 2
        self.label("TELEMETRIA", x, y, ACCENT, self.small)
        lines = [
            f"Tempo no ar: {game.elapsed:.2f} s",
            f"Melhor tempo: {game.best:.2f} s",
            f"Altitude: {rocket.y:.1f} m",
            f"Posição horizontal: {rocket.x:.1f} m",
            f"Vel. vertical: {rocket.vy:+.1f} m/s",
            f"Vel. horizontal: {rocket.vx:+.1f} m/s",
            f"Massa: {rocket.mass / 1000:.1f} t",
            f"Ângulo: {math.degrees(rocket.angle):+.1f}°",
        ]
        for i, line in enumerate(lines, 1):
            self.label(line, x, y + i * row)
        ratio = rocket.fuel / FUEL_MASS
        bar = pygame.Rect(x, y + 9 * row, width - 2 * margin, max(8, int(10 * self.ui)))
        pygame.draw.rect(self.screen, (43, 60, 80), bar, border_radius=4)
        if ratio > 0:
            pygame.draw.rect(self.screen, ACCENT if ratio > .2 else (255, 169, 77), (bar.x, bar.y, int(bar.width * ratio), bar.height), border_radius=4)
        self.label(f"Combustível: {ratio:.1%}  ({rocket.fuel / 1000:.1f} t)", x, bar.bottom + 5, MUTED, self.small)
        self.label("ESPAÇO: propulsão   |   ← →: inclinar   |   R: reiniciar   |   ESC: sair", self.sw // 2, self.sh - max(26, int(35 * self.ui)), TEXT, self.small, centered=True)
        if rocket.alive and rocket.fuel == 0:
            self.label("Combustível esgotado", self.sw // 2, margin, (255, 169, 77), centered=True)
        if not rocket.alive:
            shade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            shade.fill((3, 8, 18, 155))
            self.screen.blit(shade, (0, 0))
            card = pygame.Rect(0, 0, int(500 * self.ui), int(235 * self.ui))
            card.center = (self.sw // 2, self.sh // 2)
            self.panel(card)
            cx = card.centerx
            self.label("FIM DE VOO", cx, card.top + int(22 * self.ui), font=self.title, centered=True)
            self.label(f"Tempo no ar: {game.elapsed:.2f} s", cx, card.top + int(82 * self.ui), ACCENT, centered=True)
            self.label(f"Melhor tempo da sessão: {game.best:.2f} s", cx, card.top + int(119 * self.ui), MUTED, centered=True)
            self.label("R: tentar novamente  •  ESC: sair", cx, card.top + int(175 * self.ui), centered=True)


def main():
    pygame.init()
    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Jogo de Foguete")
        clock = pygame.time.Clock()
        renderer = Renderer(screen)
        game = Game()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        game.restart()
            if not running:
                break
            keys = pygame.key.get_pressed()
            turn = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            game.update(bool(keys[pygame.K_SPACE]), turn)
            renderer.draw(game)
            pygame.display.flip()
            clock.tick(FPS)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
