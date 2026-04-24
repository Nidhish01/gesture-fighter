"""
🎮 Gesture Fighter - Hand-Controlled Space Shooter
===================================================

Control a spaceship with your hand gestures!

GESTURES:
  ✊ Fist       → Shoot
  ✌ Peace Sign → Shield
  🖐 Open Palm  → Bomb
  👍 Thumbs Up  → Pause
  ✋ Move Hand  → Move Ship

KEYBOARD FALLBACK:
  WASD / Arrows → Move
  J / Space     → Shoot
  K             → Shield
  L             → Bomb
  P             → Pause
  ESC           → Quit
  F1            → Toggle camera overlay
  F2            → Toggle debug view

Author: Gesture Game Demo
"""

import pygame
import sys
import time
import argparse
from hand_tracker import HandTracker, GestureState
from game_engine import GameEngine


def main():
    parser = argparse.ArgumentParser(description="Gesture-Controlled Space Shooter")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--no-camera", action="store_true", help="Run without camera (keyboard only)")
    parser.add_argument("--width", type=int, default=800, help="Window width")
    parser.add_argument("--height", type=int, default=650, help="Window height")
    parser.add_argument("--fps", type=int, default=60, help="Target FPS")
    parser.add_argument("--cam-width", type=int, default=240, help="Camera overlay width")
    args = parser.parse_args()

    # Initialize game engine
    print("=" * 50)
    print("GESTURE FIGHTER - Space Shooter")
    print("=" * 50)

    game = GameEngine(args.width, args.height)

    # Initialize hand tracker
    tracker = None
    if not args.no_camera:
        print("\n[Main] Initializing hand tracker...")
        tracker = HandTracker(
            camera_index=args.camera,
            detection_confidence=0.7,
            tracking_confidence=0.6,
            smoothing_factor=0.35,
        )
        if not tracker.start():
            print("[Main] WARNING: Camera not available. Using keyboard controls.")
            tracker = None
        else:
            print("[Main] Hand tracking active! Show your hand to play.")
    else:
        print("[Main] Running in keyboard-only mode.")

    print("\n[Main] Starting game loop...")
    print("Controls:")
    print("  Hand gestures or WASD + J/K/L")
    print("  F1: Toggle camera | F2: Toggle debug | ESC: Quit")
    print()

    # Main game loop
    show_camera = True
    gesture_state = GestureState()
    running = True
    last_time = time.time()

    try:
        while running:
            # Calculate delta time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            dt = min(dt, 0.05)  # Cap at 50ms to prevent physics issues

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F1:
                        show_camera = not show_camera
                        print(f"[Main] Camera overlay: {'ON' if show_camera else 'OFF'}")
                    elif event.key == pygame.K_F2:
                        if tracker:
                            tracker.show_debug = not tracker.show_debug
                            print(f"[Main] Debug view: {'ON' if tracker.show_debug else 'OFF'}")

            # Update hand tracking
            if tracker:
                gesture_state = tracker.update()
            else:
                gesture_state = GestureState()

            # Update game
            game.update(dt, gesture_state)

            # Get camera surface for overlay
            camera_surface = None
            if tracker and show_camera:
                camera_surface = tracker.get_debug_surface(target_width=args.cam_width)

            # Draw
            game.draw(camera_surface)

            # Draw gesture state on HUD
            if game.player and game.state not in [game.STATE_TITLE, game.STATE_GAME_OVER]:
                game.ui._draw_gesture_indicator(game.screen, gesture_state)

            # FPS counter
            fps = game.clock.get_fps()
            fps_text = pygame.font.SysFont("Arial", 14).render(
                f"FPS: {fps:.0f}", True, (100, 100, 100)
            )
            game.screen.blit(fps_text, (5, args.height - 20))

            pygame.display.flip()
            game.clock.tick(args.fps)

    except KeyboardInterrupt:
        print("\n[Main] Interrupted by user.")
    finally:
        if tracker:
            tracker.stop()
        pygame.quit()
        print("[Main] Game ended. Thanks for playing!")


if __name__ == "__main__":
    main()