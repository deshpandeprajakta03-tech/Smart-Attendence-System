import gradio as gr
import cv2
import numpy as np
import pandas as pd
import os
import shutil
from datetime import datetime
from deepface import DeepFace

# ── Paths ──────────────────────────────────────────────────────────────────────
STUDENTS_DIR    = "students"
UNRECOGNIZED_DIR = "unrecognized_faces"
ATTENDANCE_CSV  = "attendance.csv"
COLUMNS = ["Name", "Date", "Login Time", "Logoff Time", "Duration"]

os.makedirs(STUDENTS_DIR, exist_ok=True)
os.makedirs(UNRECOGNIZED_DIR, exist_ok=True)


# ── CSV helpers ────────────────────────────────────────────────────────────────

def load_rows() -> list:
    """Load attendance CSV as a list of dicts (all values are strings)."""
    if not os.path.exists(ATTENDANCE_CSV):
        return []
    try:
        df = pd.read_csv(ATTENDANCE_CSV, dtype=str)
        df = df.fillna("")
        # Keep only known columns, add missing ones
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS].to_dict(orient="records")
    except Exception:
        return []


def save_rows(rows: list):
    """Save list of dicts back to CSV."""
    df = pd.DataFrame(rows, columns=COLUMNS)
    df.to_csv(ATTENDANCE_CSV, index=False)


def rows_to_df(rows: list) -> pd.DataFrame:
    """Convert rows list to a clean string DataFrame for display."""
    if not rows:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(rows, columns=COLUMNS)
    return df.fillna("").astype(str)


def load_attendance() -> pd.DataFrame:
    return rows_to_df(load_rows())


def get_csv_path() -> str:
    if not os.path.exists(ATTENDANCE_CSV):
        save_rows([])
    return ATTENDANCE_CSV


# ── Student helpers ────────────────────────────────────────────────────────────

def get_student_images() -> list:
    exts = (".jpg", ".jpeg", ".png")
    return [
        os.path.join(STUDENTS_DIR, f)
        for f in os.listdir(STUDENTS_DIR)
        if f.lower().endswith(exts)
    ]


def get_student_list() -> list:
    exts = (".jpg", ".jpeg", ".png")
    return [
        os.path.splitext(f)[0]
        for f in os.listdir(STUDENTS_DIR)
        if f.lower().endswith(exts)
    ]


# ── Face recognition ───────────────────────────────────────────────────────────

def recognize_face(img_array: np.ndarray):
    """Returns student name on match, None otherwise."""
    student_imgs = get_student_images()
    if not student_imgs:
        return None

    tmp_path = os.path.join(UNRECOGNIZED_DIR, "_tmp_capture.jpg")
    cv2.imwrite(tmp_path, cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))

    for student_path in student_imgs:
        try:
            result = DeepFace.verify(
                img1_path=tmp_path,
                img2_path=student_path,
                model_name="Facenet",
                enforce_detection=False,
                silent=True,
            )
            if result.get("verified", False):
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                return os.path.splitext(os.path.basename(student_path))[0]
        except Exception:
            continue

    # Not recognized — save snapshot
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(UNRECOGNIZED_DIR, f"unrecognized_{ts}.jpg")
    if os.path.exists(tmp_path):
        shutil.move(tmp_path, dest)
    return None


# ── Attendance actions ─────────────────────────────────────────────────────────

def login(img):
    if img is None:
        return "⚠️ No image captured. Please capture a photo first.", load_attendance()

    name = recognize_face(img)
    if name is None:
        return "❌ Face not recognized. Snapshot saved to unrecognized_faces/.", load_attendance()

    rows  = load_rows()
    today = datetime.now().strftime("%Y-%m-%d")
    now   = datetime.now().strftime("%H:%M:%S")

    # Check for existing open session today
    for row in rows:
        if row["Name"] == name and row["Date"] == today and row["Logoff Time"] == "":
            return f"ℹ️ {name} is already logged in today.", rows_to_df(rows)

    rows.append({
        "Name":        name,
        "Date":        today,
        "Login Time":  now,
        "Logoff Time": "",
        "Duration":    "",
    })
    save_rows(rows)
    return f"✅ Login recorded for {name} at {now}.", rows_to_df(rows)


def logoff(img):
    if img is None:
        return "⚠️ No image captured. Please capture a photo first.", load_attendance()

    name = recognize_face(img)
    if name is None:
        return "❌ Face not recognized. Snapshot saved to unrecognized_faces/.", load_attendance()

    rows  = load_rows()
    today = datetime.now().strftime("%Y-%m-%d")
    now   = datetime.now().strftime("%H:%M:%S")

    # Find last open session for this person today
    target_idx = None
    for i, row in enumerate(rows):
        if row["Name"] == name and row["Date"] == today and row["Logoff Time"] == "":
            target_idx = i

    if target_idx is None:
        return f"ℹ️ {name} has no active login session today.", rows_to_df(rows)

    rows[target_idx]["Logoff Time"] = now

    # Calculate duration
    try:
        fmt      = "%H:%M:%S"
        login_dt = datetime.strptime(rows[target_idx]["Login Time"], fmt)
        logoff_dt = datetime.strptime(now, fmt)
        delta    = logoff_dt - login_dt
        h, m     = divmod(int(delta.total_seconds() // 60), 60)
        rows[target_idx]["Duration"] = f"{h}h {m}m"
    except Exception:
        rows[target_idx]["Duration"] = "N/A"

    save_rows(rows)
    duration = rows[target_idx]["Duration"]
    return f"📤 Logoff recorded for {name} at {now}. Duration: {duration}.", rows_to_df(rows)


def refresh_log():
    return load_attendance()


# ── Admin actions ──────────────────────────────────────────────────────────────

def add_student(name: str, img):
    name = name.strip()
    if not name:
        return "⚠️ Please enter a student name.", gr.Dropdown(choices=get_student_list())
    if img is None:
        return "⚠️ No image captured.", gr.Dropdown(choices=get_student_list())

    safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip()
    if not safe_name:
        return "⚠️ Invalid name.", gr.Dropdown(choices=get_student_list())

    save_path = os.path.join(STUDENTS_DIR, f"{safe_name}.jpg")
    cv2.imwrite(save_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    return f"✅ Student '{safe_name}' added.", gr.Dropdown(choices=get_student_list(), value=None)


def remove_student(name: str):
    if not name:
        return "⚠️ No student selected.", gr.Dropdown(choices=get_student_list())

    for ext in (".jpg", ".jpeg", ".png"):
        path = os.path.join(STUDENTS_DIR, f"{name}{ext}")
        if os.path.exists(path):
            os.remove(path)
            return f"🗑️ Student '{name}' removed.", gr.Dropdown(choices=get_student_list(), value=None)

    return f"⚠️ Student '{name}' not found.", gr.Dropdown(choices=get_student_list())


def refresh_dropdown():
    return gr.Dropdown(choices=get_student_list(), value=None)


# ── Gradio UI ──────────────────────────────────────────────────────────────────

with gr.Blocks(title="Smart Attendance System", theme=gr.themes.Soft()) as demo:

    gr.Markdown("# 🧠 Smart Face Recognition Attendance System\nContactless, real-time attendance tracking powered by DeepFace (Facenet).")

    with gr.Tabs():

        # ── Tab 1: Mark Attendance ─────────────────────────────────────────────
        with gr.Tab("📷 Mark Attendance"):
            gr.Markdown("Capture your face then click **Log In** or **Log Off**.")

            webcam = gr.Image(sources=["webcam"], type="numpy", label="Webcam — click 📷 to capture")

            with gr.Row():
                btn_login  = gr.Button("✅ Log In",  variant="primary")
                btn_logoff = gr.Button("📤 Log Off", variant="secondary")

            status_box = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---")
            gr.Markdown("#### 📋 Attendance Log")
            attendance_table = gr.Dataframe(
                value=load_attendance(),
                headers=COLUMNS,
                interactive=False,
                wrap=True,
            )
            with gr.Row():
                btn_refresh  = gr.Button("🔄 Refresh Log")
                btn_download = gr.DownloadButton("⬇️ Download CSV", value=get_csv_path())

            btn_login.click(fn=login,       inputs=webcam, outputs=[status_box, attendance_table])
            btn_logoff.click(fn=logoff,     inputs=webcam, outputs=[status_box, attendance_table])
            btn_refresh.click(fn=refresh_log, outputs=attendance_table)

        # ── Tab 2: Full Log ────────────────────────────────────────────────────
        with gr.Tab("📊 Full Attendance Log"):
            gr.Markdown("### Complete attendance history")
            full_table = gr.Dataframe(
                value=load_attendance(),
                headers=COLUMNS,
                interactive=False,
                wrap=True,
            )
            with gr.Row():
                btn_refresh_full  = gr.Button("🔄 Refresh")
                btn_download_full = gr.DownloadButton("⬇️ Download CSV", value=get_csv_path())

            btn_refresh_full.click(fn=refresh_log, outputs=full_table)

        # ── Tab 3: Admin Panel ─────────────────────────────────────────────────
        with gr.Tab("🛠️ Admin Panel"):
            gr.Markdown("### Manage registered students")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### ➕ Add Student")
                    student_name_input = gr.Textbox(label="Student Name", placeholder="e.g. Prajakta Deshpande")
                    student_webcam     = gr.Image(sources=["webcam"], type="numpy", label="Capture Face — click 📷")
                    btn_add            = gr.Button("Add Student", variant="primary")
                    add_status         = gr.Textbox(label="Status", interactive=False)

                with gr.Column():
                    gr.Markdown("#### ➖ Remove Student")
                    student_dropdown = gr.Dropdown(
                        choices=get_student_list(),
                        label="Select Student to Remove",
                        interactive=True,
                    )
                    btn_refresh_list = gr.Button("🔄 Refresh List")
                    btn_remove       = gr.Button("Remove Student", variant="stop")
                    remove_status    = gr.Textbox(label="Status", interactive=False)

            btn_add.click(
                fn=add_student,
                inputs=[student_name_input, student_webcam],
                outputs=[add_status, student_dropdown],
            )
            btn_remove.click(
                fn=remove_student,
                inputs=student_dropdown,
                outputs=[remove_status, student_dropdown],
            )
            btn_refresh_list.click(fn=refresh_dropdown, outputs=student_dropdown)


if __name__ == "__main__":
    demo.launch()
