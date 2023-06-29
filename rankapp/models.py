import enum

from sqlalchemy import Column, ForeignKey, Integer, String, Date, Enum
from sqlalchemy.orm import relationship
from .database import mapper_registry

class VolumeType(enum.Enum):
    trading = 'trading'
    long = 'long'
    short = 'short'

@mapper_registry.mapped
class RankEntry:
    __tablename__ = "rank_entry"

    id = Column(Integer, primary_key=True)
    companyname = Column(String)
    instrumentID = Column(String)
    exchange = Column(String)
    rank = Column(Integer)
    change = Column(Integer)
    date = Column(Date)
    volume = Column(Integer)
    volumetype = Column(Enum(VolumeType))

    # Will be called when selecting the whole class object.
    def __repr__(self):
        return "<RankEntry(%r, %r, %r, %r, %r, %r, %r, %r)>" % (
            self.companyname, 
            self.instrumentID,
            self.exchange,
            self.rank,
            self.change,
            self.date,
            self.volume,
            self.volumetype
        )