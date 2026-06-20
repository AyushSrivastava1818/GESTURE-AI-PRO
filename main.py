#!/usr/bin/env python3
"""
GestureAI Pro - Intelligent Gesture Controlled Whiteboard
---------------------------------------------------------
A modular, high-performance portfolio application.
"""

import cv2
import numpy as np
import time
import os
import sys

# Import local modules
import settings
from gesture_controller import GestureController
from drawing_engine import DrawingEngine
from shape_detector import ShapeDetector
from ui_manager import UIManager
from history_manager import HistoryManager

class GestureAIProApp:
    def __init__(self):
        self.workspace_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Initialize components
        self.gesture_controller = GestureController()
        self.drawing_engine = DrawingEngine()
        self.shape_detector = ShapeDetector()
        self.ui_manager = UIManager()
        self.history_manager = HistoryManager(self.workspace_dir)
        
        # Theme configuration
        self.theme_mode = "dark"  # Default theme
        self.theme = settings.THEME_DARK
        self.drawing_engine.set_theme(self.theme)

        # Application state variables
        self.gesture_locked = False
        self.last_gesture_time = time.time()
        self.last_auto_save_time = time.time()

        # Stroke-end debounce: how many consecutive non-DRAW frames before
        # we commit the stroke. Prevents single-frame flickers from cutting strokes.
        self._non_draw_frames = 0
        self._NON_DRAW_THRESHOLD = 4  # frames
        
        # Action cooldown trackers
        self.cooldowns = {
            "undo": 0.0,
            "redo": 0.0,
            "theme": 0.0,
            "lock": 0.0,
            "save": 0.0,
            "screenshot": 0.0,
            "click": 0.0
        }

    def toggle_theme(self):
        """Toggles between Dark Mode and Light Mode."""
        if self.theme_mode == "dark":
            self.theme_mode = "light"
            self.theme = settings.THEME_LIGHT
        else:
            self.theme_mode = "dark"
            self.theme = settings.THEME_DARK
            
        self.drawing_engine.set_theme(self.theme)
        self.ui_manager.add_notification(f"Theme: {self.theme_mode.upper()} MODE", "info")

    def toggle_lock(self):
        """Toggles the gesture locking system."""
        self.gesture_locked = not self.gesture_locked
        status = "LOCKED" if self.gesture_locked else "UNLOCKED"
        alert_type = "warning" if self.gesture_locked else "success"
        self.ui_manager.add_notification(f"Gesture Control: {status}", alert_type)

    def trigger_cooldown(self, action_name, duration=settings.GESTURE_COOLDOWN):
        """Sets a timer block on a specific gesture action."""
        self.cooldowns[action_name] = time.time() + duration

    def is_in_cooldown(self, action_name):
        """Checks if a specific gesture action is currently on cooldown."""
        return time.time() < self.cooldowns[action_name]

    def blend_canvas_with_frame(self, frame, canvas):
        """
        Blends the vector-drawn canvas onto the live camera stream frame.
        Identifies canvas strokes by computing pixel difference against the theme background color.
        """
        bg_color = np.array(self.theme["canvas_bg"], dtype=np.uint8)
        
        # Calculate pixel difference from the canvas background color
        diff = cv2.absdiff(canvas, bg_color)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Binary threshold: any pixel deviating from bg color is drawing stroke
        _, mask = cv2.threshold(diff_gray, 5, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        # Mask original frame and crop canvas strokes
        frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        canvas_fg = cv2.bitwise_and(canvas, canvas, mask=mask)
        
        # Composite frame
        return cv2.add(frame_bg, canvas_fg)

    def run(self):
        print("[INFO] Launching GestureAI Pro...")
        print("[INFO] Connecting to camera feed...")
        
        # Initialize webcam capture
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] Webcam capture device could not be opened.")
            print("[INFO] Please verify webcam connection and security permissions.")
            return

        # Force resolution parameters
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.HEIGHT)

        cv2.namedWindow(settings.WINDOW_NAME)
        self.ui_manager.add_notification("Welcome to GestureAI Pro!", "success")

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("[WARNING] Empty camera frame captured. Retrying...")
                continue

            # Mirror frame for intuitive interactive drawing orientation
            frame = cv2.flip(frame, 1)

            # Process frame for hand tracking landmarks (new Tasks API takes BGR directly)
            results = self.gesture_controller.process_frame(frame)

            # Setup drawing canvas layer
            canvas = self.drawing_engine.get_canvas(settings.WIDTH, settings.HEIGHT)
            
            # Initial states
            gesture_type = "STANDBY"
            cursor_pos = (0, 0)
            fingers = [0, 0, 0, 0, 0]
            hand_detected = False
            distance = 0.0

            if results.hand_landmarks:  # new Tasks API uses .hand_landmarks
                hand_detected = True
                
                # Extract pixel-space landmark list
                lm_list = self.gesture_controller.get_landmarks(results, hand_idx=0)
                
                # Draw skeleton using pixel coords
                self.gesture_controller.draw_skeleton(frame, lm_list)
                
                # Identify raised fingers
                fingers = self.gesture_controller.get_fingers_up(results, hand_idx=0)
                
                # Classify hand gestures
                gesture_data = self.gesture_controller.get_gesture_state(lm_list, fingers)
                gesture_type = gesture_data["type"]
                cursor_pos = gesture_data["cursor"]
                distance = gesture_data["distance"]

            # --- STATE MACHINE PROCESSING ---

            # A. Process GESTURE LOCK (Active in all states, locks everything else)
            if gesture_type == "LOCK_TOGGLE":
                if not self.is_in_cooldown("lock"):
                    self.toggle_lock()
                    self.trigger_cooldown("lock", settings.GESTURE_COOLDOWN)
                    # Stop active drawing on lock
                    if self.drawing_engine.active_stroke is not None:
                        self.drawing_engine.active_stroke = None

            # B. If Locked, block all other interactions
            if self.gesture_locked:
                gesture_type = "LOCKED"
                if self.drawing_engine.active_stroke is not None:
                    self.drawing_engine.active_stroke = None
            
            # C. Active State Actions (Only when Unlocked)
            elif hand_detected:
                # 1. SCREENSHOT Gesture (Index + Thumb + Pinky)
                if gesture_type == "SCREENSHOT":
                    if not self.is_in_cooldown("screenshot"):
                        # Capture full current screen composite
                        screenshot_canvas = self.drawing_engine.get_canvas(settings.WIDTH, settings.HEIGHT)
                        screenshot_frame = self.blend_canvas_with_frame(frame.copy(), screenshot_canvas)
                        self.ui_manager.draw_toolbar(screenshot_frame, self.drawing_engine.current_tool, self.drawing_engine.current_color, self.theme)
                        self.ui_manager.draw_status_dashboard(screenshot_frame, "SCREENSHOT", self.drawing_engine.current_tool, self.drawing_engine.current_thickness, self.drawing_engine.current_color, self.theme, self.history_manager.get_session_stats())
                        self.ui_manager.draw_fps(screenshot_frame, self.theme)
                        
                        saved_path = self.history_manager.save_canvas(screenshot_frame)
                        if saved_path:
                            self.ui_manager.add_notification(f"Screenshot Saved: {os.path.basename(saved_path)}", "success")
                        self.trigger_cooldown("screenshot", settings.GESTURE_COOLDOWN)

                # 2. UNDO Gesture (Index + Middle)
                elif gesture_type == "UNDO":
                    if not self.is_in_cooldown("undo"):
                        if self.drawing_engine.undo():
                            self.history_manager.record_undo()
                            self.ui_manager.add_notification("Undo Successful", "success")
                        else:
                            self.ui_manager.add_notification("Nothing to Undo", "info")
                        self.trigger_cooldown("undo", settings.GESTURE_COOLDOWN)

                # 3. REDO Gesture (Index + Middle + Ring)
                elif gesture_type == "REDO":
                    if not self.is_in_cooldown("redo"):
                        if self.drawing_engine.redo():
                            self.history_manager.record_redo()
                            self.ui_manager.add_notification("Redo Successful", "success")
                        else:
                            self.ui_manager.add_notification("Nothing to Redo", "info")
                        self.trigger_cooldown("redo", settings.GESTURE_COOLDOWN)

                # 4. SIZE CONTROL Gesture (Thumb + Index)
                elif gesture_type == "SIZE_CONTROL":
                    # End active stroke if drawing was in progress
                    if self.drawing_engine.active_stroke is not None:
                        self.drawing_engine.end_current_stroke(self.shape_detector)
                        
                    # Map ratio (0.25 to 1.0) to brush size range (2px to 100px)
                    mapped_size = int(np.interp(distance, [0.25, 1.0], [2, 100]))
                    self.drawing_engine.set_thickness(mapped_size)

                # 5. DRAWING Mode (Index finger alone)
                elif gesture_type == "DRAW":
                    self.drawing_engine.add_point(cursor_pos[0], cursor_pos[1])

                # 6. SELECTION & CLICK hover actions (Open hand / pinch click)
                elif gesture_type in ["SELECT", "CLICK"]:
                    # End active stroke if drawing was in progress
                    if self.drawing_engine.active_stroke is not None:
                        shape_name = self.drawing_engine.end_current_stroke(self.shape_detector)
                        self.history_manager.record_stroke()
                        if shape_name:
                            self.history_manager.record_shape()
                            self.ui_manager.add_notification(f"AI: {shape_name} Detected", "success")
                            
                    if gesture_type == "CLICK" and not self.is_in_cooldown("click"):
                        click_action = self.ui_manager.handle_click(cursor_pos)
                        if click_action:
                            action_type = click_action["type"]
                            val = click_action["val"]

                            if action_type == "preset":
                                self.drawing_engine.set_preset(val)
                                self.ui_manager.add_notification(f"Tool Set: {val.upper()}", "info")
                            
                            elif action_type == "color":
                                self.drawing_engine.set_color(val)
                                self.ui_manager.add_notification("Color Palette Updated", "info")
                                
                            elif action_type == "action":
                                if val == "undo":
                                    if self.drawing_engine.undo():
                                        self.history_manager.record_undo()
                                        self.ui_manager.add_notification("Undo Successful", "success")
                                    else:
                                        self.ui_manager.add_notification("Nothing to Undo", "info")
                                elif val == "redo":
                                    if self.drawing_engine.redo():
                                        self.history_manager.record_redo()
                                        self.ui_manager.add_notification("Redo Successful", "success")
                                    else:
                                        self.ui_manager.add_notification("Nothing to Redo", "info")
                                elif val == "clear":
                                    self.drawing_engine.clear()
                                    self.ui_manager.add_notification("Canvas Cleared", "warning")
                                elif val == "theme":
                                    self.toggle_theme()
                                elif val == "lock":
                                    self.toggle_lock()
                                elif val == "save":
                                    # Save vector drawing composite
                                    save_canvas_target = self.drawing_engine.get_canvas(settings.WIDTH, settings.HEIGHT)
                                    saved_path = self.history_manager.save_canvas(save_canvas_target)
                                    if saved_path:
                                        self.ui_manager.add_notification("Drawing Exported Successfully", "success")
                        self.trigger_cooldown("click", settings.CLICK_COOLDOWN)

            # D. Debounced stroke termination — only end the stroke after
            # _NON_DRAW_THRESHOLD consecutive non-DRAW frames to avoid flicker.
            if gesture_type == "DRAW":
                self._non_draw_frames = 0
            else:
                if self.drawing_engine.active_stroke is not None:
                    self._non_draw_frames += 1
                    if self._non_draw_frames >= self._NON_DRAW_THRESHOLD:
                        self._non_draw_frames = 0
                        shape_name = self.drawing_engine.end_current_stroke(self.shape_detector)
                        self.history_manager.record_stroke()
                        if shape_name:
                            self.history_manager.record_shape()
                            self.ui_manager.add_notification(f"AI: {shape_name} Detected", "success")
                else:
                    self._non_draw_frames = 0

            # --- CANVAS COMPOSITION & RENDER PIPELINE ---

            # 1. Update drawing canvas layer to blend with live feed
            composite_frame = self.blend_canvas_with_frame(frame, canvas)

            # 2. Draw HUD UI elements on the composite frame
            # Highlight presets based on toolbar config
            active_preset = self.drawing_engine.current_tool.capitalize()
            self.ui_manager.draw_toolbar(
                composite_frame, 
                self.drawing_engine.current_tool, 
                self.drawing_engine.current_color, 
                self.theme
            )
            
            # Status and Stats Panel
            session_stats = self.history_manager.get_session_stats()
            self.ui_manager.draw_status_dashboard(
                composite_frame, 
                gesture_type, 
                self.drawing_engine.current_tool, 
                self.drawing_engine.current_thickness, 
                self.drawing_engine.current_color, 
                self.theme, 
                session_stats
            )
            
            # Recent saves panel listing
            self.ui_manager.draw_recent_saves_panel(
                composite_frame, 
                self.history_manager.get_recent_drawings(), 
                self.theme
            )

            # Cursor draw in Select/Click modes
            if gesture_type in ["SELECT", "CLICK"]:
                self.ui_manager.draw_cursor(composite_frame, cursor_pos, gesture_type, self.theme)

            # Brush size indicator in Size Control mode
            if gesture_type == "SIZE_CONTROL":
                self.ui_manager.draw_brush_size_preview(
                    composite_frame, 
                    cursor_pos, 
                    self.drawing_engine.current_thickness, 
                    self.drawing_engine.current_color, 
                    self.theme
                )

            # Toast Notifications overlay
            self.ui_manager.draw_notifications(composite_frame, self.theme)

            # Lock Screen Modal Overlay
            if self.gesture_locked:
                self.ui_manager.draw_gesture_lock(composite_frame, self.theme)

            # FPS counter
            self.ui_manager.draw_fps(composite_frame, self.theme)

            # --- BACKGROUND TASKS & EVENTS ---

            # Auto-save interval check
            now_time = time.time()
            if now_time - self.last_auto_save_time >= settings.AUTO_SAVE_INTERVAL:
                auto_save_canvas = self.drawing_engine.get_canvas(settings.WIDTH, settings.HEIGHT)
                self.history_manager.save_canvas(auto_save_canvas, is_auto_save=True)
                self.ui_manager.add_notification("Background Auto-Saved", "info")
                self.last_auto_save_time = now_time

            # Render display
            cv2.imshow(settings.WINDOW_NAME, composite_frame)

            # --- KEYBOARD INTERRUPTS & FALLBACKS ---
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC to quit
                break
            elif key == ord('s') or key == ord('S'):  # Manual save key
                save_canvas_target = self.drawing_engine.get_canvas(settings.WIDTH, settings.HEIGHT)
                saved_path = self.history_manager.save_canvas(save_canvas_target)
                if saved_path:
                    self.ui_manager.add_notification("Drawing Exported", "success")
            elif key == ord('c') or key == ord('C'):  # Clear key
                self.drawing_engine.clear()
                self.ui_manager.add_notification("Canvas Cleared", "warning")
            elif key == ord('t') or key == ord('T'):  # Theme toggle key
                self.toggle_theme()
            elif key == ord('l') or key == ord('L'):  # Lock toggle key
                self.toggle_lock()

        # Exit routine: Release resources and save final session drawing
        cap.release()
        cv2.destroyAllWindows()
        
        # Save final session whiteboard draw
        final_canvas = self.drawing_engine.get_canvas(settings.WIDTH, settings.HEIGHT)
        final_path = self.history_manager.save_canvas(final_canvas)
        print(f"[SUCCESS] GestureAI Pro closed. Session drawing exported to: {final_path}")

if __name__ == "__main__":
    app = GestureAIProApp()
    app.run()
