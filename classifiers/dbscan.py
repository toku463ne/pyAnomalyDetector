from typing import Dict, Tuple, List
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from models.models_set import ModelsSet
import data_getter 

from classifiers import *

def df2charts(df: pd.DataFrame) -> Dict[int, pd.Series]:
    charts = {}
    for _, row in df.iterrows():
        itemId = row.itemid
        if itemId not in charts:
            charts[itemId] = []
        charts[itemId].append(row["value"])
    
    # convert to series
    for itemId in charts:
        charts[itemId] = pd.Series(charts[itemId])
    
    return charts

def _run_jaccard_dbscan(sigma: float, jaccard_eps: float, min_samples: int,
                        charts: Dict[int, pd.Series], 
                        chart_stats: Dict):
    # compute jaccard distance matrix
    distance_matrix = compute_jaccard_distance_matrix(charts, chart_stats, sigma=sigma)
    matrix_size = (distance_matrix.max().max() - distance_matrix.min().min())
    # Ensure the distance matrix values are normalized between 0 and 1
    if matrix_size > 1:
        distance_matrix = (distance_matrix - distance_matrix.min().min()) / matrix_size

    # Handle NaN values
    if distance_matrix.isna().any().any():
        max_val = np.nanmax(distance_matrix.values)
        if np.isnan(max_val):
            max_val = 1.0
        distance_matrix = distance_matrix.fillna(max_val)
    np.fill_diagonal(distance_matrix.values, 0.0)

    # Run DBSCAN with precomputed distance matrix
    db = DBSCAN(eps=jaccard_eps, min_samples=min_samples, metric='precomputed').fit(distance_matrix)

    return db


def _run_correlation_dbscan(eps: float, min_samples: int,
                        charts: Dict[int, pd.Series]):
    distance_matrix = compute_correlation_distance_matrix(charts, diff_contribute_rate=0.5)
    matrix_size = (distance_matrix.max().max() - distance_matrix.min().min())
    # Ensure the distance matrix values are normalized between 0 and 1
    if matrix_size > 1:
        distance_matrix = (distance_matrix - distance_matrix.min().min()) / matrix_size
    
    # Handle NaN values
    if distance_matrix.isna().any().any():
        max_val = np.nanmax(distance_matrix.values)
        if np.isnan(max_val):
            max_val = 1.0
        distance_matrix = distance_matrix.fillna(max_val)
    np.fill_diagonal(distance_matrix.values, 0.0)

    db = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed').fit(distance_matrix)
    return db



def classify_charts(conf: Dict, data_source_name, 
        itemIds: List[int], endep: int,
        ) -> Tuple[Dict[int, int], Dict[int, pd.Series], Dict[int, pd.Series]]:

    dbscan_conf = conf.get('dbscan', {})
    jaccard_eps = dbscan_conf.get('jaccard_eps', 0.1)
    min_samples = dbscan_conf.get('min_samples', 2)
    sigma = dbscan_conf.get('sigma', 2.0)
    corr_eps = dbscan_conf.get('corr_eps', 0.4)
    
    
    data_sources = conf['data_sources']
    data_source = data_sources[data_source_name]
    classify_period = data_source.get('anomaly_keep_secs', 3600 * 24)
    startep = endep - classify_period
    trends_interval = data_source.get('trends_interval', 86400)
    trends_retention = data_source.get('trends_retention', 14)
    trends_startep = endep - trends_interval * trends_retention

    ms = ModelsSet(data_source_name)
    chart_stats = ms.trends_stats.get_stats_per_itemId(itemIds)
    itemIds = list(chart_stats.keys())
    if len(itemIds) == 0:
        return {}, {}, {}

    
    hist_df = ms.history.get_charts_df(itemIds, startep, endep)
    hist_charts = df2charts(hist_df)

    if len(hist_charts) == 0:
        return {}, {}, {}

    jaccard_db = _run_jaccard_dbscan(
        sigma=sigma,
        jaccard_eps=jaccard_eps,
        min_samples=min_samples,
        charts=hist_charts,
        chart_stats=chart_stats
    )
    # chart_ids per labels
    db_groups = {}
    chart_ids = list(hist_charts.keys())
    for i, label in enumerate(jaccard_db.labels_):
        if label not in db_groups:
            db_groups[label] = []
        db_groups[label].append(chart_ids[i])

    clusters = {chart_id: jaccard_db.labels_[i] for i, chart_id in enumerate(hist_charts.keys())}
    max_cluster_id = max(db_groups.keys())

    dg = data_getter.get_data_getter(data_source)
    trends_df = dg.get_trends_data(trends_startep, startep-1, itemIds)
    df = pd.concat([trends_df, hist_df], ignore_index=True)
    df = df.sort_values(by=['itemid', 'clock'])


    charts = df2charts(df)

    # calculate diff between current and previous values per chart
    #for itemId, series in charts.items():
    #    if len(series) > 1:
    #        charts[itemId] = series.diff().fillna(0)

    # classify each db_group by DBSCAN using correlation distance
    for label, group in db_groups.items():
        # Skip noise points
        if label == -1:
            continue

        # Skip groups with only one chart
        if len(group) < 2:
            continue
        
        db_corr = _run_correlation_dbscan(
            eps=corr_eps,
            min_samples=min_samples,
            charts={chart_id: charts[chart_id] for chart_id in group},
        )

        # Update labels for the group
        for i, chart_id in enumerate(group):
            if db_corr.labels_[i] == -1:
                clusters[chart_id] = -1
            else:
                # Assign a new cluster id based on the max_cluster_id
                clusters[chart_id] = max_cluster_id + db_corr.labels_[i] + 1
        max_cluster_id = max(clusters.values())
    
    
    # Convert chart data to a NumPy array
    aligned_charts = pd.DataFrame(charts).T  # Each row is a chart
    data = aligned_charts.values

    # Extract centroids (mean of points in each cluster)
    centroids = {}
    for cluster_id in range(max_cluster_id+1):
        if cluster_id == -1:  # Skip noise points
            continue
        cluster_points = data[np.array(list(clusters.values())) == cluster_id]
        if len(cluster_points) > 0:
            centroids[cluster_id] = np.mean(cluster_points, axis=0)

    return clusters, centroids, charts

