from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime

class FaceRecognitionSystem:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1530x790+0+0")
        self.root.title("FACE RECOGNITION SYSTEM")

        # Load logos
        img1 = Image.open("logo.png").resize((100, 100), Image.LANCZOS)
        self.photoimg1 = ImageTk.PhotoImage(img1)
        Label(self.root, image=self.photoimg1, bg="white").place(x=0, y=0, width=100, height=100)  

        img2 = Image.open("logo2.png").resize((100, 100), Image.LANCZOS)
        self.photoimg2 = ImageTk.PhotoImage(img2)
        window_width = self.root.winfo_screenwidth()
        Label(self.root, image=self.photoimg2, bg="white").place(x=window_width - 100, y=0, width=100, height=100)

        # Heading
        heading_label = Label(self.root, text="FACE RECOGNITION ATTENDANCE SYSTEM", font=("TIMES NEW ROMAN", 20, "bold"), bg="white", fg="RED")
        heading_label.place(x=110, y=0, width=window_width - 220, height=100)

        # Main banner image
        img = Image.open("banner.jpg")
        img = img.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight() - 100), Image.LANCZOS)
        self.photoimg = ImageTk.PhotoImage(img)
        Label(self.root, image=self.photoimg).place(x=0, y=100, width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight() - 100)

        # Button to start face recognition
        start_button = Button(self.root, text="Start Face Recognition", command=self.start_recognition, font=("times new roman", 15, "bold"), bg="blue", fg="white")
        start_button.place(x=600, y=700, width=300, height=50)

        # Initialize face encodings
        self.load_images_and_encodings()

    def load_images_and_encodings(self):
        self.path = 'ImageAttendance'
        self.images = []
        self.classNames = []
        self.encodeListKnown = []

        # Load images
        for cl in os.listdir(self.path):
            img = cv2.imread(f'{self.path}/{cl}')
            self.images.append(img)
            self.classNames.append(os.path.splitext(cl)[0])

        # Find encodings for loaded images
        for img in self.images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            self.encodeListKnown.append(encode)
        print("Encoding Complete")

    def markAttendance(self, name):
        with open('Attendance.csv', 'r+') as f:
            myDataList = f.readlines()
            nameList = [line.split(',')[0] for line in myDataList]

            if name not in nameList:
                now = datetime.now()
                dateString = now.strftime('%d-%m-%Y %H:%M:%S')
                f.writelines(f'\n{name}, {dateString}')

    def start_recognition(self):
        cap = cv2.VideoCapture(0)

        while True:
            success, img = cap.read()
            imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

            facesCurFrame = face_recognition.face_locations(imgSmall)
            encodeCurFrame = face_recognition.face_encodings(imgSmall, facesCurFrame)

            for encodeFace, faceloc in zip(encodeCurFrame, facesCurFrame):
                matches = face_recognition.compare_faces(self.encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(self.encodeListKnown, encodeFace)
                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    name = self.classNames[matchIndex].upper()
                    y1, x2, y2, x1 = faceloc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                    cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    self.markAttendance(name)

            cv2.imshow('Face Recognition', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    root = Tk()
    obj = FaceRecognitionSystem(root)
    root.mainloop()
