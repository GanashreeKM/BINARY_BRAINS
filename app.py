from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import requests
from googlesearch import search

app = Flask(__name__, template_folder=".")
CORS(app)

# Securely store the YouTube API key using environment variables
YOUTUBE_API_KEY = os.getenv("AIzaSyDVca-ke2gKjsucVMWCWM3xem0103vfVQk")  # Set this in your environment

# SQLite Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Student Model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    category = db.Column(db.String(10), nullable=False)  # UG or PG
    program = db.Column(db.String(50), nullable=False)  # BCA, BCOM, CS, ECE
    learning_gap_category = db.Column(db.String(100), nullable=False)  # Learning Gap

# Learning Gaps Model with UG Category
class LearningGap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gap = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="UG")  # UG Category Added

# Initialize Database
with app.app_context():
    db.create_all()

# Serve the Students Page
@app.route("/")
def index():
    return render_template("Students.html")

# Fetch all students
@app.route("/students", methods=["GET"])
def get_students():
    students = Student.query.all()
    return jsonify([{ 
        "Student_ID": s.id, 
        "Name": s.name, 
        "Roll_Number": s.roll_number, 
        "Phone_Number": s.phone_number, 
        "Category": s.category,
        "Program": s.program,
        "Learning_Gap_Category": s.learning_gap_category
    } for s in students])

# Add a student
@app.route("/add_student", methods=["POST"])
def add_student():
    data = request.json
    if not all(key in data for key in ["name", "rollNumber", "phoneNumber", "category", "program", "learningGapCategory"]):
        return jsonify({"error": "Missing required fields"}), 400

    existing_student = Student.query.filter_by(roll_number=data["rollNumber"]).first()
    if existing_student:
        return jsonify({"message": "Student already exists"}), 400

    new_student = Student(
        name=data["name"],
        roll_number=data["rollNumber"],
        phone_number=data["phoneNumber"],
        category=data["category"],
        program=data["program"],
        learning_gap_category=data["learningGapCategory"]
    )

    db.session.add(new_student)
    db.session.commit()
    return jsonify({"message": "Student added successfully"}), 201

# Fetch a specific student by ID
@app.route("/student/<int:id>", methods=["GET"])
def get_student(id):
    student = Student.query.get(id)
    if student:
        return jsonify({ 
            "Student_ID": student.id, 
            "Name": student.name, 
            "Roll_Number": student.roll_number, 
            "Phone_Number": student.phone_number,
            "Category": student.category,
            "Program": student.program,
            "Learning_Gap_Category": student.learning_gap_category
        })
    return jsonify({"error": "Student not found"}), 404

# Fetch UG learning gaps
@app.route("/learning_gaps", methods=["GET"])
def get_learning_gaps():
    gaps = LearningGap.query.filter_by(category="UG").all()
    return jsonify([{ "Name": g.name, "Learning_Gap": g.gap } for g in gaps])

# Add a new UG learning gap
@app.route("/add_learning_gap", methods=["POST"])
def add_learning_gap():
    data = request.json
    if not all(key in data for key in ["name", "gap"]):
        return jsonify({"error": "Missing required fields"}), 400

    new_gap = LearningGap(name=data["name"], gap=data["gap"], category="UG")
    db.session.add(new_gap)
    db.session.commit()
    return jsonify({"message": "UG Learning gap added successfully"}), 201

# Fetch YouTube videos for learning
import os

@app.route("/get_videos")
def get_videos():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    # Securely fetch API Key from environment variables
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    if not YOUTUBE_API_KEY:
        return jsonify({"error": "YouTube API key is missing"}), 500

    youtube_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&maxResults=3&type=video&key={YOUTUBE_API_KEY}"
    
    response = requests.get(youtube_url)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch videos"}), response.status_code

    data = response.json()

    # Mapping of learning topics to notes
    learning_notes = {
        "Programming in C and C++": "C and C++ are foundational programming languages. Learn about variables, functions, and object-oriented programming.",
        "Data Structures": "Data structures like arrays, linked lists, stacks, and queues are essential for efficient algorithms.",
        "Database Management System": "DBMS covers SQL, NoSQL, indexing, and transactions for managing large datasets.",
        "Computer Network": "Networking concepts like TCP/IP, DNS, and network security help in understanding data communication.",
        "Operating System": "OS fundamentals include process management, memory allocation, and file systems.",
        "Web Development": "Learn HTML, CSS, JavaScript, and backend development to build modern web applications."
    }

    videos = [
        {
            "id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "notes": learning_notes.get(query, "No notes available for this topic.")
        }
        for item in data.get("items", [])
    ]
    return jsonify(videos)

# Function to fetch notes from Google using Custom Search
def fetch_notes_from_google(query):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return jsonify({"error": "Google API key or Custom Search Engine ID missing"}), 500
    
    google_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"

    try:
        response = requests.get(google_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch notes from Google"}), response.status_code
        
        results = response.json().get('items', [])
        notes = []
        for item in results:
            notes.append({
                "title": item['title'],
                "link": item['link'],
                "snippet": item['snippet']
            })
        return jsonify(notes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_notes", methods=["GET"])
def get_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    return fetch_notes_from_google(query)
if __name__ == "__main__":
    app.run(debug=True)
