import cv2
import mediapipe as mp

# Initialize Mediapipe Hand Detection
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Set up webcam video feed
cap = cv2.VideoCapture(0)

# Initialize Mediapipe Hands
with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip the frame horizontally for a mirrored view
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with Mediapipe
        results = hands.process(rgb_frame)
        
        gesture_detected = False  # Reset gesture detection status for each frame

        # Draw hand landmarks and check for gestures
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Extract thumb landmarks
                thumb_cmc = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_CMC]
                thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP]
                thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                
                # Collect all other landmarks
                other_landmarks = [
                    hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
                    hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                    hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP],
                    hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP],
                    hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                ]
                
                # Step 2: Check thumb direction (upwards)
                thumb_upwards = (
                    thumb_tip.y < thumb_ip.y and
                    thumb_ip.y < thumb_mcp.y and
                    thumb_mcp.y < thumb_cmc.y
                )
                
                # Step 3: Check thumb higher than other points
                thumb_higher_than_others = all(
                    thumb_tip.y < landmark.y and
                    thumb_ip.y < landmark.y and
                    thumb_mcp.y < landmark.y
                    for landmark in other_landmarks
                )
                
                # Step 4: Detect thumbs up
                if thumb_upwards and thumb_higher_than_others:
                    gesture_detected = True
        
        # Step 5: Provide feedback
        if gesture_detected:
            cv2.putText(frame, "Thumbs Up Detected!", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No Thumbs Up Detected", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Show the frame
        cv2.imshow("Hand Gesture Recognition", frame)
        
        # Break the loop on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()
