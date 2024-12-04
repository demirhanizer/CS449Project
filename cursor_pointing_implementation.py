import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import math
import pyautogui  # For scrolling functionality

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Start video capture
cap = cv2.VideoCapture(0)

# Initialize Tkinter GUI
root = tk.Tk()
root.title("Circular Menu with Gesture Control")
root.geometry("1200x800")

# Circular menu items
menu_items = [
    "Hoş Geldiniz", "Teşekkür Ederim", "Tuş Takımı",
    "Hoşça kal", "Hayır", "Evet", "Geri", "Merhaba, Nasılsın?"
]
selected_item_index = 0

# Canvas for the circular menu and camera feed
menu_canvas = tk.Canvas(root, width=1200, height=800, bg="lightgray")
menu_canvas.pack()

# Text to display the selected option
selected_text_label = tk.Label(root, text="Selected: None", font=("Helvetica", 16), bg="lightgray", fg="black")
selected_text_label.place(x=10, y=750)

# Function to draw the circular menu
def draw_circular_menu(selected_index):
    menu_canvas.delete("menu")  # Clear previous menu elements
    center_x, center_y = 600, 250  # Center of the menu
    radius = 180
    angle_step = 360 / len(menu_items)

    for i, item in enumerate(menu_items):
        angle = math.radians(i * angle_step - 90)  # Calculate angle for item
        x = center_x + radius * math.cos(angle)  # X-coordinate
        y = center_y + radius * math.sin(angle)  # Y-coordinate
        color = "red" if i == selected_index else "black"  # Highlight selected

        # Draw menu item box
        box_x1, box_y1 = x - 50, y - 20
        box_x2, box_y2 = x + 50, y + 20
        menu_canvas.create_rectangle(box_x1, box_y1, box_x2, box_y2, fill="white", outline=color, width=2, tags="menu")

        # Draw the text
        menu_canvas.create_text(x, y, text=item, fill=color, font=("Helvetica", 12, "bold"), tags="menu")

# Function to detect thumbs up and thumbs down gestures
def detect_thumbs_gesture(landmarks):
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    thumb_ip = landmarks[mp_hands.HandLandmark.THUMB_IP]
    thumb_mcp = landmarks[mp_hands.HandLandmark.THUMB_MCP]
    thumb_cmc = landmarks[mp_hands.HandLandmark.THUMB_CMC]

    # Collect other landmarks
    other_landmarks = [
        landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP],
        landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
        landmarks[mp_hands.HandLandmark.RING_FINGER_TIP],
        landmarks[mp_hands.HandLandmark.PINKY_TIP],
        landmarks[mp_hands.HandLandmark.WRIST]
    ]

    # Check thumbs up
    thumb_upwards = thumb_tip.y < thumb_ip.y < thumb_mcp.y < thumb_cmc.y
    thumb_higher_than_others = all(
        thumb_tip.y < landmark.y for landmark in other_landmarks
    )
    if thumb_upwards and thumb_higher_than_others:
        return "Thumbs Up"

    # Check thumbs down
    thumb_downwards = thumb_tip.y > thumb_ip.y > thumb_mcp.y > thumb_cmc.y
    thumb_lower_than_others = all(
        thumb_tip.y > landmark.y for landmark in other_landmarks
    )
    if thumb_downwards and thumb_lower_than_others:
        return "Thumbs Down"

    return "No Gesture"

# Function to detect gestures and perform actions
def recognize_gesture(landmarks):
    global selected_item_index
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    wrist = landmarks[mp_hands.HandLandmark.WRIST]

    # Index Finger Pointing Gesture
    if index_tip.y < middle_tip.y:  # Index finger up
        x = index_tip.x
        y = index_tip.y

        # Determine which menu item to highlight based on finger position
        angle = math.degrees(math.atan2(y - 0.5, x - 0.5)) + 90
        angle = (angle + 360) % 360  # Normalize angle
        selected_item_index = int(len(menu_items) * angle / 360) % len(menu_items)

        return "Pointing Gesture", f"Highlighting: {menu_items[selected_item_index]}"

    # Open Hand Gesture to select
    if abs(index_tip.y - wrist.y) > 0.2 and abs(middle_tip.y - wrist.y) > 0.2:
        return "Open Hand Gesture", f"Selected: {menu_items[selected_item_index]}"

    return "Unknown Gesture", "No Action"

def update_video():
    global selected_item_index
    ret, frame = cap.read()
    if not ret:
        return

    # Flip the frame for a mirror effect
    frame = cv2.flip(frame, 1)

    # Convert the frame to RGB for Mediapipe processing
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Detect thumbs up/down gestures
            thumb_gesture = detect_thumbs_gesture(hand_landmarks.landmark)

            # Perform scrolling actions
            if thumb_gesture == "Thumbs Up":
                pyautogui.scroll(20)  # Scroll up
            elif thumb_gesture == "Thumbs Down":
                pyautogui.scroll(-20)  # Scroll down

            # Detect gesture and update menu
            gesture, action = recognize_gesture(hand_landmarks.landmark)

            # Update selected text if Open Hand Gesture is detected
            if "Selected" in action:
                selected_text_label.config(text=action)
            else:
                draw_circular_menu(selected_item_index)

            # Draw hand landmarks on the RGB frame
            mp_drawing.draw_landmarks(frame_rgb, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Convert the RGB frame directly for Tkinter display
    resized_frame = cv2.resize(frame_rgb, (450, 325))
    frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))

    # Display the frame on the canvas
    menu_canvas.create_image(400, 480, anchor=tk.NW, image=frame_image, tags="camera")

    # Keep a reference to the image to prevent garbage collection
    menu_canvas.image = frame_image

    # Schedule the next frame update
    root.after(10, update_video)

# Initial menu drawing
draw_circular_menu(selected_item_index)

# Start processing video in the background
update_video()

# Run the Tkinter main loop
root.mainloop()

# Release resources
cap.release()
cv2.destroyAllWindows()
