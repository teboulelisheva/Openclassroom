import gradio as gr
from src.train import train_dummy_model


model = train_dummy_model()

def predict(feature1, feature2):
    prediction = model.predict([[feature1, feature2]])
    return int(prediction[0])


interface = gr.Interface(
    fn=predict,
    inputs=[
        gr.Number(label="feature1"),
        gr.Number(label="feature2")
    ],
    outputs=gr.Number(label="prediction"),
    title="Projet 5 – Modèle ML déployé",
    description="Déploiement d’un modèle de machine learning avec CI/CD"
)

if __name__ == "__main__":
    interface.launch()
