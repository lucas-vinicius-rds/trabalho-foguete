"""Classe do foguete: estado e integração do movimento."""
import math

from physics import DRY_MASS, FUEL_MASS, FUEL_PER_FRAME, G, MAX_ANGLE, THRUST, TURN_RATE


class Rocket:
    def __init__(self, x=0.0, y=2500.0):
        # Posição (m): x horizontal, y altitude (0 = solo)
        self.x = x
        self.y = y
        # Velocidade (m/s)
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0  # rad, 0 = nariz para cima
        self.fuel = FUEL_MASS
        self.alive = True  # False após tocar o solo
        self.thrusting = False

    @property
    def mass(self):
        return DRY_MASS + self.fuel

    def update(self, dt, thrusting=False, turn=0):
        """Euler semi-implícito. turn: -1 (esquerda), 0 (centro) ou +1 (direita)."""
        if not self.alive:
            return
        # Rotação em torno do centro de massa: o ângulo-alvo é turn * 30°
        # e o foguete gira até ele com velocidade angular limitada.
        target = turn * MAX_ANGLE
        step = TURN_RATE * dt
        if abs(target - self.angle) <= step:
            self.angle = target
        else:
            self.angle += step if target > self.angle else -step
        # Força resultante: peso (-m*g em y) + empuxo na direção do nariz
        m = self.mass  # massa no início do frame
        fx, fy = 0.0, -m * G
        self.thrusting = thrusting and self.fuel > 0
        if self.thrusting:
            fx += THRUST * math.sin(self.angle)
            fy += THRUST * math.cos(self.angle)
            self.fuel = max(0.0, self.fuel - FUEL_PER_FRAME)
        ax = fx / m
        ay = fy / m
        self.vx += ax * dt
        self.vy += ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Colisão com o solo
        if self.y <= 0.0:
            self.y = 0.0
            self.vx = 0.0
            self.vy = 0.0
            self.alive = False
            self.thrusting = False
