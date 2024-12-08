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
    "Hoş Geldiniz", "Teşekkür Ederim", "Bugün hava nasıl?",
    "Hoşça kal", "Hayır", "Evet", "Geri", "Merhaba, Nasılsın?"
]
selected_item_index = 0

# Canvas for the circular menu and camera feed
menu_canvas = tk.Canvas(root, width=1200, height=800, bg="lightgray")
menu_canvas.pack()

# Text to display the selected option
selected_text_label = tk.Label(root, text="Selected: None", font=("Helvetica", 16), bg="lightgray", fg="black")
selected_text_label.place(x=10, y=750)

# Menu center and radius
center_x, center_y = 600, 250
menu_radius = 180

def draw_circular_menu(selected_index):
    menu_canvas.delete("menu")  # Clear previous menu elements
    angle_step = 360 / len(menu_items)

    for i, item in enumerate(menu_items):
        angle = math.radians(i * angle_step - 90)  # Calculate angle for item
        x = center_x + menu_radius * math.cos(angle)
        y = center_y + menu_radius * math.sin(angle)
        color = "red" if i == selected_index else "black"

        # Draw menu item box
        box_x1, box_y1 = x - 50, y - 20
        box_x2, box_y2 = x + 50, y + 20
        menu_canvas.create_rectangle(box_x1, box_y1, box_x2, box_y2, fill="white", outline=color, width=2, tags="menu")

        # Draw the text
        menu_canvas.create_text(x, y, text=item, fill=color, font=("Helvetica", 12, "bold"), tags="menu")

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
    thumb_higher_than_others = all(thumb_tip.y < lm.y for lm in other_landmarks)
    if thumb_upwards and thumb_higher_than_others:
        return "Thumbs Up"

    # Check thumbs down
    thumb_downwards = thumb_tip.y > thumb_ip.y > thumb_mcp.y > thumb_cmc.y
    thumb_lower_than_others = all(thumb_tip.y > lm.y for lm in other_landmarks)
    if thumb_downwards and thumb_lower_than_others:
        return "Thumbs Down"

    return "No Gesture"

def recognize_gesture(landmarks):
    global selected_item_index
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    wrist = landmarks[mp_hands.HandLandmark.WRIST]

    # Index Finger Pointing Gesture
    if index_tip.y < middle_tip.y:  # Index finger is raised
        x = index_tip.x
        y = index_tip.y
        # Compute angle for menu selection
        angle = math.degrees(math.atan2(y - 0.5, x - 0.5)) + 90
        angle = (angle + 360) % 360  # Normalize angle
        selected_item_index = int(len(menu_items) * angle / 360) % len(menu_items)

        return "Pointing Gesture", angle, f"Highlighting: {menu_items[selected_item_index]}"

    # Open Hand Gesture to select
    if abs(index_tip.y - wrist.y) > 0.2 and abs(middle_tip.y - wrist.y) > 0.2:
        return "Open Hand Gesture", None, f"Selected: {menu_items[selected_item_index]}"

    return "Unknown Gesture", None, "No Action"

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

    # Clear previous camera frame from the canvas
    menu_canvas.delete("camera")
    menu_canvas.delete("cursor")

    gesture = None
    angle = None

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
            gesture, angle, action = recognize_gesture(hand_landmarks.landmark)

            if gesture == "Open Hand Gesture":
                selected_text_label.config(text=action)
            else:
                draw_circular_menu(selected_item_index)

            # Draw landmarks on the frame (optional, just for debugging)
            mp_drawing.draw_landmarks(frame_rgb, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Convert the RGB frame for Tkinter display
    resized_frame = cv2.resize(frame_rgb, (450, 325))
    frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))

    # Display the camera frame on the canvas
    menu_canvas.create_image(400, 480, anchor=tk.NW, image=frame_image, tags="camera")
    menu_canvas.image = frame_image

    # If we have a pointing gesture, draw a cursor on the menu
    if gesture == "Pointing Gesture" and angle is not None:
        # Convert angle (0 at top, increases clockwise) to radians
        cursor_angle = math.radians(angle - 90)  
        # Choose a radius for the cursor to appear slightly inside the menu circle
        cursor_radius = menu_radius * 0.7
        cursor_x = center_x + cursor_radius * math.cos(cursor_angle)
        cursor_y = center_y + cursor_radius * math.sin(cursor_angle)

        # Draw a small circle (cursor) on the menu
        menu_canvas.create_oval(
            cursor_x - 10, cursor_y - 10, cursor_x + 10, cursor_y + 10,
            fill="blue", outline="black", tags="cursor"
        )

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
