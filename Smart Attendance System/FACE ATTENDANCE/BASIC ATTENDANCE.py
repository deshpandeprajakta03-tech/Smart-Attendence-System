import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime

# Load known images
path = 'students'
images = []
names = []

mylist = os.listdir(path)
for cl in mylist:
    img_path = os.path.join(path, cl)
    img = cv2.imread(img_path)
    if img is not None:
        images.append(img)
        names.append(os.path.splitext(cl)[0])

# Encode known faces
def encode_faces(images):
    encoded_list = []
    for img in images:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodes = face_recognition.face_encodings(rgb_img)
        if encodes:
            encoded_list.append(encodes[0])
    return encoded_list

# Initialize attendance dictionary
attendance_dict = {}

def mark_attendance(name):
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    time_now = now.strftime('%H:%M:%S')

    if name not in attendance_dict:
        # First appearance = Login time
        attendance_dict[name] = {'date': date, 'login': time_now, 'logoff': time_now}
    else:
        # Update last seen = Logoff time
        attendance_dict[name]['logoff'] = time_now

# Save attendance to CSV at the end
def save_attendance(filename='Attendance_Log.csv'):
    with open(filename, 'w') as f:
        f.write('Name,Date,Login Time,Logoff Time\n')
        for name, times in attendance_dict.items():
            f.write(f"{name},{times['date']},{times['login']},{times['logoff']}\n")

# Encode faces
print("Encoding started...")
known_encodings = encode_faces(images)
print("Encoding complete.")

# Start webcam
cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()
    if not success:
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    faces_current = face_recognition.face_locations(rgb_small)
    encodings_current = face_recognition.face_encodings(rgb_small, faces_current)

    for encode_face, face_loc in zip(encodings_current, faces_current):
        matches = face_recognition.compare_faces(known_encodings, encode_face)
        face_dis = face_recognition.face_distance(known_encodings, encode_face)
        match_index = np.argmin(face_dis)

        if matches[match_index]:
            name = names[match_index].upper()
            mark_attendance(name)

            y1, x2, y2, x1 = face_loc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, name, (x1 + 6, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Login & Logoff Attendance", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Save log when webcam stops
save_attendance()
print("Attendance saved to CSV.")
