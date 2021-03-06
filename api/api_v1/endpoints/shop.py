from typing import Any, List,Optional

from fastapi import APIRouter, Depends, HTTPException,status,Header,Security
from sqlalchemy.orm import Session
from core.config import settings
import crud, models, schemas
from crud import crud_shop,crud_shop_executor,crud_user,crud_sim,crud_channel_manager
from schemas import shop_schema,shop_executor_schema
from api import deps
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
import mysql.connector
router = APIRouter()

@router.get("/")
def All_shop(
    skip: int = 0,
    limit: int = 100,
    current_user= Security(deps.get_current_active_user,scopes=["read_shop"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View All Shop
    '''
    return crud_shop.get_all_shops(db, skip=skip, limit=limit)

@router.get("/{shopid}", response_model=shop_schema.Shop)
def Shop_detail(
    shopid:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_shop"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View Shop detail by Shop Id request
    '''
    return crud_shop.get_shop(db=db,shop_id=shopid)

@router.get("/{shop_id}/count-executors")
def Number_of_shop_executors(
    shop_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_shop"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Number of executors that managed Shop with shop id
    '''
    return crud_shop_executor.count_shop_of_executors(db=db,shop_id=shop_id)

@router.get("/{shop_id}/all-executors")
def All_shop_executors(
    shop_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_shop"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View All shop executors
    '''
    return crud_user.get_all_shop_executors(db=db,shop_id=shop_id)

@router.get("/{shop_id}/all-executors-not-shop")
def All_executor_that_not_managed_shop(
    shop_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["read_shop"]),
    db: Session = Depends(deps.get_db)
):
    '''
    View all executors that not managed shop with shop id
    '''
    return crud_user.get_all_shop_not_belong_to_executors(db=db,shop_id=shop_id)

@router.post("/{shop_id}/add-many-executor")
async def add_many_executor_to_shop(
    executors_id: List[str],
    shop_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["shop_executor"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Asign one or many executors to shop with shop id and list of executor id
    '''
    current_shop=crud_shop.get_shop(db=db,shop_id=shop_id)
    if current_user.role=="manager":
        if crud_channel_manager.get_channel_manager(db=db,channel_id=current_shop.channel_id,manager_id=current_user.id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shop not belong to your channel"
        )
    if len(executors_id) ==0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Executor id list must be not None"
        )
    if current_shop is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shop id doesn't Exist"+shop_id
        )
    for id in executors_id:
        if crud_user.get_user(db=db,user_id=id)is None or crud_user.get_user(db=db,user_id=id).role!="executor" :
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid executor id"
        )      
    for id in executors_id:
        if not crud_shop_executor.get_shop_executor(db=db,shop_id=shop_id,executor_id=id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Executor already exist in shop"
        )
    for id in executors_id:
        crud_shop_executor.create_new_shop_executor(db=db,shop_id=shop_id,executor_id=id)
    return {"message":"update success"}

@router.post("/{shop_id}/delete-many-executor")
async def delete_executors_of_shop(
    executors_id: List[str],
    shop_id:str,
    current_user= Security(deps.get_current_active_user,scopes=["shop_executor"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Delete one or many executors to shop with shop id and list of executor id
    '''
    current_shop=crud_shop.get_shop(db=db,shop_id=shop_id)
    if current_user.role=="manager":
        if crud_channel_manager.get_channel_manager(db=db,channel_id=current_shop.channel_id,manager_id=current_user.id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shop not belong to your channel"
        )
    if len(executors_id) ==0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Executor id list must be not None"
        )
    if current_shop is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shop id doesn't Exist"+shop_id
        )
    for id in executors_id:
        if crud_user.get_user(db=db,user_id=id)is None or crud_user.get_user(db=db,user_id=id).role!="executor" :
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid executor id"
        )      
    for id in executors_id:
        if crud_shop_executor.get_shop_executor(db=db,shop_id=shop_id,executor_id=id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Executor not exist in shop"
        )
    for id in executors_id:
        crud_shop_executor.delete_shop_executor(db=db,shop_id=shop_id,executor_id=id)
    return {"message":"update success"}

@router.post("/add-executors-shops")
async def add_many_executor_to_many_shop(
    executors_id: List[str],
    shop_id:List[str],
    current_user= Security(deps.get_current_active_user,scopes=["shop_executor"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Asign one or many executors to one or many shops with list of  executors and shops request
    '''  
    if len(executors_id) ==0 :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid value for executor id list"
        )
    if len(shop_id) ==0 :
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid value for shop id list"
        )
    for id in shop_id:
        current_shop=crud_shop.get_shop(db=db,shop_id=id)
        if current_shop is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Shop id doesn't Exist"+id
            )
    if current_user.role=="manager":
        for id in shop_id:
            current_shop=crud_shop.get_shop(db=db,shop_id=id)
            if crud_channel_manager.get_channel_manager(db=db,channel_id=current_shop.channel_id,manager_id=current_user.id) is None:
                raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Shop doesn't belong to your channel"
            )
            
    for id in executors_id:
        if  crud_user.get_user(db=db,user_id=id) is None or crud_user.get_user(db=db,user_id=id).role!="executor":
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User is Not executor"
        ) 
        
    for eid in executors_id:
        for sid in shop_id:
            if not crud_shop_executor.get_shop_executor(db=db,shop_id=sid,executor_id=eid) is None:
                raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Executor already exist in shop"
            )
    for eid in executors_id:
        for sid in shop_id:
            crud_shop_executor.create_new_shop_executor(db=db,shop_id=sid,executor_id=eid)
    return {"message":"update success"}

@router.post("/{shopid}/update-sim")
async def update_shop_sim(
    shop_id:str,
    sim_number:str,
    current_user= Security(deps.get_current_active_user,scopes=["shop_executor"]),
    db: Session = Depends(deps.get_db)
):
    '''
    Update sim number of shop
    '''
    current_shop=crud_shop.get_shop(db=db,shop_id=shop_id)
    if current_user.role=="manager":
        if crud_channel_manager.get_channel_manager(db=db,channel_id=current_shop.channel_id,manager_id=current_user.id) is None:
            raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shop not belong to your channel"
        )
    if crud_sim.get_sim_by_number(db=db,sim_number=sim_number) is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Sim number Not Found"
        )
    if current_shop is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Shop not found"
        )
    crud_shop.update_shop_sim(db=db,sim_number=sim_number,shop_id=shop_id)
    return {"message":"update success"}

    

