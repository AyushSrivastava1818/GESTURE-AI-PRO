"""
Settings and Configurations for GestureAI Pro.
"""

# Window configuration
WIDTH = 1280
HEIGHT = 720
WINDOW_NAME = "GestureAI Pro - Intelligent Whiteboard"

# Theme definitions (BGR format)
THEME_DARK = {
    "canvas_bg": (18, 18, 18),        # Deep Dark Slate
    "ui_bg": (28, 28, 30),            # Elevate UI Dark Gray
    "ui_border": (54, 54, 56),        # Zinc-700
    "text_primary": (242, 242, 247),  # Zinc-100 (Off-white)
    "text_secondary": (142, 142, 147),# Zinc-400 (Muted gray)
    "accent": (96, 165, 250),         # Neon Blue-500
    "success": (74, 222, 128),        # Emerald-400
}

THEME_LIGHT = {
    "canvas_bg": (250, 250, 250),     # Clean Studio White
    "ui_bg": (242, 242, 247),         # Zinc-100
    "ui_border": (209, 209, 214),     # Zinc-300
    "text_primary": (28, 28, 30),     # Zinc-900 (Near black)
    "text_secondary": (99, 99, 102),  # Zinc-500
    "accent": (29, 78, 216),          # Royal Blue-700
    "success": (22, 163, 74),         # Forest Green
}

# Color palette (BGR format)
COLORS = {
    "RED": (59, 59, 239),       # Premium Coral Red
    "GREEN": (74, 222, 128),    # Emerald Mint Green
    "BLUE": (249, 115, 22),     # Sapphire Royal Blue
    "YELLOW": (34, 211, 238),   # Cyber Cyan / Bright Yellow
    "PURPLE": (219, 39, 119),   # Neon Purple
    "ORANGE": (20, 110, 235),   # Sunset Orange
}

# Brush presets
BRUSH_PRESETS = {
    "Pencil": {
        "thickness": 4,
        "alpha": 1.0,
        "label": "Pencil"
    },
    "Marker": {
        "thickness": 12,
        "alpha": 1.0,
        "label": "Marker"
    },
    "Highlighter": {
        "thickness": 28,
        "alpha": 0.4, # Semi-transparent
        "label": "Highlighter"
    },
    "Eraser": {
        "thickness": 60,
        "alpha": 1.0,
        "label": "Eraser"
    }
}

# UI dimensions and layouts
HEADER_HEIGHT = 100
HEADER_ALPHA = 0.85

# Gesture controller configurations
MIN_DETECTION_CONFIDENCE = 0.85
MIN_TRACKING_CONFIDENCE = 0.80

# Cooldowns (in seconds)
GESTURE_COOLDOWN = 1.0   # Undo / Redo / Screenshot
CLICK_COOLDOWN = 0.25    # Toolbar button clicks
AUTO_SAVE_INTERVAL = 120.0  # 2 minutes

# Stroke smoothing window size
SMOOTHING_WINDOW = 5
