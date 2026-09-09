import gradio as gr
import cv2
import numpy as np
import os
from datetime import datetime, timedelta, date
import pandas as pd
from deepface import DeepFace

# CONFIG
STUDENT_FOLDER = "students"
CSV_FILE = "attendance.csv"
UNRECOGNIZED_FOLDER = "unrecognized_faces"
COLUMNS = ['Name', 'Date', 'Login Time', 'Logoff Time', 'Duration']

# INIT folders and CSV
for folder in [STUDENT_FOLDER, UNRECOGNIZED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

def recognize_face(frame):
    temp_path = "temp_capture.jpg"
    cv2.imwrite(temp_path, frame)
    try:
        results = DeepFace.find(
            img_path=temp_path,
            db_path=STUDENT_FOLDER,
            model_name="Facenet",
            enforce_detection=False,
            silent=True
        )
        if results and not results[0].empty:
            best = results[0].iloc[0]
            identity = best["identity"]
            return os.path.splitext(os.path.basename(identity))[0]
    except Exception as e:
        print(f"Recognition error: {e}")
    return None

def calculate_duration(login, logoff):
    FMT = "%H:%M:%S"
    try:
        t1 = datetime.strptime(str(login).strip(), FMT)
        t2 = datetime.strptime(str(logoff).strip(), FMT)
        if t2 < t1:
            t2 += timedelta(days=1)
        total = int((t2 - t1).total_seconds())
        h, m, s = total // 3600, (total % 3600) // 60, total % 60
        return f"{h}h {m}m" if h > 0 else (f"{m}m {s}s" if m > 0 else f"{s}s")
    except:
        return "N/A"

def mark_attendance(name, mode):
    today = date.today().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    try:
        df = pd.read_csv(CSV_FILE, dtype=str)
    except:
        df = pd.DataFrame(columns=COLUMNS)
    df['Name'] = df['Name'].astype(str).str.strip()
    df['Date'] = df['Date'].astype(str).str.strip()

    if mode == "login":
        mask = (df['Name'].str.lower() == name.lower()) & (df['Date'] == today) & \
               ((df['Logoff Time'].isna()) | (df['Logoff Time'].str.strip() == ""))
        if not df[mask].empty:
            return f"⚠️ {name} already logged in."
        df = pd.concat([df, pd.DataFrame([[name, today, now, "", ""]], columns=COLUMNS)], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        return f"✅ {name} logged in at {now}"

    elif mode == "logoff":
        mask = (df['Name'].str.lower() == name.lower()) & (df['Date'] == today) & \
               ((df['Logoff Time'].isna()) | (df['Logoff Time'].str.strip() == ""))
        indices = df.index[mask].tolist()
        if not indices:
            return f"⚠️ No active login found for {name}."
        idx = indices[-1]
        duration = calculate_duration(df.loc[idx, 'Login Time'], now)
        df.loc[idx, 'Logoff Time'] = now
        df.loc[idx, 'Duration'] = duration
        df.to_csv(CSV_FILE, index=False)
        return f"📤 {name} logged off at {now} — Duration: {duration}"

def attendance_action(image, mode):
    if image is None:
        return None, "🚫 No image captured."
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    name = recognize_face(frame)
    if name:
        return image, mark_attendance(name, mode)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    cv2.imwrite(os.path.join(UNRECOGNIZED_FOLDER, f"unrecognized_{ts}.jpg"), frame)
    return image, "❌ Face not recognized."

def add_student(image, name):
    if image is None or not name.strip():
        return "Please provide a name and capture an image."
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    cv2.imwrite(os.path.join(STUDENT_FOLDER, f"{name.strip()}.jpg"), frame)
    return f"✅ Student '{name}' added."

def remove_student(name):
    if not name:
        return "Please select a student."
    path = os.path.join(STUDENT_FOLDER, f"{name}.jpg")
    if os.path.exists(path):
        os.remove(path)
        return f"🗑️ Removed '{name}'."
    return "Student not found."

def get_attendance_log():
    try:
        df = pd.read_csv(CSV_FILE, dtype=str)
    except:
        df = pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNS].fillna("")

def get_student_list():
    return [os.path.splitext(f)[0] for f in os.listdir(STUDENT_FOLDER)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

# --- Gradio UI ---
with gr.Blocks(title="Smart Attendance") as demo:
    gr.Markdown("# 🧠 Smart Face Recognition Attendance\nReal-time Login & Logoff with Administrative Controls")

    with gr.Tab("📸 Attendance"):
        with gr.Row():
            with gr.Column():
                webcam = gr.Image(sources=["webcam"], label="📷 Capture Your Face", height=300)
            with gr.Column():
                gr.Markdown("### Mark Your Attendance")
                login_btn = gr.Button("📥 Log In", variant="primary", size="lg")
                logoff_btn = gr.Button("📤 Log Off", variant="secondary", size="lg")
                output_text = gr.Textbox(label="Status", interactive=False, lines=2)
                output_image = gr.Image(label="Captured Face", height=150)
        login_btn.click(lambda img: attendance_action(img, "login"), inputs=[webcam], outputs=[output_image, output_text])
        logoff_btn.click(lambda img: attendance_action(img, "logoff"), inputs=[webcam], outputs=[output_image, output_text])

    with gr.Tab("📊 Log History"):
        attendance_df = gr.DataFrame(value=get_attendance_log(), interactive=False, wrap=True)
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh Log")
            download_file = gr.DownloadButton("⬇️ Download CSV", value=CSV_FILE, variant="primary")
        refresh_btn.click(fn=get_attendance_log, outputs=attendance_df)

    with gr.Tab("🛠️ Admin Panel"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### ➕ Add New Student")
                new_student_name = gr.Textbox(label="Student Name", placeholder="Enter name here...")
                new_student_image = gr.Image(sources=["webcam"], label="Capture Face")
                add_btn = gr.Button("➕ Add Student", variant="primary")
                add_status = gr.Textbox(label="Status", interactive=False)
            with gr.Column():
                gr.Markdown("### 🗑️ Remove Student")
                remove_dropdown = gr.Dropdown(choices=get_student_list(), label="Select Student")
                remove_btn = gr.Button("🗑️ Remove", variant="stop")
                remove_status = gr.Textbox(label="Status", interactive=False)

        def handle_add(img, name):
            return add_student(img, name), gr.update(choices=get_student_list())

        def handle_remove(name):
            return remove_student(name), gr.update(choices=get_student_list(), value=None)

        add_btn.click(handle_add, inputs=[new_student_image, new_student_name], outputs=[add_status, remove_dropdown])
        remove_btn.click(handle_remove, inputs=remove_dropdown, outputs=[remove_status, remove_dropdown])

if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="127.0.0.1")
