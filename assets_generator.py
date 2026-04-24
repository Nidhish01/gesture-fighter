"""
Procedurally generates all game assets - no external files needed.
"""

import pygame
import math
import random


def create_player_ship(size=64):
    """Create a sleek spaceship surface."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    # Main body
    body_points = [
        (size // 2, 4),  # Nose
        (size // 2 + 20, size - 12),  # Right wing tip
        (size // 2 + 8, size - 20),  # Right inner
        (size // 2 + 6, size - 8),  # Right exhaust
        (size // 2 - 6, size - 8),  # Left exhaust
        (size // 2 - 8, size - 20),  # Left inner
        (size // 2 - 20, size - 12),  # Left wing tip
    ]
    pygame.draw.polygon(surf, (0, 180, 255), body_points)
    pygame.draw.polygon(surf, (0, 220, 255), body_points, 2)

    # Cockpit
    cockpit_points = [
        (size // 2, 12),
        (size // 2 + 5, 28),
        (size // 2 - 5, 28),
    ]
    pygame.draw.polygon(surf, (0, 255, 255), cockpit_points)

    # Engine glow
    pygame.draw.circle(surf, (255, 150, 0), (size // 2, size - 6), 4)
    pygame.draw.circle(surf, (255, 255, 100), (size // 2, size - 6), 2)

    return surf


def create_player_ship_shielded(size=64):
    """Create player ship with shield effect."""
    surf = create_player_ship(size)
    shield_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(shield_surf, (0, 150, 255, 80), (size // 2, size // 2), size // 2 - 2)
    pygame.draw.circle(shield_surf, (0, 200, 255, 150), (size // 2, size // 2), size // 2 - 2, 2)
    surf.blit(shield_surf, (0, 0))
    return surf


def create_enemy_basic(size=48):
    """Red angular enemy ship."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    points = [
        (size // 2, size - 4),  # Bottom point (facing down)
        (4, 8),
        (size // 2 - 6, 16),
        (size // 2 + 6, 16),
        (size - 4, 8),
    ]
    pygame.draw.polygon(surf, (255, 60, 60), points)
    pygame.draw.polygon(surf, (255, 120, 120), points, 2)
    # Eye
    pygame.draw.circle(surf, (255, 255, 0), (size // 2, 18), 4)
    pygame.draw.circle(surf, (255, 0, 0), (size // 2, 18), 2)
    return surf


def create_enemy_fast(size=40):
    """Slim, fast enemy."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    points = [
        (size // 2, size - 2),
        (8, 4),
        (size // 2, 12),
        (size - 8, 4),
    ]
    pygame.draw.polygon(surf, (255, 165, 0), points)
    pygame.draw.polygon(surf, (255, 200, 100), points, 2)
    return surf


def create_enemy_tank(size=56):
    """Big, heavy enemy."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # Wide body
    pygame.draw.rect(surf, (180, 0, 180), (8, 6, size - 16, size - 12), border_radius=6)
    pygame.draw.rect(surf, (220, 80, 220), (8, 6, size - 16, size - 12), 2, border_radius=6)
    # Cannon
    pygame.draw.rect(surf, (200, 0, 200), (size // 2 - 3, size - 14, 6, 14))
    # Eyes
    pygame.draw.circle(surf, (255, 255, 0), (size // 2 - 10, 20), 5)
    pygame.draw.circle(surf, (255, 255, 0), (size // 2 + 10, 20), 5)
    return surf


def create_boss(size=120):
    """Large boss ship."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # Main body
    pygame.draw.ellipse(surf, (150, 0, 0), (10, 10, size - 20, size // 2))
    pygame.draw.ellipse(surf, (200, 50, 50), (10, 10, size - 20, size // 2), 3)
    # Wings
    left_wing = [(10, size // 4), (0, size // 2 + 20), (30, size // 4 + 10)]
    right_wing = [(size - 10, size // 4), (size, size // 2 + 20), (size - 30, size // 4 + 10)]
    pygame.draw.polygon(surf, (180, 0, 0), left_wing)
    pygame.draw.polygon(surf, (180, 0, 0), right_wing)
    # Core
    pygame.draw.circle(surf, (255, 255, 0), (size // 2, size // 4 + 5), 12)
    pygame.draw.circle(surf, (255, 100, 0), (size // 2, size // 4 + 5), 8)
    # Cannons
    for x_off in [-25, -10, 10, 25]:
        pygame.draw.rect(surf, (255, 50, 50), (size // 2 + x_off - 2, size // 2 - 5, 4, 20))
    return surf


def create_laser(color=(0, 255, 255), length=20, width=4):
    """Create a laser bolt."""
    surf = pygame.Surface((width + 4, length), pygame.SRCALPHA)
    # Glow
    pygame.draw.rect(surf, (*color[:3], 80), (0, 0, width + 4, length), border_radius=2)
    # Core
    pygame.draw.rect(surf, color, (2, 0, width, length), border_radius=2)
    # Bright center
    pygame.draw.rect(surf, (255, 255, 255), (width // 2 + 1, 0, 2, length))
    return surf


def create_enemy_laser():
    """Red enemy laser."""
    return create_laser(color=(255, 50, 50), length=16, width=3)


def create_powerup(ptype="health", size=28):
    """Create power-up icons."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    colors = {
        "health": (255, 50, 50),
        "shield": (50, 150, 255),
        "rapid": (255, 255, 50),
        "bomb": (255, 100, 0),
        "life": (50, 255, 50),
    }
    color = colors.get(ptype, (255, 255, 255))

    # Outer glow
    pygame.draw.circle(surf, (*color, 60), (size // 2, size // 2), size // 2)
    # Inner circle
    pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2 - 4)
    pygame.draw.circle(surf, (255, 255, 255), (size // 2, size // 2), size // 2 - 4, 2)

    # Symbol
    font = pygame.font.SysFont("Arial", 16, bold=True)
    symbols = {"health": "+", "shield": "S", "rapid": "R", "bomb": "B", "life": "♥"}
    symbol = symbols.get(ptype, "?")
    text = font.render(symbol, True, (255, 255, 255))
    text_rect = text.get_rect(center=(size // 2, size // 2))
    surf.blit(text, text_rect)

    return surf


def create_star_field(width, height, num_layers=3):
    """Create parallax star field layers."""
    layers = []
    for layer in range(num_layers):
        stars = []
        count = 30 + layer * 40
        for _ in range(count):
            x = random.randint(0, width)
            y = random.randint(0, height)
            brightness = random.randint(100, 255)
            star_size = 1 + layer * 0.5
            speed = 0.5 + layer * 0.8
            stars.append({
                "x": x, "y": y,
                "brightness": brightness,
                "size": star_size,
                "speed": speed
            })
        layers.append(stars)
    return layers


def create_explosion_frames(size=64, num_frames=8):
    """Create explosion animation frames."""
    frames = []
    for i in range(num_frames):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        progress = i / num_frames
        radius = int(size * 0.1 + size * 0.4 * progress)
        alpha = int(255 * (1 - progress))

        # Outer ring
        if alpha > 0:
            color_outer = (255, 100 + int(100 * (1 - progress)), 0, max(0, alpha - 50))
            pygame.draw.circle(surf, color_outer, (size // 2, size // 2), radius)

        # Inner bright core
        inner_radius = max(1, int(radius * 0.6 * (1 - progress)))
        color_inner = (255, 255, 200, alpha)
        pygame.draw.circle(surf, color_inner, (size // 2, size // 2), inner_radius)

        # Sparks
        num_sparks = 6 + i * 2
        for j in range(num_sparks):
            angle = (j / num_sparks) * math.pi * 2 + progress * 1.5
            dist = radius * (0.8 + random.random() * 0.5)
            sx = int(size // 2 + math.cos(angle) * dist)
            sy = int(size // 2 + math.sin(angle) * dist)
            if 0 <= sx < size and 0 <= sy < size:
                spark_color = (255, 200, 50, max(0, alpha - 30))
                pygame.draw.circle(surf, spark_color, (sx, sy), max(1, 3 - i // 3))

        frames.append(surf)
    return frames