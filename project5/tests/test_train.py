from project5.src.train import train_dummy_model



def test_model_training():
    model = train_dummy_model()
    prediction = model.predict([[0, 1]])

    assert prediction is not None
