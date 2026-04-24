"""
Hand gesture detection using MediaPipe.
Detects: open palm, fist, peace sign, pointing, thumb position.
"""

import cv2
import mediapipe as mp
import numpy as np
import math
from dataclasses import dataclass, field
from typing import Optional, Tuple
import time


@dataclass
class GestureState:
    """Represents the current state of detected hand gestures."""
    hand_detected: bool = False
    # Normalized position (0-1 range)
    hand_x: float = 0.5
    hand_y: float = 0.5
    # Gestures
    is_fist: bool = False          # SHOOT
    is_peace: bool = False         # SHIELD
    is_open_palm: bool = False     # SPECIAL ATTACK / BOMB
    is_pointing: bool = False      # (future use)
    is_thumbs_up: bool = False     # PAUSE
    # Confidence / smoothing
    gesture_confidence: float = 0.0
    # Raw landmarks for advanced use
    landmarks: list = field(default_factory=list)


class HandTracker:
    """
    Tracks hand position and gestures using MediaPipe Hands.
    Designed for real-time game control.
    """

    # MediaPipe hand landmark indices
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

    def __init__(
        self,
        camera_index: int = 0,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.6,
        smoothing_factor: float = 0.35,
        flip_horizontal: bool = True,
    ):
        self.camera_index = camera_index
        self.flip_horizontal = flip_horizontal
        self.smoothing_factor = smoothing_factor

        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

        # Camera
        self.cap = None
        self.frame_width = 640
        self.frame_height = 480

        # State
        self.current_state = GestureState()
        self._prev_x = 0.5
        self._prev_y = 0.5
        self._gesture_history = []
        self._gesture_history_size = 5

        # Timing for gesture debounce
        self._last_gesture_change = 0
        self._gesture_cooldown = 0.1  # seconds

        # Debug
        self.debug_frame = None
        self.show_debug = True

    def start(self) -> bool:
        """Initialize camera capture."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"[HandTracker] ERROR: Cannot open camera {self.camera_index}")
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[HandTracker] Camera started: {actual_w}x{actual_h}")
        return True

    def stop(self):
        """Release camera and resources."""
        if self.cap:
            self.cap.release()
        self.hands.close()
        cv2.destroyAllWindows()
        print("[HandTracker] Stopped.")

    def update(self) -> GestureState:
        """
        Capture frame, detect hand, classify gesture.
        Returns current GestureState.
        """
        if not self.cap or not self.cap.isOpened():
            return self.current_state

        ret, frame = self.cap.read()
        if not ret:
            return self.current_state

        if self.flip_horizontal:
            frame = cv2.flip(frame, 1)

        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        state = GestureState()

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            state.hand_detected = True

            # Extract landmark positions
            h, w, _ = frame.shape
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append((lm.x, lm.y, lm.z))
            state.landmarks = landmarks

            # Get hand center (palm)
            palm_x, palm_y = self._get_palm_center(landmarks)

            # Smooth position
            smoothed_x = self._prev_x + self.smoothing_factor * (palm_x - self._prev_x)
            smoothed_y = self._prev_y + self.smoothing_factor * (palm_y - self._prev_y)
            self._prev_x = smoothed_x
            self._prev_y = smoothed_y
            state.hand_x = smoothed_x
            state.hand_y = smoothed_y

            # Classify gesture
            finger_states = self._get_finger_states(landmarks)
            self._classify_gesture(state, finger_states, landmarks)

            # Debug visualization
            if self.show_debug:
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
                self._draw_debug_info(frame, state, finger_states)
        else:
            state.hand_detected = False
            state.hand_x = self._prev_x
            state.hand_y = self._prev_y

        self.current_state = state

        if self.show_debug:
            self.debug_frame = frame

        return state

    def _get_palm_center(self, landmarks) -> Tuple[float, float]:
        """Calculate palm center from wrist and MCP joints."""
        indices = [
            self.WRIST,
            self.INDEX_MCP,
            self.MIDDLE_MCP,
            self.RING_MCP,
            self.PINKY_MCP,
        ]
        xs = [landmarks[i][0] for i in indices]
        ys = [landmarks[i][1] for i in indices]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def _get_finger_states(self, landmarks) -> dict:
        """
        Determine which fingers are extended.
        Returns dict with finger names and bool (True = extended).
        """
        def is_finger_extended(tip_idx, pip_idx, mcp_idx):
            """Check if fingertip is above (lower y) the PIP joint."""
            return landmarks[tip_idx][1] < landmarks[pip_idx][1]

        def is_thumb_extended(landmarks_list):
            """Thumb uses x-axis comparison (depends on hand orientation)."""
            thumb_tip = landmarks_list[self.THUMB_TIP]
            thumb_ip = landmarks_list[self.THUMB_IP]
            thumb_mcp = landmarks_list[self.THUMB_MCP]

            # Check if thumb is spread out from palm
            index_mcp = landmarks_list[self.INDEX_MCP]
            dist_thumb_index = math.sqrt(
                (thumb_tip[0] - index_mcp[0]) ** 2 +
                (thumb_tip[1] - index_mcp[1]) ** 2
            )
            return dist_thumb_index > 0.08

        fingers = {
            "thumb": is_thumb_extended(landmarks),
            "index": is_finger_extended(self.INDEX_TIP, self.INDEX_PIP, self.INDEX_MCP),
            "middle": is_finger_extended(self.MIDDLE_TIP, self.MIDDLE_PIP, self.MIDDLE_MCP),
            "ring": is_finger_extended(self.RING_TIP, self.RING_PIP, self.RING_MCP),
            "pinky": is_finger_extended(self.PINKY_TIP, self.PINKY_PIP, self.PINKY_MCP),
        }
        return fingers

    def _classify_gesture(self, state: GestureState, fingers: dict, landmarks):
        """Classify the hand gesture based on finger states."""
        extended_count = sum([
            fingers["index"], fingers["middle"],
            fingers["ring"], fingers["pinky"]
        ])

        # FIST: No fingers extended (shoot)
        if extended_count == 0 and not fingers["thumb"]:
            state.is_fist = True
            state.gesture_confidence = 0.9

        # PEACE / V-SIGN: Index + Middle extended, others closed (shield)
        elif (fingers["index"] and fingers["middle"] and
              not fingers["ring"] and not fingers["pinky"]):
            state.is_peace = True
            state.gesture_confidence = 0.85

        # POINTING: Only index extended
        elif (fingers["index"] and not fingers["middle"] and
              not fingers["ring"] and not fingers["pinky"]):
            state.is_pointing = True
            state.gesture_confidence = 0.8

        # OPEN PALM: All fingers extended (special attack)
        elif extended_count >= 3 and fingers["thumb"]:
            state.is_open_palm = True
            state.gesture_confidence = 0.9

        # THUMBS UP: Only thumb extended
        elif (fingers["thumb"] and extended_count == 0):
            state.is_thumbs_up = True
            state.gesture_confidence = 0.75

        # Default: FIST-ish (for triggering shooting)
        elif extended_count <= 1:
            state.is_fist = True
            state.gesture_confidence = 0.6

    def _draw_debug_info(self, frame, state: GestureState, fingers: dict):
        """Draw debug overlay on camera frame."""
        h, w = frame.shape[:2]

        # Gesture label
        gesture_name = "NONE"
        color = (200, 200, 200)
        if state.is_fist:
            gesture_name = "FIST (SHOOT)"
            color = (0, 0, 255)
        elif state.is_peace:
            gesture_name = "PEACE (SHIELD)"
            color = (255, 200, 0)
        elif state.is_open_palm:
            gesture_name = "OPEN PALM (BOMB)"
            color = (0, 165, 255)
        elif state.is_pointing:
            gesture_name = "POINTING"
            color = (0, 255, 0)
        elif state.is_thumbs_up:
            gesture_name = "THUMBS UP (PAUSE)"
            color = (255, 255, 0)

        # Draw gesture text
        cv2.putText(frame, f"Gesture: {gesture_name}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"Confidence: {state.gesture_confidence:.0%}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Draw crosshair at hand position
        cx = int(state.hand_x * w)
        cy = int(state.hand_y * h)
        cv2.circle(frame, (cx, cy), 15, color, 2)
        cv2.line(frame, (cx - 20, cy), (cx + 20, cy), color, 1)
        cv2.line(frame, (cx, cy - 20), (cx, cy + 20), color, 1)

        # Finger states
        finger_text = " ".join([
            f"T:{'↑' if fingers['thumb'] else '↓'}",
            f"I:{'↑' if fingers['index'] else '↓'}",
            f"M:{'↑' if fingers['middle'] else '↓'}",
            f"R:{'↑' if fingers['ring'] else '↓'}",
            f"P:{'↑' if fingers['pinky'] else '↓'}",
        ])
        cv2.putText(frame, finger_text, (10, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    def get_debug_surface(self, target_width=320) -> Optional['pygame.Surface']:
        """Convert debug frame to pygame surface for in-game overlay."""
        if self.debug_frame is None:
            return None
        import pygame

        frame = self.debug_frame
        h, w = frame.shape[:2]
        scale = target_width / w
        new_h = int(h * scale)
        frame_small = cv2.resize(frame, (target_width, new_h))
        frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        surface = pygame.surfarray.make_surface(np.transpose(frame_rgb, (1, 0, 2)))
        return surface