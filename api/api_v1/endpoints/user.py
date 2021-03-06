from typing import Any, List,Optional
from core.config import settings
from fastapi import APIRouter, Depends, HTTPException,status,Header,Security
from sqlalchemy.orm import Session
import json
import crud, models, schemas
from crud import crud_user,crud_shop,crud_channel,crud_shop_executor,crud_channel_manager,crud_url,crud_sim_url,crud_sim
from schemas import user_schema,shop_schema,channel_schema
from api import deps
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
from core import sercurity
import mysql.connector
router = APIRouter()

@router.get("/", response_model=List[user_schema.User])
def All_users(
    current_user= Security(deps.get_current_active_user,scopes=["read_user"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View All User
    '''
    return crud_user.get_all_user(db=db)


@router.get("/executors")
def All_executors(
    current_user= Security(deps.get_current_active_user,scopes=["read_user"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View All executor User
    '''
    return crud_user.get_all_executor(db=db)

@router.get("/managers")
def All_managers(
    current_user= Security(deps.get_current_active_user,scopes=["read_user"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View All manager User
    '''
    return crud_user.get_all_manager(db=db)

@router.get("/{id}", response_model=user_schema.User)
def user_detail(
    id:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_user"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View user detail  with user id 
    '''
    return crud_user.get_user(db=db,user_id=id)

@router.post("/{id}/inactivate")
def Inactivate_user(
    id:str,
    current_user= Security(deps.get_current_active_user,scopes=["inactivate_user"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Inactivate user
    '''
    crud_user.inactivate_user(db=db,user_id=id,activate="0")
    return {"message":"Inactivate success"}

@router.post("/{admin_id}/add-new-url")
def add_new_url(
    url:str,
    current_user= Security(deps.get_current_active_user,scopes=["url"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Inactivate user
    '''
    return crud_url.create_new_url(db=db,new_url=url)

@router.post("/add-new-url")
def add_new_url(
    url:str,
    current_user= Security(deps.get_current_active_user,scopes=["url"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Inactivate user
    '''
    return crud_url.create_new_url(db=db,new_url=url)

@router.post("/update-url")
def update_url(
    url_id:str,
    new_url:str,
    current_user= Security(deps.get_current_active_user,scopes=["url"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Inactivate user
    '''
    if crud_url.get_url(db=db,id=url_id) is None:
        raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Url not found"
            )
    crud_url.update_url(db=db,id=url_id,new_url=new_url)
    return {"message":" success"}


@router.post("/asign-url-to-sim")
def asign_url_to_sim(
    sim:List[str],
    url:List[str],
    current_user= Security(deps.get_current_active_user,scopes=["url"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Inactivate user
    '''
    for s in sim:
        if crud_sim.get_sim_by_number(db=db,sim_number=s) is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Sim not found"
            )
    for u in url:
        if crud_url.get_url(db=db,id=u) is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Url not found"
            )
    for s in sim:
        for u in url:
            if not crud_sim_url.get_sim_url(db=db,sim_number=s,url_id=u) is None:
                raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Sim url already exist"
            )
    for s in sim:
        for u in url:
            crud_sim_url.create_new_sim_url(db=db,sim_number=s,url_id=u)
    return {"message":" success"}



@router.post("/{id}/activate")
def activate_user(
    id:str,
    current_user= Security(deps.get_current_active_user,scopes=["inactivate_user"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Activate user
    '''
    crud_user.inactivate_user(db=db,user_id=id,activate="1")
    return {"message":"Activate success"}

@router.get("/{executor_id}/all-shop")
def get_all_shops_executor(
    executor_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_user"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View all executor shop
    '''
    executor=crud_user.get_user(db=db,user_id=executor_id)
    if executor is None or executor.role!="executor"   :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid executor id"
        ) 
    return crud_shop.get_all_shop_of_executor(db=db,executor_id=executor_id)

@router.post("/{executors_id}/add-many-shop")
async def asign_shop_to_executor(
    executors_id: str,
    shop_id:List[str],
    current_user= Security(deps.get_current_active_user,scopes=["shop_executor"]),
    db: Session = Depends(deps.get_db)
):

    if current_user.role=="manager":
        for id in shop_id:
            if crud_shop.check_shop_manager(db=db,shop_id=id,manager_id=current_user.id) is False:
                raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Shop not belong to your channel"
            )

    executor=crud_user.get_user(db=db,user_id=executors_id)
    if executor is None or executor.role!="executor"   :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid executor id"
        )

    for id in shop_id:
        if not crud_shop_executor.get_shop_executor(db=db,shop_id=id,executor_id=executors_id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Executor already exist in shop"
        )
    for id in shop_id:
        crud_shop_executor.create_new_shop_executor(db=db,shop_id=id,executor_id=executors_id)
    return {"message":"update success"}

@router.post("/{executors_id}/delete-many-shop")
async def delete_shop_for_executors(
    executors_id: str,
    shop_id:List[str],
    current_user= Security(deps.get_current_active_user,scopes=["shop_executor"]),
    db: Session = Depends(deps.get_db)
):

    if current_user.role=="manager":
        for id in shop_id:
            if crud_shop.check_shop_manager(db=db,shop_id=id,manager_id=current_user.id) is False:
                raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Shop not belong to your channel"
            )
    executor=crud_user.get_user(db=db,user_id=executors_id)
    if executor is None or executor.role!="executor"   :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid executor id"
        )

    for id in shop_id:
        if crud_shop_executor.get_shop_executor(db=db,shop_id=id,executor_id=executors_id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shop not found"
        )
    for id in shop_id:
        crud_shop_executor.delete_shop_executor(db=db,shop_id=id,executor_id=executors_id)
    return {"message":"delete success"}

@router.get("/{executor_id}/all-shop-not-asign", response_model=List[shop_schema.Shop])
def get_all_shops_executor_not_asign(
    executor_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_user"]),
    db: Session = Depends(deps.get_db)
):
    executor=crud_user.get_user(db=db,user_id=executor_id)
    if executor is None or executor.role!="executor"   :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid executor id"
        )
    return crud_shop.get_all_not_shop_of_executor(db=db,executor_id=executor_id)

@router.get("/{manager_id}/all-channel", response_model=List[channel_schema.Channel])
def get_all_channel_of_manager(
    manager_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_user"]),
    db: Session = Depends(deps.get_db)
):
    executor=crud_user.get_user(db=db,user_id=manager_id)
    if executor is None or executor.role!="manager"   :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid manager id"
        )
    return crud_channel.get_all_channel_of_manager(db=db,manager_id=manager_id)

@router.get("/{manager_id}/all-channel-not-asign", response_model=List[channel_schema.Channel])
def get_all_channel_not_asign_to_manager(
    manager_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_user"]),
    db: Session = Depends(deps.get_db)
):

    executor=crud_user.get_user(db=db,user_id=manager_id)
    if executor is None or executor.role!="manager":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid manager id"
        )
    return crud_channel.get_all_not_channel_of_manager(db=db,manager_id=manager_id)

@router.post("/{manager_id}/add-channel")
def asign_channel_to_manager(
    manager_id: str,
    channel_id:List[str],
    current_user= Security(deps.get_current_active_user,scopes=["channel_manager"]),
    db: Session = Depends(deps.get_db)
):
    manager=crud_user.get_user(db=db,user_id=manager_id)
    if manager is None or manager.role!="manager"   :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid manager id"
        )
    for id in channel_id:
        if crud_channel.get_channel(db=db,channel_id=id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid channel id"
        )
    for id in channel_id:
        if not crud_channel_manager.get_channel_manager(db=db,channel_id=id,manager_id=manager_id) is None:
            if crud_channel.get_channel(db=db,channel_id=id):
                raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Channel already asign to manager"
        )
    for id in channel_id:
        crud_channel_manager.create_channel_manager(db=db,manager_id=manager_id,channel_id=id)
    return {"message":"update success"}

@router.post("/{manager_id}/delete-channel")
def delete_channel_of_manager(
    manager_id: str,
    channel_id:List[str],
    current_user= Security(deps.get_current_active_user,scopes=["channel_manager"]),
    db: Session = Depends(deps.get_db)
):
    manager=crud_user.get_user(db=db,user_id=manager_id)
    if manager is None or manager.role!="manager"   :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid manager id"
        )
    for id in channel_id:
        if crud_channel.get_channel(db=db,channel_id=id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid channel id"
        )
    for id in channel_id:
        if crud_channel_manager.get_channel_manager(db=db,channel_id=id,manager_id=manager_id) is None:
            if crud_channel.get_channel(db=db,channel_id=id):
                raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Channel not  asign to manager"
        )
    for id in channel_id:
        crud_channel_manager.delete_channel_manager(db=db,manager_id=manager_id,channel_id=id)
    return {"message":"delete success"}