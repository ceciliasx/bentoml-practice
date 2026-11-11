# BentoML Walkthrough: Heart Disease Dataset

Tested with BentoML 1.4.40. Dataset: Kaggle `johnsmith88/heart-disease-dataset`.
This is a learning exercise, not a medical tool.

---

## Part 1: The concepts (read first)

**What problem does BentoML solve?**
A trained model is just a file/object in a notebook. To be *used* by an app, it has to
become a service: something that accepts a request, runs the model, returns a response,
validates input, scales, and ships with the right dependencies. BentoML provides that
layer so you write Python, not web-server plumbing.

**The lifecycle**

```
train.py            service.py              bentofile.yaml            Docker / cloud
 train model  ->  wrap in a Service  ->  `bentoml build`  ->  `bentoml containerize`
 save to store    `bentoml serve`        = a versioned Bento     = image you deploy
```

**The 5 building blocks**

| Term | What it is | Where in this project |
|------|-----------|------------------------|
| Model store | Local versioned registry of saved models (`name:version`, `:latest`) | `train.py` saves `heart_clf` |
| Service | A Python class decorated with `@bentoml.service` | `HeartService` in `service.py` |
| API | A method decorated with `@bentoml.api` = one HTTP endpoint (`POST /<method>`) | `predict`, `predict_batch`, `model_info` |
| Schema | Pydantic classes describing input/output; invalid input is rejected with HTTP 400 | `Patient`, `Prediction` |
| Bento | Built, self-contained package: code + pinned model + dependency list | produced by `bentoml build` |

**Two design decisions worth understanding**
1. **Preprocessing lives inside the model** (an sklearn `Pipeline`). The API accepts raw
   values (age, cholesterol...) and the scaler/encoder runs inside. Otherwise you have to
   duplicate preprocessing in the service and the two copies can silently drift apart.
2. **The model loads once, in `__init__`**, not inside the endpoint. Loading per request
   would make every call slow.

---

## Part 2: Walkthrough (do these in order)

Open the folder `heart-bentoml` in your editor. Use two terminals, both `cd`'d into it.

### Step 0: Setup
```
pip install bentoml scikit-learn pandas
```

### Step 1: Train and save the model: `python train.py`
Read `train.py` while it runs. Expected output (yours should match closely):
```
rows: 1025 raw -> 302 after removing duplicates
test accuracy=0.842  roc_auc=0.902  (n_test=76)
saved to model store: Model(tag="heart_clf:<version>")
```
**What to notice**
- 723 of 1025 rows were duplicates. Without removing them, test accuracy looks inflated
  because identical rows land in both train and test.
- Only 76 test rows, so the 84% is a rough estimate, not a precise one.

**Try it:** `bentoml models list` and `bentoml models get heart_clf:latest` (see the
stored metadata). Run `python train.py` again: you get a *second version*, and `:latest`
moves to it. That is model versioning.

### Step 2: Serve: `bentoml serve service:HeartService` (terminal 1)
- `service:HeartService` means file `service.py`, class `HeartService`. That's why you
  must run it from inside this folder.
- Open <http://localhost:3000>. This is the auto-generated Swagger UI, built from your
  Pydantic schemas. Expand `POST /predict`, click **Try it out**, edit the values, **Execute**.
- Try an invalid value (age = 250) in the UI and see the 400 error. Your code never ran;
  the schema rejected it.

### Step 3: Call it from code: `python client.py` (terminal 2)
You'll see `model_info`, a single prediction, a batch prediction, and the rejected invalid input.
The same calls work from any language because it is plain HTTP, for example PowerShell:
```
Invoke-RestMethod -Method Post -Uri http://localhost:3000/predict -ContentType "application/json" -Body '{"patient":{"age":62,"sex":1,"cp":0,"trestbps":140,"chol":268,"fbs":0,"restecg":0,"thalach":160,"exang":0,"oldpeak":3.6,"slope":0,"ca":2,"thal":3}}'
```

### Step 4: Build a Bento: `bentoml build` (stop the server first with Ctrl+C)
- Reads `bentofile.yaml`: which service, which files, which pip packages, which model.
- Produces `heart_service:<version>`. See it with `bentoml list`.
- The Bento has the **exact model version pinned inside**, so it is reproducible even if
  you retrain later.

### Step 5 (optional, needs Docker): `bentoml containerize heart_service:latest`
Creates a Docker image. Run it with `docker run -p 3000:3000 heart_service:<tag>`.
This is the artifact you hand to whoever deploys it.

---

## Part 3: Important caveat: the label coding in this dataset

The Kaggle page says `target = 1` means heart disease. But in this file, `target = 1`
goes with **higher** max heart rate, **lower** ST depression, **fewer** blocked vessels
and **less** exercise angina (means below, after removing duplicates), which clinically
points to the *healthier* group. This is a known quirk of the dataset.

| target | thalach (max HR) | oldpeak | ca | exang |
|--------|------|------|------|------|
| 0 | 139.1 | 1.59 | 1.17 | 0.55 |
| 1 | 158.4 | 0.59 | 0.34 | 0.14 |

So the API returns `target` and `probability_target_1` exactly as the dataset codes them,
instead of claiming "has disease". I did not flip the labels myself because that is an
inference; confirm it before any real use. (Good talking point for your internship: always
verify what a label means before shipping a model.)

---

## Part 4: Exercises (do these after the basic flow works)

1. **Swap the model.** In `train.py` replace `LogisticRegression` with
   `RandomForestClassifier`. Retrain, check `bentoml models list`, restart the server.
   Did `service.py` need to change? (It shouldn't. That's the point of the separation.)
2. **Tighten validation.** Make `chol` limited to `ge=100, le=600` and confirm 99 is rejected.
3. **Add an endpoint** `predict_proba_all` that returns the probabilities for both classes.
4. **Add a threshold parameter.** Let the caller pass `threshold: float = 0.5` to `predict`.
5. **Pin a version.** Change `heart_clf:latest` in `service.py` to a specific tag from
   `bentoml models list`. Retrain, and confirm the service still uses the old one.
6. **Add adaptive batching.** Look up `@bentoml.api(batchable=True)` (from the earlier
   practice pack, `ex3_batching`) and apply it to a numpy-based endpoint.
7. **Next step up:** replace the model with a Hugging Face pipeline while keeping the same
   Service/API structure.

## Troubleshooting
- `bentoml: command not found` -> `python -m bentoml serve service:HeartService`.
- `Model 'heart_clf' not found` -> run `python train.py` first (the store is per-machine).
- Port 3000 busy -> add `--port 3001` and change the URL in `client.py`.
- Changed `service.py` while serving? Use `bentoml serve service:HeartService --reload`.
