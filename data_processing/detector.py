import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

import utils.config_loader as config_loader
import data_getter
from models.models_set import ModelsSet
import utils.kmeans as kmeans
import utils.normalizer as normalizer


def _detect1_batch(ms: ModelsSet, 
    itemIds: List[int], lambda1_threshold: float, ignore_diff_rate: float, trends_min_count: int
) -> List[int]:
    
    history_df = ms.history.get_data(itemIds)
    if history_df.empty:
        return []
    
   # stats df
    means = history_df.groupby('itemid')['value'].mean().reset_index()
    means.columns = ['itemid', 'mean']

    # get stats
    t_stats = ms.trends_stats.read_stats(itemIds)[['itemid', 'mean', 'std', 'cnt']]
    t_stats = t_stats[t_stats['cnt'] > trends_min_count]

    # merge stats
    h_stats_df = pd.merge(means, t_stats, on='itemid', how='inner', suffixes=('_h', '_t'))
    h_stats_df = h_stats_df[h_stats_df['std']>0]

    # filter h_stats_df where mean_h > mean_t + lambda1_threshold * std_t | mean_h < mean_t - lambda1_threshold * std_t
    h_stats_df = h_stats_df[(h_stats_df['mean_h'] > h_stats_df['mean_t'] + lambda1_threshold * h_stats_df['std']) | (h_stats_df['mean_h'] < h_stats_df['mean_t'] - lambda1_threshold * h_stats_df['std'])]

    # ignore small diffs
    h_stats_df = h_stats_df[h_stats_df['mean_t'] > 0 & (abs(h_stats_df['mean_h'] - h_stats_df['mean_t'])/h_stats_df['mean_t'] > ignore_diff_rate)]

    # get itemIds
    itemIds = h_stats_df['itemid'].tolist()

    return itemIds



def _filter_anomalies(stats_df: pd.DataFrame, df: pd.DataFrame, lambda_threshold: float, is_up=True) -> Tuple[pd.DataFrame]:
    df_new = pd.DataFrame(columns=['itemid', 'clock', 'value'])
    if is_up:
        for row in stats_df.itertuples():
            itemId = row.itemid
            df_part = df[(df['itemid'] == itemId) & (df['value'] > row.mean + lambda_threshold * row.std)]
            if df_part.empty:
                continue
            df_new = pd.concat([df_new, df_part])
    else:
        for row in stats_df.itertuples():
            itemId = row.itemid
            df_part = df[(df['itemid'] == itemId) & (df['value'] < row.mean - lambda_threshold * row.std)]
            if df_part.empty:
                continue
            df_new = pd.concat([df_new, df_part])

    cnts = df_new.groupby('itemid')['value'].count().reset_index()
    means = df_new.groupby('itemid')['value'].mean().reset_index()
    stds = df_new.groupby('itemid')['value'].std().reset_index()
    itemIds = means['itemid'].tolist()
    df = pd.DataFrame({'itemid': itemIds, 'mean': means['value'], 'std': stds['value'], 'cnt': cnts['value']})
    df = df[df['std'] > 0]  
    return df

def _filter_by_anomaly_cnt(stats_df_up: pd.DataFrame, stats_df_dw: pd.DataFrame, 
    df: pd.DataFrame, 
    lamdba_threshold: float,
    anomaly_valid_count_rate: float) -> List[int]:
    # get history_df1 count
    df_counts = df.groupby('itemid')['value'].count().reset_index()
    df_counts.columns = ['itemid', 'h_total_cnt']

    # filter anomalies in history_df1
    stats_df_up = _filter_anomalies(stats_df_up, df, lamdba_threshold, is_up=True)
    stats_df_dw = _filter_anomalies(stats_df_dw, df, lamdba_threshold, is_up=False)

    stats_df_up = pd.merge(stats_df_up, df_counts, on='itemid', how='inner')
    stats_df_dw = pd.merge(stats_df_dw, df_counts, on='itemid', how='inner')

    # filter itemIds where cnt >= anomaly_valid_count_rate * h_total_cnt
    stats_df_up = stats_df_up[stats_df_up['cnt'] >= anomaly_valid_count_rate * stats_df_up['h_total_cnt']]
    stats_df_dw = stats_df_dw[stats_df_dw['cnt'] >= anomaly_valid_count_rate * stats_df_dw['h_total_cnt']]

    itemIds = stats_df_up['itemid'].tolist() + stats_df_dw['itemid'].tolist()
    # make unique
    itemIds = list(set(itemIds))
    return itemIds


def _detect2_batch(
        dg, ms: ModelsSet, itemIds: List[int], 
        t_startep: int, startep2: int, endep: int,
        lambda1_threshold: float,
        lambda2_threshold: float,
        lambda3_threshold: float,
        anomaly_valid_count_rate: float = 0.8,
    ) -> List[int]:
    # get trends data
    trends_df = dg.get_trends_data(startep=t_startep, endep=endep, itemIds=itemIds)
    if trends_df.empty:
        return []
    
    # get trends stats
    trends_stats_df = ms.trends_stats.read_stats(itemIds)
    if trends_stats_df.empty:
        return []
    
    # filter anomal trends_df
    trends_stats_df_up = _filter_anomalies(trends_stats_df, trends_df, lambda1_threshold, is_up=True)
    trends_stats_df_dw = _filter_anomalies(trends_stats_df, trends_df, lambda1_threshold, is_up=False)

    # get history data
    history_df1 = ms.history.get_data(itemIds)
    if history_df1.empty:
        return []

    itemIds = _filter_by_anomaly_cnt(trends_stats_df_up, trends_stats_df_dw, 
                                     history_df1, lambda2_threshold, anomaly_valid_count_rate)
    
    # get history starting with startep2, and exclude itemIds 
    history_df2 = history_df1[~history_df1['itemid'].isin(itemIds)]
    history_df2 = history_df2[history_df1['clock'] >= startep2]
    if history_df2.empty:
        return itemIds
    
    itemIds += _filter_by_anomaly_cnt(trends_stats_df_up, trends_stats_df_dw, 
                                      history_df2, lambda3_threshold, anomaly_valid_count_rate)
    
    return list(set(itemIds))

def _classify_anomalies(ms: ModelsSet, itemIds: List[int], 
                        k: int, threshold: float, 
                        max_iterations: int, n_rounds: int) -> Dict[int, List[int]]:
    # get history data
    history_df = ms.history.get_data(itemIds)
    if history_df.empty:
        return []

    base_clocks = list(set(history_df["clock"].tolist()))

    
    # normalize history data so that max=1 and min=0
    history_df['value'] = history_df.groupby('itemid')['value'].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

    # fill na with 0
    history_df['value'] = history_df['value'].fillna(0)

    # convert df to charts: Dict[int, pd.Series]
    charts = {}
    for itemId in itemIds:
        #charts[itemId] = history_df[history_df['itemid'] == itemId]['value'].reset_index(drop=True)
        clocks = history_df[history_df['itemid'] == itemId]['clock'].tolist()
        values = history_df[history_df['itemid'] == itemId]['value'].tolist()
        values = normalizer.fit_to_base_clocks(base_clocks, clocks, values)
        charts[itemId] = pd.Series(data=values)

    # run kmeans
    clusters, _ = kmeans.run_kmeans(charts, k, threshold, max_iterations, n_rounds)

    # convert clusters to dict of list of itemIds
    clusters_dict = {}
    for itemId, clusterId in clusters.items():
        if clusterId not in clusters_dict.keys():
            clusters_dict[clusterId] = []
        clusters_dict[clusterId].append(itemId)

    return clusters_dict

    

def detect(data_source, 
           t_startep: int, startep2: int, endep: int, 
           lambda1_threshold: float, lambda2_threshold: float, lambda3_threshold: float,
           trends_min_count: int,
           itemIds: List[int] = [],
           group_names: List[str] = [],  
           k=10, threshold=0.1, max_iterations=100, n_rounds=10,
           anomaly_valid_count_rate=0.8) -> Dict:
    batch_size = config_loader.conf["batch_size"]
    ignore_diff_rate = config_loader.conf["ignore_diff_rate"]
    dg = data_getter.get_data_getter(data_source)
    ms = ModelsSet(data_source["name"])
    anomaly_itemIds = []
    
    for i in range(0, len(itemIds), batch_size):
        batch_itemIds = itemIds[i:i+batch_size]
        # first detection
        batch_anomaly_itemIds = _detect1_batch(ms, batch_itemIds, lambda1_threshold, 
                                               ignore_diff_rate, trends_min_count)
        if len(batch_anomaly_itemIds) == 0:
            continue
        anomaly_itemIds.extend(batch_anomaly_itemIds)

    # second detection
    anomaly_itemIds2 = []
    
    for i in range(0, len(anomaly_itemIds), batch_size):
        batch_itemIds = anomaly_itemIds[i:i+batch_size]
        history_df = ms.history.get_data(batch_itemIds)
        if history_df.empty:
            continue
        batch_anomaly_itemIds = _detect2_batch(dg, ms, batch_itemIds, t_startep, startep2, endep, 
                                               lambda1_threshold, lambda2_threshold, lambda3_threshold,
                                               anomaly_valid_count_rate)
        if len(batch_anomaly_itemIds) == 0:
            continue
        anomaly_itemIds2.extend(batch_anomaly_itemIds)

    host_itemIds = dg.get_item_host_dict(anomaly_itemIds2)

    if len(anomaly_itemIds2) < 2:
        return {
        'clusters': {},
        'groups': {},
        'anomaly_itemIds': anomaly_itemIds,
        'anomaly_itemIds2': anomaly_itemIds2
    }

    if len(anomaly_itemIds2) < k:
        k = 2


    # classify anomaly_itemIds2 by kmeans
    clusters = _classify_anomalies(ms, anomaly_itemIds2, 
                                   k=k, threshold=threshold, max_iterations=max_iterations, n_rounds=n_rounds)
    
    clusters_info = {}
    for clusterId, itemIds in clusters.items():
        if clusterId not in clusters_info:
            clusters_info[clusterId] = {}
        for itemId in itemIds:
            if itemId not in host_itemIds:
                print(f"itemId {itemId} not in host_itemIds")
                continue
            hostId = host_itemIds[itemId]
            if hostId not in clusters_info[clusterId].keys():
                clusters_info[clusterId][hostId] = []
            clusters_info[clusterId][hostId].append(itemId)


            
    groups_info = dg.classify_by_groups(anomaly_itemIds2, group_names)


    result = {
        'clusters': clusters_info,
        'groups': groups_info,
        'anomaly_itemIds': anomaly_itemIds,
        'anomaly_itemIds2': anomaly_itemIds2
    }

    return result

    