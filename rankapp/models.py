from sqlalchemy import Column, ForeignKey, Integer, String, Date, Float
from .database import mapper_registry

@mapper_registry.mapped
class RankEntry:
    __tablename__ = "rank_entry"

    id = Column(Integer, primary_key=True)
    company = Column(String)
    contractType = Column(String)
    contractTypeC = Column(String)
    contractID = Column(String)
    ex = Column(String)
    rank = Column(Integer)
    chg = Column(Integer)
    date = Column(Date)
    vol = Column(Integer)
    volType = Column(String)

    # Will be called when selecting the whole class object.
    def __repr__(self):
        return "<RankEntry(%r, %r, %r, %r, %r, %r, %r, %r, %r, %r)>" % (
            self.company, 
            self.contractType,
            self.contractTypeC,
            self.contractID,
            self.ex,
            self.rank,
            self.chg,
            self.date,
            self.vol,
            self.volType
        )
    
@mapper_registry.mapped
class NetPosition:
    __tablename__ = "net_position"

    id = Column(Integer, primary_key=True)
    net = Column(Integer)
    rank_id = Column(ForeignKey("rank_entry.id"), nullable=False)
    
    def __repr__(self):
        return "<NetPosition(%r)>" % (
            self.net
        )
    
@mapper_registry.mapped
class MarketInfo:
    __tablename__ = "market_info"

    id = Column(Integer, primary_key=True)
    contractType = Column(String)
    contractTypeC = Column(String)
    contractID = Column(String)
    ex = Column(String)
    date = Column(Date)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    vol = Column(Integer)
    turnover = Column(Float)
    settle = Column(Float)
    settle_prev = Column(Float)
    interest = Column(Integer)

    def __repr__(self):
        return "<RankEntry(%r, %r, %r, %r, %r, %r, %r, %r, %r, %r, %r, %r)>" % (
            self.contractType,
            self.contractTypeC,
            self.contractID,
            self.ex,
            self.date,
            self.open,
            self.close,
            self.high,
            self.low,
            self.vol,
            self.turnover,
            self.settle,
            self.settle_prev,
            self.interest,
        )