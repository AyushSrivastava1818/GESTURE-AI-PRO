import cv2
import numpy as np

class ShapeDetector:
    def __init__(self):
        pass

    def detect_shape(self, points):
        """
        Analyzes a list of points from a completed stroke.
        Returns:
            (shape_type, shape_data) or (None, None)
            - shape_type: 'line', 'circle', 'rectangle', 'triangle'
            - shape_data: Dictionary containing geometric properties
        """
        if len(points) < 8:
            return None, None

        # Convert to numpy arrays for calculation
        pts_arr = np.array(points, dtype=np.int32)
        start_pt = points[0]
        end_pt = points[-1]
        
        # Calculate endpoint distance and approximate stroke length
        endpoint_dist = np.hypot(end_pt[0] - start_pt[0], end_pt[1] - start_pt[1])
        
        # Sum segment lengths
        total_len = 0.0
        for i in range(1, len(points)):
            total_len += np.hypot(points[i][0] - points[i-1][0], points[i][1] - points[i-1][1])

        if total_len == 0:
            return None, None

        # 1. Check for LINE:
        # A stroke is a straight line if it doesn't deviate much from the direct path between start and end
        if endpoint_dist > 35:
            # Perpendicular distance check
            p1 = np.array(start_pt)
            p2 = np.array(end_pt)
            line_vec = p2 - p1
            line_len = np.linalg.norm(line_vec)
            
            deviations = []
            for pt in points:
                p = np.array(pt)
                # Distance of point p from line p1->p2
                dev = np.abs(np.cross(line_vec, p - p1)) / line_len
                deviations.append(dev)
            
            max_dev = max(deviations) if deviations else 999
            
            # If the max deviation is less than 15% of the total length, it's a straight line
            if max_dev < min(25, 0.15 * line_len) and endpoint_dist / total_len > 0.82:
                return "line", {
                    "start": (int(start_pt[0]), int(start_pt[1])),
                    "end": (int(end_pt[0]), int(end_pt[1]))
                }

        # 2. Check for CLOSED SHAPES (Circle, Rectangle, Triangle)
        # Closed shapes have start and end points relatively close
        is_closed = (endpoint_dist < 90) or (endpoint_dist / total_len < 0.28)

        if is_closed:
            # Calculate key parameters
            perimeter = cv2.arcLength(pts_arr, True)
            # Use convex hull to filter drawing noise
            hull = cv2.convexHull(pts_arr)
            hull_area = cv2.contourArea(hull)
            
            # Approximate the polygon using approxPolyDP on the convex hull
            # (Hull is smoother and less noisy than the raw contour)
            approx = cv2.approxPolyDP(hull, 0.04 * perimeter, True)
            
            # A. TRIANGLE check (3 vertices)
            if len(approx) == 3:
                vertices = [tuple(pt[0]) for pt in approx]
                return "triangle", {"vertices": vertices}
                
            # B. RECTANGLE check (4 vertices)
            elif len(approx) == 4:
                x, y, w, h = cv2.boundingRect(pts_arr)
                # Prevent thin lines from becoming tiny rectangles
                if w > 20 and h > 20:
                    return "rectangle", {
                        "top_left": (x, y),
                        "bottom_right": (x + w, y + h)
                    }

            # C. CIRCLE check:
            # Let's see how closely points fit a circular radius around the center of mass
            (cx, cy), radius = cv2.minEnclosingCircle(pts_arr)
            dists = [np.hypot(p[0] - cx, p[1] - cy) for p in points]
            mean_dist = np.mean(dists)
            std_dist = np.std(dists)
            
            # Low coefficient of variation indicates circularity
            if mean_dist > 15 and (std_dist / mean_dist) < 0.18:
                return "circle", {
                    "center": (int(cx), int(cy)),
                    "radius": int(mean_dist)
                }

            # D. FALLBACK CLOSED SHAPES:
            # Sometimes a rough rectangle or circle has extra noise vertices (e.g. 5 or 6)
            x, y, w, h = cv2.boundingRect(pts_arr)
            if w > 20 and h > 20:
                rect_area = w * h
                # If hull fills most of the bounding rect, classify as rectangle
                if hull_area / rect_area > 0.82:
                    return "rectangle", {
                        "top_left": (x, y),
                        "bottom_right": (x + w, y + h)
                    }
                # If it's fairly round, classify as circle
                circularity = 4 * np.pi * hull_area / (perimeter ** 2) if perimeter > 0 else 0
                if circularity > 0.65:
                    return "circle", {
                        "center": (int(x + w//2), int(y + h//2)),
                        "radius": int(max(w, h) // 2)
                    }

        return None, None
