
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from sqlalchemy.orm import sessionmaker
from db.database import Base

class Channel(Base):
    __tablename__ = "channel"
    id = Column(String(45), primary_key=True)
    name  = Column(String(45))  
