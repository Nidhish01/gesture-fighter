"""
Game entities: Player, Enemies, Bullets, Power-ups, Boss.
"""

import pygame
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class Player:
    """Player spaceship controlled by hand gestures."""

    def __init__(self, x, y, ship_img, ship_shield_img):
        self.x = float(x)
        self.y = float(y)
        self.image = ship_img
        self.shield_image = ship_shield_img
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.width = self.rect.width
        self.height = self.rect.height

        # Stats
        self.max_health = 100
        self.health = self.max_health
        self.lives = 3
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        self.combo_timeout = 2.0  # seconds

        # Shooting
        self.shoot_cooldown = 0.18  # seconds between shots
        self.last_shot_time = 0
        self.rapid_fire = False
        self.rapid_fire_timer = 0
        self.bullet_damage = 25

        # Shield
        self.shield_active = False
        self.shield_energy = 100
        self.shield_max = 100
        self.shield_drain_rate = 30  # per second
        self.shield_regen_rate = 15  # per second

        # Special
        self.bomb_count = 2
        self.bomb_cooldown = 0
        self.invincible = False
        self.invincible_timer = 0

        # Visual
        self.engine_particles = []
        self.tilt = 0  # rotation based on horizontal movement
        self._prev_x = x

    def update(self, target_x, target_y, screen_w, screen_h, dt):
        """Move player toward target position."""
        # Calculate movement with smoothing
        margin = 30
        target_x = max(margin, min(screen_w - margin, target_x))
        target_y = max(margin, min(screen_h - margin, target_y))

        # Smooth interpolation
        lerp_speed = 8.0
        self.x += (target_x - self.x) * lerp_speed * dt
        self.y += (target_y - self.y) * lerp_speed * dt

        # Calculate tilt based on horizontal velocity
        dx = self.x - self._prev_x
        self.tilt = max(-25, min(25, dx * 2))
        self._prev_x = self.x

        self.rect.center = (int(self.x), int(self.y))

        # Update timers
        if self.rapid_fire:
            self.rapid_fire_timer -= dt
            if self.rapid_fire_timer <= 0:
                self.rapid_fire = False
                self.shoot_cooldown = 0.18

        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False

        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= dt

        # Shield regen when not active
        if not self.shield_active and self.shield_energy < self.shield_max:
            self.shield_energy = min(
                self.shield_max,
                self.shield_energy + self.shield_regen_rate * dt
            )

        # Shield drain when active
        if self.shield_active:
            self.shield_energy -= self.shield_drain_rate * dt
            if self.shield_energy <= 0:
                self.shield_energy = 0
                self.shield_active = False

        # Combo timer
        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

    def try_shoot(self, laser_img) -> Optional[List['Bullet']]:
        """Attempt to fire. Returns list of bullets or None."""
        now = time.time()
        if now - self.last_shot_time < self.shoot_cooldown:
            return None
        self.last_shot_time = now

        bullets = []
        if self.rapid_fire:
            # Triple shot
            for offset in [-12, 0, 12]:
                b = Bullet(
                    self.x + offset, self.y - self.height // 2,
                    0, -600, self.bullet_damage, laser_img
                )
                bullets.append(b)
        else:
            b = Bullet(
                self.x, self.y - self.height // 2,
                0, -600, self.bullet_damage, laser_img
            )
            bullets.append(b)
        return bullets

    def take_damage(self, amount):
        """Apply damage to player."""
        if self.invincible:
            return False
        if self.shield_active and self.shield_energy > 0:
            self.shield_energy -= amount * 0.5
            return False
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            return True  # Player died
        # Brief invincibility after hit
        self.invincible = True
        self.invincible_timer = 1.0
        return False

    def add_score(self, points):
        """Add score with combo multiplier."""
        self.combo += 1
        self.combo_timer = self.combo_timeout
        multiplier = min(self.combo, 10)
        self.score += points * multiplier

    def activate_rapid_fire(self, duration=5.0):
        self.rapid_fire = True
        self.rapid_fire_timer = duration
        self.shoot_cooldown = 0.08

    def draw(self, surface):
        """Draw player with tilt and effects."""
        if self.invincible and int(time.time() * 10) % 2 == 0:
            return  # Flicker effect

        img = self.shield_image if self.shield_active else self.image
        if abs(self.tilt) > 1:
            img = pygame.transform.rotate(img, -self.tilt)
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(img, rect)


class Bullet:
    """Projectile fired by player or enemy."""

    def __init__(self, x, y, vx, vy, damage, image):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.image = image
        self.rect = image.get_rect(center=(int(x), int(y)))
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))
        # Off-screen check
        if self.y < -50 or self.y > 900 or self.x < -50 or self.x > 1000:
            self.alive = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Enemy:
    """Base enemy class."""

    BASIC = "basic"
    FAST = "fast"
    TANK = "tank"

    def __init__(self, x, y, enemy_type, image, health=50, speed=100, score_value=100):
        self.x = float(x)
        self.y = float(y)
        self.enemy_type = enemy_type
        self.image = image
        self.rect = image.get_rect(center=(int(x), int(y)))
        self.max_health = health
        self.health = health
        self.speed = speed
        self.score_value = score_value
        self.alive = True

        # Movement pattern
        self.time_alive = 0
        self.base_x = x
        self.shoot_cooldown = random.uniform(1.5, 3.0)
        self.shoot_timer = random.uniform(0, self.shoot_cooldown)

        # Movement variation
        self.wave_amplitude = random.uniform(30, 80)
        self.wave_frequency = random.uniform(1.0, 2.5)
        self.wave_phase = random.uniform(0, math.pi * 2)

    def update(self, dt, screen_w):
        self.time_alive += dt
        self.y += self.speed * dt

        # Sinusoidal horizontal movement
        self.x = self.base_x + math.sin(
            self.time_alive * self.wave_frequency + self.wave_phase
        ) * self.wave_amplitude

        # Keep on screen
        self.x = max(20, min(screen_w - 20, self.x))
        self.rect.center = (int(self.x), int(self.y))

        # Shooting timer
        self.shoot_timer -= dt

        # Off screen
        if self.y > 750:
            self.alive = False

    def try_shoot(self, laser_img) -> Optional[Bullet]:
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_cooldown
            return Bullet(
                self.x, self.y + self.rect.height // 2,
                random.uniform(-30, 30), 300, 15, laser_img
            )
        return None

    def take_damage(self, amount) -> bool:
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        # Health bar
        if self.health < self.max_health:
            bar_w = self.rect.width
            bar_h = 4
            bar_x = self.rect.x
            bar_y = self.rect.y - 8
            ratio = self.health / self.max_health
            pygame.draw.rect(surface, (80, 80, 80), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (255, 50, 50), (bar_x, bar_y, int(bar_w * ratio), bar_h))


class Boss(Enemy):
    """Boss enemy with multiple attack patterns."""

    def __init__(self, x, y, image, level=1):
        hp = 500 + level * 200
        super().__init__(x, y, "boss", image, health=hp, speed=30, score_value=1000 + level * 500)
        self.level = level
        self.phase = 0
        self.attack_pattern = 0
        self.pattern_timer = 0
        self.pattern_duration = 3.0
        self.target_y = 80
        self.entering = True
        self.shoot_cooldown = 0.3

    def update(self, dt, screen_w):
        self.time_alive += dt

        if self.entering:
            self.y += 60 * dt
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entering = False
        else:
            # Horizontal sweep
            self.x = screen_w // 2 + math.sin(self.time_alive * 0.8) * (screen_w // 3)

            # Pattern switching
            self.pattern_timer += dt
            if self.pattern_timer >= self.pattern_duration:
                self.pattern_timer = 0
                self.attack_pattern = (self.attack_pattern + 1) % 3

        self.rect.center = (int(self.x), int(self.y))
        self.shoot_timer -= dt

        # Phase change at 50% health
        if self.health <= self.max_health * 0.5 and self.phase == 0:
            self.phase = 1
            self.shoot_cooldown = 0.2
            self.speed = 50

    def try_shoot(self, laser_img) -> Optional[List[Bullet]]:
        if self.entering or self.shoot_timer > 0:
            return None

        self.shoot_timer = self.shoot_cooldown
        bullets = []

        if self.attack_pattern == 0:
            # Spread shot
            for angle_deg in range(-30, 31, 15):
                angle = math.radians(angle_deg + 90)
                vx = math.cos(angle) * 250
                vy = math.sin(angle) * 250
                bullets.append(Bullet(self.x, self.y + 40, vx, vy, 12, laser_img))

        elif self.attack_pattern == 1:
            # Aimed burst
            bullets.append(Bullet(self.x - 25, self.y + 40, -20, 350, 15, laser_img))
            bullets.append(Bullet(self.x + 25, self.y + 40, 20, 350, 15, laser_img))

        elif self.attack_pattern == 2:
            # Spiral
            angle = self.time_alive * 5
            vx = math.cos(angle) * 200
            vy = abs(math.sin(angle)) * 200 + 100
            bullets.append(Bullet(self.x, self.y + 40, vx, vy, 10, laser_img))

        return bullets if bullets else None


class PowerUp:
    """Collectible power-up."""

    HEALTH = "health"
    SHIELD = "shield"
    RAPID = "rapid"
    BOMB = "bomb"
    LIFE = "life"

    def __init__(self, x, y, ptype, image):
        self.x = float(x)
        self.y = float(y)
        self.ptype = ptype
        self.image = image
        self.rect = image.get_rect(center=(int(x), int(y)))
        self.alive = True
        self.time_alive = 0
        self.bob_offset = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self.time_alive += dt
        self.y += 80 * dt
        # Bobbing motion
        bob = math.sin(self.time_alive * 3 + self.bob_offset) * 8
        self.rect.center = (int(self.x + bob), int(self.y))
        if self.y > 750:
            self.alive = False

    def draw(self, surface):
        # Glow effect
        glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        alpha = int(100 + 50 * math.sin(self.time_alive * 4))
        pygame.draw.circle(glow_surf, (255, 255, 255, alpha), (20, 20), 18)
        surface.blit(glow_surf, (self.rect.centerx - 20, self.rect.centery - 20))
        surface.blit(self.image, self.rect)

    def apply(self, player: Player):
        """Apply power-up effect to player."""
        if self.ptype == self.HEALTH:
            player.health = min(player.max_health, player.health + 30)
        elif self.ptype == self.SHIELD:
            player.shield_energy = player.shield_max
        elif self.ptype == self.RAPID:
            player.activate_rapid_fire(6.0)
        elif self.ptype == self.BOMB:
            player.bomb_count = min(5, player.bomb_count + 1)
        elif self.ptype == self.LIFE:
            player.lives += 1