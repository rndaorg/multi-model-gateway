from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    owner = Column(String)
    rate_limit = Column(Integer, default=60) # requests per minute
    requests = relationship("RequestLog", back_populates="api_key")

class RequestLog(Base):
    __tablename__ = "request_logs"
    id = Column(Integer, primary_key=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    model_used = Column(String)
    strategy = Column(String)
    latency_ms = Column(Float)
    total_tokens = Column(Integer)
    estimated_cost = Column(Float)
    status = Column(String) # success, fallback, error
    timestamp = Column(DateTime, default=datetime.utcnow)
    api_key = relationship("APIKey", back_populates="requests")
