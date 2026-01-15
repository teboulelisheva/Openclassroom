from fastapi import FastAPI
from pydantic import BaseModel, Field
import pandas as pd
from sklearn.linear_model import LogisticRegression

# Création de l'app
app = FastAPI(title="API Projet 5 - ML")

# Entraînement du modèle (simple, comme avant)
X = pd.DataFrame({
    "feature1": [0, 1, 0, 1],
    "feature2": [1, 0, 1, 0]
})
y = [0, 1, 0, 1]

model = LogisticRegression()
model.fit(X, y)

# -----------------------
# Pydantic - Validation
# -----------------------

class PredictionInput(BaseModel):
    feature1: float = Field(..., example=0)
    feature2: float = Field(..., example=1)

class PredictionOutput(BaseModel):
    prediction: int

# -----------------------
# Endpoints
# -----------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictionOutput)
def predict(data: PredictionInput):
    df = pd.DataFrame([[data.feature1, data.feature2]],
                      columns=["feature1", "feature2"])
    pred = model.predict(df)[0]
    return {"prediction": int(pred)}
