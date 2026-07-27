from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# -----------------------------
# Database Configuration
# -----------------------------
DATABASE_URL = "sqlite:///./students.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# -----------------------------
# Student Table
# -----------------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    course = Column(String)
    email = Column(String, unique=True)

Base.metadata.create_all(bind=engine)

# -----------------------------
# Pydantic Model
# -----------------------------
class StudentCreate(BaseModel):
    name: str
    age: int
    course: str
    email: str

class StudentResponse(StudentCreate):
    id: int

    class Config:
        from_attributes = True

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="Student CRUD API")

# Database Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# CREATE Student
# -----------------------------
@app.post("/students", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):

    existing = db.query(Student).filter(Student.email == student.email).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_student = Student(
        name=student.name,
        age=student.age,
        course=student.course,
        email=student.email
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student

# -----------------------------
# READ All Students
# -----------------------------
@app.get("/students", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).all()

# -----------------------------
# READ Student by ID
# -----------------------------
@app.get("/students{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):

    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return student

# -----------------------------
# UPDATE Student
# -----------------------------
@app.put("/students{student_id}", response_model=StudentResponse)
def update_student(student_id: int, data: StudentCreate, db: Session = Depends(get_db)):

    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.name = data.name
    student.age = data.age
    student.course = data.course
    student.email = data.email

    db.commit()
    db.refresh(student)

    return student

# -----------------------------
# DELETE Student
# -----------------------------
@app.delete("/students{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):

    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()

    return {"message": "Student deleted successfully"}


