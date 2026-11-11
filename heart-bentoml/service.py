"""STEP 2 - SERVE: wrap the saved model in a BentoML Service (an HTTP API).

Run:  bentoml serve service:HeartService        (then open http://localhost:3000)

Read this file top to bottom, it is the core of BentoML:

  * Pydantic classes  = the API CONTRACT. BentoML rejects bad input (HTTP 400) before
                        your code runs, and builds the Swagger docs from them.
  * @bentoml.service  = turns a class into a deployable service (workers, timeouts,
                        resources are configured here).
  * __init__          = runs ONCE per worker at startup. Load the model here, never
                        inside the endpoint (that would reload it on every request).
  * @bentoml.api      = every decorated method becomes an endpoint: POST /<method_name>.
"""
import bentoml
import pandas as pd
from pydantic import BaseModel, Field

FEATURES = [
    "age", "trestbps", "chol", "thalach", "oldpeak",
    "sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal",
]


class Patient(BaseModel):
    """Input schema. Field(ge=, le=) are validation rules: values outside them are rejected."""

    age: int = Field(ge=1, le=120, description="Age in years")
    sex: int = Field(ge=0, le=1, description="1 = male, 0 = female")
    cp: int = Field(ge=0, le=3, description="Chest pain type (0-3)")
    trestbps: int = Field(ge=50, le=300, description="Resting blood pressure (mm Hg)")
    chol: int = Field(ge=50, le=700, description="Serum cholesterol (mg/dl)")
    fbs: int = Field(ge=0, le=1, description="Fasting blood sugar > 120 mg/dl (1 = yes)")
    restecg: int = Field(ge=0, le=2, description="Resting ECG result (0-2)")
    thalach: int = Field(ge=40, le=250, description="Max heart rate achieved")
    exang: int = Field(ge=0, le=1, description="Exercise-induced angina (1 = yes)")
    oldpeak: float = Field(ge=0, le=10, description="ST depression induced by exercise")
    slope: int = Field(ge=0, le=2, description="Slope of peak exercise ST segment (0-2)")
    ca: int = Field(ge=0, le=4, description="Number of major vessels colored (0-4)")
    thal: int = Field(ge=0, le=3, description="Thalassemia code (0-3)")


class Prediction(BaseModel):
    """Output schema.

    NOTE: we return the dataset's own `target` value (0/1) rather than "has_disease".
    In this Kaggle file target=1 goes with HIGHER max heart rate, LOWER ST depression and
    fewer blocked vessels, i.e. the healthier group, which contradicts the dataset
    description ("1 = disease"). Until the coding is confirmed, claiming a diagnosis
    would be misleading, so the API reports the label exactly as the data defines it.
    """

    target: int = Field(description="Predicted class as coded in the dataset (0 or 1)")
    probability_target_1: float = Field(description="Model probability that target == 1")


@bentoml.service(
    resources={"cpu": "1"},     # resource hint; matters when deploying
    traffic={"timeout": 30},    # seconds before a request is cancelled
)
class HeartService:
    # Declares a dependency on a model in the store. When you `bentoml build`,
    # this exact model version is bundled into the package.
    bento_model = bentoml.models.BentoModel("heart_clf:latest")

    def __init__(self) -> None:
        # Runs once at startup: load the sklearn Pipeline (preprocessing + classifier).
        self.model = bentoml.sklearn.load_model(self.bento_model)
        self.threshold = 0.5

    def _predict(self, rows: list[Patient]) -> list[Prediction]:
        # Pydantic objects -> DataFrame with the SAME column names used in training.
        df = pd.DataFrame([r.model_dump() for r in rows], columns=FEATURES)
        probs = self.model.predict_proba(df)[:, 1]
        return [
            Prediction(target=int(p >= self.threshold), probability_target_1=round(float(p), 4))
            for p in probs
        ]

    @bentoml.api
    def predict(self, patient: Patient) -> Prediction:
        """One patient in, one prediction out  ->  POST /predict"""
        return self._predict([patient])[0]

    @bentoml.api
    def predict_batch(self, patients: list[Patient]) -> list[Prediction]:
        """Many patients in one call  ->  POST /predict_batch"""
        return self._predict(patients)

    @bentoml.api
    def model_info(self) -> dict:
        """Returns the metadata we stored at training time (version, metrics) -> POST /model_info"""
        return {"tag": str(self.bento_model.tag), **self.bento_model.info.metadata}
