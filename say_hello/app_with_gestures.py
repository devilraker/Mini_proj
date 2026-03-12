import cv2
import mediapipe as mp
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading

# Initialize Flask and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'manblahblah'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize MediaPipe hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/fan")
def fan():
    return render_template("fan.html")

@app.route("/light")
def light():
    return render_template("light.html")

@app.route("/bed")
def bed():
    return render_template("bed.html")

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

def gesture_detection_thread():
    """Run gesture detection in background thread"""
    cap = cv2.VideoCapture(0)
    print("Hand Gesture Control Started!")
    print("Gesture Guide:")
    print("  1 finger = Fan")
    print("  2 fingers = Light")
    print("  3 fingers = Bed Angle")
    print("  4 fingers = Decrease")
    print("  5 fingers = Increase")
    
    last_action_time = 0
    action_cooldown = 1.5  # Increased from 1.5 to 2.5 seconds
    last_gesture = None
    gesture_buffer = []  # Buffer to store recent detections
    buffer_size = 10  # Need 10 consistent frames
    
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
        finger_count = 0
        
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
                
                # Add to buffer for stability
                gesture_buffer.append(finger_count)
                if len(gesture_buffer) > buffer_size:
                    gesture_buffer.pop(0)
                
                # Only proceed if we have enough samples
                if len(gesture_buffer) == buffer_size:
                    # Check if all recent detections are the same
                    if len(set(gesture_buffer)) == 1:
                        stable_gesture = gesture_buffer[0]
                        
                        gesture_map = {
                            1: ("fan", "Fan Control"),
                            2: ("light", "Light Control"),
                            3: ("bed", "Bed Angle Control"),
                            4: ("decrease", "Decrease"),
                            5: ("increase", "Increase")
                        }
                        
                        action, message = gesture_map.get(stable_gesture, (None, None))
                        current_gesture = f"Fingers: {stable_gesture} - {message if message else 'No Action'}"
                        
                        # Perform action with cooldown
                        current_time = time.time()
                        if action and (current_time - last_action_time) > action_cooldown:
                            if stable_gesture != last_gesture:  # Only trigger on gesture change
                                # Send gesture to frontend via SocketIO
                                socketio.emit('gesture_detected', {'action': action, 'message': message})
                                print(f"✓ Gesture {stable_gesture}: {message}")
                                last_action_time = current_time
                                last_gesture = stable_gesture
                                gesture_buffer = []  # Clear buffer after action
                    else:
                        current_gesture = f"Stabilizing... ({gesture_buffer[-1]} fingers detected)"
                else:
                    current_gesture = f"Detecting... ({len(gesture_buffer)}/{buffer_size})"
        else:
            last_gesture = None  # Reset when no hand detected
            gesture_buffer = []  # Clear buffer when hand disappears
        
        # Display info on screen
        cv2.putText(frame, current_gesture, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show cooldown timer
        current_time = time.time()
        time_since_last = current_time - last_action_time
        if time_since_last < action_cooldown:
            cooldown_left = action_cooldown - time_since_last
            cv2.putText(frame, f"waitt: {cooldown_left:.1f}s", (10, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
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

if __name__ == "__main__":
    # Start gesture detection in background thread
    gesture_thread = threading.Thread(target=gesture_detection_thread, daemon=True)
    gesture_thread.start()
    
    # Run Flask app
    print("\n🚀 Starting Flask app on http://localhost:5000")
    print("📷 Camera window will open shortly...")
    socketio.run(app, debug=False, port=5000)