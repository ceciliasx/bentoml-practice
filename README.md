# bentoml-practice
doing a little practice with bentoml
dataset source: [heart disease dataset](https://www.kaggle.com/datasets/johnsmith88/heart-disease-dataset)

## contents
- `heart-bentoml/` – train a classifier, serve it with bentoml, call it with a client
- `rollout-bentoml/` – streaming-rollout skeleton (frame-by-frame output)
- `monitoring-bentoml/` – concurrency and adaptive-batching tests (`square_one` vs `square_batch`), plus custom cpu/ram metrics added to `/metrics`
