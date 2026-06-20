import numpy as np
import sys
sys.path.insert(0, ".")
from gesture_controller import GestureController

def create_mock_hand(fingers_up, thumb_spread=False, pinch=False, undo_spread=False):
    """
    Creates mock landmark list (21 points) and finger status array.
    Landmarks to mock:
      0: Wrist (0, 0)
      9: Middle MCP (0, -100) -> hand_scale will be 100px.
      
      5: Index MCP (20, -100)
      4: Thumb tip
      8: Index tip
      6: Index PIP
      12: Middle tip
      10: Middle PIP
      16: Ring tip
      20: Pinky tip
    """
    # 21 points
    lm_list = [(0, 0)] * 21
    lm_list[0] = (0, 0)
    lm_list[9] = (0, -100)  # wrist to middle MCP = 100px (hand_scale)
    lm_list[5] = (20, -100) # Index MCP
    
    # Define PIP points
    lm_list[6] = (20, -120)  # Index PIP
    lm_list[10] = (0, -120)  # Middle PIP
    lm_list[14] = (-20, -120) # Ring PIP
    lm_list[18] = (-40, -120) # Pinky PIP

    # Index tip
    if fingers_up[1]:
        lm_list[8] = (20, -180) # extended (above PIP)
    else:
        lm_list[8] = (20, -90)  # folded (below PIP)

    # Middle tip
    if fingers_up[2]:
        if undo_spread:
            lm_list[12] = (-30, -180) # spread wide from index tip
        else:
            lm_list[12] = (0, -180)  # extended straight
    else:
        lm_list[12] = (0, -90)   # folded

    # Ring tip
    if fingers_up[3]:
        lm_list[16] = (-20, -180)
    else:
        lm_list[16] = (-20, -90)

    # Pinky tip
    if fingers_up[4]:
        lm_list[20] = (-40, -180)
    else:
        lm_list[20] = (-40, -90)

    # Thumb tip (4) and Index MCP (5) / Index tip (8)
    if thumb_spread:
        # thumb tip far from index MCP (> 55px relative to 100px hand_scale, i.e., > 55px)
        lm_list[4] = (90, -100)  # distance to index MCP (20, -100) is 70px (>55)
    else:
        # thumb tip close to index MCP (< 55px)
        lm_list[4] = (45, -100)  # distance to index MCP is 25px (<55)

    if pinch:
        # thumb tip very close to index tip (8)
        # index tip is at (20, -180)
        lm_list[4] = (25, -175)  # distance is sqrt(5^2 + 5^2) = 7.07px (<30px relative to 100px)

    return lm_list

def run_tests():
    gc = GestureController()
    
    # Test cases: (fingers_up, thumb_spread, pinch, undo_spread, expected_gesture)
    tests = [
        ([0, 0, 0, 0, 1], False, False, False, "LOCK_TOGGLE"),
        ([0, 1, 0, 0, 1], False, False, False, "SCREENSHOT"),
        ([0, 1, 1, 1, 0], False, False, False, "REDO"),
        ([0, 1, 1, 0, 0], False, False, True, "UNDO"),
        ([0, 1, 1, 1, 1], False, False, False, "SELECT"),
        ([0, 1, 1, 1, 1], False, True, False, "CLICK"),
        ([0, 1, 0, 0, 0], True, False, False, "SIZE_CONTROL"),
        ([0, 1, 0, 0, 0], False, False, False, "DRAW"),
    ]

    passed = 0
    for idx, (fingers_up, t_spread, pinch, u_spread, expected) in enumerate(tests):
        lm_list = create_mock_hand(fingers_up, t_spread, pinch, u_spread)
        raw_result = gc._raw_gesture(lm_list, fingers_up)
        actual = raw_result["type"]
        if actual == expected:
            print(f"Test {idx+1} PASSED: fingers={fingers_up} (spread={t_spread}, pinch={pinch}, undo_spread={u_spread}) -> {actual}")
            passed += 1
        else:
            print(f"Test {idx+1} FAILED: expected {expected}, got {actual} (fingers={fingers_up})")

    print(f"\nCompleted: {passed}/{len(tests)} tests passed.")

if __name__ == "__main__":
    run_tests()
