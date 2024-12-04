import cv2
import mediapipe as mp
import pyautogui  # For controlling the cursor and scrolling
import tkinter as tk
from PIL import Image, ImageTk

# Initialize MediaPipe Hand solution
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Get screen dimensions for cursor mapping
screen_width, screen_height = pyautogui.size()

# Start video capture
cap = cv2.VideoCapture(1)  # Adjust the camera index if necessary

# Initialize Tkinter GUI
root = tk.Tk()
root.title("Enhanced Gesture-Controlled Interface")
root.geometry("1280x720")

# Add a frame for navigation buttons
nav_frame = tk.Frame(root, bg="black", width=200, height=720)
nav_frame.pack(side=tk.LEFT, fill=tk.Y)

# Add navigation buttons
tk.Label(nav_frame, text="Navigator", font=("Helvetica", 16), fg="white", bg="black").pack(pady=10)
buttons = [
    ("Open Menu", "Open Menu Gesture"),
    ("Close Menu", "Close Menu Gesture"),
    ("Machine Control", "Machine Gesture"),
    ("Power Control", "Power Gesture"),
    ("Speed Control", "Speed Gesture"),
]
for btn_text, gesture in buttons:
    btn = tk.Button(nav_frame, text=btn_text, font=("Helvetica", 12), width=18)
    btn.pack(pady=10)

# Canvas for video feed (Right side)
video_canvas = tk.Canvas(root, width=960, height=720, bg="black")
video_canvas.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

# Define gesture recognition function
def recognize_gesture(landmarks, frame_width, frame_height):
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    # Example gesture logic
    if index_tip.y < middle_tip.y < ring_tip.y < pinky_tip.y:
        return "Cursor-Pointing Gesture", "Moving Cursor"
    elif abs(index_tip.y - wrist.y) < 0.2 and abs(middle_tip.y - wrist.y) < 0.2:
        return "Close Hand Gesture", "Confirm Action"
    return "Unknown Gesture", "No Action"

# Function to process video and update GUI
def update_video():
    ret, frame = cap.read()
    if not ret:
        return

    # Flip the frame for a mirror effect
    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape

    # Convert the frame to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    action = "No Action"  # Default action
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the landmarks on the frame
            mp_drawing.draw_landmarks(frame_rgb, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Detect gesture and perform actions
            gesture, action = recognize_gesture(hand_landmarks.landmark, frame_width, frame_height)

    # Overlay the action name on the camera feed
    cv2.putText(
        frame_rgb,
        f"Action: {action}",
        (10, 50),  # Position on the frame
        cv2.FONT_HERSHEY_SIMPLEX,
        1,  # Font scale
        (0, 255, 0),  # Text color (green)
        2,  # Line thickness
        cv2.LINE_AA,
    )

    # Resize frame to match Canvas size
    resized_frame = cv2.resize(frame_rgb, (960, 720))

    # Convert the frame to a format compatible with Tkinter
    frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))

    # Display the frame on the Canvas
    video_canvas.create_image(0, 0, anchor=tk.NW, image=frame_image)

    # Keep a reference to the image to prevent garbage collection
    video_canvas.image = frame_image

    # Schedule the next frame update
    root.after(10, update_video)

# Start processing video in the background
update_video()

# Run the Tkinter main loop
root.mainloop()

# Release resources
cap.release()
cv2.destroyAllWindows()
