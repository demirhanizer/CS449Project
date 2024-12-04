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
cap = cv2.VideoCapture(0)  # Adjust the camera index if necessary

# Initialize Tkinter GUI
root = tk.Tk()
root.title("Gesture Recognition GUI with Camera Feed and Landmarks")
root.geometry("1000x800")

# Add GUI elements
gesture_label = tk.Label(root, text="Gesture: None", font=("Helvetica", 16))
gesture_label.pack(pady=10)

action_label = tk.Label(root, text="Action: None", font=("Helvetica", 16))
action_label.pack(pady=10)

# Canvas for video feed (Enlarged)
video_canvas = tk.Canvas(root, width=960, height=720)  # Set the larger size for the camera feed
video_canvas.pack()

# Define gesture recognition function
def recognize_gesture(landmarks, frame_width, frame_height):
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
        return "Cursor-Pointing Gesture", "Moving Cursor"

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
        return "Open Hand Gesture", "Scrolling"

    # Close Hand Gesture: All fingers near wrist
    if (
        abs(index_tip.y - wrist.y) < 0.2  # Index finger close to wrist
        and abs(middle_tip.y - wrist.y) < 0.2  # Middle finger close to wrist
        and abs(ring_tip.y - wrist.y) < 0.2  # Ring finger close to wrist
        and abs(pinky_tip.y - wrist.y) < 0.2  # Pinky finger close to wrist
        and abs(thumb_tip.x - wrist.x) < 0.3  # Thumb close to wrist
        and abs(thumb_tip.y - index_tip.y) < 0.1  # Thumb close to index finger
    ):
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

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the landmarks on the frame
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Detect gesture and perform actions
            gesture, action = recognize_gesture(hand_landmarks.landmark, frame_width, frame_height)

            # Update the GUI with the detected gesture and action
            gesture_label.config(text=f"Gesture: {gesture}")
            action_label.config(text=f"Action: {action}")

    # Resize frame to match Canvas size
    resized_frame = cv2.resize(frame, (960, 720))

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