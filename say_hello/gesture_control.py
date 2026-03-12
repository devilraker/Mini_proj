import cv2
import mediapipe as mp
import webbrowser
import time

# Initialize MediaPipe hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

def count_fingers(hand_landmarks):
    """Count the number of extended fingers"""
    finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
    thumb_tip = 4
    
    fingers_up = 0
    
    # Check thumb (different logic - compare x coordinates)
    if hand_landmarks.landmark[thumb_tip].x < hand_landmarks.landmark[thumb_tip - 1].x:
        fingers_up += 1
    
    # Check other fingers (compare y coordinates)
    for tip in finger_tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers_up += 1
    
    return fingers_up

def get_gesture_action(finger_count):
    """Map finger count to actions"""
    gesture_map = {
        1: ("fan", "Opening Fan Control"),
        2: ("light", "Opening Light Control"),
        3: ("bed", "Opening Bed Angle Control"),
        4: ("decrease", "Decreasing Value"),
        5: ("increase", "Increasing Value")
    }
    return gesture_map.get(finger_count, (None, None))

# Open camera
cap = cv2.VideoCapture(0)
print("Hand Gesture Control Started!")
print("Gesture Guide:")
print("  1 finger = Fan")
print("  2 fingers = Light")
print("  3 fingers = Bed Angle")
print("  4 fingers = Decrease")
print("  5 fingers = Increase")
print("\nPress 'q' to quit")

last_action_time = 0
action_cooldown = 2  # seconds between actions

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    
    # Flip frame horizontally for mirror view
    frame = cv2.flip(frame, 1)
    
    # Convert to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process frame
    results = hands.process(rgb_frame)
    
    current_gesture = "No Hand Detected"
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks
            mp_drawing.draw_landmarks(
                frame, 
                hand_landmarks, 
                mp_hands.HAND_CONNECTIONS
            )
            
            # Count fingers
            finger_count = count_fingers(hand_landmarks)
            action, message = get_gesture_action(finger_count)
            
            current_gesture = f"Fingers: {finger_count} - {message if message else 'No Action'}"
            
            # Perform action with cooldown
            current_time = time.time()
            if action and (current_time - last_action_time) > action_cooldown:
                if action in ["fan", "light", "bed"]:
                    url = f"http://localhost:5000/{action}"
                    webbrowser.open(url)
                    print(f"✓ {message}")
                    last_action_time = current_time
                elif action in ["decrease", "increase"]:
                    print(f"✓ {message}")
                    # Note: You'll need JavaScript integration to actually trigger buttons
                    last_action_time = current_time
    
    # Display gesture info on screen
    cv2.putText(frame, current_gesture, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Show frame
    cv2.imshow('Hand Gesture Control', frame)
    
    # Quit on 'q' press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()