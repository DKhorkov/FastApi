import asyncio
import datetime
import os
import uvicorn

from fastapi import FastAPI, Request, WebSocket
from starlette.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory='./templates')


@app.get("/")
async def get_date(request: Request):
    return templates.TemplateResponse(
        name="current_datetime.html",
        context={'request': request},
        status_code=200,
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await websocket.send_text(data)
        await asyncio.sleep(1)


if __name__ == '__main__':
    uvicorn.run("current_datetime:app", host="0.0.0.0", port=os.getenv("PORT", default=8090), log_level="info")
