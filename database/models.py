# database/models.py

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Time, BigInteger
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    telegram_id = Column(BigInteger, nullable=True, unique=True)  # 🔹 Новый атрибут
    notes = Column(String)

    appointments = relationship("Appointment", back_populates="client")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    date_time = Column(DateTime, nullable=False)
    service = Column(String, nullable=False)
    status = Column(String, default="active")  # active / cancelled / completed
    confirmed = Column(Boolean, default=None)  # True / False / None

    client = relationship("Client", back_populates="appointments")

class UnavailableSlot(Base):
    __tablename__ = "unavailable_slots"

    id = Column(Integer, primary_key=True)
    date_time_start = Column(DateTime, nullable=False)
    date_time_end = Column(DateTime, nullable=False)
    reason = Column(String)  # отпуск, внешняя запись и т.д.

class WorkSchedule(Base):
    __tablename__ = "work_schedule"

    id = Column(Integer, primary_key=True)
    weekday = Column(Integer, nullable=False)  # 0 = Пн, 6 = Вс
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
