---
title: Attendance Tracker
emoji: 🐠
colorFrom: yellow
colorTo: green
sdk: gradio
sdk_version: 5.30.0
app_file: app.py
pinned: false
license: mit
short_description: Smart Face Recognition Attendance System
---


# Face Recognition Attendance System

A seamless and intelligent face recognition-based attendance system built using Python, OpenCV, and deep learning techniques. Designed for automation and accuracy, this application allows real-time detection and recognition of faces, logging attendance efficiently. It is deployable on platforms like Hugging Face Spaces using Gradio for a smooth web interface.

---

## 🚀 Features

* 🎯 Real-time face detection and recognition
* 📝 Automatic attendance marking with timestamps
* 📦 User-friendly interface with Gradio
* 🧠 Uses deep learning-based face encodings
* 💾 Attendance data stored in CSV format
* ☁️ Deployable on Hugging Face Spaces (no local setup required)

---

## 🛠️ Technologies Used

* Python
* OpenCV
* NumPy
* Gradio
* face\_recognition (dlib)
* Pandas

---

## 📂 Project Structure

```
FACE_ATTENDANCE/
├── app.py                 # Main Gradio app
├── attendance.csv         # Auto-generated attendance log
├── Students/                # Folder containing images of known individuals
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## ⚙️ Installation

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/face-recognition-attendance.git
cd face-recognition-attendance
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Add Known Faces**
   Place images of individuals in the `images/` folder. Filenames will be used as names in the attendance log.

4. **Encode Faces**

```bash
python encode_faces.py
```

5. **Run the App**

```bash
python app.py
```

---

## 🌐 Deployment on Hugging Face Spaces

This application can be deployed using [Gradio](https://gradio.app/) on [Hugging Face Spaces](https://huggingface.co/spaces):

1. Create a new Space using the "Gradio" SDK.
2. Upload all project files including `app.py`, `functions.py`, `images/`, and `requirements.txt`.
3. Ensure `app.py` runs the Gradio app as `gr.Interface(...)`.

---

## 📈 Use Case Scenarios

* Educational Institutions
* Corporate Offices
* Workshops and Events
* Remote Team Check-ins

---

## 📌 Future Improvements

* Face registration via webcam
* Admin dashboard
* Integration with cloud databases
* SMS/email notifications

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss the proposed changes.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---


## 📬 Contact

Developed by \[Amitha]
📧 Email: [amitharajakumar1979@gmail.com](mailto:amitharajakumar1979@gmail.com)
🌐 GitHub: [Amitha07amy](https://github.com/Amitha07amy)
