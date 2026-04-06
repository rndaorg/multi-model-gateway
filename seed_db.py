from database import init_db
from models import APIKey, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://gateway_user:gateway_pass@localhost:5432/gateway_db")
SessionLocal = sessionmaker(bind=engine)

init_db()
session = SessionLocal()

# Create a demo key
if not session.query(APIKey).filter_by(key="demo-key-123").first():
    key = APIKey(key="demo-key-123", owner="demo_user", rate_limit=100)
    session.add(key)
    session.commit()
    print("✅ API Key 'demo-key-123' created.")
else:
    print("ℹ️ API Key already exists.")
