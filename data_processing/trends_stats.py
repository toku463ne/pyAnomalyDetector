import pandas as pd
from typing import List
import numpy as np
import utils.config_loader as config_loader
import data_getter
from models.models_set import ModelsSet

def square_sum(x):
    return np.sum(np.square(x))

def _update_trends_stats_batch(dg, 
                               ms: ModelsSet, itemIds: List[int], 
                               startep: int, diff_startep: int, endep: int, oldstartep: int):
    if diff_startep == 0:
        raise ValueError("diff_startep must be given")
    trends = dg.get_trends_data(startep=diff_startep, endep=endep, itemIds=itemIds)
    # calculate sum, sqr_sum, count
    new_stats = trends.groupby('itemid').agg(
        sum=('value', 'sum'),
        sqr_sum=('value', square_sum),
        cnt=('value', 'count')
    ).reset_index()

    if len(new_stats) == 0:
        return
    
    
    # get stats from trends_stats
    stats = ms.trends_stats.read_stats(itemIds)

    if len(stats) > 0:
        # merge new stats to stats
        stats = pd.merge(stats, new_stats, on='itemid', how='inner', suffixes=('', '_new'))

        # add new stats to stats
        if len(new_stats) > 0:
            stats['sum'] = stats['sum'] + stats['sum_new']
            stats['sqr_sum'] = stats['sqr_sum'] + stats['sqr_sum_new']
            stats['cnt'] = stats['cnt'] + stats['cnt_new']

        stats = stats[['itemid', 'sum', 'sqr_sum', 'cnt']]
    else:
        stats = new_stats

    # fillna
    stats = stats.fillna(0)


    # get old trends
    if oldstartep > 0:
        old_trends = dg.get_trends_data(itemIds=itemIds, startep=oldstartep, endep=startep)
        if len(old_trends) > 0:
            old_stats = old_trends.groupby('itemid').agg(
                sum=('value', 'sum'),
                sqr_sum=('value', square_sum),
                cnt=('value', 'count')
            ).reset_index()

            # subtract old stats from stats
            if len(old_stats) > 0:
                stats = pd.merge(stats, old_stats, on='itemid', how='outer', suffixes=('', '_old'))
                stats = stats.fillna(0)
                stats['sum'] = stats['sum'] - stats['sum_old']
                stats['sqr_sum'] = stats['sqr_sum'] - stats['sqr_sum_old']
                stats['cnt'] = stats['cnt'] - stats['cnt_old']
                stats = stats[['itemid', 'sum', 'sqr_sum', 'cnt']]

    
    # calculate mean and std
    stats = stats.fillna(0)
    stats = stats[stats['cnt'] > 0]
    stats['mean'] = stats['sum'] / stats['cnt']
    stats['std'] = np.sqrt(abs(stats['sqr_sum'] / stats['cnt'] - np.square(stats['mean'])))
    # Replace inf values in the entire DataFrame with 0
    stats.replace([np.inf, -np.inf], 0, inplace=True)


    # fillna
    stats = stats.fillna(0)

    ## calculate over2std_cnt which is the number of absolute values of data points that are over 2 std from the mean
    #stats['over2std_cnt'] = 0
    #for itemId in itemIds:
    #    if itemId in stats['itemid'].values:
    #        mean = stats[stats['itemid'] == itemId]['mean'].values[0]
    #        std = stats[stats['itemid'] == itemId]['std'].values[0]
    #        over2std_cnt = len(trends[(trends['itemid'] == itemId) & (np.abs(trends['value'] - mean) > 2 * std)])
    #        stats.loc[stats['itemid'] == itemId, 'over2std_cnt'] = over2std_cnt
    
    #names = dg.get_item_names(itemIds)

    # upsert stats
    for _, row in stats.iterrows():
        ms.trends_stats.upsert_stats(
            row['itemid'], row['sum'], row['sqr_sum'], row['cnt'], 
            row['mean'], row['std']
        )


def update_trends_stats(data_source, 
                    startep: int, diff_startep: int, endep: int, oldstartep: int,
                    item_names: List[str] = None, 
                    host_names: List[str] = None, 
                    group_names: List[str] = None,
                    itemIds: List[int] = None,
                    initialize=False, max_itemIds=0):
    if item_names is None:
        item_names = []
    if host_names is None:
        host_names = []
    if group_names is None:
        group_names = []
    if itemIds is None:
        itemIds = []
    batch_size = config_loader.conf["batch_size"]
    dg = data_getter.get_data_getter(data_source)
    itemIds = dg.get_itemIds(item_names=item_names, 
                             host_names=host_names, group_names=group_names, 
                             itemIds=itemIds,
                             max_itemIds=max_itemIds)
    ms = ModelsSet(data_source["name"])

    if initialize:
        ms.initialize()

    existing, nonexisting = ms.trends_stats.separate_existing_itemIds(itemIds)
    
    # import diff for existing itemIds
    for i in range(0, len(existing), batch_size):
        batch_itemIds = existing[i:i+batch_size]
        _update_trends_stats_batch(dg, ms, batch_itemIds, startep, diff_startep, endep, oldstartep)

    # import full for non existing itemIds
    for i in range(0, len(nonexisting), batch_size):
        batch_itemIds = nonexisting[i:i+batch_size]
        _update_trends_stats_batch(dg, ms, batch_itemIds, startep, startep, endep, oldstartep)
