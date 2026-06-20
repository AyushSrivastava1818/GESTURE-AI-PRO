"""Quick debug: prints gesture state live for 15 seconds so we can see what's being detected."""
import cv2
import numpy as np
import time
import sys
sys.path.insert(0, ".")
import settings
from gesture_controller import GestureController

gc = GestureController()
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

end = time.time() + 30
prev_type = None
while time.time() < end:
    ok, frame = cap.read()
    if not ok:
        continue
    frame = cv2.flip(frame, 1)
    results = gc.process_frame(frame)

    gesture_type = "NO_HAND"
    fingers_str = "-"
    if results.hand_landmarks:
        lm_list = gc.get_landmarks(results, 0)
        fingers = gc.get_fingers_up(results, 0)
        gdata = gc.get_gesture_state(lm_list, fingers)
        gesture_type = gdata["type"]
        fingers_str = str(fingers)

        # Show thumb distances for diagnosis
        if len(lm_list) >= 21:
            thumb_tip   = lm_list[4]
            index_tip   = lm_list[8]
            index_mcp   = lm_list[5]
            middle_tip  = lm_list[12]
            t_i_dist  = int(np.hypot(thumb_tip[0]-index_tip[0], thumb_tip[1]-index_tip[1]))
            t_base    = int(np.hypot(thumb_tip[0]-index_mcp[0], thumb_tip[1]-index_mcp[1]))
            i_m_dist  = int(np.hypot(middle_tip[0]-index_tip[0], middle_tip[1]-index_tip[1]))
            if gesture_type != prev_type:
                print(f"GESTURE={gesture_type:16s}  fingers={fingers_str}  thumb-tip={t_i_dist}px  thumb-base={t_base}px  idx-mid={i_m_dist}px")
                prev_type = gesture_type

    cv2.putText(frame, f"GESTURE: {gesture_type}  fingers: {fingers_str}", (20,50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
    cv2.imshow("DEBUG", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
