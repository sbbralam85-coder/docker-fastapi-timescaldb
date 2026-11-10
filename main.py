import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:mysecretpassword@localhost:5432/sensor_data")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# TimescaleDB হাইপারটেবলের জন্য মডেল
class SensorRecord(Base):
    __tablename__ = "sensor_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    time = Column(DateTime, default=datetime.utcnow, index=True)
    temperature = Column(Float)
    humidity = Column(Float)

# টেবিল তৈরি করা (যদি না থাকে)
Base.metadata.create_all(bind=engine)

# TimescaleDB-তে হাইপারটেবল (Hypertable) কনভার্ট করার জন্য রফে এসকিউএল রান করা যেতে পারে, 
# অথবা প্রথমবার সংযোগের সময় কনসোল থেকে করা যায়: 
# SELECT create_hypertable('sensor_logs', 'time', if_not_exists => TRUE);

app = FastAPI()

class SensorData(BaseModel):
    temperature: float
    humidity: float

@app.post("/api/sensors")
def receive_data(data: SensorData):
    db = SessionLocal()
    try:
        db_record = SensorRecord(
            temperature=data.temperature,
            humidity=data.humidity,
            time=datetime.utcnow()
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return {"status": "success", "id": db_record.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()