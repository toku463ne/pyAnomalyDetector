import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

import utils.config_loader as config_loader
import data_getter
from models.models_set import ModelsSet
import data_processing.history as history
import utils.kmeans as kmeans
import utils.normalizer as normalizer


def _detect_diff_anomalies(itemIds: List[int], 
                           trends_df: pd.DataFrame, recent_stats: pd.DataFrame, 
                           lamnda_threshold: float, 
                           ignore_diff_rate: float,
                           is_up=True) -> List[int]:
    
    if is_up:
        trends_df2 = trends_df[['itemid', 'clock', 'value_max']]
        trends_df2.columns = ['itemid', 'clock', 'value']
    else:
        trends_df2 = trends_df[['itemid', 'clock', 'value_min']]
        trends_df2.columns = ['itemid', 'clock', 'value']


    # create a dataframe with adjacent value_xx peaks from trends_df
    trends_diff = pd.DataFrame(columns=['itemid', 'clock', 'value', 'diff'])
    for itemId in itemIds:
        df = trends_df2[trends_df2['itemid'] == itemId]
        df['diff'] = df['value'].diff().fillna(0)
        df = df[df['diff'] != 0]
        trends_diff = pd.concat([trends_diff, df])

    # calculate trends_diff mean and std
    trends_diff_stats = trends_diff.groupby('itemid')['diff'].agg(['mean', 'std']).reset_index()
    #recent_stats = recent_diff.groupby('itemid')['diff'].agg(['min', 'max']).reset_index()
    
    # merge with hist_stats by itemid
    stats_df = pd.merge(recent_stats, trends_diff_stats, on='itemid', how='inner')
    stats_df = stats_df[stats_df['std'] > 0]

    if is_up:
        # filter by lambda_threshold
        stats_df = stats_df[stats_df['max'] > stats_df['mean'] + lamnda_threshold * stats_df['std']]
        # filter by ignore_diff_rate
        stats_df = stats_df[abs(stats_df['max'] - stats_df['mean'])/stats_df['mean'] > ignore_diff_rate]
    else:
        # filter by lambda_threshold
        stats_df = stats_df[stats_df['min'] < stats_df['mean'] - lamnda_threshold * stats_df['std']]
        # filter by ignore_diff_rate
        stats_df = stats_df[abs(stats_df['min'] - stats_df['mean'])/stats_df['mean'] > ignore_diff_rate]

    # get itemIds
    itemIds = stats_df['itemid'].tolist()
    return itemIds

    


def _detect1_batch(ms: ModelsSet, 
    itemIds: List[int], lambda1_threshold: float, ignore_diff_rate: float, trends_min_count: int
) -> List[int]:
    
    means = ms.history_stats.read_stats(itemIds)[['itemid', 'mean']]

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



def _filter_by_anomaly_cnt(stats_df: pd.DataFrame, 
    hist_count: int,
    df: pd.DataFrame, 
    lamdba_threshold: float,
    anomaly_valid_count_rate: float, is_up=True) -> List[int]:
    # get history_df1 count
    #df_counts = df.groupby('itemid')['value'].count().reset_index()
    #df_counts.columns = ['itemid', 'h_total_cnt']

    # filter anomalies in history_df1
    df = _filter_anomalies(df, stats_df, lamdba_threshold, is_up=is_up)

    if df.empty:
        return []

    # get anomaly counts
    df_anom_counts = df.groupby('itemid')['value'].count().reset_index()
    df_anom_counts.columns = ['itemid', 'anom_cnt']
    
    # merge counts
    #df_anom_counts = pd.merge(df_counts, df_anom_counts, on='itemid', how='left')
    df_anom_counts = df_anom_counts.fillna(0)

    # filter by anomaly up count
    itemIds = df_anom_counts[(df_anom_counts['anom_cnt'] / hist_count > anomaly_valid_count_rate)]['itemid'].tolist()

    # make unique
    itemIds = list(set(itemIds))
    return itemIds



def _filter_anomalies(df: pd.DataFrame, 
                      stats_df: pd.DataFrame,
                      lambda_threshold: float,
                      is_up=True) -> pd.DataFrame:
    dtypes = np.dtype([('itemid', 'int64'), ('clock', 'int64'), ('value', 'float64')])
    new_df = pd.DataFrame(np.empty(0, dtype=dtypes))
    #new_df = pd.DataFrame(columns=['itemid', 'clock', 'value'])
    for row in stats_df.itertuples():
        itemId = row.itemid
        std = row.std
        mean = row.mean
        if is_up:
            df_part = df[(df['itemid'] == itemId) & (df['value'] > mean + lambda_threshold * std)]
        else:
            df_part = df[(df['itemid'] == itemId) & (df['value'] < mean - lambda_threshold * std)]
        if df_part.empty:
            continue
        new_df = pd.concat([new_df, df_part])

    return new_df

def _calc_local_peak(itemIds: List[int], df: pd.DataFrame, window: int, is_up=True) -> pd.DataFrame:
    new_df = []
    for itemId in itemIds:
        df_item = df[df['itemid'] == itemId]
        if df_item.empty:
            continue
        epoch = df_item.iloc[-1]['clock']
        startep = df_item.iloc[0]['clock']
        window_half = window // 2
        peak_val = -float('inf') if is_up else float('inf')
        peak_epoch = 0
        while epoch >= startep:
            val = df_item[(df_item['clock'] <= epoch) & (df_item['clock'] > epoch - window)]['value'].mean()
            if is_up:
                peak_val = max(peak_val, val)
                peak_epoch = epoch
            else:
                peak_val = min(peak_val, val)
                peak_epoch = epoch
            epoch -= window_half
        new_df.append({'itemid': itemId, 'local_peak': peak_val, 'peak_clock': peak_epoch})
        
    return pd.DataFrame(new_df)


def _get_trends_stats(trends_df: pd.DataFrame, cnts_df: pd.DataFrame) -> Tuple[pd.DataFrame]:
    means = trends_df.groupby('itemid')['value'].mean().reset_index()
    means.columns = ['itemid', 'mean']
    stds = trends_df.groupby('itemid')['value'].std().reset_index()
    stds.columns = ['itemid', 'std']
    trends_stats_df = pd.merge(means, stds, on='itemid', how='inner')
    trends_stats_df = pd.merge(trends_stats_df, cnts_df, on='itemid', how='inner')
    return trends_stats_df

# df_counts, lambda2_threshold, density_window
def _filter_anomal_history(itemIds: List[int], 
                           df: pd.DataFrame, 
                           trends_peak: pd.DataFrame,
                           hist_count: int,
                           trends_stas_df: pd.DataFrame,
                           lambda_threshold: float,
                           density_window: int,
                           anomaly_valid_count_rate,
                           is_up=True) -> List[int]:
    
    # filter by anomaly count
    itemIds = _filter_by_anomaly_cnt(trends_stas_df, hist_count, df, lambda_threshold, anomaly_valid_count_rate, is_up=is_up)
    if len(itemIds) == 0:
        return []
    local_peaks = _calc_local_peak(itemIds, trends_peak, density_window, is_up=is_up)
    
    means = df.groupby('itemid')['value'].mean().reset_index()
    local_peaks = pd.merge(local_peaks, means, on='itemid', how='inner')

    if is_up:
        itemIds = local_peaks[(local_peaks['local_peak'] < local_peaks['value'])]['itemid'].tolist()  
    else:
        itemIds = local_peaks[(local_peaks['local_peak'] > local_peaks['value'])]['itemid'].tolist()

    itemIds = list(set(itemIds))
    return itemIds


def _detect2_batch(history_df: pd.DataFrame, trends_df: pd.DataFrame,
        itemIds: List[int],
        lambda2_threshold: float,
        ignore_diff_rate: float,):
    
    # group by itemid and get min, max and the first value
    r_stats = history_df.groupby('itemid')['value'].agg(['min', 'max', 'first']).reset_index()
    r_stats["min_diff"] = r_stats["min"] - r_stats["first"]
    r_stats["max_diff"] = r_stats["max"] - r_stats["first"]
    r_stats = r_stats[['itemid', 'min_diff', 'max_diff']]
    r_stats.columns = ['itemid', 'min', 'max']


    itemIds_up = _detect_diff_anomalies(itemIds, trends_df, r_stats, lambda2_threshold, ignore_diff_rate, is_up=True)
    itemIds_dw = _detect_diff_anomalies(itemIds, trends_df, r_stats, lambda2_threshold, ignore_diff_rate, is_up=False)

    itemIds = itemIds_up + itemIds_dw
    itemIds = list(set(itemIds))
    return itemIds


def _detect3_batch(
        ms: ModelsSet, 
        trends_df: pd.DataFrame,
        base_clocks: List[int],
        itemIds: List[int], 
        startep2: int, 
        lambda3_threshold: float,
        lambda4_threshold: float,
        anomaly_valid_count_rate: float) -> List[int]:
    
    
    cnts = trends_df.groupby('itemid')['value_avg'].count().reset_index()
    cnts.columns = ['itemid', 'cnt']
    itemIds = cnts[cnts['cnt'] > 0]['itemid'].tolist()

    trends_max = trends_df[['itemid', 'clock', 'value_max']]
    trends_max.columns = ['itemid', 'clock', 'value']
    trends_min = trends_df[['itemid', 'clock', 'value_min']]
    trends_min.columns = ['itemid', 'clock', 'value']

    
    # get history data
    history_df1 = ms.history.get_data(itemIds)
    if history_df1.empty:
        return []
    
    trends_stats_df_up = _get_trends_stats(trends_max, cnts)
    trends_stats_df_dw = _get_trends_stats(trends_min, cnts)

    
    #df_counts = history_df1.groupby('itemid')['value'].count().reset_index()
    #df_counts.columns = ['itemid', 'cnt']
    hist_count = len(base_clocks)

    density_window = config_loader.conf['history_interval'] * config_loader.conf['history_retention']

    itemIds_up = _filter_anomal_history(itemIds, history_df1, trends_max, hist_count, trends_stats_df_up, 
                                        lambda3_threshold, density_window, anomaly_valid_count_rate, is_up=True)
    itemIds_dw = _filter_anomal_history(itemIds, history_df1, trends_min, hist_count, trends_stats_df_dw, 
                                        lambda3_threshold, density_window, anomaly_valid_count_rate, is_up=False)

    itemIds1 = itemIds_up + itemIds_dw
    
    # get history starting with startep2, and exclude itemIds 
    history_df2 = history_df1[~history_df1['itemid'].isin(itemIds1)]
    history_df2 = history_df2[history_df2['clock'] >= startep2]
    if history_df2.empty:
        return itemIds
    
    # base clocks >= startep2
    base_clocks2 = [clock for clock in base_clocks if clock >= startep2]
    hist_count = len(base_clocks2)
    
    #df_counts = history_df2.groupby('itemid')['value'].count().reset_index()
    #df_counts.columns = ['itemid', 'cnt']

    itemIds_up = _filter_anomal_history(itemIds, history_df2, trends_max, hist_count, trends_stats_df_up, 
                                        lambda4_threshold, density_window, anomaly_valid_count_rate, is_up=True)
    itemIds_dw = _filter_anomal_history(itemIds, history_df2, trends_min, hist_count, trends_stats_df_dw, 
                                        lambda4_threshold, density_window, anomaly_valid_count_rate, is_up=False)

    itemIds2 = itemIds_up + itemIds_dw
    itemIds1.extend(itemIds2)
    itemIds = list(set(itemIds1))

    return itemIds

def _update_history_batch(dg, ms: ModelsSet, itemIds: List[int], 
            base_clocks: List[int], oldep: int):
    # update history data
    hist_df = dg.get_history_data(startep=base_clocks[0], endep=base_clocks[-1], itemIds=itemIds)
    if hist_df.empty:
        return 

    for itemId in itemIds:
        item_hist_df = hist_df[hist_df['itemid'] == itemId]
        if item_hist_df.empty:
            continue

        # sort by clock
        item_hist_df = item_hist_df.sort_values(by='clock')

        values = normalizer.fit_to_base_clocks(
            base_clocks, 
            item_hist_df['clock'].tolist(), 
            item_hist_df['value'].tolist())
        ms.history.upsert([itemId]*len(base_clocks), base_clocks, values)

    if oldep > 0:
        # delete old history data
        ms.history.remove_old_data(oldep)



def _update_history(data_source, itemIds: List[int], base_clocks: List[int], oldep: int):
    batch_size = config_loader.conf["batch_size"]
    dg = data_getter.get_data_getter(data_source)
    ms = ModelsSet(data_source["name"])
    #itemIds = dg.get_itemIds(itemIds=itemIds)

    for i in range(0, len(itemIds), batch_size):
        batch_itemIds = itemIds[i:i+batch_size]
        # update history
        _update_history_batch(dg, ms, batch_itemIds, base_clocks, oldep)
        


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
    return clusters

    

def detect(data_source, 
           t_startep: int, startep1: int, startep2: int, endep: int, anomaly_keep_secs: int,
           lambda1_threshold: float, lambda2_threshold: float, lambda3_threshold: float, lambda4_threshold: float, 
           trends_min_count: int,
           base_clocks: List[int],
           itemIds: List[int] = [],
           group_names: List[str] = [],  
           k=10, threshold=0.1, max_iterations=100, n_rounds=10,
           anomaly_valid_count_rate=0.8,
           skip_history_update=False) -> pd.DataFrame:
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

    if len(anomaly_itemIds) == 0:
        return None
    
    ## import history data using batch
    #for i in range(0, len(anomaly_itemIds), batch_size):
    #    batch_itemIds = anomaly_itemIds[i:i+batch_size]
    #    history_df = dg.get_history_data(base_clocks[0], base_clocks[-1], batch_itemIds)
    #    if history_df.empty:
    #        continue
    #    ms.history.import_history(history_df, base_clocks)
    
    if not skip_history_update:
        _update_history(data_source, anomaly_itemIds, base_clocks, startep1)
        ms.history.remove_itemIds_not_in(anomaly_itemIds)

    
    anomaly_itemIds2 = []
    for i in range(0, len(anomaly_itemIds), batch_size):
        # get trends data
        trends_df = dg.get_trends_full_data(startep=t_startep, endep=endep, itemIds=itemIds)
        if trends_df.empty:
            return []


        # second detection
        batch_itemIds = anomaly_itemIds[i:i+batch_size]
        history_df = ms.history.get_data(batch_itemIds)
        if history_df.empty:
            continue

            
        batch_anomaly_itemIds = _detect2_batch(history_df, trends_df, batch_itemIds, lambda2_threshold, ignore_diff_rate)
        if len(batch_anomaly_itemIds) == 0:
            continue
        

        # third detection
        batch_anomaly_itemIds = _detect3_batch(ms, trends_df, base_clocks, batch_anomaly_itemIds, startep2, 
                                               lambda3_threshold, lambda4_threshold, anomaly_valid_count_rate)
        if len(batch_anomaly_itemIds) == 0:
            continue
        anomaly_itemIds2.extend(batch_anomaly_itemIds)



    host_itemIds = dg.get_item_host_dict(anomaly_itemIds2)

    clusters = {}
    if len(anomaly_itemIds2) > 2:
        if len(anomaly_itemIds2) < k:
            k = 2

        # classify anomaly_itemIds3 by kmeans
        clusters = _classify_anomalies(ms, anomaly_itemIds2, 
                                    k=k, threshold=threshold, max_iterations=max_iterations, n_rounds=n_rounds)
                
    groups_info = dg.classify_by_groups(anomaly_itemIds2, group_names)

    # results in df with columns: itemId, hostId, host_name, item_name, clusterId, group_name
    target_itemIds = []
    hostIds = []
    host_names = []
    item_names = []
    clusterIds = []
    group_names = []
    item_details = dg.get_item_details(anomaly_itemIds2)
    for group_name, itemIds in groups_info.items():
        for itemId in itemIds:
            target_itemIds.append(itemId)
            hostIds.append(host_itemIds.get(itemId, -1))
            host_names.append(item_details[itemId]['host_name'])
            item_names.append(item_details[itemId]['item_name'])
            group_names.append(group_name)
            clusterIds.append(clusters.get(itemId, -1))
            
    results = pd.DataFrame({'itemid': target_itemIds, 
                            'created': [endep] * len(target_itemIds),
                            'group_name': group_names, 
                            'hostid': hostIds, 
                            'clusterid': clusterIds,
                            'host_name': host_names, 'item_name': item_names})
    
    # remove duplicates
    results = results.drop_duplicates(subset=['itemid', 'group_name', 'created'], keep='first')
    
    ms.anomalies.insert_data(results)
    ms.anomalies.delete_old_entries(endep - anomaly_keep_secs)
    return results

    