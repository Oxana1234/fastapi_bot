# server.py
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Date, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from pydantic import BaseModel
import logging
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройка базы данных SQLite
DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    deadline = Column(Date, nullable=False)

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Таблица 'tasks' создана")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка создания таблицы: {e}")

class TaskCreate(BaseModel):
    name: str
    deadline: str

app = FastAPI()

@app.on_event("startup")
async def startup():
    create_tables()

@app.get("/tasks")
def get_tasks():
    db = SessionLocal()
    try:
        tasks = db.query(TaskDB).order_by(TaskDB.id).all()
        return [{"id": t.id, "name": t.name, "deadline": t.deadline.strftime("%d.%m.%Y")} for t in tasks]
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise HTTPException(500, "Ошибка сервера")
    finally:
        db.close()

@app.post("/tasks")
def add_task(task: TaskCreate):
    try:
        deadline = datetime.strptime(task.deadline, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(400, "Неверный формат даты")

    db = SessionLocal()
    try:
        db_task = TaskDB(name=task.name, deadline=deadline)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return {"id": db_task.id, "name": db_task.name, "deadline": task.deadline}
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка: {e}")
        raise HTTPException(500, "Ошибка сервера")
    finally:
        db.close()

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task:
            raise HTTPException(404, "Задача не найдена")

        db.delete(task)
        db.commit()
        return {"message": f"Задача {task_id} удалена"}
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка: {e}")
        raise HTTPException(500, "Ошибка сервера")
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)