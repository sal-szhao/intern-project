import re
import datetime, time
from sqlalchemy import select, and_, or_, func
from collections import defaultdict
from rankapp.database import Session, engine, mapper_registry
from rankapp.models import RankEntry, NetPosition


with engine.begin() as connection:
    mapper_registry.metadata.create_all(connection)

db = Session()

# Get all the available dates.
date_query = (select(RankEntry.date).distinct())
date_results= db.execute(date_query).all()
date_list = [date for (date, ) in date_results]

contractID_query = (select(RankEntry.contractID).distinct())
contractID_results= db.execute(contractID_query).all()
contractID_list = [id for (id, ) in contractID_results]

for date in date_list:
    insert_list = []

    for contractID in contractID_list:
        res_dict = defaultdict(lambda: 0)

        # Calculate net positions.
        for volType in ['b', 's']:
            query = (
                select(
                    RankEntry.company,
                    RankEntry.vol,
                )
                .where(
                    RankEntry.date == date,
                    RankEntry.contractID == contractID,
                    RankEntry.volType == volType,
                )
            )

            results= db.execute(query).all()

            if volType == 'b':
                for (name, volume, ) in results:
                    res_dict[name] += volume
            elif volType == 's':
                for (name, volume, ) in results:
                    res_dict[name] -= volume

        # Store in the table NetPosition.
        query = (
            select(
                RankEntry.id,
                RankEntry.company,
            )
            .where(
                RankEntry.date == date,
                RankEntry.contractID == contractID,
                RankEntry.volType != "v",
            )
        )

        results = db.execute(query).all()

        for (id, company, ) in results:
            net2insert = NetPosition(
                net = res_dict[company],
                rank_id = id,
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