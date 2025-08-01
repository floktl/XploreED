from dotenv import load_dotenv
import os

load_dotenv()
print("PATH + ")
print(os.getcwd())
print("DB_PORT raw value:", os.getenv("DB_PORT"))

DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

