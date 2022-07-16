

from fastapi import FastAPI
from src.hooks.db import useDB
from src.hooks.server import useServer
from src.router.users import app as users

def main():
    app = useServer(useDB(FastAPI()))   
    app.include_router(users)
    return app
