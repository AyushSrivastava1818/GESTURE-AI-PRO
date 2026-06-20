import cv2
import numpy as np
import time
import settings
import os

class UIManager:
    def __init__(self):
        # Configure button definitions
        self.buttons = [
            # Brush Presets (x1, x2, y1, y2, type, value, label)
            {"x1": 15, "x2": 95, "y1": 20, "y2": 80, "type": "preset", "val": "Pencil", "label": "PENCIL"},
            {"x1": 105, "x2": 185, "y1": 20, "y2": 80, "type": "preset", "val": "Marker", "label": "MARKER"},
            {"x1": 195, "x2": 295, "y1": 20, "y2": 80, "type": "preset", "val": "Highlighter", "label": "HIGHLIGHT"},
            {"x1": 305, "x2": 385, "y1": 20, "y2": 80, "type": "preset", "val": "Eraser", "label": "ERASER"},

            # Colors
            {"x1": 415, "x2": 450, "y1": 32, "y2": 67, "type": "color", "val": settings.COLORS["RED"], "label": "RED"},
            {"x1": 460, "x2": 495, "y1": 32, "y2": 67, "type": "color", "val": settings.COLORS["GREEN"], "label": "GREEN"},
            {"x1": 505, "x2": 540, "y1": 32, "y2": 67, "type": "color", "val": settings.COLORS["BLUE"], "label": "BLUE"},
            {"x1": 550, "x2": 585, "y1": 32, "y2": 67, "type": "color", "val": settings.COLORS["YELLOW"], "label": "YELLOW"},
            {"x1": 595, "x2": 630, "y1": 32, "y2": 67, "type": "color", "val": settings.COLORS["PURPLE"], "label": "PURPLE"},
            {"x1": 640, "x2": 675, "y1": 32, "y2": 67, "type": "color", "val": settings.COLORS["ORANGE"], "label": "ORANGE"},

            # Actions
            {"x1": 705, "x2": 775, "y1": 20, "y2": 80, "type": "action", "val": "undo", "label": "UNDO"},
            {"x1": 785, "x2": 855, "y1": 20, "y2": 80, "type": "action", "val": "redo", "label": "REDO"},
            {"x1": 865, "x2": 935, "y1": 20, "y2": 80, "type": "action", "val": "clear", "label": "CLEAR"},
            {"x1": 945, "x2": 1025, "y1": 20, "y2": 80, "type": "action", "val": "theme", "label": "THEME"},
            {"x1": 1035, "x2": 1115, "y1": 20, "y2": 80, "type": "action", "val": "lock", "label": "LOCK"},
            {"x1": 1125, "x2": 1205, "y1": 20, "y2": 80, "type": "action", "val": "save", "label": "SAVE"},
        ]

        self.notifications = []  # List of dicts: {"text": str, "expiry": float, "color": tuple, "start_time": float}
        self.fps_start_time = time.time()
        self.fps_counter = 0
        self.fps = 0.0

    def add_notification(self, text, alert_type="info"):
        """Adds a message notification with transition metadata."""
        now = time.time()
        color = settings.THEME_DARK["accent"]
        if alert_type == "success":
            color = settings.THEME_DARK["success"]
        elif alert_type == "warning":
            color = (59, 59, 239)  # Premium Coral Red BGR
            
        self.notifications.append({
            "text": text,
            "expiry": now + 2.5,
            "start_time": now,
            "color": color
        })
        # Limit to last 3 active notifications
        if len(self.notifications) > 3:
            self.notifications.pop(0)

    def draw_rounded_rect(self, img, pt1, pt2, color, thickness=1, radius=6):
        """Draws a rounded rectangle using OpenCV shapes."""
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Draw edges
        cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness, cv2.LINE_AA)

        # Draw corners
        cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness, cv2.LINE_AA)
        cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness, cv2.LINE_AA)
        cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness, cv2.LINE_AA)
        cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness, cv2.LINE_AA)

    def draw_rounded_filled_rect(self, img, pt1, pt2, color, radius=6):
        """Draws a filled rounded rectangle."""
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Center block
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, cv2.FILLED)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, cv2.FILLED)
        
        # Corners
        cv2.circle(img, (x1 + radius, y1 + radius), radius, color, cv2.FILLED)
        cv2.circle(img, (x2 - radius, y1 + radius), radius, color, cv2.FILLED)
        cv2.circle(img, (x2 - radius, y2 - radius), radius, color, cv2.FILLED)
        cv2.circle(img, (x1 + radius, y2 - radius), radius, color, cv2.FILLED)

    def draw_toolbar(self, frame, active_tool, active_color, theme):
        """Renders the glassmorphic top header toolbar and its action/palette buttons."""
        # 1. Glassmorphism background overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (settings.WIDTH, settings.HEADER_HEIGHT), theme["ui_bg"], cv2.FILLED)
        cv2.addWeighted(overlay, settings.HEADER_ALPHA, frame, 1 - settings.HEADER_ALPHA, 0, frame)

        # 2. Border separator
        cv2.line(frame, (0, settings.HEADER_HEIGHT), (settings.WIDTH, settings.HEADER_HEIGHT), theme["ui_border"], 2)

        # 3. Draw buttons
        for btn in self.buttons:
            x1, y1, x2, y2 = btn["x1"], btn["y1"], btn["x2"], btn["y2"]
            btn_type = btn["type"]
            val = btn["val"]
            label = btn["label"]

            # Compute button active state
            is_active = False
            if btn_type == "preset" and active_tool.lower() == val.lower():
                is_active = True
            elif btn_type == "color" and active_tool.lower() != "eraser" and np.array_equal(active_color, val):
                is_active = True

            # Draw coloring/border styling
            if btn_type == "color":
                # Draw color circle
                radius = (y2 - y1) // 2
                cx, cy = x1 + radius, y1 + radius
                cv2.circle(frame, (cx, cy), radius, val, cv2.FILLED, cv2.LINE_AA)
                
                # Active glow border
                if is_active:
                    cv2.circle(frame, (cx, cy), radius + 4, theme["text_primary"], 2, cv2.LINE_AA)
                else:
                    cv2.circle(frame, (cx, cy), radius, theme["ui_border"], 1, cv2.LINE_AA)
            
            else:
                # Text/Command button rounded container
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.4
                thickness = 1
                text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                text_x = x1 + (x2 - x1 - text_size[0]) // 2
                text_y = y1 + (y2 - y1 + text_size[1]) // 2

                if is_active:
                    # Filled background for active buttons
                    self.draw_rounded_filled_rect(frame, (x1, y1), (x2, y2), theme["accent"], radius=8)
                    cv2.putText(frame, label, (text_x, text_y), font, font_scale, theme["canvas_bg"], thickness + 1, cv2.LINE_AA)
                else:
                    # Outlined container for inactive buttons
                    self.draw_rounded_rect(frame, (x1, y1), (x2, y2), theme["ui_border"], thickness=2, radius=8)
                    # Add micro-fill overlay for inactive buttons
                    btn_overlay = frame.copy()
                    self.draw_rounded_filled_rect(btn_overlay, (x1, y1), (x2, y2), theme["ui_border"], radius=8)
                    cv2.addWeighted(btn_overlay, 0.15, frame, 0.85, 0, frame)
                    
                    cv2.putText(frame, label, (text_x, text_y), font, font_scale, theme["text_primary"], thickness, cv2.LINE_AA)

    def draw_status_dashboard(self, frame, mode_text, active_tool, active_thickness, active_color, theme, stats):
        """Renders the status panel overlay in the bottom left containing statistics."""
        panel_w, panel_h = 320, 160
        panel_x, panel_y = 20, settings.HEIGHT - panel_h - 20

        # Glass background
        overlay = frame.copy()
        self.draw_rounded_filled_rect(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), theme["ui_bg"], radius=12)
        cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)

        # Border outline
        self.draw_rounded_rect(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), theme["ui_border"], thickness=2, radius=12)

        # Text elements
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Mode
        mode_color = theme["accent"]
        if mode_text == "DRAWING":
            mode_color = theme["success"]
        elif mode_text.startswith("LOCK"):
            mode_color = (59, 59, 239) # Coral Red BGR
            
        cv2.putText(frame, f"MODE: {mode_text}", (panel_x + 20, panel_y + 30), font, 0.6, mode_color, 2, cv2.LINE_AA)
        
        # Tool and Size info
        cv2.putText(frame, f"TOOL: {active_tool.upper()} ({active_thickness}px)", (panel_x + 20, panel_y + 60), font, 0.45, theme["text_primary"], 1, cv2.LINE_AA)

        # Color dot representation
        cv2.putText(frame, "COLOR:", (panel_x + 20, panel_y + 85), font, 0.45, theme["text_primary"], 1, cv2.LINE_AA)
        if active_tool.lower() == "eraser":
            cv2.putText(frame, "N/A", (panel_x + 85, panel_y + 85), font, 0.45, theme["text_secondary"], 1, cv2.LINE_AA)
        else:
            cv2.circle(frame, (panel_x + 90, panel_y + 81), 6, active_color, cv2.FILLED, cv2.LINE_AA)
            cv2.circle(frame, (panel_x + 90, panel_y + 81), 7, theme["ui_border"], 1, cv2.LINE_AA)

        # Divider line
        cv2.line(frame, (panel_x + 20, panel_y + 105), (panel_x + panel_w - 20, panel_y + 105), theme["ui_border"], 1)

        # Stats logs (Time, strokes, shape, undo)
        stats_line1 = f"Time: {stats['time_spent']}  |  Strokes: {stats['strokes']}"
        stats_line2 = f"Shapes AI: {stats['shapes']}  |  Undos: {stats['undos']}"
        cv2.putText(frame, stats_line1, (panel_x + 20, panel_y + 125), font, 0.4, theme["text_secondary"], 1, cv2.LINE_AA)
        cv2.putText(frame, stats_line2, (panel_x + 20, panel_y + 145), font, 0.4, theme["text_secondary"], 1, cv2.LINE_AA)

    def draw_recent_saves_panel(self, frame, recent_drawings, theme):
        """Renders the recent drawings log history in the bottom right corner."""
        if not recent_drawings:
            return

        panel_w, panel_h = 240, 140
        panel_x, panel_y = settings.WIDTH - panel_w - 20, settings.HEIGHT - panel_h - 20

        # Glass background
        overlay = frame.copy()
        self.draw_rounded_filled_rect(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), theme["ui_bg"], radius=12)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Outline
        self.draw_rounded_rect(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), theme["ui_border"], thickness=2, radius=12)

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "RECENT SAVES", (panel_x + 15, panel_y + 25), font, 0.5, theme["accent"], 2, cv2.LINE_AA)
        cv2.line(frame, (panel_x + 15, panel_y + 35), (panel_x + panel_w - 15, panel_y + 35), theme["ui_border"], 1)

        # Draw filename listing
        for idx, path in enumerate(recent_drawings[:3]):
            filename = os.path.basename(path)
            # Remove prefix and extension to show a shorter timestamp format
            disp_name = filename.replace("drawing_", "").replace(".png", "")
            # Convert timestamp format YYYY_MM_DD_HHMMSS to human readable
            parts = disp_name.split("_")
            if len(parts) >= 4:
                disp_name = f"Save {parts[0]}/{parts[1]}/{parts[2]} {parts[3][:2]}:{parts[3][2:4]}"
            
            y_offset = panel_y + 60 + idx * 25
            
            # Circle bullet point
            cv2.circle(frame, (panel_x + 25, y_offset - 4), 3, theme["text_secondary"], cv2.FILLED, cv2.LINE_AA)
            cv2.putText(frame, disp_name, (panel_x + 38, y_offset), font, 0.4, theme["text_primary"], 1, cv2.LINE_AA)

    def draw_notifications(self, frame, theme):
        """Draws animated alert notification toasts stacked vertically with smooth fade."""
        now = time.time()
        self.notifications = [n for n in self.notifications if n["expiry"] > now]

        for idx, notify in enumerate(self.notifications):
            text = notify["text"]
            start_time = notify["start_time"]
            expiry = notify["expiry"]
            color = notify["color"]

            # Calculate opacity based on fade timings
            total_duration = expiry - start_time
            elapsed = now - start_time
            remaining = expiry - now

            alpha = 1.0
            if elapsed < 0.3: # Fade in
                alpha = elapsed / 0.3
            elif remaining < 0.4: # Fade out
                alpha = remaining / 0.4

            alpha = max(0.0, min(1.0, alpha))

            # Position coordinate stacking
            toast_w, toast_h = 320, 42
            toast_x = settings.WIDTH // 2 - toast_w // 2
            toast_y = settings.HEADER_HEIGHT + 20 + idx * 52

            # Render overlay with calculated alpha transparency
            overlay = frame.copy()
            # Draw dark toast container background
            self.draw_rounded_filled_rect(overlay, (toast_x, toast_y), (toast_x + toast_w, toast_y + toast_h), theme["ui_bg"], radius=8)
            # Draw color-coded indicator edge
            cv2.rectangle(overlay, (toast_x, toast_y), (toast_x + 8, toast_y + toast_h), color, cv2.FILLED)
            # Draw container outline
            self.draw_rounded_rect(overlay, (toast_x, toast_y), (toast_x + toast_w, toast_y + toast_h), theme["ui_border"], thickness=1, radius=8)

            # Draw toast text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45
            thickness = 1
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = toast_x + 20
            text_y = toast_y + (toast_h + text_size[1]) // 2

            cv2.putText(overlay, text, (text_x, text_y), font, font_scale, theme["text_primary"], thickness + 1, cv2.LINE_AA)

            # Apply alphablending
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def draw_gesture_lock(self, frame, theme):
        """Displays locked screen modal overlay when gesture controller is paused."""
        # Semi-transparent screen overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (settings.WIDTH, settings.HEIGHT), theme["canvas_bg"], cv2.FILLED)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Draw lock panel in center
        panel_w, panel_h = 500, 140
        panel_x = settings.WIDTH // 2 - panel_w // 2
        panel_y = settings.HEIGHT // 2 - panel_h // 2

        self.draw_rounded_filled_rect(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), theme["ui_bg"], radius=16)
        self.draw_rounded_rect(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (59, 59, 239), thickness=2, radius=16)

        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Draw glowing warning text
        txt_lock = "GESTURE CONTROL LOCKED"
        sz_lock = cv2.getTextSize(txt_lock, font, 0.7, 2)[0]
        cv2.putText(frame, txt_lock, (settings.WIDTH // 2 - sz_lock[0] // 2, panel_y + 50), font, 0.7, (59, 59, 239), 2, cv2.LINE_AA)

        txt_unlock = "RAISE PINKY FINGER ALONE TO UNLOCK"
        sz_unlock = cv2.getTextSize(txt_unlock, font, 0.45, 1)[0]
        cv2.putText(frame, txt_unlock, (settings.WIDTH // 2 - sz_unlock[0] // 2, panel_y + 90), font, 0.45, theme["text_primary"], 1, cv2.LINE_AA)

    def draw_cursor(self, frame, cursor_pos, gesture_type, theme):
        """Renders a sleek double ring cursor overlay at pointer coordinates."""
        cx, cy = cursor_pos
        # Validate coordinate limits
        if cx <= 0 or cy <= 0 or cx >= settings.WIDTH or cy >= settings.HEIGHT:
            return

        # Cursor color changes based on gesture action
        cursor_color = theme["accent"]
        if gesture_type == "CLICK":
            cursor_color = theme["success"]
            # Visual click expansion pulse
            cv2.circle(frame, (cx, cy), 18, cursor_color, 2, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), 4, cursor_color, cv2.FILLED, cv2.LINE_AA)
        else:
            # Selection mode default cursor styling
            cv2.circle(frame, (cx, cy), 12, cursor_color, 2, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), 4, cursor_color, cv2.FILLED, cv2.LINE_AA)

    def draw_brush_size_preview(self, frame, cursor_pos, size, active_color, theme):
        """Renders brush thickness preview bubble when size control mode is active."""
        cx, cy = cursor_pos
        radius = size // 2
        # Overlay ring
        cv2.circle(frame, (cx, cy), max(5, radius), active_color, 2, cv2.LINE_AA)
        # Size caption bubble
        cap_y = max(settings.HEADER_HEIGHT + 20, cy - radius - 20)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"{size}px"
        text_size = cv2.getTextSize(text, font, 0.4, 1)[0]
        
        # Glass bubble background
        bg_x1, bg_y1 = cx - text_size[0] // 2 - 8, cap_y - text_size[1] - 8
        bg_x2, bg_y2 = cx + text_size[0] // 2 + 8, cap_y + 4
        
        overlay = frame.copy()
        self.draw_rounded_filled_rect(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), theme["ui_bg"], radius=4)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        self.draw_rounded_rect(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), theme["ui_border"], thickness=1, radius=4)
        
        cv2.putText(frame, text, (cx - text_size[0] // 2, cap_y - 2), font, 0.4, theme["text_primary"], 1, cv2.LINE_AA)

    def draw_fps(self, frame, theme):
        """Updates FPS counter and overlays it on the frame."""
        self.fps_counter += 1
        now = time.time()
        elapsed = now - self.fps_start_time
        
        if elapsed >= 1.0:
            self.fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = now

        fps_text = f"FPS: {self.fps:.1f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        # Draw top-right just below header boundary
        cv2.putText(frame, fps_text, (settings.WIDTH - 110, settings.HEADER_HEIGHT + 30), font, 0.45, theme["text_secondary"], 1, cv2.LINE_AA)

    def handle_click(self, cursor_pos):
        """
        Translates a hover coordinate click into toolbar button action mapping.
        Returns:
            dict containing click match data (e.g. type, val) or None.
        """
        cx, cy = cursor_pos
        if cy > settings.HEADER_HEIGHT:
            return None

        for btn in self.buttons:
            if btn["x1"] <= cx <= btn["x2"] and btn["y1"] <= cy <= btn["y2"]:
                return {"type": btn["type"], "val": btn["val"]}
        return None
