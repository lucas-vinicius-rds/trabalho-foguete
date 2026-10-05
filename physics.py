"""Constantes físicas do jogo de foguete."""
import math

DT = 1 / 60  # passo de tempo fixo (s)
FPS = 60

G = 9.8  # m/s²
DRY_MASS = 100_000.0  # kg (100 ton)
FUEL_MASS = 100_000.0  # kg (100 ton)
THRUST = 2e6  # N
FUEL_PER_FRAME = 0.001 * FUEL_MASS  # 0,1% do combustível total por frame
MAX_ANGLE_DEG = 30
MAX_ANGLE = math.radians(MAX_ANGLE_DEG)  # rad
TURN_RATE = math.radians(60)  # velocidade angular do giro (rad/s)
