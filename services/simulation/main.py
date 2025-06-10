from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import numpy as np
import redis
import json

class SimConfig(BaseModel):
    id: str

app = FastAPI()
r = redis.Redis(host="redis", port=6379)

@app.post("/simulate")
def simulate(config: SimConfig):
    key = config.id
    for t in np.linspace(0, 2*np.pi, 100):
        frame = {"x": float(t), "y": float(np.sin(t))}
        r.publish(key, json.dumps(frame))
    return {"status": "started"}