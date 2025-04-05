import sys, os
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

def calculate_distance(chart1: pd.Series, chart2: pd.Series) -> float:
    return np.linalg.norm(chart1 - chart2) / np.sqrt(len(chart1))


def calculate_k(charts: Dict[int, pd.Series], threshold: float) -> int:
    """
    Calculate the number of clusters using determined distance threshold.
    """
    assigned_chart_ids = set()
    n_groups = 0

    for chart_id, chart in charts.items():
        if chart_id in assigned_chart_ids:
            continue

        n_groups += 1
        assigned_chart_ids.add(chart_id)

        for other_chart_id, other_chart in charts.items():
            if other_chart_id in assigned_chart_ids:
                continue

            distance = calculate_distance(chart, other_chart)
            if distance < threshold:
                assigned_chart_ids.add(other_chart_id)
    return n_groups



def run_kmeans(
    charts: Dict[int, pd.Series],
    threshold: float,
    max_iterations: int,
) -> Tuple[Dict[int, int], Dict[int, pd.Series]]:

    k = calculate_k(charts, threshold)
    if k == 0:
        return {}, {}
    if k == 1:
        return {chart_id: 0 for chart_id in charts.keys()}, {0: charts[list(charts.keys())[0]]}

    data = np.array([list(chart) for chart in charts.values()])
    km = KMeans(n_clusters=k, max_iter=max_iterations, tol=1e-4, random_state=42)
    km.fit(data)

    # Extract clusters and centroids
    clusters = {chart_id: km.labels_[i] for i, chart_id in enumerate(charts.keys())}
    centroids = {i: centroid for i, centroid in enumerate(km.cluster_centers_)}

    return clusters, centroids