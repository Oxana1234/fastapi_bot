from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from server import TaskDB

def print_tasks():
    engine = create_engine("sqlite:///./tasks.db")

    with Session(engine) as session:
        tasks = session.query(TaskDB).order_by(TaskDB.id).all()

        if not tasks:
            print("\n📭 База данных пуста")
            return

        print("\n📋 Задачи в базе данных:")
        print("-" * 60)
        print(f"| {'ID':^5} | {'Название':^30} | {'Дедлайн':^15} |")
        print("-" * 60)

        for task in tasks:
            print(f"| {task.id:^5} | {task.name[:30]:<30} | {task.deadline.strftime('%d.%m.%Y'):^15} |")

        print("-" * 60)
        print(f"Всего задач: {len(tasks)}")

if __name__ == "__main__":
    print_tasks()
