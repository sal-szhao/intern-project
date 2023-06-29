from .database import Session
from .models import RankEntry
from . import schemas
from sqlalchemy import select, and_


def get_rank_entries(db: Session, rank_query: schemas.RankQuery):
    query = (
        select(RankEntry).where(
            and_(
                RankEntry.instrumentID == rank_query.instrumentID,
                RankEntry.date == rank_query.date,
                RankEntry.exchange == rank_query.exchange,
            )
        )
        .order_by(RankEntry.rank)
    )

    result = db.execute(query).all()
    return result

# def get_instrument_type(db: Session, rank_query: schemas.RankQuery):
#      query = (
#         select(RankEntry.instrumentID).where(
#             and_(
#                 RankEntry.instrumentID == rank_query.instrumentID,
#                 RankEntry.date == rank_query.date,
#                 RankEntry.exchange == rank_query.exchange,
#             )
#         )
#         .order_by(RankEntry.rank)
#     )
