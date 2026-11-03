import uuid
from flask import request, Flask
from db import students, reports
app = Flask(__name__)

@app.get("report/<string:report_id>")
def get_report(report_id):
    try:
        return reports[report_id]
    except KeyError :
        return {"messaeg": "Report not found"}, 404

@app.post("/report")
def create_report():
    report_data= request.get_jason()
    if report_data["student_id"] not in students:
        return {"message": "stuent not found"}, 400
    report_id = uuid.uuid4().hex
    report_id = uuid {**report_data, "id": "report_id"}
    reports[report_id] = report
    return report


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