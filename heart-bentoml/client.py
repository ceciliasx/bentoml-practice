"""STEP 3 - CALL the running service from Python.  (Server must be running: bentoml serve ...)

Run:  python client.py

bentoml.SyncHTTPClient reads the service's schema and gives you a Python method per
endpoint. The same calls work from curl, Postman, or any language, because it's plain HTTP.
"""
import bentoml

# Two made-up patient profiles plus one deliberately invalid input.
# (Which one the model puts in class 1 follows the dataset's own coding, see the
#  note in service.py about the target label.)
profile_a = dict(age=41, sex=0, cp=1, trestbps=130, chol=204, fbs=0, restecg=0,
                 thalach=172, exang=0, oldpeak=1.4, slope=2, ca=0, thal=2)
profile_b = dict(age=62, sex=1, cp=0, trestbps=140, chol=268, fbs=0, restecg=0,
                 thalach=160, exang=0, oldpeak=3.6, slope=0, ca=2, thal=3)
invalid = dict(profile_a, age=250)  # age out of range -> must be rejected

with bentoml.SyncHTTPClient("http://localhost:3000") as client:
    print("model_info   :", client.model_info())
    print("single       :", client.predict(patient=profile_a))
    print("batch        :", client.predict_batch(patients=[profile_a, profile_b]))
    try:
        client.predict(patient=invalid)
    except Exception as e:
        print("invalid input rejected ->", type(e).__name__, "|", str(e)[:140])
