import json

from flask import Flask, request

app = Flask(__name__)

students = [
{
"id": 1,
"name": "Rhea Kapoor",
"course": "Python",
"score": 82
},
{
"id": 2,
"name": "Zain Malik",
"course": "SQL",
"score": 76
},
{
"id": 3,
"name": "Devika Rao",
"course": "Cloud",
"score": 91
}
]



@app.route("/students", methods=["POST"])
def create_student():
    data = request.json

    students.append(data)

    return {
        "message": "Student created"
    }

@app.route("/students")
def get_students():
    return json.dumps(students)

@app.route("/students/<int:student_id>")
def get_student(student_id):
    for student in students:
        if student["id"] == student_id:
            return json.dumps(student)

    return {
        "message": "Student not found"
    }

@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.json

    for student in students:
        if student["id"] == student_id:
            student["name"] = data["name"]
            student["course"] = data["course"]
            student["score"] = data["score"]

    return {
        "message": "Student updated successfully"
    }

@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    for student in students:
        if student["id"] == student_id:
            students.remove(student)

            return {
                "message": "Student deleted successfully"
            }

    return {
        "message": "Student not found"
    }