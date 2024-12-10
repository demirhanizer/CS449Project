import cv2
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# Start Webcam Capture
import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not accessible!")
else:
    print("Camera is accessible!")




def detect_gesture(landmarks):
    """
    Detects gestures:
    - One finger up: Index finger is extended upward while other fingers are curled.
    - One finger down: Index finger is extended downward while other fingers are curled.
    - Avoids detecting lateral (right/left) finger movements as up/down.
    """
    # Get landmarks for thumb, index, middle, ring, and pinky fingers
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    index_base = landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP]

    # Tolerances for detecting significant vertical movement (to reduce lateral errors)
    vertical_tolerance = 0.1
    lateral_tolerance = 0.15 

    # Check if the index finger is pointing up
    if (
        index_tip.y < index_base.y  # Ensure finger is pointing up
        and abs(index_tip.x - index_base.x) < lateral_tolerance  # Ensure minimal lateral movement
        and all(
            other_tip.y > index_tip.y for other_tip in [middle_tip, ring_tip, pinky_tip]
        )
    ):
        return "One Finger Up"

    # Check if the index finger is pointing down
    if (
        index_tip.y > index_base.y  # Ensure finger is pointing down
        and abs(index_tip.x - index_base.x) < lateral_tolerance  # Ensure minimal lateral movement
        and all(
            other_tip.y < index_tip.y for other_tip in [middle_tip, ring_tip, pinky_tip]
        )
    ):
        return "One Finger Down"

    return "Unknown Gesture"

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    # Process each hand detected
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            gesture = detect_gesture(hand_landmarks.landmark)

            # Display Gesture on Screen
            cv2.putText(frame, f'Gesture: {gesture}', (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show the Frame
    cv2.imshow('Gesture Recognition', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
        break

cap.release()
cv2.destroyAllWindows()
