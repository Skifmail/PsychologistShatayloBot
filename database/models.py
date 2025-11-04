"""
Модели данных для работы с базой данных.

Содержит ORM-модели SQLAlchemy для управления клиентами, записями на приём,
рабочим расписанием психолога и недоступными временными слотами.
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    Time,
    BigInteger
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.
    
    Все модели данных наследуются от этого класса для обеспечения
    единой структуры метаданных.
    """
    pass


class Client(Base):
    """
    Модель клиента (пользователя бота).
    
    Attributes:
        id (int): Уникальный идентификатор клиента
        full_name (str): Полное имя клиента (ФИО)
        phone_number (str): Номер телефона клиента
        telegram_id (int): Telegram ID клиента (уникальный, может быть None)
        notes (str): Дополнительные заметки психолога о клиенте
        appointments (list[Appointment]): Список всех записей клиента
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False, comment="ФИО клиента")
    phone_number = Column(String(32), nullable=False, comment="Телефон клиента")
    telegram_id = Column(
        BigInteger,
        nullable=True,
        unique=True,
        comment="Telegram ID клиента"
    )
    notes = Column(String(256), comment="Заметки психолога")

    appointments = relationship("Appointment", back_populates="client")

class Appointment(Base):
    """
    Модель записи клиента к психологу.
    
    Attributes:
        id (int): Уникальный идентификатор записи
        client_id (int): ID клиента (внешний ключ)
        date_time (datetime): Дата и время приёма
        service (str): Тип услуги ('consult', 'intro', 'supervision')
        status (str): Статус записи ('active', 'cancelled', 'completed')
        confirmed (bool): Подтверждена ли запись клиентом (None - не отвечено)
        client (Client): Связанный объект клиента
    """
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    date_time = Column(DateTime, nullable=False, comment="Дата и время записи")
    service = Column(String(64), nullable=False, comment="Услуга")
    status = Column(
        String(16),
        default="active",
        comment="Статус: active/cancelled/completed"
    )
    confirmed = Column(Boolean, default=None, comment="Подтверждена ли запись")

    client = relationship("Client", back_populates="appointments")

class UnavailableSlot(Base):
    """
    Модель недоступного временного слота.
    
    Используется для блокировки времени, когда психолог не может принимать
    клиентов (отпуск, личные дела, внешние записи и т.д.).
    
    Attributes:
        id (int): Уникальный идентификатор слота
        date_time_start (datetime): Начало недоступного периода
        date_time_end (datetime): Конец недоступного периода
        reason (str): Причина недоступности
    """
    __tablename__ = "unavailable_slots"

    id = Column(Integer, primary_key=True)
    date_time_start = Column(
        DateTime,
        nullable=False,
        comment="Начало недоступного слота"
    )
    date_time_end = Column(
        DateTime,
        nullable=False,
        comment="Конец недоступного слота"
    )
    reason = Column(String(128), comment="Причина недоступности")

class WorkSchedule(Base):
    """
    Модель рабочего расписания психолога.
    
    Определяет регулярное расписание работы по дням недели.
    
    Attributes:
        id (int): Уникальный идентификатор записи расписания
        weekday (int): День недели (0 = понедельник, 6 = воскресенье)
        start_time (time): Время начала рабочего дня
        end_time (time): Время окончания рабочего дня
    """
    __tablename__ = "work_schedule"

    id = Column(Integer, primary_key=True)
    weekday = Column(Integer, nullable=False, comment="0 = Пн, 6 = Вс")
    start_time = Column(Time, nullable=False, comment="Время начала работы")
    end_time = Column(Time, nullable=False, comment="Время окончания работы")
