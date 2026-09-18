import pandas as pd
from sklearn.linear_model import LogisticRegression

def train_dummy_model():
    X = pd.DataFrame({
        "feature1": [0, 1, 0, 1],
        "feature2": [1, 0, 1, 0]
    })
    y = [0, 1, 0, 1]

    model = LogisticRegression()
    model.fit(X, y)
    return model

def test_model_prediction_type():
    model = train_dummy_model()
    pred = model.predict([[0, 1]])
    assert isinstance(pred[0], (int, float)) or hasattr(pred[0], "item")


def test_model_prediction_value():
    model = train_dummy_model()
    pred = model.predict([[0, 1]])[0]
    assert pred in [0, 1]
