from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.database import init_db, add_user, get_all_users

app = FastAPI(title="IRIT TeamFinder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    name: str
    role: str
    skills: str
    tg_username: str

@app.on_event("startup")
def startup():
    init_db()

@app.get("/users")
def list_users():
    return get_all_users()

@app.post("/users")
def create_user(user: UserCreate):
    return add_user(user.name, user.role, user.skills, user.tg_username)
