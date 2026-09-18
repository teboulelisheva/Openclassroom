from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MLInput(Base):
    __tablename__ = "ml_inputs"

    id = Column(Integer, primary_key=True)
    feature1 = Column(Float, nullable=False)
    feature2 = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True)
    input_id = Column(Integer, ForeignKey("ml_inputs.id"))
    prediction = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
