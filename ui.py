import pygame
import random

class GameUI:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font_large = pygame.font.SysFont("impact", 48)
        self.font_medium = pygame.font.SysFont("impact", 32)
        self.font_small = pygame.font.SysFont("arial", 20, bold=True)
        
        self.notifications = []
        self.shake_intensity = 0
        self.flash_timer = 0
        self.flash_color = (255, 255, 255)
        self.flash_duration = 0.1

    def update(self, dt):
        for notif in self.notifications:
            notif['timer'] -= dt
        self.notifications = [n for n in self.notifications if n['timer'] > 0]
        
        if self.shake_intensity > 0:
            self.shake_intensity -= 30 * dt
            if self.shake_intensity < 0:
                self.shake_intensity = 0
                
        if self.flash_timer > 0:
            self.flash_timer -= dt

    def add_notification(self, text, color, duration=2.0, size="medium"):
        self.notifications.append({
            'text': text,
            'color': color,
            'timer': duration,
            'max_timer': duration,
            'size': size
        })

    def trigger_shake(self, intensity):
        self.shake_intensity = intensity

    def trigger_flash(self, color=(255, 0, 0), duration=0.1):
        self.flash_color = color
        self.flash_timer = duration
        self.flash_duration = max(0.01, duration)

    def get_shake_offset(self):
        if self.shake_intensity > 0:
            dx = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            dy = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            return dx, dy
        return 0, 0

    def draw_hud(self, surface, player, wave):
        # Health bar
        pygame.draw.rect(surface, (100, 0, 0), (20, 20, 200, 20))
        health_width = max(0, int(200 * (player.health / player.max_health)))
        pygame.draw.rect(surface, (255, 50, 50), (20, 20, health_width, 20))
        pygame.draw.rect(surface, (255, 255, 255), (20, 20, 200, 20), 2)
        
        # Shield bar
        pygame.draw.rect(surface, (0, 0, 100), (20, 50, 200, 15))
        shield_width = max(0, int(200 * (player.shield_energy / player.shield_max)))
        pygame.draw.rect(surface, (50, 150, 255), (20, 50, shield_width, 15))
        pygame.draw.rect(surface, (255, 255, 255), (20, 50, 200, 15), 2)
        
        # Score and Lives
        score_text = self.font_medium.render(f"SCORE: {player.score}", True, (255, 255, 255))
        surface.blit(score_text, (self.screen_w - score_text.get_width() - 20, 20))
        
        lives_text = self.font_medium.render(f"LIVES: {player.lives}", True, (255, 100, 100))
        surface.blit(lives_text, (self.screen_w - lives_text.get_width() - 20, 60))
        
        wave_text = self.font_medium.render(f"WAVE: {wave}", True, (0, 255, 255))
        surface.blit(wave_text, (self.screen_w // 2 - wave_text.get_width() // 2, 20))
        
        # Bomb count
        bomb_text = self.font_small.render(f"BOMBS: {player.bomb_count}", True, (255, 200, 50))
        surface.blit(bomb_text, (20, 80))
        
        # Combo Multiplier
        if player.combo > 1:
            multiplier = min(player.combo, 10)
            combo_text = self.font_medium.render(f"COMBO x{multiplier}!", True, (255, 200, 0))
            surface.blit(combo_text, (self.screen_w - combo_text.get_width() - 20, 100))
            
            # Combo timer bar
            bar_w = 150
            ratio = max(0, player.combo_timer / player.combo_timeout)
            pygame.draw.rect(surface, (100, 100, 0), (self.screen_w - bar_w - 20, 140, bar_w, 5))
            pygame.draw.rect(surface, (255, 255, 0), (self.screen_w - bar_w - 20, 140, int(bar_w * ratio), 5))

        # Flash overlay
        if self.flash_timer > 0:
            flash_surf = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            alpha = max(0, min(255, int(150 * (self.flash_timer / self.flash_duration))))
            flash_surf.fill((*self.flash_color[:3], alpha))
            surface.blit(flash_surf, (0, 0))

    def draw_notifications(self, surface):
        y_offset = 120
        for notif in self.notifications:
            alpha = min(255, int(255 * (notif['timer'] / 0.5))) if notif['timer'] < 0.5 else 255
            font = self.font_large if notif['size'] == "large" else self.font_medium
            text_surface = font.render(notif['text'], True, notif['color'])
            text_surface.set_alpha(alpha)
            x = self.screen_w // 2 - text_surface.get_width() // 2
            surface.blit(text_surface, (x, y_offset))
            y_offset += text_surface.get_height() + 10

    def draw_title_screen(self, surface):
        title = self.font_large.render("GESTURE FIGHTER", True, (0, 255, 255))
        subtitle = self.font_medium.render("Show Hand or Press SPACE to Start", True, (255, 255, 255))
        
        surface.blit(title, (self.screen_w // 2 - title.get_width() // 2, self.screen_h // 4))
        surface.blit(subtitle, (self.screen_w // 2 - subtitle.get_width() // 2, self.screen_h // 4 + 60))

        rules = [
            "--- GESTURE CONTROLS ---",
            "Fist: Shoot",
            "Peace Sign: Shield",
            "Pointed Finger: Move AND Shoot",
            "Thumbs Up: Pause",
            "Open Palm: Track and move!",
            "",
            "Keyboard fallback: WASD to move, J/K/L/P for actions"
        ]
        
        y_offset = self.screen_h // 2
        for rule in rules:
            color = (0, 255, 100) if "GESTURE" in rule else (200, 200, 200)
            rule_text = self.font_small.render(rule, True, color)
            surface.blit(rule_text, (self.screen_w // 2 - rule_text.get_width() // 2, y_offset))
            y_offset += 30

    def draw_pause_screen(self, surface):
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        text = self.font_large.render("PAUSED", True, (255, 255, 255))
        surface.blit(text, (self.screen_w // 2 - text.get_width() // 2, self.screen_h // 2 - text.get_height() // 2))

    def draw_game_over(self, surface, score, wave):
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((50, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        title = self.font_large.render("GAME OVER", True, (255, 50, 50))
        score_text = self.font_medium.render(f"Final Score: {score}  |  Wave Reached: {wave}", True, (255, 255, 255))
        restart_text = self.font_small.render("Show Hand or Press SPACE to Restart", True, (200, 200, 200))
        
        surface.blit(title, (self.screen_w // 2 - title.get_width() // 2, self.screen_h // 3))
        surface.blit(score_text, (self.screen_w // 2 - score_text.get_width() // 2, self.screen_h // 2))
        surface.blit(restart_text, (self.screen_w // 2 - restart_text.get_width() // 2, self.screen_h // 2 + 50))

    def _draw_gesture_indicator(self, surface, gesture_state):
        if not gesture_state or not gesture_state.hand_detected:
            text = "No Hand Detected"
            color = (150, 150, 150)
        else:
            if gesture_state.is_fist:
                text = "FIST: Shoot"
                color = (255, 100, 100)
            elif gesture_state.is_peace:
                text = "PEACE: Shield"
                color = (100, 150, 255)
            elif gesture_state.is_pointing:
                text = "POINTED FINGER: Move & Shoot"
                color = (255, 150, 50)
            elif gesture_state.is_thumbs_up:
                text = "THUMBS UP: Pause"
                color = (100, 255, 100)
            elif gesture_state.is_open_palm:
                text = "OPEN PALM: Move"
                color = (100, 255, 255)
            else:
                text = "Hand Detected"
                color = (200, 200, 200)

        indicator_text = self.font_small.render(text, True, color)
        surface.blit(indicator_text, (20, self.screen_h - 40))
