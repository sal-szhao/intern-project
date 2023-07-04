import re
import datetime, time

from rankapp.database import Session, engine, mapper_registry
from rankapp.models import RankEntry, NetPosition
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
    insert_list = []

    for instrumentID in instrument_list:
        long_dict, short_dict = defaultdict(lambda: 0), defaultdict(lambda: 0)
        res_dict = {}
        long_names, short_names = [], []

        # Calculate net positions.
        for volumeType in type_list:
            query = (
                select(
                    RankEntry.companyname,
                    RankEntry.volume,
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

            if volumeType == VolumeType.long:
                for (name, volume, ) in results:
                    long_dict[name] = volume
                    long_names.append(name)
            else:
                for (name, volume, ) in results:
                    short_dict[name] = volume
                    short_names.append(name)


        # Store in the table NetPosition.
        for name in long_names:
            res_dict[name] = long_dict[name] - short_dict[name]
        for name in short_names:
            if name not in res_dict.keys():
                res_dict[name] = long_dict[name] - short_dict[name]

        for name in res_dict.keys():
            query = (
                select(
                    RankEntry.id,
                )
                .where(
                    RankEntry.date == date,
                    RankEntry.instrumentID == instrumentID,
                    RankEntry.companyname == name,
                    or_(
                        RankEntry.volumetype == VolumeType.long,
                        RankEntry.volumetype == VolumeType.short,
                    )
                )
            )

            results = db.execute(query).all()

            for (id, ) in results:
                net2insert = NetPosition(
                    net_pos = res_dict[name],
                    rank_entry_id = id
                )
                insert_list.append(net2insert)
    

    db.add_all(insert_list)

    # # Testing.
    # query = (
    #     select(
    #         RankEntry.date,
    #         RankEntry.instrumentID,
    #         RankEntry.companyname,
    #         RankEntry.volumetype,
    #         NetPosition.net_pos
    #     )
    #     .where(
    #         RankEntry.date == date,
    #         RankEntry.instrumentID == instrument_list[0],
    #         or_(
    #             RankEntry.volumetype == VolumeType.long,
    #             RankEntry.volumetype == VolumeType.short,
    #         )
    #     )
    #     .join(NetPosition, NetPosition.rank_entry_id == RankEntry.id)
    # )

    # results = db.execute(query).all()

    # for (date, iid, name, type, net, ) in results:
    #    print(date, iid, name, type, net)
            
db.commit()
db.close()