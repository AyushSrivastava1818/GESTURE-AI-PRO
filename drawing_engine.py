import cv2
import numpy as np
import settings

class Stroke:
    def __init__(self, color, thickness, tool, points=None, shape_type=None, shape_data=None):
        self.points = points if points is not None else []
        self.color = color
        self.thickness = thickness
        self.tool = tool  # 'pencil', 'marker', 'highlighter', 'eraser'
        self.shape_type = shape_type  # None, 'line', 'circle', 'rectangle', 'triangle'
        self.shape_data = shape_data  # Dictionary containing geometry parameters

class DrawingEngine:
    def __init__(self):
        self.strokes = []      # List of completed Stroke objects
        self.redo_stack = []   # Redo stack containing Stroke objects
        self.active_stroke = None
        
        # Default state
        self.current_color = settings.COLORS["RED"]
        self.current_thickness = settings.BRUSH_PRESETS["Pencil"]["thickness"]
        self.current_tool = "pencil"
        self.current_theme = settings.THEME_DARK
        
        # Smoothing window for active coordinates
        self.smoothing_history = []

    def set_theme(self, theme):
        """Sets the active theme (Dark Mode / Light Mode)."""
        self.current_theme = theme

    def set_color(self, color):
        """Sets the drawing color."""
        self.current_color = color
        # Automatically switch back to pencil/marker if eraser was active
        if self.current_tool == "eraser":
            self.current_tool = "pencil"
            self.current_thickness = settings.BRUSH_PRESETS["Pencil"]["thickness"]

    def set_preset(self, preset_name):
        """Applies a brush preset (Pencil, Marker, Highlighter, Eraser)."""
        if preset_name in settings.BRUSH_PRESETS:
            preset = settings.BRUSH_PRESETS[preset_name]
            self.current_tool = preset_name.lower()
            self.current_thickness = preset["thickness"]

    def adjust_thickness(self, delta):
        """Adjusts the brush thickness within bounds."""
        self.current_thickness = max(2, min(150, self.current_thickness + delta))

    def set_thickness(self, val):
        """Directly sets the brush thickness within bounds."""
        self.current_thickness = max(2, min(150, int(val)))

    def start_new_stroke(self):
        """Starts tracking a new stroke."""
        self.active_stroke = Stroke(
            color=self.current_color,
            thickness=self.current_thickness,
            tool=self.current_tool
        )
        self.smoothing_history = []

    def add_point(self, x, y):
        """
        Adds a raw coordinate, smooths it using a moving average filter,
        and interpolates intermediate points if the cursor moved rapidly.
        """
        if self.active_stroke is None:
            self.start_new_stroke()

        # 1. Apply Moving Average Smoothing Filter
        self.smoothing_history.append((x, y))
        if len(self.smoothing_history) > settings.SMOOTHING_WINDOW:
            self.smoothing_history.pop(0)
            
        avg_x = int(sum(pt[0] for pt in self.smoothing_history) / len(self.smoothing_history))
        avg_y = int(sum(pt[1] for pt in self.smoothing_history) / len(self.smoothing_history))
        smoothed_pt = (avg_x, avg_y)

        # 2. Interpolate intermediate points for fast cursor movements
        if len(self.active_stroke.points) > 0:
            last_pt = self.active_stroke.points[-1]
            dist = np.hypot(smoothed_pt[0] - last_pt[0], smoothed_pt[1] - last_pt[1])
            
            # If distance exceeds threshold, interpolate linearly
            if dist > 8:
                steps = int(dist / 6)
                for i in range(1, steps):
                    interp_x = int(last_pt[0] + (smoothed_pt[0] - last_pt[0]) * (i / steps))
                    interp_y = int(last_pt[1] + (smoothed_pt[1] - last_pt[1]) * (i / steps))
                    self.active_stroke.points.append((interp_x, interp_y))

        self.active_stroke.points.append(smoothed_pt)

    def end_current_stroke(self, shape_detector=None):
        """
        Finalizes the current stroke.
        Optionally runs shape recognition to replace hand-drawn contours with beautified geometry.
        """
        if self.active_stroke is None or len(self.active_stroke.points) < 2:
            self.active_stroke = None
            return None

        # Process shape beautification if shape detector is provided and tool is NOT eraser
        shape_detected_name = None
        if shape_detector is not None and self.active_stroke.tool != "eraser":
            shape_type, shape_data = shape_detector.detect_shape(self.active_stroke.points)
            if shape_type is not None:
                self.active_stroke.shape_type = shape_type
                self.active_stroke.shape_data = shape_data
                shape_detected_name = shape_type.upper()

        self.strokes.append(self.active_stroke)
        self.redo_stack.clear()  # Clear redo stack on new action
        self.active_stroke = None
        return shape_detected_name

    def undo(self):
        """Undoes the last stroke. Returns True if successful."""
        if self.strokes:
            undone_stroke = self.strokes.pop()
            self.redo_stack.append(undone_stroke)
            return True
        return False

    def redo(self):
        """Redoes the last undone stroke. Returns True if successful."""
        if self.redo_stack:
            redone_stroke = self.redo_stack.pop()
            self.strokes.append(redone_stroke)
            return True
        return False

    def clear(self):
        """Resets the entire canvas."""
        self.strokes.clear()
        self.redo_stack.clear()
        self.active_stroke = None

    def _render_stroke(self, canvas, stroke):
        """
        Draws a single stroke (pencil, marker, eraser, or beautified shape) directly
        onto canvas with full opacity. Highlighter strokes are blended separately.
        """
        if not stroke.points and stroke.shape_type is None:
            return
        if not stroke.points:
            return

        color = stroke.color
        thickness = stroke.thickness

        # Eraser paints the background color
        if stroke.tool == "eraser":
            color = self.current_theme["canvas_bg"]

        # --- Draw beautified geometry ---
        if stroke.shape_type is not None:
            s = stroke.shape_data
            if stroke.shape_type == "line":
                cv2.line(canvas, s["start"], s["end"], color, thickness, cv2.LINE_AA)
            elif stroke.shape_type == "circle":
                cv2.circle(canvas, s["center"], s["radius"], color, thickness, cv2.LINE_AA)
            elif stroke.shape_type == "rectangle":
                cv2.rectangle(canvas, s["top_left"], s["bottom_right"], color, thickness, cv2.LINE_AA)
            elif stroke.shape_type == "triangle":
                pts = np.array(s["vertices"], np.int32).reshape((-1, 1, 2))
                cv2.polylines(canvas, [pts], True, color, thickness, cv2.LINE_AA)
            return

        # --- Draw freehand points ---
        pts = stroke.points
        for i in range(len(pts) - 1):
            cv2.line(canvas, pts[i], pts[i + 1], color, thickness, cv2.LINE_AA)

    def get_canvas(self, width, height):
        """
        Renders all vector strokes onto the canvas layer.
        - Pencil / Marker / Eraser are drawn directly (full opacity).
        - Highlighter strokes are alpha-blended per-stroke so only THEY are
          transparent — other tools are completely unaffected.
        """
        canvas = np.full((height, width, 3), self.current_theme["canvas_bg"], dtype=np.uint8)

        all_strokes = list(self.strokes)
        if self.active_stroke is not None:
            all_strokes.append(self.active_stroke)

        for stroke in all_strokes:
            if not stroke.points:
                continue

            if stroke.tool == "highlighter":
                # Per-stroke alpha blend: draw to a copy then blend back
                overlay = canvas.copy()
                self._render_stroke(overlay, stroke)
                alpha = settings.BRUSH_PRESETS["Highlighter"]["alpha"]
                cv2.addWeighted(overlay, alpha, canvas, 1.0 - alpha, 0, canvas)
            else:
                # Full-opacity draw directly on canvas
                self._render_stroke(canvas, stroke)

        return canvas
