import cv2
from deepface import DeepFace
import mysql.connector
from datetime import datetime, timedelta

# Connect to the database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="ATTENDANCE"
)

cursor = db.cursor()

# Cooldown period (in seconds) to prevent rapid detections
cooldown_period = 10  # Adjust this value as needed

# Dictionary to store the entry time for each person
entry_time_dict = {}

# Dictionary to store the total time spent for each person during the cooldown period
total_time_inside_dict = {}

# Dictionary to map person IDs to names
person_id_name_map = {1: "steve", 2: "arun", 3: "benetta", 4: "anwin", 5: "angela", 6: "babu", 7: "ben"}  # You should populate this with your own mapping

# Capture video from a camera (you can modify it to read from a video file)
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    # Find all face locations in the current frame
    face_locations = DeepFace.face_locations(frame)

    for (top, right, bottom, left) in face_locations:
        cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

        # Recognize the face
        name = "Unknown"

        # Check if cooldown period has passed since the last detection
        if name != "Unknown" and (name not in entry_time_dict or (
                datetime.now() - entry_time_dict[name]).total_seconds() > cooldown_period):
            # If cooldown period has passed or it's the first detection, treat it as an entry
            # Update entry time
            entry_time_dict[name] = datetime.now()

            # Insert initial entry into the database
            query = f"INSERT INTO attendance (name, timestamp) VALUES ('{name}', NOW()) ON DUPLICATE KEY UPDATE timestamp=NOW()"
            cursor.execute(query)
            db.commit()

            # Start or reset the total time spent for the cooldown period
            total_time_inside_dict[name] = timedelta()

        else:
            if name != "Unknown":
                # If cooldown period has not passed, treat it as an exit and update the total time spent
                # Calculate time spent inside during the cooldown period
                entry_time = entry_time_dict[name]
                exit_time = datetime.now()
                time_inside = exit_time - entry_time

                # Accumulate the time spent during the cooldown period
                total_time_inside_dict[name] += time_inside

                # Convert total time spent to TIME format
                time_format = str(total_time_inside_dict[name])

                # Update total_time_spent column in the database
                query = f"UPDATE attendance SET total_time_spent = '{time_format}' WHERE name = '{name}'"
                cursor.execute(query)
                db.commit()

                # Update entry time for the next detection (treat it as a new entry)
                entry_time_dict[name] = datetime.now()

        # Display the name on the frame
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the result
    cv2.imshow("Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera
cap.release()

# Close all OpenCV windows
cv2.destroyAllWindows()
