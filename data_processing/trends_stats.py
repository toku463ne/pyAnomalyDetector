import pandas as pd
import numpy as np
import utils.config_loader as config_loader
import data_getter
from models.models_set import ModelsSet



def _update_trends_stats_batch(dg, 
                               ms: ModelsSet, itemIds: list[int], 
                               startep: int, diff_startep: int, endep: int, oldstartep: int):
    if diff_startep == 0:
        raise ValueError("diff_startep must be given")
    trends = dg.get_trends_data(startep=diff_startep, endep=endep, itemIds=itemIds)
    # calculate sum, sqr_sum, count
    new_stats = trends.groupby('itemid').agg(
        sum=('value', 'sum'),
        sqr_sum=('value', lambda x: np.sum(np.square(x))),
        cnt=('value', 'count')
    ).reset_index()

    if len(new_stats) == 0:
        return
    
    
    # get stats from trends_stats
    stats = ms.trends_stats.read_stats(itemIds)

    # merge new stats to stats
    stats = pd.merge(stats, new_stats, on='itemid', how='outer', suffixes=('', '_new'))

    # fillna
    stats = stats.fillna(0)

    # add new stats to stats
    if len(new_stats) > 0:
        stats['sum'] = stats['sum'] + stats['sum_new']
        stats['sqr_sum'] = stats['sqr_sum'] + stats['sqr_sum_new']
        stats['cnt'] = stats['cnt'] + stats['cnt_new']


    # get old trends
    if oldstartep > 0:
        old_trends = dg.get_trends_data(itemIds=itemIds, startep=oldstartep, endep=startep)
        if len(old_trends) > 0:
            old_stats = old_trends.groupby('itemid').agg(
                sum=('value', 'sum'),
                sqr_sum=('value', lambda x: np.sum(np.square(x))),
                cnt=('value', 'count')
            ).reset_index()

            # subtract old stats from stats
            if len(old_stats) > 0:
                stats = pd.merge(stats, old_stats, on='itemid', how='outer', suffixes=('', '_old'))
                stats = stats.fillna(0)
                stats['sum'] = stats['sum'] - stats['sum_old']
                stats['sqr_sum'] = stats['sqr_sum'] - stats['sqr_sum_old']
                stats['cnt'] = stats['cnt'] - stats['cnt_old']

    
    # calculate mean and std
    stats['mean'] = stats['sum'] / stats['cnt']
    stats['std'] = np.sqrt(stats['sqr_sum'] / stats['cnt'] - np.square(stats['mean']))

    ## calculate over2std_cnt which is the number of absolute values of data points that are over 2 std from the mean
    #stats['over2std_cnt'] = 0
    #for itemId in itemIds:
    #    if itemId in stats['itemid'].values:
    #        mean = stats[stats['itemid'] == itemId]['mean'].values[0]
    #        std = stats[stats['itemid'] == itemId]['std'].values[0]
    #        over2std_cnt = len(trends[(trends['itemid'] == itemId) & (np.abs(trends['value'] - mean) > 2 * std)])
    #        stats.loc[stats['itemid'] == itemId, 'over2std_cnt'] = over2std_cnt
    

    # upsert stats
    for _, row in stats.iterrows():
        ms.trends_stats.upsert_stats(
            row['itemid'], row['sum'], row['sqr_sum'], row['cnt'], 
            row['mean'], row['std']
        )


def update_trends_stats(data_source, 
                    startep: int, diff_startep: int, endep: int, oldstartep: int,
                    item_names: list[str] = [], 
                    host_names: list[str] = [], 
                    group_names: list[str] = [],
                    initialize=False):
    batch_size = config_loader.conf["batch_size"]
    dg = data_getter.get_data_getter(data_source)
    itemIds = dg.get_itemIds(item_names=item_names, host_names=host_names, group_names=group_names)
    ms = ModelsSet(data_source["name"])

    if initialize:
        ms.initialize()
    
    for i in range(0, len(itemIds), batch_size):
        batch_itemIds = itemIds[i:i+batch_size]
        _update_trends_stats_batch(dg, ms, batch_itemIds, startep, diff_startep, endep, oldstartep)

