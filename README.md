# 🧠 Smart Face Recognition Attendance System

A contactless, real-time attendance system that uses face recognition to automatically mark student login and logoff with timestamps — no manual entry, no ID cards needed.

---

## 📸 Demo

> Open the app → Capture your face → Click Log In ✅  
> Your attendance is marked instantly with time and duration.

---

## 🚀 Features

- 📷 Real-time face recognition via webcam
- ✅ Login & 📤 Logoff with automatic duration calculation
- 📊 Attendance log viewer with CSV download
- 🛠️ Admin panel to add or remove students dynamically
- ❌ Unrecognized face snapshots saved automatically
- 🌐 Web-based UI — runs in browser, no desktop app needed

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core language |
| DeepFace (Facenet) | Face recognition model |
| OpenCV | Image capture & processing |
| Gradio | Web UI |
| Pandas | Attendance CSV management |
| NumPy | Image array handling |

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/deshpandeprajakta03-tech/Smart-Attendence-System.git
cd Smart-Attendence-System/Smart\ Attendance\ System/Attendance\ Tracker
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:7860
```

> ⚠️ First run will download the Facenet model (~96MB). This is a one-time download.

---

## 📂 Project Structure

```
Attendance Tracker/
├── app.py                  # Main Gradio application
├── students/               # Student face images (jpg/png/jpeg)
├── attendance.csv          # Auto-generated attendance log
├── unrecognized_faces/     # Snapshots of unrecognized faces
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🖥️ How It Works

1. Student face images are stored in the `students/` folder
2. When a student clicks **Log In**, webcam captures their face
3. DeepFace compares the captured face against all stored student images using the **Facenet** deep learning model
4. If matched → attendance is marked in `attendance.csv` with name, date, login time
5. When they click **Log Off** → logoff time and total duration are recorded
6. If face is not recognized → snapshot is saved to `unrecognized_faces/`

---

## 📋 Attendance Log Format

| Name | Date | Login Time | Logoff Time | Duration |
|---|---|---|---|---|
| Prajakta Deshpande | 2026-01-01 | 09:00:00 | 17:00:00 | 8h 0m |

---

## 🛠️ Admin Panel

- **Add Student** — Enter name + capture face via webcam → saved to `students/` folder
- **Remove Student** — Select from dropdown → removes image from system

---

## 📦 Requirements

```
gradio
deepface
tf-keras
opencv-python
numpy
pandas
```

---

## 🔮 Future Improvements

- Replace CSV with SQLite or Firebase database
- Add anti-spoofing to prevent photo-based attacks
- Email or SMS notification on attendance marked
- Dashboard with attendance analytics and charts
- Multi-camera support for large classrooms

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 👩‍💻 Developer

**Prajakta Deshpande**  
📧 [deshpandeprajakta03@gmail.com](mailto:deshpandeprajakta03@gmail.com)  
🌐 [GitHub](https://github.com/deshpandeprajakta03-tech)
