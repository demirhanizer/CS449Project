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
        
        gesture = "No gestures!"  # Default message

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
                
                # Check for "thumbs up"
                thumb_upwards = (
                    thumb_tip.y < thumb_ip.y and
                    thumb_ip.y < thumb_mcp.y and
                    thumb_mcp.y < thumb_cmc.y
                )
                thumb_higher_than_others = all(
                    thumb_tip.y < landmark.y and
                    thumb_ip.y < landmark.y and
                    thumb_mcp.y < landmark.y
                    for landmark in other_landmarks
                )
                
                # Check for "thumbs down"
                thumb_downwards = (
                    thumb_tip.y > thumb_ip.y and
                    thumb_ip.y > thumb_mcp.y and
                    thumb_mcp.y > thumb_cmc.y
                )
                thumb_lower_than_others = all(
                    thumb_tip.y > landmark.y and
                    thumb_ip.y > landmark.y and
                    thumb_mcp.y > landmark.y
                    for landmark in other_landmarks
                )
                
                # Determine the gesture
                if thumb_upwards and thumb_higher_than_others:
                    gesture = "Thumbs up detected!"
                elif thumb_downwards and thumb_lower_than_others:
                    gesture = "Thumbs down detected!"
        
        # Display the detected gesture
        cv2.putText(frame, gesture, (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if "detected" in gesture else (0, 0, 255), 2)
        
        # Show the frame
        cv2.imshow("Hand Gesture Recognition", frame)
        
        # Break the loop on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows
