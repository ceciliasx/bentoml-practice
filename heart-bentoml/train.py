"""STEP 1 - TRAIN: build a model and put it into the BentoML model store.

Run:  python train.py

What happens here (and why):
  1. Load heart.csv and DROP DUPLICATES. The raw file has 1025 rows but only 302 unique
     patients; if duplicates land in both train and test the score is inflated.
  2. Build ONE sklearn Pipeline = preprocessing + classifier. This is the key
     deployment idea: because the preprocessing lives INSIDE the model object, the API
     can accept raw patient values and nothing can drift between training and serving.
  3. Evaluate on a held-out test set (honest numbers).
  4. Save to the BentoML model store with metadata (metrics, feature list). The store
     versions it automatically: heart_clf:<random-version-tag>, and `heart_clf:latest`
     always points at the newest one.
"""
import bentoml
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Columns are numeric measurements vs. coded categories (e.g. cp = chest pain type 0-3).
NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL = ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"]
FEATURES = NUMERIC + CATEGORICAL
TARGET = "target"

# ---- 1. data -------------------------------------------------------------------
df = pd.read_csv("heart.csv")
n_raw = len(df)
df = df.drop_duplicates().reset_index(drop=True)
print(f"rows: {n_raw} raw -> {len(df)} after removing duplicates")

X, y = df[FEATURES], df[TARGET]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

# ---- 2. model: preprocessing + classifier in ONE object -------------------------
preprocess = ColumnTransformer(
    [
        ("num", StandardScaler(), NUMERIC),  # put numbers on the same scale
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),  # codes -> 0/1 columns
    ]
)
model = Pipeline([("prep", preprocess), ("clf", RandomForestClassifier())])
model.fit(X_train, y_train)

# ---- 3. honest evaluation on unseen data -----------------------------------------
acc = accuracy_score(y_test, model.predict(X_test))
auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
print(f"test accuracy={acc:.3f}  roc_auc={auc:.3f}  (n_test={len(X_test)})")

# ---- 4. save into the BentoML model store ----------------------------------------
saved = bentoml.sklearn.save_model(
    "heart_clf",
    model,
    labels={"task": "heart-disease", "stage": "practice"},  # searchable tags
    metadata={  # free-form info that travels with the model version
        "features": FEATURES,
        "test_accuracy": round(float(acc), 4),
        "test_roc_auc": round(float(auc), 4),
        "n_train": int(len(X_train)),
        "dataset": "kaggle johnsmith88/heart-disease-dataset (deduplicated)",
    },
)
print("saved to model store:", saved)
print("inspect with:  bentoml models list   |   bentoml models get heart_clf:latest")
