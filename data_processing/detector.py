import pandas as pd
import numpy as np
import utils.config_loader as config_loader
import data_getter
from models.models_set import ModelsSet
import utils.kmeans as kmeans
from typing import Dict, List


def _detect1_batch(ms: ModelsSet, 
    itemIds: list[int], lambda1_threshold: float
) -> list[int]:
    
    history_df = ms.history.get_data(itemIds)
    if history_df.empty:
        return []
    
   # stats df
    means = history_df.groupby('itemid')['value'].mean().reset_index()
    means.columns = ['itemid', 'mean']

    # get stats
    t_stats = ms.trends_stats.read_stats(itemIds)[['itemid', 'mean', 'std']]

    # merge stats
    h_stats_df = pd.merge(means, t_stats, on='itemid', how='left', suffixes=('_h', '_t'))

    # filter h_stats_df where mean_h > mean_t + lambda1_threshold * std_t | mean_h < mean_t - lambda1_threshold * std_t
    h_stats_df = h_stats_df[(h_stats_df['mean_h'] > h_stats_df['mean_t'] + lambda1_threshold * h_stats_df['std']) | (h_stats_df['mean_h'] < h_stats_df['mean_t'] - lambda1_threshold * h_stats_df['std'])]

    # get itemIds
    itemIds = h_stats_df['itemid'].tolist()

    return itemIds


def _filter_df(stats_df: pd.DataFrame, df: pd.DataFrame, lambda_threshold: float) -> pd.DataFrame:
    # Filter the dataframe using vectorized operations for better performance
    df = df.merge(stats_df, on='itemid', how='left', suffixes=('', '_stats'))
    filtered_df = df[(df['value'] > df['mean'] + lambda_threshold * df['std']) | 
                     (df['value'] < df['mean'] - lambda_threshold * df['std'])]
    means = filtered_df.groupby('itemid')['value'].mean().reset_index()
    stds = filtered_df.groupby('itemid')['value'].std().reset_index()
    itemIds = means['itemid'].tolist()
    return pd.DataFrame({'itemid': itemIds, 'mean': means['value'], 'std': stds['value']})
    
def _filter_df2(stats_df: pd.DataFrame, df: pd.DataFrame, lambda_threshold: float) -> list[int]:
    # Filter the dataframe using vectorized operations for better performance
    df = df.merge(stats_df, on='itemid', how='left', suffixes=('', '_stats'))
    filtered_df = df[(df['value'] > df['mean'] + lambda_threshold * df['std']) | 
                     (df['value'] < df['mean'] - lambda_threshold * df['std'])]
    
    return filtered_df['itemid'].unique().tolist()
    


def _detect2_batch(
        dg, ms: ModelsSet, itemIds: list[int], 
        t_startep: int, startep2: int, endep: int,
        lambda1_threshold: float,
        lambda2_threshold: float,
        lambda3_threshold: float
    ) -> list[int]:
    # get trends data
    trends_df = dg.get_trends_data(startep=t_startep, endep=endep, itemIds=itemIds)
    if trends_df.empty:
        return []
    
    # get trends stats
    trends_stats_df = ms.trends_stats.read_stats(itemIds)
    if trends_stats_df.empty:
        return []
    
    # filter trends_df where value > mean + lambda1_threshold * std | value < mean - lambda1_threshold * std
    trends_stats_df = _filter_df(trends_stats_df.set_index('itemid'), trends_df, lambda1_threshold)

    # get history data
    history_df1 = ms.history.get_data(itemIds)
    if history_df1.empty:
        return []
    
    # filter history_df1 where value > mean + lambda2_threshold * std | value < mean - lambda2_threshold * std
    itemIds = _filter_df2(trends_stats_df.set_index('itemid'), history_df1, lambda2_threshold)

    # get history starting with startep2, and exclude itemIds 
    history_df2 = history_df1[history_df1['clock'] >= startep2 & ~history_df1['itemid'].isin(itemIds)]
    if history_df2.empty:
        return itemIds
    
    # filter history_df2 where value > mean + lambda3_threshold * std | value < mean - lambda3_threshold * std
    itemIds.extend(_filter_df2(trends_stats_df.set_index('itemid'), history_df2, lambda3_threshold))
    
    return list(set(itemIds))

def _classify_anomalies(ms: ModelsSet, itemIds: list[int], 
                        k: int, threshold: float, 
                        max_iterations: int, n_rounds: int) -> Dict[int, List[int]]:
    # get history data
    history_df = ms.history.get_data(itemIds)
    if history_df.empty:
        return []
    
    # normalize history data so that max=1 and min=0
    history_df['value'] = history_df.groupby('itemid')['value'].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

    # fill na with 0
    history_df['value'] = history_df['value'].fillna(0)

    # convert df to charts: Dict[int, pd.Series]
    charts = {}
    for itemId in itemIds:
        charts[itemId] = history_df[history_df['itemid'] == itemId]['value'].reset_index(drop=True)

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
           itemIds: list[int] = [],
           group_names: list[str] = [],  
           k=10, threshold=0.1, max_iterations=100, n_rounds=10) -> Dict:
    batch_size = config_loader.conf["batch_size"]
    dg = data_getter.get_data_getter(data_source)
    ms = ModelsSet(data_source["name"])
    anomaly_itemIds = []
    
    for i in range(0, len(itemIds), batch_size):
        batch_itemIds = itemIds[i:i+batch_size]
        # first detection
        batch_anomaly_itemIds = _detect1_batch(ms, batch_itemIds, lambda1_threshold)
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
                                               lambda1_threshold, lambda2_threshold, lambda3_threshold)
        if len(batch_anomaly_itemIds) == 0:
            continue
        anomaly_itemIds2.extend(batch_anomaly_itemIds)

    merged_itemIds = list(set(anomaly_itemIds + anomaly_itemIds2))
    host_itemIds = dg.get_item_host_dict(merged_itemIds)

    if len(merged_itemIds) < 2:
        return {}, anomaly_itemIds, anomaly_itemIds2

    if len(merged_itemIds) < k:
        k = 2

    # classify merged_itemIds by kmeans
    clusters = _classify_anomalies(ms, merged_itemIds, 
                                   k=k, threshold=threshold, max_iterations=max_iterations, n_rounds=n_rounds)
    
    clusters_info = {}
    for clusterId, itemIds in clusters.items():
        if clusterId not in clusters_info.keys():
            clusters_info[clusterId] = {'itemIds': itemIds, 'hostIds': []}
        for itemId in itemIds:
            hostId = host_itemIds[itemId]
            if hostId not in clusters_info[clusterId]['hostIds']:
                clusters_info[clusterId]['hostIds'].append(hostId)
            
    groups_info = dg.classify_by_groups(merged_itemIds, group_names)

    result = {
        'clusters': clusters_info,
        'groups': groups_info,
        'anomaly_itemIds': anomaly_itemIds,
        'anomaly_itemIds2': anomaly_itemIds2
    }

    return result

    