import cv2
import mediapipe as mp
import pyautogui  # For controlling the cursor and scrolling

# Initialize MediaPipe Hand solution
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Get screen dimensions for cursor mapping
screen_width, screen_height = pyautogui.size()

# Start video capture
cap = cv2.VideoCapture(1)  # Adjust the camera index if necessary

def recognize_gesture(landmarks, frame_width, frame_height):
    """
    Recognize gestures and perform actions.
    Arguments:
    - landmarks: Normalized hand landmarks from MediaPipe.
    - frame_width: Width of the video frame.
    - frame_height: Height of the video frame.

    Returns:
    - Detected gesture name.
    """
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    # Cursor-Pointing Gesture: Index finger up, others curled
    if (
        index_tip.y < middle_tip.y  # Index finger above middle finger
        and index_tip.y < ring_tip.y  # Index finger above ring finger
        and index_tip.y < pinky_tip.y  # Index finger above pinky
        and middle_tip.y > wrist.y  # Middle finger curled
        and ring_tip.y > wrist.y  # Ring finger curled
        and pinky_tip.y > wrist.y  # Pinky curled
    ):
        screen_x = int(index_tip.x * screen_width)
        screen_y = int(index_tip.y * screen_height)
        pyautogui.moveTo(screen_x, screen_y)  # Move the cursor
        return "Cursor-Pointing Gesture"

    # Scrolling Gesture: Open palm
    if (
        abs(thumb_tip.y - wrist.y) > 0.2  # Thumb away from wrist
        and abs(index_tip.y - wrist.y) > 0.2  # Index finger extended
        and abs(middle_tip.y - wrist.y) > 0.2  # Middle finger extended
        and abs(ring_tip.y - wrist.y) > 0.2  # Ring finger extended
        and abs(pinky_tip.y - wrist.y) > 0.2  # Pinky finger extended
    ):
        scroll_speed = 10 if index_tip.y > frame_height // 2 else -10
        pyautogui.scroll(scroll_speed)  # Scroll up or down
        return "Scrolling Gesture"

    return "Unknown Gesture"

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame for a mirror effect
    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape

    # Convert the frame to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the landmarks on the frame
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Detect gesture and perform actions
            gesture = recognize_gesture(hand_landmarks.landmark, frame_width, frame_height)

            # Display the gesture on the frame
            cv2.putText(frame, gesture, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if gesture == "Cursor-Pointing Gesture" else (0, 255, 255), 2)

    # Display the video feed
    cv2.imshow("Hand Gesture Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
