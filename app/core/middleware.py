import time
from urllib import response
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

BLACKLIST = {}


def register_middleware(app: FastAPI):

    app.add.middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        print(f"**ENTRADA: {request.method} {request.url}")
        response = await call_next(request)
        print(f"**SALIDA: {response.status_code}")
        return response

    @app.middleware("http")
    async def add_request_id_header(request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.middleware("http")
    async def block_ip_middleware(request: Request, call_next):
        client_ip = request.client.host
        if client_ip in BLACKLIST:
            raise HTTPException(status_code=403, detail="Forbidden")
        return await call_next(request)
