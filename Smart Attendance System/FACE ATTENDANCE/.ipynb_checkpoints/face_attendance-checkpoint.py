import gradio as gr
import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime, timedelta, date
import pandas as pd

# CONFIG
STUDENT_FOLDER = "students"
CSV_FILE = "attendance.csv"
UNRECOGNIZED_LOG = "unrecognized_log.csv"

# INIT
if not os.path.exists(STUDENT_FOLDER):
    os.makedirs(STUDENT_FOLDER)

if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=['Name', 'Date', 'Login Time', 'Logoff Time', 'Duration'])
    df.to_csv(CSV_FILE, index=False)

if not os.path.exists("unrecognized_faces"):
    os.makedirs("unrecognized_faces")

# Load known faces and encodings
def load_known_faces():
    images, names = [], []
    for file in os.listdir(STUDENT_FOLDER):
        img_path = os.path.join(STUDENT_FOLDER, file)
        img = cv2.imread(img_path)
        if img is not None:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encs = face_recognition.face_encodings(rgb)
            if encs:
                images.append(encs[0])
                names.append(os.path.splitext(file)[0])
    return images, names

known_encodings, known_names = load_known_faces()

def calculate_duration(login, logoff):
    FMT = "%H:%M:%S"
    try:
        t1 = datetime.strptime(login, FMT)
        t2 = datetime.strptime(logoff, FMT)
        if t2 < t1:
            t2 += timedelta(days=1)
        dur = t2 - t1
        mins = dur.total_seconds() / 60
        return f"{int(mins)} min" if mins < 60 else f"{mins/60:.1f} hr"
    except:
        return "Invalid"

def recognize_face(image):
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)
    encs = face_recognition.face_encodings(rgb, faces)
    for encode, loc in zip(encs, faces):
        matches = face_recognition.compare_faces(known_encodings, encode)
        face_dis = face_recognition.face_distance(known_encodings, encode)
        match_index = np.argmin(face_dis)
        if matches[match_index]:
            return known_names[match_index]
    return None

def log_unrecognized(frame):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"unrecognized_{ts}.jpg"
    path = os.path.join("unrecognized_faces", filename)
    cv2.imwrite(path, frame)
    with open(UNRECOGNIZED_LOG, "a") as f:
        f.write(f"{filename},{ts}\n")

def mark_attendance(name, mode):
    today = date.today().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")

    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_FILE, encoding='latin1')

    today_data = df[(df['Name'] == name) & (df['Date'] == today)]

    if mode == "login":
        if today_data.empty:
            new_row = pd.DataFrame([[name, today, now, "", ""]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False, encoding='utf-8')
            return f"✅ {name} logged in at {now}"
        else:
            return f"⚠️ {name} already logged in today."
    elif mode == "logoff":
        if not today_data.empty and pd.isna(today_data.iloc[0]['Logoff Time']):
            login_time = today_data.iloc[0]['Login Time']
            duration = calculate_duration(login_time, now)
            df.loc[(df['Name'] == name) & (df['Date'] == today), ['Logoff Time', 'Duration']] = [now, duration]
            df.to_csv(CSV_FILE, index=False, encoding='utf-8')
            return f"📤 {name} logged off at {now} — Duration: {duration}"
        else:
            return f"⚠️ {name} hasn't logged in yet or already logged off."

def attendance_action(image, mode):
    if image is None:
        return None, "🚫 No image captured."

    # Convert PIL Image to OpenCV format
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    name = recognize_face(frame)
    if name:
        msg = mark_attendance(name, mode)
        return image, msg
    else:
        log_unrecognized(frame)
        return image, "❌ Face not recognized."

def add_student(image, name):
    if image is None or not name.strip():
        return "Please provide a name and capture an image."

    file_path = os.path.join(STUDENT_FOLDER, f"{name}.jpg")
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    cv2.imwrite(file_path, frame)

    # Reload known faces after adding
    global known_encodings, known_names
    known_encodings, known_names = load_known_faces()

    return f"✅ Student '{name}' added."

def remove_student(name):
    if not name:
        return "Please select a student to remove."
    file_path = os.path.join(STUDENT_FOLDER, f"{name}.jpg")
    if os.path.exists(file_path):
        os.remove(file_path)
        global known_encodings, known_names
        known_encodings, known_names = load_known_faces()
        return f"🗑️ Removed student '{name}'."
    else:
        return "Student image not found."

def get_attendance_log():
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_FILE, encoding='latin1')
    return df

# --- Gradio UI ---

with gr.Blocks() as demo:
    gr.Markdown("# 🧠 Smart Face Recognition Attendance System")
    gr.Markdown("Real-time Login / Logoff using Face Recognition with Admin Controls")

    with gr.Tab("📸 Attendance"):
        with gr.Row():
            webcam = gr.Image(source="webcam", streaming=True, tool=None)
            output_image = gr.Image()
        output_text = gr.Textbox(label="Status", interactive=False)

        login_btn = gr.Button("📥 Log In")
        logoff_btn = gr.Button("📤 Log Off")

        login_btn.click(attendance_action, inputs=[webcam, gr.State("login")], outputs=[output_image, output_text], queue=False)
        logoff_btn.click(attendance_action, inputs=[webcam, gr.State("logoff")], outputs=[output_image, output_text], queue=False)

    with gr.Tab("📊 Log History"):
        attendance_df = gr.DataFrame(value=get_attendance_log())
        refresh_btn = gr.Button("🔄 Refresh Log")
        refresh_btn.click(lambda: get_attendance_log(), outputs=attendance_df)

        download_btn = gr.DownloadButton("⬇️ Download CSV", file_name="attendance.csv", data=CSV_FILE)

    with gr.Tab("🛠️ Admin Panel"):
        with gr.Row():
            new_student_name = gr.Textbox(label="New Student Name")
            new_student_image = gr.Image(source="webcam", streaming=True, tool=None)
        add_btn = gr.Button("➕ Add Student")
        add_status = gr.Textbox(interactive=False)

        add_btn.click(add_student, inputs=[new_student_image, new_student_name], outputs=add_status)

        with gr.Row():
            all_students = os.listdir(STUDENT_FOLDER)
            all_students = [os.path.splitext(f)[0] for f in all_students]
            remove_student_dropdown = gr.Dropdown(all_students, label="Remove Student")
        remove_btn = gr.Button("🗑️ Remove Student")
        remove_status = gr.Textbox(interactive=False)

        remove_btn.click(remove_student, inputs=remove_student_dropdown, outputs=remove_status)

if __name__ == "__main__":
    demo.launch()
