import pygame
import random
import math

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def update(self, dt):
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['timer'] -= dt
        self.particles = [p for p in self.particles if p['timer'] > 0]

    def draw(self, surface):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p['timer'] / p['max_timer']))))
            color = p['color']
            if len(color) == 3:
                color = (*color, alpha)
            
            size = max(1, int(p['size'] * (p['timer'] / p['max_timer'])))
            if size <= 1:
                surface.set_at((int(p['x']), int(p['y'])), color[:3])
            else:
                s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (size, size), size)
                surface.blit(s, (int(p['x'] - size), int(p['y'] - size)))

    def emit_bomb(self, x, y):
        for _ in range(100):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 500)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'timer': 1.0,
                'max_timer': 1.0,
                'color': (255, 200, 50),
                'size': random.uniform(2, 6)
            })

    def emit_explosion(self, x, y, color=None, count=25, speed_mult=100):
        if color is None:
            color = (255, 100, 50)
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, speed_mult)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'timer': random.uniform(0.3, 0.8),
                'max_timer': 0.8,
                'color': color,
                'size': random.uniform(2, 5)
            })

    def emit_engine_trail(self, x, y, intensity=1.0):
        for _ in range(int(2 * intensity)):
            self.particles.append({
                'x': x + random.uniform(-5, 5), 
                'y': y + random.uniform(0, 5),
                'vx': random.uniform(-10, 10),
                'vy': random.uniform(20, 50),
                'timer': random.uniform(0.1, 0.3),
                'max_timer': 0.3,
                'color': (100, 200, 255),
                'size': random.uniform(1, 3)
            })

    def emit_damage_sparks(self, x, y):
        self.emit_explosion(x, y, color=(255, 255, 0), count=10, speed_mult=150)

    def emit_shield_hit(self, x, y):
        self.emit_explosion(x, y, color=(100, 150, 255), count=15, speed_mult=100)

    def emit_powerup_collect(self, x, y):
        self.emit_explosion(x, y, color=(50, 255, 50), count=20, speed_mult=80)
