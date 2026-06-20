import cv2
import os
import time
from datetime import datetime

class HistoryManager:
    def __init__(self, workspace_dir):
        self.workspace_dir = workspace_dir
        self.history_dir = os.path.join(workspace_dir, "history")
        
        # Ensure directories exist
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

        self.session_start_time = time.time()
        self.stroke_count = 0
        self.shape_count = 0
        self.undo_count = 0
        self.redo_count = 0
        self.recent_drawings = []
        
        # Load any existing historical entries
        self.scan_recent_drawings()

    def scan_recent_drawings(self):
        """Scans the history directory to populate recent drawings."""
        try:
            if not os.path.exists(self.history_dir):
                return
            
            files = [f for f in os.listdir(self.history_dir) if f.startswith("drawing_") and f.endswith(".png")]
            # Sort by filename (which starts with timestamp, so alphabetical sort equals chronological)
            files.sort(reverse=True)
            self.recent_drawings = [os.path.join(self.history_dir, f) for f in files[:4]]
        except Exception as e:
            print(f"[WARNING] Error scanning history directory: {e}")

    def save_canvas(self, canvas, is_auto_save=False):
        """
        Saves the current canvas frame to the history directory.
        Format: history/drawing_YYYY_MM_DD_HH_MM_SS.png or history/autosave_...
        Returns:
            The path of the saved file.
        """
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        prefix = "autosave_" if is_auto_save else "drawing_"
        filename = f"{prefix}{timestamp}.png"
        filepath = os.path.join(self.history_dir, filename)

        try:
            cv2.imwrite(filepath, canvas)
            if not is_auto_save:
                # Add to recent list and keep only top 4
                if filepath not in self.recent_drawings:
                    self.recent_drawings.insert(0, filepath)
                    if len(self.recent_drawings) > 4:
                        self.recent_drawings.pop()
            return filepath
        except Exception as e:
            print(f"[ERROR] Failed to save canvas: {e}")
            return None

    def record_stroke(self):
        """Tracks the total number of strokes created."""
        self.stroke_count += 1

    def record_shape(self):
        """Tracks the total number of shapes recognized."""
        self.shape_count += 1

    def record_undo(self):
        """Tracks the total number of undos performed."""
        self.undo_count += 1

    def record_redo(self):
        """Tracks the total number of redos performed."""
        self.redo_count += 1

    def get_session_stats(self):
        """Returns statistical tracking logs for the active session."""
        elapsed_seconds = int(time.time() - self.session_start_time)
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        time_str = f"{minutes:02d}m {seconds:02d}s"
        if hours > 0:
            time_str = f"{hours}h {time_str}"

        return {
            "time_spent": time_str,
            "strokes": self.stroke_count,
            "shapes": self.shape_count,
            "undos": self.undo_count,
            "redos": self.redo_count
        }

    def get_recent_drawings(self):
        """Returns the list of the 4 most recent drawings."""
        return self.recent_drawings
