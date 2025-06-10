"""
This is the main simulation service built with FastAPI.
It generates simulation frames (sine wave data) and streams them via WebSockets.
Written with extensive documentation so even the newest developers understand each step.
"""

from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel, Field
import numpy as np
import redis
import json

# Define a Pydantic model for request validation.
# This provides clear feedback on what data is expected.
class SimConfig(BaseModel):
    id: str = Field(..., description="Unique channel id for simulation results, e.g., 'sim-1'")
    amplitude: float = Field(1.0, description="Amplitude of the sine wave (default is 1.0)")
    frequency: float = Field(1.0, description="Frequency multiplier for sine computation (default: 1.0)")
    phase: float = Field(0.0, description="Phase shift of the sine wave in radians (default is 0.0)")
    frames: int = Field(100, gt=0, description="Number of simulation frames to generate (must be > 0)")

app = FastAPI()
# Connect to a Redis server; the hostname 'redis' is set via Docker Compose.
r = redis.Redis(host="redis", port=6379)

@app.post("/simulate")
def simulate(config: SimConfig):
    """
    POST endpoint to start a simulation.
    Calculates a sine wave based on the input configuration and publishes each frame to a Redis channel.
    """
    key = config.id
    # Create a time vector and compute sine values using numpy.
    t = np.linspace(0, 2 * np.pi, config.frames)
    y = config.amplitude * np.sin(config.frequency * t + config.phase)
    # Generate a list of frames containing x and y values.
    frames = [{"x": float(x), "y": float(y_val)} for x, y_val in zip(t, y)]
    
    # Publish each frame as a JSON string to the Redis channel.
    for frame in frames:
        r.publish(key, json.dumps(frame))
    return {"status": "started", "frames": config.frames}

@app.websocket("/ws/{key}")
async def ws_endpoint(websocket: WebSocket, key: str):
    """
    WebSocket endpoint to subscribe to simulation data.
    Clients connect here to receive simulation frames in real time.
    """
    await websocket.accept()
    pubsub = r.pubsub()
    pubsub.subscribe(key)
    try:
        # Listen for messages and forward each frame to the WebSocket client.
        for msg in pubsub.listen():
            if msg.get('type') == 'message' and msg.get('data'):
                await websocket.send_text(msg['data'].decode())
    except Exception:
        # Ensure the connection is closed cleanly on error.
        await websocket.close(code=1001)