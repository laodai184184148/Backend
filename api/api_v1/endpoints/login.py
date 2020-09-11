from typing import Any, List
from models import token,user
from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from core.config import settings
from fastapi.responses import JSONResponse
from core import sercurity
import crud, models, schemas
from schemas import channel_manager_schema
from api import deps
import requests
from datetime import datetime, timedelta
import mysql.connector
router = APIRouter()




def check_sercurity_scopes(role,scopes):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    if role=="executor":
        if not (scopes in settings.EXECUTOR_SCOPES):
            raise  credentials_exception
    elif role=="manager":
        if not (scopes in settings.MANAGER_SCOPES):
            raise  credentials_exception
    elif role=="newuser":
        if not (scopes in settings.NEWUSER_SCOPES):
            raise  credentials_exception

def get_scopes(role):
    if role=="executor":
        return settings.EXECUTOR_SCOPES
    elif role=="manager":
        return settings.MANAGER_SCOPES
    elif role=="admin":
        return settings.ADMIN_SCOPES
    else:
        return settings.NEWUSER_SCOPES

@router.post("/login/token", response_model= token.Token,tags=["login"])
async def login_for_access_token(User_Account :  user.User_Account,db: Session = Depends(deps.get_db)):
    try:
        curent_user=crud.crud_user.get_user_by_username(db,User_Account.username)
        if curent_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username ",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token =sercurity.create_access_token(
            data={"sub": curent_user.user_name,
            "role":curent_user.role,
            "id":curent_user.id,
            "scopes":get_scopes(curent_user.role)
            
            }, expires_delta=access_token_expires
        )
    except (mysql.connector.Error):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="My sql connection error ",
            headers={"WWW-Authenticate": "Bearer"},
        ) 
    return JSONResponse({"access_token": access_token, "token_type": "bearer"})



@router.get("/gmail/access-token")
async def login_with_google(google_token_id:str ):
    try:

        idinfo = id_token.verify_oauth2_token(google_token_id, requests.Request())
        curent_user=user.get_user_db(idinfo["email"])
        if curent_user is None :
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un registered"
            ) 
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token =sercurity.c(
            data={"sub": curent_user["username"],
            "role":curent_user["role"],
            "id":curent_user["id"],
            "scopes":get_scopes(curent_user.role)
            }, expires_delta=access_token_expires
        )
        userid = idinfo['sub']
    except ValueError:
        raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="token id error ",
                headers={"WWW-Authenticate": "Bearer"},
            ) 
    pass
    return {"access_token": access_token,"token_type": "bearer"}