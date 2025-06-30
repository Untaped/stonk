from sqlalchemy import create_engine, Column, String, Float, Date, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()

class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    name = Column(String)
    date = Column(Date, default=datetime.date.today)
    price = Column(Float)
    market_cap = Column(Float)
    average_volume = Column(Float)
    revenue_growth = Column(Float)
    earnings_growth = Column(Float)
    net_income = Column(Float)
    roe = Column(Float)
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    free_cashflow = Column(Float)
    forward_pe = Column(Float)
    peg_ratio = Column(Float)
    score = Column(Float)
    recommendation = Column(String)

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    date = Column(Date, index=True)
    close_price = Column(Float)

# Database setup (only run once to create tables)
DATABASE_URL = "sqlite:///stocks.db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
