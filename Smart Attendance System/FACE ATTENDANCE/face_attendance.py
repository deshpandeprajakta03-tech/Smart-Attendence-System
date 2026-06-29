import os
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
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
    valid_exts = {".jpg", ".jpeg", ".png"}
    for file in os.listdir(STUDENT_FOLDER):
        if not any(file.lower().endswith(ext) for ext in valid_exts):
            continue
        img_path = os.path.join(STUDENT_FOLDER, file)
        img = cv2.imread(img_path)
        if img is not None:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            try:
                encs = face_recognition.face_encodings(rgb)
                if encs:
                    images.append(encs[0])
                    names.append(os.path.splitext(file)[0])
            except Exception as e:
                print(f"Error encoding {file}: {e}")
    return images, names

known_encodings, known_names = load_known_faces()

def calculate_duration(login, logoff):
    FMT = "%H:%M:%S"
    try:
        # Strip in case of leading/trailing spaces in CSV
        t1 = datetime.strptime(str(login).strip(), FMT)
        t2 = datetime.strptime(str(logoff).strip(), FMT)
        if t2 < t1:
            t2 += timedelta(days=1)
        dur = t2 - t1
        total_seconds = int(dur.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except Exception as e:
        print(f"Duration error: {e}")
        return "N/A"

def recognize_face(image):
    if not known_encodings:
        return None
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)
    encs = face_recognition.face_encodings(rgb, faces)
    for encode in encs:
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
    name = name.strip()
    today = date.today().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    print(f"Attendance Action: {mode} for {name} at {now}")

    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8', dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_FILE, encoding='latin1', dtype=str)
    except Exception:
        df = pd.DataFrame(columns=COLUMNS)

    # Clean data for comparison
    df['Name'] = df['Name'].astype(str).str.strip()
    df['Date'] = df['Date'].astype(str).str.strip()

    if mode == "login":
        # Check if already logged in today (active session)
        mask = (df['Name'].str.lower() == name.lower()) & (df['Date'] == today) & \
               ((df['Logoff Time'].isna()) | (df['Logoff Time'].astype(str).str.strip() == ""))
        
        if not df[mask].empty:
            return f"⚠️ {name} is already logged in (active session found)."
        
        # Create new login
        new_row = pd.DataFrame([[name, today, now, "", ""]], columns=COLUMNS)
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(CSV_FILE, index=False, encoding='utf-8')
        print(f"Login successful for {name}")
        return f"✅ {name} logged in at {now}"

    elif mode == "logoff":
        # Find active session (today, name, no logoff time)
        mask = (df['Name'].str.lower() == name.lower()) & (df['Date'] == today) & \
               ((df['Logoff Time'].isna()) | (df['Logoff Time'].astype(str).str.strip() == ""))
        
        indices = df.index[mask].tolist()
        
        if not indices:
            print(f"Logoff failed: No active login for {name} on {today}")
            return f"⚠️ No active login found for {name} today. Please Log In first."
        
        # Update the last active row
        idx = indices[-1]
        login_time = df.loc[idx, 'Login Time']
        duration = calculate_duration(login_time, now)
        
        df.loc[idx, 'Logoff Time'] = now
        df.loc[idx, 'Duration'] = duration
        df.to_csv(CSV_FILE, index=False, encoding='utf-8')
        print(f"Logoff successful for {name}. Duration: {duration}")
        return f"📤 {name} logged off at {now} — Duration: {duration}"

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

COLUMNS = ['Name', 'Date', 'Login Time', 'Logoff Time', 'Duration']

def get_attendance_log():
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8', dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_FILE, encoding='latin1', dtype=str)
    # Ensure all columns always exist
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNS].fillna("")

def get_student_list():
    if not os.path.exists(STUDENT_FOLDER): return []
    return [os.path.splitext(f)[0] for f in os.listdir(STUDENT_FOLDER) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

# --- Gradio UI ---
with gr.Blocks(title="Smart Attendance") as demo:
    gr.Markdown("# 🧠 Smart Face Recognition Attendance\nReal-time Login & Logoff with Administrative Controls")

    with gr.Tab("📸 Attendance"):
        with gr.Row():
            with gr.Column(scale=1):
                webcam = gr.Image(sources=["webcam"], label="📷 Capture Your Face", height=300)

            with gr.Column(scale=1):
                gr.Markdown("### Mark Your Attendance")
                login_btn = gr.Button("📥 Log In", variant="primary", size="lg")
                logoff_btn = gr.Button("📤 Log Off", variant="secondary", size="lg")
                output_text = gr.Textbox(label="Status", interactive=False, lines=2)
                output_image = gr.Image(label="Recognized Face", height=150)

        def do_login(image):
            return attendance_action(image, "login")

        def do_logoff(image):
            return attendance_action(image, "logoff")

        login_btn.click(do_login, inputs=[webcam], outputs=[output_image, output_text])
        logoff_btn.click(do_logoff, inputs=[webcam], outputs=[output_image, output_text])

    with gr.Tab("📊 Log History"):
        with gr.Column():
            attendance_df = gr.DataFrame(value=get_attendance_log(), interactive=False, wrap=True)
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh Log")
                download_file = gr.DownloadButton("⬇️ Download CSV", value=CSV_FILE, variant="primary")

        refresh_btn.click(fn=get_attendance_log, outputs=attendance_df)

    with gr.Tab("🛠️ Admin Panel") as tab_admin:
        with gr.Row():
            with gr.Column():
                gr.Markdown("### ➕ Add New Student")
                new_student_name = gr.Textbox(label="Student Name", placeholder="Enter name here...")
                new_student_image = gr.Image(sources=["webcam"], label="Capture Face")
                add_btn = gr.Button("➕ Add Student", variant="primary")
                add_status = gr.Textbox(label="Add Status", interactive=False)
            
            with gr.Column():
                gr.Markdown("### 🗑️ Manage Students")
                remove_student_dropdown = gr.Dropdown(choices=get_student_list(), label="Select Student to Remove")
                remove_btn = gr.Button("🗑️ Remove Student", variant="stop")
                remove_status = gr.Textbox(label="Remove Status", interactive=False)

        # Dynamic updates
        def handle_add(img, name):
            status = add_student(img, name)
            return status, gr.update(choices=get_student_list())
            
        def handle_remove(name):
            status = remove_student(name)
            return status, gr.update(choices=get_student_list(), value=None)

        add_btn.click(handle_add, inputs=[new_student_image, new_student_name], outputs=[add_status, remove_student_dropdown])
        remove_btn.click(handle_remove, inputs=remove_student_dropdown, outputs=[remove_status, remove_student_dropdown])

if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="127.0.0.1")
