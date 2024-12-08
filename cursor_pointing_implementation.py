import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import math
import pyautogui  # For scrolling functionality
import time

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

# Global state
initial_mode = True  # Start with initial mode
mode = None           # Will be "menu" or "list" after initial selection
finger_up_start = None
finger_down_start = None
GESTURE_HOLD_TIME = 3.0  # seconds required to hold a gesture (for initial menu)

# For listed mode: continuous navigation
SCROLL_DELAY = 0.5  # How often to move when holding thumbs up/down
last_gesture = None
last_gesture_time = None

# Circular menu items
menu_items = [
    "Listed", "Hoş Geldiniz", "Teşekkür Ederim", "Tuş Takımı",
    "Hoşça kal", "Hayır", "Evet", "Geri", "Merhaba, Nasılsın?",
    "Ekstra 1", "Ekstra 2", "Ekstra 3", "Ekstra 4", "Ekstra 5",
    "Ekstra 6", "Ekstra 7", "Ekstra 8", "Ekstra 9", "Ekstra 10"
]
selected_item_index = 0

# Canvas for the menu and camera feed
menu_canvas = tk.Canvas(root, width=1200, height=800, bg="lightgray")
menu_canvas.pack()

# Text to display the selected option
selected_text_label = tk.Label(root, text="Selected: None", font=("Helvetica", 16), bg="lightgray", fg="black")
selected_text_label.place(x=10, y=750)

# Menu center and radius
center_x, center_y = 600, 250
menu_radius = 180

# In listed mode, we will display a Listbox with multiple items
listbox = tk.Listbox(root, width=50, height=20, font=("Helvetica", 20))
listbox.place_forget()  # Hide initially
for item in menu_items:
    listbox.insert(tk.END, item)

# Keep track of currently highlighted item in list mode
listed_highlight_index = 0
listbox.select_set(listed_highlight_index)
listbox.activate(listed_highlight_index)

def draw_initial_menu():
    """Draw the initial screen with two options: Listed and Menu Tab."""
    menu_canvas.delete("all")
    menu_canvas.create_text(600, 100, text="Choose Your Option by Holding Gesture for 3s",
                            fill="black", font=("Helvetica", 24, "bold"))

    # Draw "Listed" button
    menu_canvas.create_rectangle(400, 300, 550, 400, fill="white", outline="black", width=2, tags="initial")
    menu_canvas.create_text(475, 350, text="Listed", fill="black", font=("Helvetica", 16, "bold"), tags="initial")

    # Draw "Menu Tab" button
    menu_canvas.create_rectangle(650, 300, 800, 400, fill="white", outline="black", width=2, tags="initial")
    menu_canvas.create_text(725, 350, text="Menu Tab", fill="black", font=("Helvetica", 16, "bold"), tags="initial")

def draw_circular_menu(selected_index):
    if initial_mode:
        return  # Don't draw the circular menu during initial mode
    menu_canvas.delete("menu")  # Clear previous menu elements
    angle_step = 360 / len(menu_items)

    for i, item in enumerate(menu_items):
        angle = math.radians(i * angle_step - 90)
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

    if mode == "menu":
        # Index Finger Pointing Gesture
        if index_tip.y < middle_tip.y:  # Index finger is raised
            x = index_tip.x
            y = index_tip.y
            # Compute angle for menu selection
            angle = math.degrees(math.atan2(y - 0.5, x - 0.5)) + 90
            angle = (angle + 360) % 360  # Normalize angle
            selected_item_index = int(len(menu_items) * angle / 360) % len(menu_items)
            return "Pointing Gesture", angle, f"Highlighting: {menu_items[selected_item_index]}"

        # Open Hand Gesture to select (in menu mode only)
        if abs(index_tip.y - wrist.y) > 0.2 and abs(middle_tip.y - wrist.y) > 0.2:
            return "Open Hand Gesture", None, f"Selected: {menu_items[selected_item_index]}"

    return "Unknown Gesture", None, "No Action"

def check_initial_selection(landmarks):
    global finger_up_start, finger_down_start, initial_mode, mode
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

    # Finger up criteria
    finger_up = index_tip.y < middle_tip.y
    current_time = time.time()

    if finger_up:
        # Reset down timer
        finger_down_start = None
        if finger_up_start is None:
            finger_up_start = current_time
        else:
            if current_time - finger_up_start >= GESTURE_HOLD_TIME:
                # User chose "Listed"
                mode = "list"
                initial_mode = False
                clear_initial_screen()
    else:
        # Finger down
        finger_up_start = None
        if finger_down_start is None:
            finger_down_start = current_time
        else:
            if current_time - finger_down_start >= GESTURE_HOLD_TIME:
                # User chose "Menu Tab"
                mode = "menu"
                initial_mode = False
                clear_initial_screen()

def clear_initial_screen():
    """Clear the initial screen and proceed according to chosen mode."""
    menu_canvas.delete("all")
    if mode == "menu":
        draw_circular_menu(selected_item_index)
    elif mode == "list":
        show_listed_view()

def show_listed_view():
    """Show the listbox of items in listed mode."""
    listbox.place(x=400, y=100)
    selected_text_label.config(text="Selected: None (Listed Mode)")

def switch_to_listed_mode():
    global mode, listed_highlight_index
    mode = "list"
    menu_canvas.delete("all")
    listbox.place(x=400, y=100)
    selected_text_label.config(text="Selected: None (Listed Mode)")
    # Reset highlight to 0 or keep current
    listed_highlight_index = 0
    listbox.select_clear(0, tk.END)
    listbox.select_set(listed_highlight_index)
    listbox.activate(listed_highlight_index)

def switch_to_menu_mode():
    global mode
    mode = "menu"
    listbox.place_forget()
    draw_circular_menu(selected_item_index)
    selected_text_label.config(text="Selected: None")

def move_list_highlight(direction):
    """Move the highlighted selection in the list up or down by one item."""
    global listed_highlight_index
    if direction == "up":
        if listed_highlight_index > 0:
            listed_highlight_index -= 1
    elif direction == "down":
        if listed_highlight_index < listbox.size() - 1:
            listed_highlight_index += 1

    listbox.select_clear(0, tk.END)
    listbox.select_set(listed_highlight_index)
    listbox.activate(listed_highlight_index)

def handle_listed_mode_gesture(gesture):
    """
    In listed mode:
    - Holding Thumbs Up moves continuously up through the items.
    - Holding Thumbs Down moves continuously down through the items.
    - Movement happens at an interval defined by SCROLL_DELAY.
    """
    global last_gesture, last_gesture_time
    current_time = time.time()

    if gesture in ["Thumbs Up", "Thumbs Down"]:
        if last_gesture == gesture:
            # Same gesture continues
            # Check if enough time passed since last move
            if current_time - last_gesture_time >= SCROLL_DELAY:
                # Move one step in the given direction
                direction = "up" if gesture == "Thumbs Up" else "down"
                move_list_highlight(direction)
                last_gesture_time = current_time
        else:
            # New gesture detected (or different from last)
            last_gesture = gesture
            last_gesture_time = current_time
            # Move once immediately
            direction = "up" if gesture == "Thumbs Up" else "down"
            move_list_highlight(direction)
    else:
        # No thumbs gesture, reset
        last_gesture = None
        last_gesture_time = None

def update_video():
    global selected_item_index, initial_mode, mode
    ret, frame = cap.read()
    if not ret:
        return

    # Flip the frame
    frame = cv2.flip(frame, 1)

    # Convert the frame to RGB for Mediapipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if initial_mode:
        draw_initial_menu()

    if initial_mode and results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            check_initial_selection(hand_landmarks.landmark)
    else:
        # After initial mode is done, proceed according to current mode
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                thumb_gesture = detect_thumbs_gesture(hand_landmarks.landmark)

                if mode == "menu":
                    menu_canvas.delete("camera")
                    menu_canvas.delete("cursor")

                    # System scrolling if you wish to keep it
                    if thumb_gesture == "Thumbs Up":
                        pyautogui.scroll(20)
                    elif thumb_gesture == "Thumbs Down":
                        pyautogui.scroll(-20)

                    gesture, angle, action = recognize_gesture(hand_landmarks.landmark)

                    if gesture == "Open Hand Gesture":
                        selected_text_label.config(text=action)
                        # If user selected "Listed"
                        if menu_items[selected_item_index] == "Listed":
                            switch_to_listed_mode()
                    else:
                        draw_circular_menu(selected_item_index)

                    # Draw hand landmarks for debugging (optional)
                    mp_drawing.draw_landmarks(frame_rgb, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Display camera in menu mode
                    resized_frame = cv2.resize(frame_rgb, (450, 325))
                    frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))
                    menu_canvas.create_image(400, 480, anchor=tk.NW, image=frame_image, tags="camera")
                    menu_canvas.image = frame_image

                    # Draw cursor if pointing
                    if gesture == "Pointing Gesture" and angle is not None:
                        cursor_angle = math.radians(angle - 90)
                        cursor_radius = menu_radius * 0.7
                        cursor_x = center_x + cursor_radius * math.cos(cursor_angle)
                        cursor_y = center_y + cursor_radius * math.sin(cursor_angle)
                        menu_canvas.create_oval(
                            cursor_x - 10, cursor_y - 10, cursor_x + 10, cursor_y + 10,
                            fill="blue", outline="black", tags="cursor"
                        )

                elif mode == "list":
                    # In listed mode, handle thumbs gestures for continuous navigation
                    handle_listed_mode_gesture(thumb_gesture)

                    # Draw hand landmarks for debugging (optional)
                    mp_drawing.draw_landmarks(frame_rgb, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Display camera feed in listed mode (top-left corner)
                    menu_canvas.delete("all")
                    resized_frame = cv2.resize(frame_rgb, (200, 150))
                    frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))
                    menu_canvas.create_image(10, 10, anchor=tk.NW, image=frame_image)
                    menu_canvas.image = frame_image
        else:
            # No hands detected
            if mode == "menu":
                # Still need to show camera feed
                menu_canvas.delete("camera")
                menu_canvas.delete("cursor")
                resized_frame = cv2.resize(frame_rgb, (450, 325))
                frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))
                menu_canvas.create_image(400, 480, anchor=tk.NW, image=frame_image, tags="camera")
                menu_canvas.image = frame_image
            elif mode == "list":
                # Just keep showing the list and camera feed in the corner
                menu_canvas.delete("all")
                resized_frame = cv2.resize(frame_rgb, (200, 150))
                frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))
                menu_canvas.create_image(10, 10, anchor=tk.NW, image=frame_image)
                menu_canvas.image = frame_image

    # Schedule next frame
    root.after(10, update_video)

# Start processing video in the background
update_video()

# Run the Tkinter main loop
root.mainloop()

# Release resources
cap.release()
cv2.destroyAllWindows()
