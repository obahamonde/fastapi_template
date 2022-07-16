from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, File, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from requests import get, post
from pydantic import HttpUrl, EmailStr

from faunadb import query as q
from src.func import get_token, upload_file, send_email, make_qrcode, verify_token
from src.model.tables import User
from src.lib.fql import fql, Q
from src.utils import id, now, avatar, jsonify
from src.conf import env

app = APIRouter()


@app.get("/")
def root(token: str = Depends(get_token)):
    return token

@app.get("/token/{token}")
def verify(token:str = Depends(root)):
    return verify_token(token)