"""
Core game engine: wave management, collision detection, game loop logic.
"""

import pygame
import random
import math
import time
from typing import List, Optional

from entities import Player, Bullet, Enemy, Boss, PowerUp
from particles import ParticleSystem
from assets_generator import (
    create_player_ship, create_player_ship_shielded,
    create_enemy_basic, create_enemy_fast, create_enemy_tank, create_boss,
    create_laser, create_enemy_laser, create_powerup,
    create_star_field, create_explosion_frames
)
from ui import GameUI


class WaveManager:
    """Manages enemy wave spawning and progression."""

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.current_wave = 0
        self.enemies_to_spawn = 0
        self.spawn_timer = 0
        self.spawn_interval = 1.0
        self.wave_active = False
        self.wave_complete = False
        self.between_wave_timer = 3.0
        self.boss_wave = False
        self.boss_spawned = False

    def start_next_wave(self):
        """Initialize the next wave."""
        self.current_wave += 1
        self.wave_active = True
        self.wave_complete = False
        self.boss_spawned = False
        self.spawn_timer = 0

        # Boss every 5 waves
        self.boss_wave = (self.current_wave % 5 == 0)

        if self.boss_wave:
            self.enemies_to_spawn = 0  # Boss only
        else:
            self.enemies_to_spawn = 4 + self.current_wave * 2
            self.spawn_interval = max(0.4, 1.2 - self.current_wave * 0.05)

    def update(self, dt, enemies, enemy_images, enemy_laser_img, boss_image):
        """Spawn enemies as needed. Returns list of new enemies."""
        if not self.wave_active:
            return []

        new_enemies = []

        # Boss wave
        if self.boss_wave and not self.boss_spawned:
            boss = Boss(
                self.screen_w // 2, -80,
                boss_image, level=self.current_wave // 5
            )
            new_enemies.append(boss)
            self.boss_spawned = True
            return new_enemies

        # Regular wave spawning
        if self.enemies_to_spawn > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer = self.spawn_interval
                enemy = self._create_random_enemy(enemy_images)
                new_enemies.append(enemy)
                self.enemies_to_spawn -= 1

        # Check wave completion
        if self.enemies_to_spawn <= 0 and len(enemies) == 0:
            self.wave_complete = True
            self.wave_active = False

        return new_enemies

    def _create_random_enemy(self, enemy_images):
        """Create a random enemy based on current wave difficulty."""
        x = random.randint(50, self.screen_w - 50)
        y = random.randint(-100, -40)

        wave = self.current_wave
        # Higher waves introduce harder enemies
        roll = random.random()

        if wave >= 8 and roll < 0.2:
            return Enemy(x, y, Enemy.TANK, enemy_images["tank"],
                         health=150 + wave * 10, speed=60 + wave * 2,
                         score_value=250)
        elif wave >= 3 and roll < 0.5:
            return Enemy(x, y, Enemy.FAST, enemy_images["fast"],
                         health=40 + wave * 5, speed=150 + wave * 5,
                         score_value=150)
        else:
            return Enemy(x, y, Enemy.BASIC, enemy_images["basic"],
                         health=50 + wave * 8, speed=80 + wave * 3,
                         score_value=100)


class GameEngine:
    """Main game engine managing all game state."""

    # Game states
    STATE_TITLE = "title"
    STATE_PLAYING = "playing"
    STATE_PAUSED = "paused"
    STATE_GAME_OVER = "game_over"
    STATE_WAVE_TRANSITION = "wave_transition"

    def __init__(self, screen_width=800, screen_height=650):
        self.screen_w = screen_width
        self.screen_h = screen_height
        self.state = self.STATE_TITLE

        # Initialize Pygame
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("🎮 Gesture Fighter - Hand-Controlled Space Shooter")
        self.clock = pygame.time.Clock()

        # Generate assets
        print("[GameEngine] Generating assets...")
        self._create_assets()

        # Generate sounds
        self._create_sounds()

        # Game objects
        self.player = None
        self.player_bullets: List[Bullet] = []
        self.enemy_bullets: List[Bullet] = []
        self.enemies: List[Enemy] = []
        self.powerups: List[PowerUp] = []
        self.particles = ParticleSystem()

        # Managers
        self.wave_manager = WaveManager(screen_width, screen_height)
        self.ui = GameUI(screen_width, screen_height)

        # Star field
        self.star_layers = create_star_field(screen_width, screen_height)

        # Explosion animations
        self.explosion_frames = create_explosion_frames()
        self.active_explosions = []  # (x, y, frame_index, timer)

        # Wave transition
        self.wave_transition_timer = 0

        # Game stats
        self.game_time = 0
        self.enemies_killed = 0
        self.shots_fired = 0

        # Pause debounce
        self._pause_cooldown = 0

        # Bomb active
        self._bomb_active = False
        self._bomb_timer = 0
        self._bomb_radius = 0

    def _create_assets(self):
        """Generate all game graphic assets."""
        self.img_player = create_player_ship(64)
        self.img_player_shield = create_player_ship_shielded(64)
        self.img_enemy = {
            "basic": create_enemy_basic(48),
            "fast": create_enemy_fast(40),
            "tank": create_enemy_tank(56),
        }
        self.img_boss = create_boss(120)
        self.img_laser = create_laser((0, 255, 255), 20, 4)
        self.img_enemy_laser = create_enemy_laser()
        self.img_powerups = {
            "health": create_powerup("health"),
            "shield": create_powerup("shield"),
            "rapid": create_powerup("rapid"),
            "bomb": create_powerup("bomb"),
            "life": create_powerup("life"),
        }

    def _create_sounds(self):
        """Generate synthetic sound effects."""
        self.sounds = {}
        try:
            sample_rate = 22050

            # Laser sound
            self.sounds["shoot"] = self._synth_sound(
                sample_rate, 0.08,
                lambda t: math.sin(2 * math.pi * (800 - t * 5000) * t) * max(0, 1 - t * 12),
                volume=0.15
            )

            # Explosion
            self.sounds["explode"] = self._synth_sound(
                sample_rate, 0.3,
                lambda t: (random.random() * 2 - 1) * max(0, 1 - t * 3.5) * 0.5,
                volume=0.2
            )

            # Power-up
            self.sounds["powerup"] = self._synth_sound(
                sample_rate, 0.2,
                lambda t: math.sin(2 * math.pi * (400 + t * 2000) * t) * max(0, 1 - t * 5),
                volume=0.2
            )

            # Hit
            self.sounds["hit"] = self._synth_sound(
                sample_rate, 0.1,
                lambda t: math.sin(2 * math.pi * 200 * t) * max(0, 1 - t * 10) * 0.3 +
                          (random.random() * 2 - 1) * max(0, 1 - t * 10) * 0.2,
                volume=0.15
            )

            # Bomb
            self.sounds["bomb"] = self._synth_sound(
                sample_rate, 0.5,
                lambda t: (
                    math.sin(2 * math.pi * max(20, 100 - t * 200) * t) * 0.5 +
                    (random.random() * 2 - 1) * 0.5
                ) * max(0, 1 - t * 2),
                volume=0.3
            )

        except Exception as e:
            print(f"[GameEngine] Sound generation failed: {e}")
            self.sounds = {}

    def _synth_sound(self, sample_rate, duration, wave_func, volume=0.3):
        """Synthesize a sound effect."""
        import array
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            t = i / sample_rate
            sample = wave_func(t) * volume
            buf[i] = max(-32767, min(32767, int(sample * 32767)))
        sound = pygame.mixer.Sound(buffer=buf)
        return sound

    def play_sound(self, name):
        """Play a sound effect by name."""
        if name in self.sounds:
            self.sounds[name].play()

    def new_game(self):
        """Reset everything for a new game."""
        self.player = Player(
            self.screen_w // 2, self.screen_h - 100,
            self.img_player, self.img_player_shield
        )
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles = ParticleSystem()
        self.active_explosions.clear()
        self.wave_manager = WaveManager(self.screen_w, self.screen_h)
        self.game_time = 0
        self.enemies_killed = 0
        self.shots_fired = 0
        self._bomb_active = False

        self.state = self.STATE_WAVE_TRANSITION
        self.wave_transition_timer = 2.0
        self.wave_manager.start_next_wave()
        self.ui.add_notification("WAVE 1", (0, 255, 255), 2.0, "large")

    def handle_input(self, gesture_state, dt):
        """Process gesture and keyboard input."""
        if not self.player:
            return

        keys = pygame.key.get_pressed()

        # --- Keyboard fallback ---
        kb_dx = 0
        kb_dy = 0
        kb_speed = 400
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            kb_dx = -kb_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            kb_dx = kb_speed * dt
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            kb_dy = -kb_speed * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            kb_dy = kb_speed * dt

        kb_shoot = keys[pygame.K_j] or keys[pygame.K_SPACE]
        kb_shield = keys[pygame.K_k]
        kb_bomb = keys[pygame.K_l]

        # --- Target position ---
        if gesture_state and gesture_state.hand_detected:
            if gesture_state.is_open_palm or gesture_state.is_pointing:
                target_x = gesture_state.hand_x * self.screen_w
                target_y = gesture_state.hand_y * self.screen_h
            else:
                target_x = self.player.x + kb_dx
                target_y = self.player.y + kb_dy
        else:
            target_x = self.player.x + kb_dx
            target_y = self.player.y + kb_dy

        # --- Update player position ---
        self.player.update(target_x, target_y, self.screen_w, self.screen_h, dt)

        # --- Shooting ---
        should_shoot = kb_shoot
        if gesture_state and gesture_state.hand_detected and (gesture_state.is_fist or gesture_state.is_pointing):
            should_shoot = True

        if should_shoot:
            bullets = self.player.try_shoot(self.img_laser)
            if bullets:
                self.player_bullets.extend(bullets)
                self.shots_fired += len(bullets)
                self.play_sound("shoot")

        # --- Shield ---
        should_shield = kb_shield
        if gesture_state and gesture_state.hand_detected and gesture_state.is_peace:
            should_shield = True
        self.player.shield_active = should_shield and self.player.shield_energy > 0

        # --- Bomb ---
        should_bomb = kb_bomb

        if should_bomb and self.player.bomb_count > 0 and self.player.bomb_cooldown <= 0:
            self._activate_bomb()

        # --- Pause ---
        self._pause_cooldown -= dt
        should_pause = keys[pygame.K_p]
        if gesture_state and gesture_state.hand_detected and gesture_state.is_thumbs_up:
            should_pause = True

        if should_pause and self._pause_cooldown <= 0:
            self._pause_cooldown = 1.0
            if self.state == self.STATE_PLAYING:
                self.state = self.STATE_PAUSED
            elif self.state == self.STATE_PAUSED:
                self.state = self.STATE_PLAYING

    def _activate_bomb(self):
        """Activate bomb special attack."""
        self.player.bomb_count -= 1
        self.player.bomb_cooldown = 1.5
        self._bomb_active = True
        self._bomb_timer = 0.5
        self._bomb_radius = 0
        self.play_sound("bomb")
        self.ui.trigger_shake(15)
        self.particles.emit_bomb(self.player.x, self.player.y)

        # Damage all enemies
        for enemy in self.enemies:
            damage = 200
            enemy.take_damage(damage)
            if not enemy.alive:
                self.player.add_score(enemy.score_value)
                self.enemies_killed += 1
                self.particles.emit_explosion(enemy.x, enemy.y, count=25)
                self._spawn_explosion(enemy.x, enemy.y)
                self._try_spawn_powerup(enemy.x, enemy.y)

        # Clear enemy bullets
        self.enemy_bullets.clear()
        self.enemies = [e for e in self.enemies if e.alive]

    def update(self, dt, gesture_state=None):
        """Main update loop."""

        # --- Title screen ---
        if self.state == self.STATE_TITLE:
            self._update_stars(dt)
            hand_detected = gesture_state and gesture_state.hand_detected
            if hand_detected or pygame.key.get_pressed()[pygame.K_SPACE]:
                self.new_game()
            return

        # --- Game Over ---
        if self.state == self.STATE_GAME_OVER:
            self._update_stars(dt)
            self.particles.update(dt)
            hand_detected = gesture_state and gesture_state.hand_detected
            if hand_detected or pygame.key.get_pressed()[pygame.K_SPACE]:
                self.new_game()
            return

        # --- Paused ---
        if self.state == self.STATE_PAUSED:
            self.handle_input(gesture_state, dt)
            return

        # --- Wave transition ---
        if self.state == self.STATE_WAVE_TRANSITION:
            self._update_stars(dt)
            self.particles.update(dt)
            self.wave_transition_timer -= dt
            if self.wave_transition_timer <= 0:
                self.state = self.STATE_PLAYING
            self.handle_input(gesture_state, dt)
            return

        # --- Playing ---
        self.game_time += dt
        self.handle_input(gesture_state, dt)

        # Update stars
        self._update_stars(dt)

        # Engine particles
        if self.player:
            self.particles.emit_engine_trail(
                self.player.x,
                self.player.y + self.player.height // 2,
                intensity=1.5 if self.player.rapid_fire else 1.0
            )

        # Update bullets
        for b in self.player_bullets:
            b.update(dt)
        for b in self.enemy_bullets:
            b.update(dt)
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

        # Spawn enemies from wave manager
        new_enemies = self.wave_manager.update(
            dt, self.enemies, self.img_enemy,
            self.img_enemy_laser, self.img_boss
        )
        self.enemies.extend(new_enemies)
        for ne in new_enemies:
            if isinstance(ne, Boss):
                self.ui.add_notification("⚠ BOSS INCOMING ⚠", (255, 50, 50), 3.0, "large")
                self.ui.trigger_flash((255, 255, 255), 0.4)

        # Update enemies
        for enemy in self.enemies:
            enemy.update(dt, self.screen_w)
            result = enemy.try_shoot(self.img_enemy_laser)
            if result:
                if isinstance(result, list):
                    self.enemy_bullets.extend(result)
                else:
                    self.enemy_bullets.append(result)

        # Collision detection
        self._check_collisions()

        # Update power-ups
        for pu in self.powerups:
            pu.update(dt)
        self.powerups = [pu for pu in self.powerups if pu.alive]

        # Update particles
        self.particles.update(dt)

        # Update explosions
        self._update_explosions(dt)

        # Update bomb effect
        if self._bomb_active:
            self._bomb_timer -= dt
            self._bomb_radius += 800 * dt
            if self._bomb_timer <= 0:
                self._bomb_active = False

        # Update UI
        self.ui.update(dt)

        # Check wave completion
        if self.wave_manager.wave_complete:
            self.wave_manager.start_next_wave()
            self.state = self.STATE_WAVE_TRANSITION
            self.wave_transition_timer = 2.5
            wave_num = self.wave_manager.current_wave
            self.ui.add_notification(
                f"WAVE {wave_num}",
                (0, 255, 255), 2.0, "large"
            )
            if wave_num % 5 == 0:
                self.ui.add_notification("BOSS WAVE!", (255, 50, 50), 2.0, "medium")

        # Clean up dead enemies
        self.enemies = [e for e in self.enemies if e.alive]

    def _check_collisions(self):
        """Handle all collision detection."""
        if not self.player:
            return

        # Player bullets vs enemies
        for bullet in self.player_bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if bullet.rect.colliderect(enemy.rect):
                    bullet.alive = False
                    killed = enemy.take_damage(bullet.damage)
                    self.particles.emit_damage_sparks(bullet.x, bullet.y)
                    self.play_sound("hit")

                    if killed:
                        self.player.add_score(enemy.score_value)
                        self.enemies_killed += 1
                        self.particles.emit_explosion(enemy.x, enemy.y)
                        self._spawn_explosion(enemy.x, enemy.y)
                        self.play_sound("explode")
                        self._try_spawn_powerup(enemy.x, enemy.y)
                        self.ui.trigger_shake(5 if not isinstance(enemy, Boss) else 12)

                        if isinstance(enemy, Boss):
                            self.ui.add_notification(
                                "BOSS DEFEATED!", (255, 215, 0), 3.0, "large"
                            )
                    break

        # Enemy bullets vs player
        for bullet in self.enemy_bullets:
            if not bullet.alive:
                continue
            if bullet.rect.colliderect(self.player.rect):
                bullet.alive = False
                if self.player.shield_active:
                    self.particles.emit_shield_hit(bullet.x, bullet.y)
                    self.play_sound("hit")
                else:
                    died = self.player.take_damage(bullet.damage)
                    self.ui.trigger_shake(3)
                    self.ui.trigger_flash((255, 0, 0), 0.2)
                    self.play_sound("hit")
                    if died:
                        self._player_death()

        # Enemies vs player (collision)
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy.rect.colliderect(self.player.rect):
                if not self.player.shield_active:
                    died = self.player.take_damage(30)
                    self.ui.trigger_shake(8)
                    self.ui.trigger_flash((255, 0, 0), 0.3)
                    enemy.take_damage(enemy.max_health)  # Destroy enemy on contact
                    self.particles.emit_explosion(enemy.x, enemy.y)
                    self.play_sound("explode")
                    if died:
                        self._player_death()
                else:
                    self.particles.emit_shield_hit(
                        (self.player.x + enemy.x) // 2,
                        (self.player.y + enemy.y) // 2
                    )
                    enemy.take_damage(50)

        # Player vs power-ups
        for pu in self.powerups:
            if not pu.alive:
                continue
            if pu.rect.colliderect(self.player.rect):
                pu.apply(self.player)
                pu.alive = False
                self.particles.emit_powerup_collect(pu.x, pu.y)
                self.play_sound("powerup")
                names = {
                    "health": "+HEALTH",
                    "shield": "+SHIELD",
                    "rapid": "RAPID FIRE!",
                    "bomb": "+BOMB",
                    "life": "+1 LIFE!"
                }
                self.ui.add_notification(
                    names.get(pu.ptype, "POWER UP"),
                    (255, 255, 100), 1.5
                )

    def _player_death(self):
        """Handle player death."""
        self.player.lives -= 1
        self.player.combo = 0
        self.particles.emit_explosion(self.player.x, self.player.y, (0, 200, 255), 40, 300)
        self._spawn_explosion(self.player.x, self.player.y)
        self.play_sound("explode")
        self.ui.trigger_shake(12)

        if self.player.lives <= 0:
            self.state = self.STATE_GAME_OVER
            self.ui.add_notification("GAME OVER", (255, 50, 50), 5.0, "large")
        else:
            self.player.health = self.player.max_health
            self.player.invincible = True
            self.player.invincible_timer = 3.0
            self.player.shield_energy = self.player.shield_max
            self.ui.add_notification(f"Lives: {self.player.lives}", (255, 100, 100), 2.0)

    def _try_spawn_powerup(self, x, y):
        """Randomly spawn power-up at enemy death location."""
        if random.random() < 0.2:  # 20% chance
            ptypes = ["health", "health", "shield", "rapid", "bomb"]
            if random.random() < 0.05:
                ptypes.append("life")
            ptype = random.choice(ptypes)
            pu = PowerUp(x, y, ptype, self.img_powerups[ptype])
            self.powerups.append(pu)

    def _spawn_explosion(self, x, y):
        """Add explosion animation."""
        self.active_explosions.append({
            "x": x, "y": y,
            "frame": 0,
            "timer": 0,
            "frame_duration": 0.05,
        })

    def _update_explosions(self, dt):
        """Update explosion animations."""
        for exp in self.active_explosions:
            exp["timer"] += dt
            if exp["timer"] >= exp["frame_duration"]:
                exp["timer"] = 0
                exp["frame"] += 1
        self.active_explosions = [
            e for e in self.active_explosions
            if e["frame"] < len(self.explosion_frames)
        ]

    def _update_stars(self, dt):
        """Scroll star field."""
        for layer in self.star_layers:
            for star in layer:
                star["y"] += star["speed"] * 60 * dt
                if star["y"] > self.screen_h:
                    star["y"] = 0
                    star["x"] = random.randint(0, self.screen_w)

    def draw(self, camera_surface=None):
        """Render everything."""
        # Get shake offset
        shake_x, shake_y = self.ui.get_shake_offset()

        # Clear screen
        self.screen.fill((5, 5, 15))

        # Create game surface for shake effect
        game_surf = pygame.Surface((self.screen_w, self.screen_h))
        game_surf.fill((5, 5, 15))

        # Draw stars
        for layer in self.star_layers:
            for star in layer:
                brightness = star["brightness"]
                size = max(1, int(star["size"]))
                color = (brightness, brightness, min(255, brightness + min(40, brightness)))
                if size <= 1:
                    game_surf.set_at((int(star["x"]), int(star["y"])), color)
                else:
                    pygame.draw.circle(
                        game_surf, color,
                        (int(star["x"]), int(star["y"])), size
                    )

        # Draw based on state
        if self.state == self.STATE_TITLE:
            self.screen.blit(game_surf, (0, 0))
            self.ui.draw_title_screen(self.screen)
            if camera_surface:
                self.screen.blit(camera_surface, (self.screen_w - camera_surface.get_width() - 10, 10))
            return

        # Game objects
        # Power-ups
        for pu in self.powerups:
            pu.draw(game_surf)

        # Enemy bullets
        for b in self.enemy_bullets:
            b.draw(game_surf)

        # Player bullets
        for b in self.player_bullets:
            b.draw(game_surf)

        # Enemies
        for enemy in self.enemies:
            enemy.draw(game_surf)

        # Explosions
        for exp in self.active_explosions:
            if 0 <= exp["frame"] < len(self.explosion_frames):
                frame_img = self.explosion_frames[exp["frame"]]
                rect = frame_img.get_rect(center=(int(exp["x"]), int(exp["y"])))
                game_surf.blit(frame_img, rect)

        # Bomb flash
        if self._bomb_active:
            bomb_surf = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            alpha = int(150 * (self._bomb_timer / 0.5))
            pygame.draw.circle(
                bomb_surf, (255, 200, 50, min(200, alpha)),
                (int(self.player.x), int(self.player.y)),
                int(self._bomb_radius)
            )
            game_surf.blit(bomb_surf, (0, 0))

        # Particles
        self.particles.draw(game_surf)

        # Player
        if self.player and self.state != self.STATE_GAME_OVER:
            self.player.draw(game_surf)

        # Apply shake and blit
        self.screen.blit(game_surf, (shake_x, shake_y))

        # HUD (not affected by shake)
        if self.player:
            gesture = None
            self.ui.draw_hud(self.screen, self.player, self.wave_manager.current_wave)

        # Notifications
        self.ui.draw_notifications(self.screen)

        # State overlays
        if self.state == self.STATE_PAUSED:
            self.ui.draw_pause_screen(self.screen)
        elif self.state == self.STATE_GAME_OVER:
            self.ui.draw_game_over(
                self.screen, self.player.score,
                self.wave_manager.current_wave
            )

        # Camera feed overlay
        if camera_surface:
            # Semi-transparent background
            cam_bg = pygame.Surface(
                (camera_surface.get_width() + 4, camera_surface.get_height() + 4),
                pygame.SRCALPHA
            )
            cam_bg.fill((0, 0, 0, 150))
            cam_x = self.screen_w - camera_surface.get_width() - 12
            cam_y = self.screen_h - camera_surface.get_height() - 90
            self.screen.blit(cam_bg, (cam_x - 2, cam_y - 2))
            self.screen.blit(camera_surface, (cam_x, cam_y))