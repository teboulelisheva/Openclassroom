from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import pandas as pd
from sklearn.linear_model import LogisticRegression

from project5.db.database import SessionLocal
from project5.db.models import MLInput, MLPrediction

# --------- FastAPI ---------
app = FastAPI(title="API ML avec PostgreSQL")

# --------- DB Dependency ---------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------- Modèle ML (simple) ---------
X = pd.DataFrame({
    "feature1": [0, 1, 0, 1],
    "feature2": [1, 0, 1, 0]
})
y = [0, 1, 0, 1]

model = LogisticRegression()
model.fit(X, y)

# --------- Pydantic ---------
class PredictionInput(BaseModel):
    feature1: float = Field(..., example=0)
    feature2: float = Field(..., example=1)

class PredictionOutput(BaseModel):
    prediction: int

# --------- Endpoints ---------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictionOutput)
def predict(data: PredictionInput, db: Session = Depends(get_db)):
    # 1️⃣ enregistrer l'input
    ml_input = MLInput(
        feature1=data.feature1,
        feature2=data.feature2
    )
    db.add(ml_input)
    db.commit()
    db.refresh(ml_input)

    # 2️⃣ prédiction
    df = pd.DataFrame([[data.feature1, data.feature2]],
                      columns=["feature1", "feature2"])
    pred = int(model.predict(df)[0])

    # 3️⃣ enregistrer la prédiction
    ml_pred = MLPrediction(
        input_id=ml_input.id,
        prediction=pred
    )
    db.add(ml_pred)
    db.commit()

    return {"prediction": pred}
