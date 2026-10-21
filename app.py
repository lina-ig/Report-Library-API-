from flask import request, Flask
app = Flask(__name__)

students = []

@app.get("/student")
def get_students ():
    return {"students": students}

@app.post("/student")
def post_student():
    request_data = request.get_json()
    student = {
        "id": len(students)+1,
        "Fname": request_data.get("Fname"),
        "Lname": request_data.get("Lname"),
        "reports": request_data.get("reports", [])
    }
    students.append(student)
    return student, 201

@app.post("/student/<int:student_id>/report")
def add_report(student_id):
    request_data = request.get_json()
    student = next((s for s in students if s["id"] == student_id), None)

    if student is None:
        return {"message": "Student not found"}, 404

    new_report = {
        "title": request_data.get("title"),
        "type": request_data.get("type"),
    }
    student["reports"].append(new_report)

    return {"message": "Report added successfully", "report": new_report}