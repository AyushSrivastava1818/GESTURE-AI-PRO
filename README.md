# GestureAI Pro — Intelligent Gesture-Controlled Whiteboard

[![Python Version](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-green.svg)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-red.svg)](https://google.github.io/mediapipe/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)

**GestureAI Pro** is a premium, real-time virtual canvas application that leverages advanced Computer Vision and Hand Tracking to transform physical hand movements into digital drawing commands. By moving beyond traditional raster whiteboards, GestureAI Pro uses a state-of-the-art **Vector-Based Stroke Engine** coupled with **AI Shape Beautification** to classify and replace hand-drawn contours with perfect geometry.

The application features a modern semi-transparent glassmorphic user interface (Light & Dark theme matching), session statistics logging, animated toast notifications, and dynamic gesture-driven configurations.

---

## Key Features

1. **Vector-Based Canvas Architecture**
   * Storing strokes as vector arrays rather than destructive canvas pixels.
   * Enables unlimited, instant Undo and Redo operations.
   * Supports flawless theme toggling (Light/Dark Mode) by dynamically re-rendering existing strokes with color-inversion.

2. **AI Shape Recognition & Beautification**
   * Uses real-time contour analysis and Ramer-Douglas-Peucker (`cv2.approxPolyDP`) polygonal approximations.
   * Automatically detects and beautifies rough shapes into:
     * **Straight Lines** (slope fitting & deviation mapping)
     * **Perfect Circles** (minimum enclosing circles with standard deviation filters)
     * **Rectangles** (orthogonal axis-aligned bounding rectangles)
     * **Triangles** (3-vertex contour approximation)

3. **Smart Stroke Smoothing Filter**
   * Integrates a moving average window to eliminate high-frequency hand tremors.
   * Employs linear point interpolation to fill in coordinates during fast finger motions, maintaining fluid and cohesive lines.

4. **Modern Glassmorphic UI Dashboard**
   * **HUD Top Menu**: Sleek presets bar (Pencil, Marker, Highlighter, Eraser), a curated color palette (Red, Green, Blue, Yellow, Purple, Orange), and utility actions (Undo, Redo, Clear, Theme Toggle, Save, and Gesture Lock).
   * **Status & Stats Overlay**: Bottom-left glass panel displaying active mode, tool thickness, color indicators, drawing session durations, total strokes, and AI shape detection counts.
   * **Recent Saves Log**: Bottom-right sidebar showing timestamped drawing archives.

5. **Dynamic Brush Size Control**
   * Real-time brush sizing using the distance between the tips of the Index finger and Thumb.
   * Visual feedback bubble showing the precise pixel size dynamically next to the user's hand.

6. **History & Autosave Manager**
   * Automatically saves local session snapshots every 2 minutes.
   * Performs manual screenshot captures and exports a clean whiteboard drawing automatically when the application exits.

7. **Smart Gesture Feedback Toasts**
   * Displays non-intrusive alert banners at the top of the window when actions occur (e.g. "Undo Successful", "AI: Circle Detected!").
   * Designed with alpha-blended slide-in/fade-out transitions.

---

## Gesture Guide

Use the following non-overlapping finger combinations for gesture control. Ensure your hand is clearly visible to the webcam.

| Mode / Gesture | Finger Configuration | Action / Operation |
| --- | --- | --- |
| **Drawing Mode** | ☝️ **Index finger UP** (others down, thumb tucked) | Draws freehand strokes on the canvas using active presets. |
| **Selection Mode** | 🖐️ **Open Hand** (4 or 5 fingers UP) | Displays a dual-ring cursor. Move hand to hover over toolbar buttons. |
| **Click / Select** | 🤌 **Pinch** (Index + Thumb tips close together while in Selection Mode) | Selects the hovered color, brush preset, theme toggle, or toolbar action. |
| **Dynamic Brush Size** | ✌️ **Thumb + Index UP** (others down, spread wide) | Adjusts brush size dynamically. Spacing ratio is normalized by hand scale. |
| **Undo Action** | ✌️ **Index + Middle UP** (others down, spread apart) | Triggers **Undo** (1.0s gesture trigger cooldown). |
| **Redo Action** | 🤟 **Index + Middle + Ring UP** (others down) | Triggers **Redo** (1.0s gesture trigger cooldown). |
| **Gesture Lock** | 🤙 **Pinky UP only** (others closed in a fist) | Toggles **Gesture Lock**. Freezes canvas input. Raise pinky again to unlock. |
| **Instant Screenshot**| 🤘 **Index + Pinky UP** (others down, Rock-on sign) | Captures a full frame composite showing the UI overlays and saves it. |

---

## Project Directory Architecture

```
gesture_ai_pro/
│
├── main.py                # Main loop entry point; coordinates loop and camera feeds.
├── settings.py            # Global variables, themes, brush presets, and constants.
├── gesture_controller.py  # MediaPipe Hand Landmarks processing & gesture state classifier.
├── drawing_engine.py      # Stroke tracker, smoothers, interpolations, and vector stacks.
├── shape_detector.py      # AI geometry contour-fitting & polygon beautification.
├── ui_manager.py          # HUD Toolbar, dashboard, toasts, stats overlay, and cursor draw.
├── history_manager.py     # Image exports, auto-saves, directories, and session logs.
├── requirements.txt       # Project dependencies.
└── history/               # Directory containing exported drawings and autosaves.
```

---

## Installation & Setup

### Prerequisites
* Python 3.8 or higher.
* A connected webcam device.

### Step-by-Step Installation

1. **Clone or Navigate to the Directory**:
   ```bash
   cd "C:\Users\Ayush Srivastava\.gemini\antigravity-ide\scratch\gesture_ai_pro"
   ```

2. **Create a Python Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   * **On Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   * **On Windows (CMD)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**:
   ```bash
   python main.py
   ```

*Press **ESC** on your keyboard inside the window to exit the application clean.*

---
