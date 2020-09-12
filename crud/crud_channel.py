from sqlalchemy.orm import Session
from crud import crud_channel_manager
from models import channel
from schemas import channel_schema

def get_channel(db: Session, channel_id: str):
    return db.query(channel.Channel).filter(channel.Channel.id == channel_id).first()

def get_all_channel(db: Session, skip: int = 0, limit: int = 100):
    return db.query(channel.Channel).offset(skip).limit(limit).all()

def get_all_channel_db(db: Session):
    return db.query(channel.Channel).all()

def create_channel(db: Session, created_channel: channel_schema.ChannelCreate):
    db_channel = channel.Channel(id=created_channel.id,name=created_channel.name)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

def get_all_channel_of_manager(db:Session,manager_id:str):
    all_channel_id=[]
    for id in crud_channel_manager.get_channel_id_of_manager(db=db,manager_id=manager_id):
        all_channel_id.append(id[0])

    return db.query(channel.Channel).filter(channel.Channel.id.in_(all_channel_id)).all()

def get_all_not_channel_of_manager(db:Session,manager_id:str):
    all_channel_id=[]
    for id in crud_channel_manager.get_channel_id_of_manager(db=db,manager_id=manager_id):
        all_channel_id.append(id[0])

    return db.query(channel.Channel).filter(channel.Channel.id.notin_(all_channel_id)).all()


