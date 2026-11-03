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
        return {"message": "stduent not found"}, 404
    report_id = uuid.uuid4().hex
    report ={**report_data, "id": report_id}
    reports[report_id] = report
    return report

@app.post("/report")
def get_all_reports():
    return {"reports":list(reports.values())}



@app.get("/student")
def get_students ():
    return {"students": list(students.values())}

@app.post("/student")
def add_student():
    student_data = request.get_json()
    student_id= uuid.uuid4.hex
    student = {**student_data, "id": student_id}
    students[student_id] = student
    return student, 201


@app.post("/student/<int:student_id>")
def get_student(student_id):
    try:
        return students[student_id]
    except KeyError:
        return {"message": "Student not found"}, 404

    