import tkinter as tk
from tkinter import messagebox
import cv2
import mediapipe as mp
import pyautogui

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Gesture recognition logic
def recognize_gesture(landmarks):
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    wrist = landmarks[mp_hands.HandLandmark.WRIST]

    if index_tip.y < middle_tip.y and middle_tip.y > wrist.y:
        return "Cursor-Pointing Gesture"
    elif abs(thumb_tip.y - wrist.y) > 0.2 and abs(index_tip.y - wrist.y) > 0.2:
        return "Open Hand Gesture"
    elif abs(index_tip.y - wrist.y) < 0.2:
        return "Close Hand Gesture"
    return "Unknown Gesture"

# GUI functions
def perform_action(action):
    if action == "Open Hand Gesture":
        messagebox.showinfo("Gesture Detected", "Scrolling Action Triggered")
    elif action == "Cursor-Pointing Gesture":
        messagebox.showinfo("Gesture Detected", "Cursor Movement Triggered")
    elif action == "Close Hand Gesture":
        messagebox.showinfo("Gesture Detected", "Confirm Action Triggered")

# Tkinter GUI setup
def create_gui():
    root = tk.Tk()
    root.title("Gesture-Controlled Interface")
    root.geometry("600x400")

    # Create a grid layout for buttons
    for row in range(3):
        for col in range(3):
            btn = tk.Button(root, text=f"Button {row*3 + col + 1}", width=20, height=5)
            btn.grid(row=row, column=col, padx=5, pady=5)

    # Main interface loop
    def update_interface():
        ret, frame = cap.read()
        if not ret:
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                gesture = recognize_gesture(hand_landmarks.landmark)
                perform_action(gesture)

        root.after(10, update_interface)

    root.after(10, update_interface)
    root.mainloop()

# Video capture
cap = cv2.VideoCapture(1)

# Start the application
create_gui()

# Release resources
cap.release()
cv2.destroyAllWindows()
