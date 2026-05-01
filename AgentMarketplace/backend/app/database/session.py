from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

from app.config import settings

# Pre-create database if not exists (Only if using MySQL)
def create_db_if_not_exists():
    if "mysql" not in settings.DATABASE_URL:
        return
    try:
        conn = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

create_db_if_not_exists()

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
