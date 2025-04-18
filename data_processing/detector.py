import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

import utils
import utils.config_loader as config_loader
import data_getter
from models.models_set import ModelsSet
#import utils.kmeans as kmeans
import utils.classifiers as classifiers
import utils.normalizer as normalizer


def log(msg, level=logging.INFO):
    msg = f"[data_processing/detector.py] {msg}"
    logging.log(level, msg)

class Detector:
    def __init__(self, data_source: Dict, trace_mode=False):
        self.data_source = data_source
        self.trace_mode = trace_mode
        self.dg = data_getter.get_data_getter(data_source)
        self.ms = ModelsSet(data_source["name"])
        self.conf = config_loader.conf
        self.lambda1_threshold = self.conf['lambda1_threshold']
        self.lambda2_threshold = self.conf['lambda2_threshold']
        self.lambda3_threshold = self.conf['lambda3_threshold']
        self.lambda4_threshold = self.conf['lambda4_threshold']
        self.anomaly_valid_count_rate = self.conf['anomaly_valid_count_rate']
        self.batch_size = self.conf["batch_size"]
        self.ignore_diff_rate = self.conf["ignore_diff_rate"]
        self.trends_min_count = self.conf["trends_min_count"]
        self.history_interval = self.conf["history_interval"]
        self.history_retention = self.conf["history_retention"]
        self.anomaly_keep_secs = self.conf["anomaly_keep_secs"]
        self.history_recent_retention = self.conf["history_recent_retention"]
        
        self.kconf = self.conf.get("kmeans", {})
        self.k = self.kconf.get("k", 10)
        self.km_threshold = self.kconf.get("threshold", 0.8)
        self.km_threshold2 = self.kconf.get("threshold2", 1.5)
        self.km_detection_period = self.kconf["detection_period"]
        
        dbscan_conf = self.kconf.get("dbscan", {})
        self.dbscan_eps = dbscan_conf.get("eps", 0.5)
        self.dbscan_min_samples = dbscan_conf.get("min_samples", 2)
        self.dbscan_detection_period = dbscan_conf.get("detection_period", 10)
        self.dbscan_sigma = dbscan_conf.get("sigma", 2.0)
        self.dbscan_jaccard_threshold = dbscan_conf.get("jaccard_threshold", 0.5)
        self.dbscan_correlation_threshold = dbscan_conf.get("correlation_threshold", 0.5)

        
        self.max_iterations = self.kconf.get("max_iterations", 10)
        self.n_rounds = self.kconf.get("n_rounds", 10)
        self.item_conds = data_source.get("item_conds", [])
        self.item_diff_conds = data_source.get("item_diff_conds", [])
        self.centroid_dir = self.conf.get('centroid_dir', '')
        if self.centroid_dir != '':
            utils.ensure_dir(self.centroid_dir)

    def _print_trace(self, title: str, df: pd.DataFrame):
        itemIds = df['itemid'].tolist()
        itemIds = list(set(itemIds))
        self._print_item_trace(title, itemIds)

    def _print_item_trace(self, title: str, itemIds: List[int]):
        log(f"{title}: {len(itemIds)}")
        log(itemIds)

    def _detect_diff_anomalies(self, itemIds: List[int], 
                            trends_df: pd.DataFrame, recent_stats: pd.DataFrame, 
                            lamnda_threshold: float,
                            is_up=True) -> List[int]:
        ignore_diff_rate = self.ignore_diff_rate
        if is_up:
            trends_df2 = trends_df[['itemid', 'clock', 'value_max']]
            trends_df2.columns = ['itemid', 'clock', 'value']
        else:
            trends_df2 = trends_df[['itemid', 'clock', 'value_min']]
            trends_df2.columns = ['itemid', 'clock', 'value']


        # create a dataframe with adjacent value_xx peaks from trends_df
        trends_diff = pd.DataFrame(columns=['itemid', 'clock', 'value', 'diff'], dtype=object)
        for itemId in itemIds:
            df = trends_df2[trends_df2['itemid'] == itemId]
            df = df.copy()
            df['diff'] = df['value'].diff().fillna(0)
            df = df[df['diff'] != 0]
            if trends_diff.empty:
                trends_diff = df
            elif not df.empty and len(df) > 0:
                trends_diff = pd.concat([trends_diff, df])

        # calculate trends_diff mean and std
        trends_diff_stats = trends_diff.groupby('itemid')['diff'].agg(['mean', 'std']).reset_index()
        #recent_stats = recent_diff.groupby('itemid')['diff'].agg(['min', 'max']).reset_index()
        
        # merge with hist_stats by itemid
        stats_df = pd.merge(recent_stats, trends_diff_stats, on='itemid', how='inner')
        stats_df = stats_df[stats_df['std'] > 0]

        if is_up:
            stats_df['diff'] = abs(stats_df['max'] - stats_df['mean'])
            # filter by lambda_threshold
            stats_df = stats_df[stats_df['diff'] > lamnda_threshold * stats_df['std']]

            # filter by ignore_diff_rate
            stats_df = stats_df[abs(stats_df['max'] - stats_df['mean'])/stats_df['mean'] > ignore_diff_rate]
        else:
            stats_df['diff'] = abs(stats_df['mean'] - stats_df['min'])

            # filter by lambda_threshold
            stats_df = stats_df[stats_df['diff'] > lamnda_threshold * stats_df['std']]
            # filter by ignore_diff_rate
            stats_df = stats_df[abs(stats_df['min'] - stats_df['mean'])/stats_df['mean'] > ignore_diff_rate]

        # get itemIds
        itemIds = stats_df['itemid'].tolist()

        return itemIds

    def _evaluate_cond(self, value: float, cond: Dict) -> bool:
        if "condition" not in cond.keys():
            return False

        operator = cond["condition"].get("operator", "")
        threshold = cond["condition"].get("value", "")
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == "=":
            return value == threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        return False


    def _detect1_batch(self,  
        itemIds: List[int], 
        t_stats: pd.DataFrame,
        lambda1_threshold: float
    ) -> List[int]:
        ms = self.ms
        trends_min_count = self.trends_min_count
        ignore_diff_rate = self.ignore_diff_rate
        means = ms.history_stats.read_stats(itemIds)[['itemid', 'mean']]

        # get stats
        #t_stats = ms.trends_stats.read_stats(itemIds)[['itemid', 'mean', 'std', 'cnt']]
        t_stats = t_stats[t_stats['cnt'] > trends_min_count]

        # merge stats
        h_stats_df = pd.merge(means, t_stats, on='itemid', how='inner', suffixes=('_h', '_t'))
        h_stats_df = h_stats_df[h_stats_df['std']>0]

        # filter h_stats_df where mean_h > mean_t + lambda1_threshold * std_t | mean_h < mean_t - lambda1_threshold * std_t
        h_stats_df = h_stats_df[(h_stats_df['mean_h'] > h_stats_df['mean_t'] + lambda1_threshold * h_stats_df['std']) | (h_stats_df['mean_h'] < h_stats_df['mean_t'] - lambda1_threshold * h_stats_df['std'])]
        if self.trace_mode:
            self._print_trace("detect1: filter by lamda1", h_stats_df)

        if len(h_stats_df) == 0:
            return []

        # ignore small diffs
        h_stats_df = h_stats_df[h_stats_df['mean_t'] > 0 & (abs(h_stats_df['mean_h'] - h_stats_df['mean_t'])/h_stats_df['mean_t'] > ignore_diff_rate)]
        if self.trace_mode:
            self._print_trace("detect1: filter by ignore_diff_rate", h_stats_df)

        if len(h_stats_df) == 0:
            return []

        # get itemIds
        itemIds = h_stats_df['itemid'].tolist()
        itemIds = list(set(itemIds))

        dg = self.dg

        # filter by defined conds
        #log(f"detector.filter_by_cond(itemIds)")
        item_conds = self.item_conds
        if len(item_conds) > 0 and len(itemIds) > 0:
            for cond in item_conds:
                #if cond['filter'] == "key_ LIKE 'vmware.vm.guest.osuptime%'":
                #    print("")
                if len(itemIds) == 0:
                    break
                itemIds2 = dg.check_itemId_cond(itemIds, cond["filter"])
                for itemId in itemIds2:    
                    value = means[means['itemid'] == itemId].iloc[0]['mean']
                    if self._evaluate_cond(value, cond) == False:
                        itemIds.remove(itemId)

        if self.trace_mode:
            self._print_item_trace("filter by item_conds", itemIds)


        if len(itemIds) == 0:
            return []

        # filter by defined diff conds
        item_diff_conds = self.item_diff_conds
        h_stats_df['diff'] = abs(h_stats_df['mean_h'] - h_stats_df['mean_t'])

        if len(item_diff_conds) > 0 and len(itemIds) > 0:
            for cond in item_diff_conds:
                if len(itemIds) == 0:
                    break
                itemIds2 = dg.check_itemId_cond(itemIds, cond['filter'])
                for itemId in itemIds2:
                    #if cond['filter'] == "key_ LIKE 'vmware.vm.guest.osuptime%'":
                    #    print("")
                    value = h_stats_df[h_stats_df['itemid'] == itemId].iloc[0]['diff']
                    if self._evaluate_cond(value, cond) == False:
                        itemIds.remove(itemId)
        
        if self.trace_mode:
            self._print_item_trace("filter by diff item_conds", itemIds)

        return itemIds


    def _filter_by_anomaly_cnt(self, stats_df: pd.DataFrame, 
        hist_count: int,
        df: pd.DataFrame, 
        lamdba_threshold: float,
        is_up=True) -> List[int]:
        anomaly_valid_count_rate = self.anomaly_valid_count_rate

        # filter anomalies in history_df1
        df = self._filter_anomalies(df, stats_df, lamdba_threshold, is_up=is_up)
        if self.trace_mode:
            self._print_trace("detect3: filter anomalies by lambda %f: is_up=%d" % (lamdba_threshold, is_up), df)

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
        if self.trace_mode:
            self._print_item_trace("detect3: filter by anomaly count: is_up=%d" % is_up, itemIds)

        # make unique
        itemIds = list(set(itemIds))
        return itemIds



    def _filter_anomalies(self, df: pd.DataFrame, 
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
            if new_df.empty:
                new_df = df_part
            else:
                new_df = pd.concat([new_df, df_part])

        return new_df

    def _calc_local_peak(self, itemIds: List[int], df: pd.DataFrame, window: int, is_up=True) -> pd.DataFrame:
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


    def _get_trends_stats(self, trends_df: pd.DataFrame, cnts_df: pd.DataFrame) -> Tuple[pd.DataFrame]:
        means = trends_df.groupby('itemid')['value'].mean().reset_index()
        means.columns = ['itemid', 'mean']
        stds = trends_df.groupby('itemid')['value'].std().reset_index()
        stds.columns = ['itemid', 'std']
        trends_stats_df = pd.merge(means, stds, on='itemid', how='inner')
        trends_stats_df = pd.merge(trends_stats_df, cnts_df, on='itemid', how='inner')
        return trends_stats_df

    # df_counts, lambda2_threshold, density_window
    def _filter_anomal_history(self, itemIds: List[int], 
                            df: pd.DataFrame, 
                            trends_peak: pd.DataFrame,
                            hist_count: int,
                            trends_stas_df: pd.DataFrame,
                            density_window: int,
                            lambda_threshold: float,
                            is_up=True) -> List[int]:
        # filter by anomaly count
        itemIds = self._filter_by_anomaly_cnt(trends_stas_df, hist_count, df, lambda_threshold, is_up=is_up)
        if self.trace_mode:
            self._print_item_trace("detect3: filter by anomaly count: is_up=%d" % is_up, itemIds)

        if len(itemIds) == 0:
            return []
        local_peaks = self._calc_local_peak(itemIds, trends_peak, density_window, is_up=is_up)
        
        means = df.groupby('itemid')['value'].mean().reset_index()
        local_peaks = pd.merge(local_peaks, means, on='itemid', how='inner')

        if is_up:
            itemIds = local_peaks[(local_peaks['local_peak'] < local_peaks['value'])]['itemid'].tolist()  
        else:
            itemIds = local_peaks[(local_peaks['local_peak'] > local_peaks['value'])]['itemid'].tolist()

        if self.trace_mode:
            self._print_item_trace("detect3: filter by local peak: is_up=%d" % is_up, itemIds)

        itemIds = list(set(itemIds))
        return itemIds


    def _detect2_batch(self, history_df: pd.DataFrame, trends_df: pd.DataFrame,
            itemIds: List[int],
            lambda2_threshold: float):

        # group by itemid and get min, max and the first value
        r_stats = history_df.groupby('itemid')['value'].agg(['min', 'max', 'first']).reset_index()
        r_stats["min_diff"] = r_stats["min"] - r_stats["first"]
        r_stats["max_diff"] = r_stats["max"] - r_stats["first"]
        r_stats = r_stats[['itemid', 'min_diff', 'max_diff']]
        r_stats.columns = ['itemid', 'min', 'max']


        itemIds_up = self._detect_diff_anomalies(itemIds, trends_df, r_stats, lambda2_threshold, is_up=True)
        itemIds_dw = self._detect_diff_anomalies(itemIds, trends_df, r_stats, lambda2_threshold, is_up=False)

        itemIds = itemIds_up + itemIds_dw
        itemIds = list(set(itemIds))
        return itemIds


    def _detect3_batch(self, 
            trends_df: pd.DataFrame,
            base_clocks: List[int],
            itemIds: List[int], 
            startep2: int, 
            lambda3_threshold: float,
            lambda4_threshold: float) -> List[int]:

        ms = self.ms
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
        
        trends_stats_df_up = self._get_trends_stats(trends_max, cnts)
        trends_stats_df_dw = self._get_trends_stats(trends_min, cnts)

        
        #df_counts = history_df1.groupby('itemid')['value'].count().reset_index()
        #df_counts.columns = ['itemid', 'cnt']
        hist_count = len(base_clocks)

        density_window = self.history_interval * self.history_retention

        itemIds_up = self._filter_anomal_history(itemIds, history_df1, trends_max, hist_count, trends_stats_df_up, 
                                            density_window, lambda3_threshold, is_up=True)
        itemIds_dw = self._filter_anomal_history(itemIds, history_df1, trends_min, hist_count, trends_stats_df_dw, 
                                            density_window, lambda3_threshold, is_up=False)

        itemIds1 = itemIds_up + itemIds_dw
        if self.trace_mode:
            self._print_item_trace("detect3: filter by lambda3", itemIds1)
        
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

        itemIds_up = self._filter_anomal_history(itemIds, history_df2, trends_max, hist_count, trends_stats_df_up, 
                                            density_window, lambda4_threshold, is_up=True)
        itemIds_dw = self._filter_anomal_history(itemIds, history_df2, trends_min, hist_count, trends_stats_df_dw, 
                                            density_window, lambda4_threshold, is_up=False)

        itemIds2 = itemIds_up + itemIds_dw
        if self.trace_mode:
            self._print_item_trace("detect3: filter by lambda4", itemIds2)
        itemIds1.extend(itemIds2)
        itemIds = list(set(itemIds1))

        return itemIds

    def _get_normalized_charts(self, itemIds: List[int], 
                base_clocks: List[int]) -> Dict[int, pd.Series]:
        dg = self.dg
        hist_df = dg.get_history_data(startep=base_clocks[0], endep=base_clocks[-1], itemIds=itemIds)
        if hist_df.empty:
            return 
        charts = {}
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
            charts[itemId] = pd.Series(data=values)
        
        return charts



    def _update_history_batch(self, itemIds: List[int], 
                base_clocks: List[int], oldep: int):
        dg = self.dg
        ms = self.ms
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



    def _update_history(self, itemIds: List[int], base_clocks: List[int], oldep: int):
        batch_size = self.batch_size
        for i in range(0, len(itemIds), batch_size):
            batch_itemIds = itemIds[i:i+batch_size]
            # update history
            self._update_history_batch(batch_itemIds, base_clocks, oldep)
            


    def _classify_anomalies(self, itemIds: List[int], 
                            endep: int) -> Dict[int, List[int]]:
        #ms = self.ms
        dg = self.dg
        #k = self.k
        if len(itemIds) < 2:    
            return {}

        startep = endep - self.dbscan_detection_period

        #if k >= len(itemIds):
        #    k = 2
        #threshold = self.km_threshold
        #max_iterations = self.max_iterations
        #n_rounds = self.n_rounds
        # get history data
        #history_df = ms.history.get_data(itemIds)
        history_df = dg.get_history_data(startep=startep, endep=endep, itemIds=itemIds)
        if history_df.empty:
            return {}
    
        base_clocks = normalizer.get_base_clocks(startep, endep, self.history_interval)
        
        # normalize history data so that max=1 and min=0
        history_df = normalizer.normalize_metric_df(history_df)

        # fill na with 0
        history_df['value'] = history_df['value'].fillna(0)

        # convert df to charts: Dict[int, pd.Series]
        charts = {}
        for itemId in itemIds:
            #charts[itemId] = history_df[history_df['itemid'] == itemId]['value'].reset_index(drop=True)
            clocks = history_df[history_df['itemid'] == itemId]['clock'].tolist()
            values = history_df[history_df['itemid'] == itemId]['value'].tolist()
            if len(values) > 0:
                values = normalizer.fit_to_base_clocks(base_clocks, clocks, values)
                charts[itemId] = pd.Series(values)

        if len(charts) < 2:
            return {}
        
        chart_stats = normalizer.get_chart_stats(history_df, itemIds) 

        #if k >= len(charts):
        #    k = 2

        #if len(charts)/2 < k:
        #    k = int(len(charts)/2)

        # run dbscan
        clusters, centroids, _ = classifiers.run_dbscan(charts, 
                                        chart_stats, 
                                        min_samples=self.dbscan_min_samples,
                                        sigma=self.dbscan_sigma,
                                        jaccard_eps=self.dbscan_jaccard_threshold,
                                        corr_eps=self.dbscan_correlation_threshold)
        if self.centroid_dir != "":
            filename = f"{self.centroid_dir}/centroids_{endep}.json.gz"
            log(f"save centroids to {filename}")
            classifiers.save_centroids(centroids, filename=filename)

        # assing -1 to charts not included in clusters
        for chartid in charts.keys():
            if chartid not in clusters:
                clusters[chartid] = -1

        #centroids, old_new_mapping = kmeans.rearange_centroids(centroids, self.km_threshold2)
        #for chartid, clusterid in clusters.items():
        #    clusters[chartid] = old_new_mapping[clusterid]

        # reassign clusters
        #classifiers.reassign_charts(charts, clusters, centroids, self.km_threshold2)

        # get charts with clusterid = -1
        #clusters_0 = {chartid: clusterid for chartid, clusterid in clusters.items() if clusterid == -1}
        #if len(clusters_0) > 3:
        #    # do kmeans again
        #    clusters_0, centroids_0 = kmeans.run_kmeans(charts, k, threshold, max_iterations, n_rounds)

        #if len(clusters_0) > 0:
        #    max_clusterid = max(clusters.values())
        #    # update clusters with clusters_0 starting from max_clusterid + 1
        #    for chartid, clusterid in clusters_0.items():
        #        clusters[chartid] = clusterid + max_clusterid + 1

        #    # update centroids with centroids_0
        #    for chartid, clusterid in clusters.items():
        #        if clusterid in centroids_0:
        #            centroids[chartid] = centroids_0[clusterid]

        return clusters

    # filter by cond
    def _filter_by_cond(self, itemIds: List[int]) -> List[int]:
        ms = self.ms
        dg = self.dg
        means = ms.history_stats.read_stats(itemIds)[['itemid', 'mean']]
        item_conds = self.item_conds
        # filter by item_conds
        if len(item_conds) > 0 and len(itemIds) > 0:
            for cond in item_conds:
                """
                conf format:
                    name: ignore traffic lower than 8Mbps
                    item: key_ LIKE 'net.if.%.[%]' AND units = 'bps' 
                    value: #'value > 8000000'
                    operator: '>'
                    value: 8000000
                """
                itemIds2 = dg.check_itemId_cond(itemIds, cond["item"])
                for itemId in itemIds2:    
                    value = means[means['itemid'] == itemId].iloc[0]['mean']
                    if self._evaluate_cond(value, cond) == False:
                        itemIds.remove(itemId)

        if self.trace_mode:
            self._print_item_trace("filter by item_conds", itemIds)
        return itemIds
                        



    def detect(self,  
            t_startep: int, startep1: int, startep2: int, endep: int,
            base_clocks: List[int],
            itemIds: List[int] = [],
            group_names: List[str] = [],  
            skip_history_update=False) -> pd.DataFrame:
        anomaly_itemIds = []
        batch_size = self.batch_size
        anomaly_keep_secs = self.anomaly_keep_secs
        ms = self.ms
        dg = self.dg
        lambda1_threshold = self.lambda1_threshold
        lambda2_threshold = self.lambda2_threshold
        lambda3_threshold = self.lambda3_threshold
        lambda4_threshold = self.lambda4_threshold
        #k = self.k

        log(f"First count: {len(itemIds)}")

        log(f"detector.detect1_batch(batch_itemIds, {lambda1_threshold}) (1st time)")
        for i in range(0, len(itemIds), batch_size):
            batch_itemIds = itemIds[i:i+batch_size]
            t_stats = ms.trends_stats.read_stats(itemIds)[['itemid', 'mean', 'std', 'cnt']]
            # first detection
            batch_anomaly_itemIds = self._detect1_batch(batch_itemIds, t_stats, lambda1_threshold)
            if len(batch_anomaly_itemIds) == 0:
                continue
            anomaly_itemIds.extend(batch_anomaly_itemIds)        

        if self.trace_mode:
            self._print_item_trace("detect1(trends filter) result (1st time):", batch_anomaly_itemIds)

        log(f"After detector.detect1_batch count: {len(anomaly_itemIds)}")

        #if len(anomaly_itemIds) == 0:
        #    return None
        
        if not skip_history_update and len(anomaly_itemIds) > 0:
            log(f"detector.update_history(anomaly_itemIds, base_clocks, {startep1})")
            itemIds_to_renew = ms.anomalies.get_itemids()
            itemIds_to_renew.extend(anomaly_itemIds)
            itemIds_to_renew = list(set(itemIds_to_renew))

            self._update_history(itemIds_to_renew, base_clocks, startep1)
            ms.history.remove_itemIds_not_in(itemIds_to_renew)
        
        log("starting detect1(2nd time),detect2,detect3")
        anomaly_itemIds2 = []
        for i in range(0, len(anomaly_itemIds), batch_size):
            # second detection
            batch_itemIds = anomaly_itemIds[i:i+batch_size]
            
            # get trends data
            trends_df = dg.get_trends_full_data(startep=t_startep, endep=startep1, itemIds=batch_itemIds)
            if trends_df.empty:
                return []
            
            # calculate trends stats again as trends_df is newer than ms.trends_stats
            trends_stats_df = trends_df.groupby('itemid')['value_avg'].agg(['mean', 'std', 'count']).reset_index()
            trends_stats_df.columns = ['itemid', 'mean', 'std', 'cnt']
            #log(f"detector.detect1_batch(batch_itemIds, trends_stats_df, {lambda1_threshold}) (2nd time)")
            batch_itemIds = self._detect1_batch(batch_itemIds, trends_stats_df, lambda1_threshold)
            if len(batch_itemIds) == 0:
                continue
            if self.trace_mode:
                self._print_item_trace("detect1(trends filter) result (2nd time):", batch_itemIds)


            history_df = ms.history.get_data(batch_itemIds)
            if history_df.empty:
                continue

            trends_df = trends_df[trends_df["itemid"].isin(batch_itemIds)]
            
            #log(f"detector.detect2_batch(history_df, trends_df, batch_itemIds, {lambda2_threshold})")
            batch_anomaly_itemIds = self._detect2_batch(history_df, trends_df, batch_itemIds, lambda2_threshold)
            if len(batch_anomaly_itemIds) == 0:
                continue
            if self.trace_mode:
                self._print_item_trace("detect2(diff filter by lambda2) result:", batch_anomaly_itemIds)

            trends_df = trends_df[trends_df["itemid"].isin(batch_anomaly_itemIds)]

            # third detection
            #log(f"detector.detect3_batch(trends_df, base_clocks, batch_anomaly_itemIds, {startep2}, {lambda3_threshold}, {lambda4_threshold})")
            batch_anomaly_itemIds = self._detect3_batch(trends_df, base_clocks, batch_anomaly_itemIds, startep2, 
                                                lambda3_threshold, lambda4_threshold)
            if self.trace_mode:
                self._print_item_trace("detect3(filter by lambda3 and lambda4) result:", batch_anomaly_itemIds)
            if len(batch_anomaly_itemIds) == 0:
                continue
            anomaly_itemIds2.extend(batch_anomaly_itemIds)

        if self.trace_mode:
            self._print_item_trace("detect2, detect3 result:", anomaly_itemIds2)

        log(f"final count: {len(anomaly_itemIds2)}")

        #if len(anomaly_itemIds2) == 0:
        #    return None

        clusters = {}
        all_anomaly_itemIds = ms.anomalies.get_itemids()
        all_anomaly_itemIds.extend(anomaly_itemIds2)
        if len(all_anomaly_itemIds) > 2:
            #if len(all_anomaly_itemIds) < k:
            #    k = 2

            # get anomalies in the db
            #all_anomaly_itemIds = ms.anomalies.get_itemids()
            all_anomaly_itemIds.extend(anomaly_itemIds2)
            all_anomaly_itemIds = list(set(all_anomaly_itemIds))

            # classify anomaly_itemIds3 by kmeans
            log(f"detector.classify_anomalies(anomaly_itemIds2)")
            clusters = self._classify_anomalies(all_anomaly_itemIds, endep)
                    
        groups_info = dg.classify_by_groups(anomaly_itemIds2, group_names)
        if len(anomaly_itemIds2) == 0:
            return None

        host_itemIds = dg.get_item_host_dict(anomaly_itemIds2)
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
        results = results.drop_duplicates(subset=['itemid', 'group_name', 'clusterid'], keep='first')
        
        # insert anomalies
        log(f"detector.insert_data(results)")
        ms.anomalies.insert_data(results)
        ms.anomalies.update_clusterid(clusters)
        log(f"detector.delete_old_entries({endep - anomaly_keep_secs})")
        ms.anomalies.delete_old_entries(endep - anomaly_keep_secs)
        return results


    def update_anomalies(self, epoch=0):
        ms = self.ms
        all_anomaly_itemIds = ms.anomalies.get_itemids()
        all_anomaly_itemIds = list(set(all_anomaly_itemIds))

        if epoch == 0:
            epoch = ms.anomalies.get_last_updated()

        # classify anomaly_itemIds3 by kmeans
        log(f"detector.classify_anomalies(anomaly_itemIds2)")
        clusters = self._classify_anomalies(all_anomaly_itemIds, epoch)
        ms.anomalies.update_clusterid(clusters)

    def check_distance(self, itemId1, itemId2, endep=0):
        ms = self.ms
        dg = self.dg
        if endep == 0:
            endep = ms.anomalies.get_last_updated()

        startep = endep - self.km_detection_period

        itemIds = [itemId1, itemId2]
        history_df = dg.get_history_data(startep=startep, endep=endep, itemIds=itemIds)
        if history_df.empty:
            return {}
    
        base_clocks = list(set(history_df["clock"].tolist()))
        
        # normalize history data so that max=1 and min=0
        history_df = normalizer.normalize_metric_df(history_df)

        # convert df to charts: Dict[int, pd.Series]
        charts = {}
        for itemId in itemIds:
            #charts[itemId] = history_df[history_df['itemid'] == itemId]['value'].reset_index(drop=True)
            clocks = history_df[history_df['itemid'] == itemId]['clock'].tolist()
            values = history_df[history_df['itemid'] == itemId]['value'].tolist()
            if len(values) > 0:
                values = normalizer.fit_to_base_clocks(base_clocks, clocks, values)
                charts[itemId] = pd.Series(data=values)

        if len(charts) < 2:
            return {}

        op_chart = 1 - charts[itemId1]
        d = classifiers.calculate_distance(charts[itemId1], op_chart, charts[itemId2])
        return d


def detect(data_source: Dict, 
           t_startep: int, h_startep1: int, h_startep2: int, endep: int,
           base_clocks: List[int],
           itemIds: List[int], group_names: List[str], 
           skip_history_update=False,
           trace_mode=False) -> pd.DataFrame:
    detector = Detector(data_source, trace_mode=trace_mode)
    return detector.detect(t_startep, h_startep1, h_startep2, endep, 
                           base_clocks, itemIds, group_names, 
                           skip_history_update=skip_history_update)

def update_anomalies(data_source: Dict, epoch=0):
    detector = Detector(data_source)
    detector.update_anomalies(epoch)

def check_distance(data_source: Dict, itemId1, itemId2, endep=0):
    detector = Detector(data_source)

    return detector.check_distance(itemId1, itemId2, endep)