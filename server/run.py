from typing import List, Dict
import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket):
        self.active_connections[websocket] = {
            'last_message_time': datetime.datetime.now(),
            'ignore': False
        }
        await websocket.accept()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket)

    async def process_message(self, websocket: WebSocket, message: str):
        conn_data = self.active_connections[websocket]

        curr_message_time = datetime.datetime.now()
        message_interval = curr_message_time - conn_data['last_message_time']

        conn_data['last_message_time'] = curr_message_time

        if not conn_data['ignore']:
            if message_interval <= datetime.timedelta(seconds=0.1):
                conn_data['ignore'] = True
            else:
                await manager.broadcast(message)
        else:
            if message_interval >= datetime.timedelta(seconds=1):
                conn_data['ignore'] = False

    async def send_personal_message(self, message: str, websocket: WebSocket):
        if websocket not in self.ignored_connections:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
manager = ConnectionManager()


@app.websocket("/subscribe")
async def websocket_endpoint(websocket: WebSocket):
    #TODO: Check, if there is the same WebSocket instance for all connections
    print(web)
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.process_message(websocket, message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
