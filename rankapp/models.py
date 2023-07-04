import enum

from sqlalchemy import Column, ForeignKey, Integer, String, Date, Enum
from sqlalchemy.orm import relationship
from .database import mapper_registry
from .schemas import VolumeType

@mapper_registry.mapped
class RankEntry:
    __tablename__ = "rank_entry"

    id = Column(Integer, primary_key=True)
    companyname = Column(String)
    instrumentType = Column(String)
    instrumentID = Column(String)
    exchange = Column(String)
    rank = Column(Integer)
    change = Column(Integer)
    date = Column(Date)
    volume = Column(Integer)
    volumetype = Column(Enum(VolumeType))

    # Will be called when selecting the whole class object.
    def __repr__(self):
        return "<RankEntry(%r, %r, %r, %r, %r, %r, %r, %r, %r)>" % (
            self.companyname, 
            self.instrumentType,
            self.instrumentID,
            self.exchange,
            self.rank,
            self.change,
            self.date,
            self.volume,
            self.volumetype
        )
    
@mapper_registry.mapped
class NetPosition:
    __tablename__ = "net_position"

    id = Column(Integer, primary_key=True)
    net_pos = Column(Integer)
    rank_entry_id = Column(ForeignKey("rank_entry.id"), nullable=False)
    
    # Will be called when selecting the whole class object.
    def __repr__(self):
        return "<NetPosition(%r)>" % (
            self.net_pos
        )