import re
import datetime, time

from rankapp.database import Session, engine, mapper_registry
from rankapp.models import RankEntry
from rankapp.schemas import VolumeType

from sqlalchemy import select, and_, or_, func

from collections import defaultdict

db = Session()

with engine.begin() as connection:
    mapper_registry.metadata.create_all(connection)

datequery = (select(RankEntry.date).distinct()).where(
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short,
            )
        )
date_results= db.execute(datequery).all()
date_list = [date for (date, ) in date_results]


instrumentquery = (select(RankEntry.instrumentID).distinct()).where(
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short,
            )
        )
instrument_results= db.execute(instrumentquery).all()
instrument_list = [id for (id, ) in instrument_results]

type_list = [VolumeType.long, VolumeType.short]

for date in date_list:
    for instrumentID in instrument_list:
        for volumeType in type_list:
            query = (
                select(
                    RankEntry.companyname,
                    RankEntry.volume,
                    RankEntry.volumetype,
                )
                .where(
                    RankEntry.date == date,
                    RankEntry.instrumentID == instrumentID,
                    RankEntry.volumetype == volumeType,
                    or_(
                        RankEntry.volumetype == VolumeType.long,
                        RankEntry.volumetype == VolumeType.short,
                    )
                )
            )

            results= db.execute(query).all()

            long_dict, short_dict = defaultdict(lambda: 0), defaultdict(lambda: 0)
            res_dict = {}
            long_names, short_names = [], []

            for (name, volume, type, ) in results:
                if type == VolumeType.long:
                    long_dict[name] = volume
                    long_names.append(name)
                elif type == VolumeType.short:
                    short_dict[name] = volume
                    short_names.append(name)
            
    sums = {}
    sums['long'], sums['short'] = 0, 0
    
    for name in long_names:
        res_dict[name] = long_dict[name] - short_dict[name]
        sums['long'] += res_dict[name]
    for name in short_names:
        if name not in res_dict.keys():
            res_dict[name] = long_dict[name] - short_dict[name]
        sums['short'] += res_dict[name]
    

db.close()