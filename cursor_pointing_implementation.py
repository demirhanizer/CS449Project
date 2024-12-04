import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import math

# Initialize MediaPipe Hand solution
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Start video capture
cap = cv2.VideoCapture(1)  # Adjust camera index if necessary

# Initialize Tkinter GUI
root = tk.Tk()
root.title("Circular Menu with Gesture Control")
root.geometry("1200x800")

# Circular menu items
menu_items = [
    "Hoş Geldiniz", "Teşekkür Ederim", "Tuş Takımı",
    "Hoşça kal", "Hayır", "Evet", "Geri", "Merhaba, Nasılsın?"
]
selected_item_index = 0  # Index of the currently highlighted menu item

# Canvas for the circular menu and camera feed
menu_canvas = tk.Canvas(root, width=1200, height=800, bg="lightgray")
menu_canvas.pack()

# Text to display the selected option
selected_text_label = tk.Label(root, text="Selected: None", font=("Helvetica", 16), bg="lightgray", fg="black")
selected_text_label.place(x=500, y=720)

# Function to draw the circular menu
def draw_circular_menu(selected_index):
    menu_canvas.delete("all")  # Clear canvas
    center_x, center_y = 600, 250  # Center of the menu
    radius = 250  # Radius of the menu circle
    angle_step = 360 / len(menu_items)

    for i, item in enumerate(menu_items):
        angle = math.radians(i * angle_step - 90)  # Calculate angle for item
        x = center_x + radius * math.cos(angle)  # X-coordinate
        y = center_y + radius * math.sin(angle)  # Y-coordinate
        color = "red" if i == selected_index else "black"  # Highlight selected

        # Draw box around the menu item
        box_x1, box_y1 = x - 75, y - 25
        box_x2, box_y2 = x + 75, y + 25
        menu_canvas.create_rectangle(box_x1, box_y1, box_x2, box_y2, fill="white", outline=color, width=2)

        # Draw the text
        menu_canvas.create_text(x, y, text=item, fill=color, font=("Helvetica", 14, "bold"))

# Function to detect gestures and update menu selection
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
    global selected_item_index
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
            # Detect gesture and perform actions
            gesture, action = recognize_gesture(hand_landmarks.landmark)

            # Update selected text if Open Hand Gesture is detected
            if "Selected" in action:
                selected_text_label.config(text=action)
            else:
                # Draw updated menu
                draw_circular_menu(selected_item_index)

            # Draw hand landmarks
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Resize frame for Tkinter display
    resized_frame = cv2.resize(frame, (400, 300))
    frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))

    # Display the frame centered at the bottom
    menu_canvas.create_image(400, 450, anchor=tk.NW, image=frame_image)

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