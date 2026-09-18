import pandas as pd
from sklearn.linear_model import LogisticRegression


def train_dummy_model():
    """
    Entraîne un modèle simple sur un dataset minimal.
    Utilisé uniquement pour les tests CI.
    """
    X = pd.DataFrame({
        "feature1": [0, 1, 0, 1],
        "feature2": [1, 0, 1, 0]
    })
    y = [0, 1, 0, 1]

    model = LogisticRegression()
    model.fit(X, y)

    return model
