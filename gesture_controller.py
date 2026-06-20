import cv2
import numpy as np
import os
import collections
import settings

from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.hand_landmarker import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarkerResult,
)
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
import mediapipe as mp

# Hand skeleton connections (21 landmarks)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]

# Debounce window: how many consecutive frames a gesture must persist before accepted
DEBOUNCE_FRAMES = 3

# ── Thresholds (Ratios relative to hand scale) ────────────────────────────────
THUMB_SPREAD_RATIO  = 0.55   # Ratio of thumb tip to index MCP vs hand scale
CLICK_PINCH_RATIO   = 0.30   # Ratio of thumb tip to index tip vs hand scale
UNDO_SPREAD_RATIO   = 0.40   # Ratio of index tip to middle tip vs hand scale
# ─────────────────────────────────────────────────────────────────────────────


class GestureController:
    def __init__(self):
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets", "hand_landmarker.task"
        )
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Hand landmarker model not found at: {model_path}\n"
                "Download it with:\n"
                "  python -c \"import urllib.request; urllib.request.urlretrieve("
                "'https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
                "hand_landmarker/float16/1/hand_landmarker.task', 'assets/hand_landmarker.task')\""
            )

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionTaskRunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=settings.MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=settings.MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=settings.MIN_TRACKING_CONFIDENCE,
        )
        self.detector = HandLandmarker.create_from_options(options)

        # Debounce queue: stores last N gesture type strings
        self._debounce_queue = collections.deque(maxlen=DEBOUNCE_FRAMES)
        self._committed_gesture = "STANDBY"

    # ── Core processing ──────────────────────────────────────────────────────

    def process_frame(self, frame_bgr):
        """Runs hand detection on a BGR frame. Returns HandLandmarkerResult."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        return self.detector.detect(mp_image)

    def get_landmarks(self, result, hand_idx=0):
        """Scales normalized landmarks to pixel coordinates. Returns list of (x,y)."""
        if not result.hand_landmarks or hand_idx >= len(result.hand_landmarks):
            return []
        lm_list = []
        for lm in result.hand_landmarks[hand_idx]:
            cx = int(lm.x * settings.WIDTH)
            cy = int(lm.y * settings.HEIGHT)
            lm_list.append((cx, cy))
        return lm_list

    # ── Finger state ─────────────────────────────────────────────────────────

    def get_fingers_up(self, result, hand_idx=0):
        """
        Returns [Thumb, Index, Middle, Ring, Pinky] — 1=extended, 0=folded.
        NOTE: Thumb uses y-axis only as a rough guide — do NOT rely on it for
        gesture logic (use thumb_extended() instead for accuracy).
        """
        if not result.hand_landmarks or hand_idx >= len(result.hand_landmarks):
            return [0, 0, 0, 0, 0]
        lm = result.hand_landmarks[hand_idx]
        fingers = []
        # Thumb rough estimate (unreliable for pointing poses — use thumb_extended instead)
        fingers.append(1 if lm[4].y < lm[2].y else 0)
        # Index: tip(8) above PIP(6)
        fingers.append(1 if lm[8].y < lm[6].y else 0)
        # Middle: tip(12) above PIP(10)
        fingers.append(1 if lm[12].y < lm[10].y else 0)
        # Ring: tip(16) above PIP(14)
        fingers.append(1 if lm[16].y < lm[14].y else 0)
        # Pinky: tip(20) above PIP(18)
        fingers.append(1 if lm[20].y < lm[18].y else 0)
        return fingers

    # ── Skeleton rendering ───────────────────────────────────────────────────

    def draw_skeleton(self, frame, lm_list):
        """Draws the hand skeleton directly onto frame using pixel coords."""
        if not lm_list or len(lm_list) < 21:
            return
        for start, end in HAND_CONNECTIONS:
            cv2.line(frame, lm_list[start], lm_list[end], (200, 200, 200), 2, cv2.LINE_AA)
        for idx, pt in enumerate(lm_list):
            if idx in (4, 8, 12, 16, 20):
                cv2.circle(frame, pt, 7, (239, 68, 68), cv2.FILLED, cv2.LINE_AA)
                cv2.circle(frame, pt, 7, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, pt, 4, (255, 105, 180), cv2.FILLED, cv2.LINE_AA)

    # ── Gesture classification ────────────────────────────────────────────────

    def _raw_gesture(self, lm_list, fingers):
        """
        Classifies the instantaneous hand pose. Called every frame.
        Returns a dict {type, cursor, distance}.

        KEY DESIGN DECISIONS (fixing the pencil/thumb/pinch bugs):
          • Normalizes all distances with respect to a dynamic hand scale
            (wrist-to-middle MCP distance) to make tracking independent of depth.
          • SELECT / CLICK is triggered with open hand (Index, Middle, Ring, Pinky UP).
            Clicking is a thumb-to-index pinch, which has no conflict with drawing or V-sign.
          • DRAW is 1 finger (Index UP, all others down). Ignored/tucked thumb.
          • SIZE_CONTROL is 1 finger + Thumb spread open.
          • UNDO is Index + Middle UP (V-sign) + spread apart.
          • REDO is Index + Middle + Ring UP.
          • SCREENSHOT is Index + Pinky UP (Rock-on).
          • LOCK_TOGGLE is Pinky UP only.
        """
        if not lm_list or len(lm_list) < 21:
            return {"type": "STANDBY", "cursor": (0, 0), "distance": 0.0}

        thumb_tip   = lm_list[4]
        index_tip   = lm_list[8]
        index_mcp   = lm_list[5]   # base of index finger (knuckle)
        middle_tip  = lm_list[12]

        thumb_to_index_tip  = np.hypot(thumb_tip[0] - index_tip[0],  thumb_tip[1] - index_tip[1])
        thumb_to_index_base = np.hypot(thumb_tip[0] - index_mcp[0],  thumb_tip[1] - index_mcp[1])
        index_to_middle     = np.hypot(index_tip[0] - middle_tip[0], index_tip[1] - middle_tip[1])

        # Dynamic hand scale to normalize depth
        hand_scale = np.hypot(lm_list[0][0] - lm_list[9][0], lm_list[0][1] - lm_list[9][1])
        hand_scale = max(1.0, hand_scale)

        # Normalized features
        thumb_spread = (thumb_to_index_base / hand_scale) > THUMB_SPREAD_RATIO
        is_pinched   = (thumb_to_index_tip / hand_scale) < CLICK_PINCH_RATIO
        undo_spread  = (index_to_middle / hand_scale) > UNDO_SPREAD_RATIO

        cursor   = index_tip
        idx_up   = fingers[1] == 1
        mid_up   = fingers[2] == 1
        ring_up  = fingers[3] == 1
        pinky_up = fingers[4] == 1

        # ─── Priority 1: GESTURE LOCK — only pinky raised ────────────────────
        if pinky_up and not idx_up and not mid_up and not ring_up:
            return {"type": "LOCK_TOGGLE", "cursor": cursor, "distance": 0.0}

        # ─── Priority 2: SCREENSHOT — index + pinky up, middle + ring down (Rock-on) ───
        if idx_up and pinky_up and not mid_up and not ring_up:
            return {"type": "SCREENSHOT", "cursor": cursor, "distance": 0.0}

        # ─── Priority 3: REDO — index + middle + ring up, pinky down ─────────
        if idx_up and mid_up and ring_up and not pinky_up:
            return {"type": "REDO", "cursor": cursor, "distance": 0.0}

        # ─── Priority 4: UNDO — index + middle up, ring + pinky down + spread ─
        if idx_up and mid_up and not ring_up and not pinky_up and undo_spread:
            return {"type": "UNDO", "cursor": cursor, "distance": index_to_middle}

        # ─── Priority 5: SELECT / CLICK — open hand (index, middle, ring, pinky all up) ───
        if idx_up and mid_up and ring_up and pinky_up:
            sel_cursor = ((index_tip[0] + middle_tip[0]) // 2, (index_tip[1] + middle_tip[1]) // 2)
            if is_pinched:
                return {"type": "CLICK", "cursor": sel_cursor, "distance": thumb_to_index_tip / hand_scale}
            return {"type": "SELECT", "cursor": sel_cursor, "distance": thumb_to_index_tip / hand_scale}

        # ─── Priority 6: SIZE CONTROL — index up + thumb physically spread ───
        if idx_up and not mid_up and not ring_up and not pinky_up and thumb_spread:
            return {"type": "SIZE_CONTROL", "cursor": cursor, "distance": thumb_to_index_tip / hand_scale}

        # ─── Priority 7: DRAW — index up, middle down, ring down, pinky down ──
        if idx_up and not mid_up and not ring_up and not pinky_up:
            return {"type": "DRAW", "cursor": cursor, "distance": 0.0}

        return {"type": "STANDBY", "cursor": cursor, "distance": 0.0}

    def get_gesture_state(self, lm_list, fingers):
        """
        Debounced gesture classification.
        A gesture must appear in DEBOUNCE_FRAMES consecutive frames before it
        becomes the committed gesture. This prevents single-frame flickers from
        interrupting drawing strokes.

        Exempts transient CLICK actions so pinch interaction registers instantly.
        Returns dict {type, cursor, distance}.
        """
        raw = self._raw_gesture(lm_list, fingers)
        raw_type = raw["type"]

        if raw_type == "CLICK":
            # Return CLICK instantly without overriding/persisting in the debounce queue
            # so selection returns smoothly when pinch is released.
            return {
                "type": "CLICK",
                "cursor": raw["cursor"],
                "distance": raw["distance"],
            }

        self._debounce_queue.append(raw_type)

        # Only change committed gesture if all recent frames agree
        if len(self._debounce_queue) == DEBOUNCE_FRAMES:
            if all(g == raw_type for g in self._debounce_queue):
                self._committed_gesture = raw_type

        # Always return the latest cursor/distance with the committed type
        return {
            "type": self._committed_gesture,
            "cursor": raw["cursor"],
            "distance": raw["distance"],
        }
