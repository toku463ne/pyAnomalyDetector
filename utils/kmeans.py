import random
import numpy as np
import pandas as pd
import gzip
import json
from collections import OrderedDict as ordered_dict
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from sklearn.decomposition import PCA

def calculate_distance(chart1: pd.Series, op_chart1: pd.Series, chart2: pd.Series) -> float:
    """
    Calculate the Euclidean distance between two charts.

    Parameters:
        chart1 (pd.Series): Data of the first chart.
        op_chart1 (pd.Series): Opposite data of the first chart.
        chart2 (pd.Series): Data of the second chart.

    Returns:
        float: Euclidean distance between the two charts.
    """
    d1 = np.linalg.norm(chart1 - chart2) / np.sqrt(len(chart1))
    d2 = np.linalg.norm(op_chart1 - chart2) / np.sqrt(len(chart1))
    return min(d1, d2)

def initialize_centroids(charts: Dict[int, pd.Series], k: int) -> Dict[int, pd.Series]:
    """
    Initialize centroids for KMeans clustering.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        k (int): Number of clusters.

    Returns:
        dict: Dictionary of centroids with clusterId as key and itemId as value.
    """
    if k >= len(charts.keys()):
        raise ValueError("k must be less than the number of unique chart ids")
    centroids = {}
    initial_centroid_ids = random.sample(list(charts.keys()), k)
    for i, centroid_id in enumerate(initial_centroid_ids):
        centroids[i] = charts[centroid_id]

    # if there are multiple centroids with the same value, make them unique by reducing the overlaps
    new_centroid_ids = []
    excluded_centroid_ids = []
    for i, centroid_id in enumerate(centroids):
        values = centroids[centroid_id].values
        for j in range(i+1, len(centroids)):
            if j in excluded_centroid_ids:
                continue
            if np.array_equal(values, centroids[j].values):
                excluded_centroid_ids.append(j)
    new_centroid_ids = [i for i in range(k) if i not in excluded_centroid_ids]
    new_centroids = {}
    for i, centroid_id in enumerate(new_centroid_ids):
        new_centroids[i] = centroids[centroid_id]

    return new_centroids

def calculate_centroids(charts: Dict[int, pd.Series], clusters: Dict[int, int]) -> Dict[int, pd.Series]:
    """
    Calculate centroids for KMeans clustering.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        clusters (dict): Dictionary of itemId to clusterId.

    Returns:
        dict: Dictionary of centroids with clusterId as key and itemId as value.
    """
    centroids = {}
    counts = {}
    
    for chart_id, cluster_id in clusters.items():
        if cluster_id not in centroids:
            centroids[cluster_id] = charts[chart_id]
            counts[cluster_id] = 1
        else:
            centroids[cluster_id] += charts[chart_id]
            counts[cluster_id] += 1

    for cluster_id in centroids:
        if counts[cluster_id] > 0:
            centroids[cluster_id] /= counts[cluster_id]
    
    return centroids

def assign_clusters(charts: Dict[int, pd.Series], 
                    op_charts: Dict[int, pd.Series],
                    centroids: Dict[int, pd.Series], threshold: float) -> Dict[int, int]:
    """
    Assign clusters to charts based on centroids.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        centroids (dict): Dictionary of centroids with clusterId as key and itemId as value.
        threshold (float): Minimum distance threshold for assigning clusters.

    Returns:
        dict: Dictionary of itemId to clusterId.
    """
    clusters = {}
    chart_ids = list(charts.keys())
    chart_data = np.array([charts[chart_id] for chart_id in chart_ids])
    centroid_ids = list(centroids.keys())
    centroid_data = np.array([centroids[centroid_id] for centroid_id in centroid_ids])
    distances = np.linalg.norm(chart_data[:, np.newaxis] - centroid_data, axis=2)

    min_distances = np.min(distances, axis=1)
    assigned_clusters = np.argmin(distances, axis=1)
    
    for i, chart_id in enumerate(chart_ids):
        if min_distances[i] <= threshold:
            clusters[chart_id] = centroid_ids[assigned_clusters[i]]
        else:
            new_cluster_id = max(centroids.keys()) + 1
            centroids[new_cluster_id] = charts[chart_id]
            clusters[chart_id] = new_cluster_id
    return clusters

def kmeans(charts: Dict[int, pd.Series], op_charts: Dict[int, pd.Series],
           k: int, threshold: float, max_iterations: int) -> Tuple[Dict[int, int], Dict[int, pd.Series]]:
    """
    Run KMeans clustering.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        k (int): Number of clusters.
        threshold (float): Minimum distance threshold for assigning clusters.
        max_iterations (int): Maximum number of iterations.

    Returns:
        dict: Dictionary of itemId to clusterId.
    """
    clusters = {}
    for i in range(max_iterations):
        if i == 0:
            centroids = initialize_centroids(charts, k)
        else:
            centroids = calculate_centroids(charts, clusters)
        new_clusters = assign_clusters(charts, op_charts, centroids, threshold)
        if clusters == new_clusters:
            break
        clusters = new_clusters
    return clusters, centroids

def run_kmeans(
    charts: Dict[int, pd.Series],
    k: int,
    threshold: float,
    max_iterations: int,
    n_rounds: int
) -> Tuple[Dict[int, int], Dict[int, pd.Series]]:

    """
    Run customized KMeans clustering.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        k (int): Number of clusters.
        threshold (float): Minimum distance threshold for assigning clusters.
        max_iterations (int): Maximum number of iterations.
        n_rounds (int): Number of rounds to run the clustering.

    Returns:
        dict: Dictionary of itemId to clusterId for the best clustering.
    """
    best_clusters = None
    best_score = float('inf')
    best_centroids = None

    # create the opposite of the charts
    op_charts = {}
    for chart_id, chart_data in charts.items():
        op_charts[chart_id] = 1 - chart_data

    
    for _ in range(n_rounds):
        clusters, centroids = kmeans(charts, op_charts, k, threshold, max_iterations)
        score = len(centroids)
        if score < best_score:
            best_clusters = clusters
            best_score = score
            best_centroids = centroids            

    return best_clusters, best_centroids

# Rearange the centroids and assign the charts to the new centroid
# How to rearange the centroids:
# 1. check the centroids and if the euclidean distance between the centroids are less than the threshold
# then integrate the centroids and assign the charts to the new centroid
# 2. repeat the above step until there is no more centroids to integrate
# 3. return the new centroids and the mapping of the old centroid to the new centroid
def rearange_centroids(centroids: Dict[int, pd.Series], threshold: float) -> Tuple[Dict[int, pd.Series], Dict[int, int]]:
    clusterids = list(centroids.keys())
    old_new_mapping = {}
    new_centroids = {}
    new_clusterid = 0

    op_centroids = {}
    for clusterid, centroid in centroids.items():
        op_centroids[clusterid] = 1 - centroid

    for i, clusterid in enumerate(clusterids):
        if clusterid in old_new_mapping:
            continue
        old_new_mapping[clusterid] = new_clusterid
        new_centroids[clusterid] = centroids[clusterid]
        sum_centroid = centroids[clusterid].copy()
        cnt_centroid = 1
        for j in range(i+1, len(clusterids)):
            clusterid2 = clusterids[j]
            dist = calculate_distance(centroids[clusterid], op_centroids[clusterid], centroids[clusterid2])
            if dist < threshold:
                if clusterid2 in old_new_mapping:
                    continue
                else:
                    sum_centroid += centroids[clusterid2].copy()
                    cnt_centroid += 1
                    old_new_mapping[clusterid2] = new_clusterid
        new_clusterid += 1
        if cnt_centroid > 1:
            new_centroids[clusterid] = sum_centroid / cnt_centroid            

    return new_centroids, old_new_mapping


def reassign_charts(charts: Dict[int, pd.Series], 
                    clusters: Dict[int, int], 
                    centroids: Dict[int, pd.Series],
                    threshold: float) -> Dict[int, int]:
    """
    check all charts and calculate the distance to the centroids and if the distance is less than the threshold
    then assign the chart to the cluster with clusterid = -1 
    """
    op_charts = {}
    for chart_id, chart_data in charts.items():
        op_charts[chart_id] = 1 - chart_data

    for chart_id, cluster_id in clusters.items():
        if cluster_id == -1:
            continue
        dist = calculate_distance(charts[chart_id], op_charts[chart_id], centroids[cluster_id])
        if dist < threshold:
            clusters[chart_id] = -1

    # check if charts in clusterid = -1 belong to other clusters
    for chart_id, cluster_id in clusters.items():
        if cluster_id != -1:
            continue
        min_dist = float('inf')
        min_cluster_id = -1
        for centroid_id, centroid in centroids.items():
            dist = calculate_distance(charts[chart_id], op_charts[chart_id], centroid)
            if dist < min_dist and dist < threshold:
                min_dist = dist
                min_cluster_id = centroid_id
        clusters[chart_id] = min_cluster_id

    return clusters
                

def process_clusters(charts: Dict[int, pd.Series], clusters: Dict[int, int]) -> Tuple[ordered_dict, Dict[int, List[int]]]:
    """
    Process clusters to order by cluster size descending.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        clusters (dict): Dictionary of itemId to clusterId.

    Returns:
        tuple: Ordered dictionary of clusters and chart ids.
    """
    ordered_charts = ordered_dict()
    chart_ids = {}
    for chart_id, cluster_id in clusters.items():
        if cluster_id not in ordered_charts:
            ordered_charts[cluster_id] = []
            chart_ids[cluster_id] = []
        ordered_charts[cluster_id].append(charts[chart_id])
        chart_ids[cluster_id].append(chart_id)

    # order by cluster size descending
    ordered_charts = ordered_dict(sorted(ordered_charts.items(), key=lambda x: len(x[1]), reverse=True))
    return ordered_charts, chart_ids


def save_centroids(centroids, filename="centroids.json.gz"):
    """
    Saves centroids to a compressed JSON file.
    """
    centroids_dict = {key: value.tolist() for key, value in centroids.items()}
    with gzip.open(filename, 'wt', encoding='utf-8') as f:
        json.dump(centroids_dict, f)

def load_centroids(filename="centroids.json.gz"):
    """
    Loads centroids from a compressed JSON file.
    """
    with gzip.open(filename, 'rt', encoding='utf-8') as f:
        centroids_dict = json.load(f)
    return {int(key): pd.Series(value) for key, value in centroids_dict.items()}

def load_csv_metrics(csv_path: str, base_clocks: List[int]) -> Dict[int, pd.Series]:
    """
    Load metrics data from a CSV file.
    CSV file should have the following columns:
    - id: Unique identifier for each chart.
    - time: Epoch time of the chart.
    - value: Value of the metric.

    Parameters:
        csv_path (str): Path to the CSV file.
        base_clocks (list): List of base clock times.

    Returns:
        dict: Dictionary of itemId to chart data.
    """
    data = pd.read_csv(csv_path, header=None, names=['itemid', 'clock', 'value'])
    data = data.sort_values(['itemid', 'clock'])
    data['value'] = data['value'].astype(float)

    charts = {}

    # Get unique chart ids
    chart_ids = data['itemid'].unique().astype(int).tolist()
    for chart_id in chart_ids:
        chart_data = data[data['itemid'] == chart_id]

        # Interpolate missing values
        chart_data = chart_data.set_index('clock').reindex(base_clocks)
        chart_data = chart_data['value'].fillna(0).reset_index()

        # normalize chart_data
        avg = chart_data['value'].mean()
        std = chart_data['value'].std()
        chart_data['value'] = (chart_data['value'] - avg) / (2 * std)
        chart_data['value'] = chart_data['value'].clip(0, 1)
        charts[chart_id] = chart_data['value']

    return charts


def plot_clusters(charts: Dict[int, pd.Series], clusters: Dict[int, int]):
    """
    Plot clusters of charts.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        clusters (dict): Dictionary of itemId to clusterId.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set(style='whitegrid')
    unique_clusters = set(clusters.values())

    for cluster_id in unique_clusters:
        fig, ax = plt.subplots(figsize=(12, 8))
        for chart_id, assigned_cluster_id in clusters.items():
            if assigned_cluster_id == cluster_id:
                chart_data = charts[chart_id]
                ax.plot(chart_data, label=f'Chart {chart_id}')
        
        ax.set_title(f'Cluster {cluster_id}')
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        ax.legend()
        plt.show()

def plot_heatmap(org_centroids, N: int = 0):
    """
    Plots a heatmap of the pairwise Euclidean distances between cluster centroids.
    
    Parameters:
        centroids (dict): Dictionary of clusterId to pd.Series representing centroids.
    """
    op_centroids = {}
    for clusterid, centroid in org_centroids.items():
        op_centroids[clusterid] = 1 - centroid

    if N > 0:
        centroids = dict(list(org_centroids.items())[:N]).copy()
    else:  
        centroids = org_centroids.copy()
    
    k = len(centroids)  # Number of clusters
    clusterids = list(centroids.keys())
    
    # Compute pairwise distances between centroids
    distance_matrix = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            distance_matrix[i, j] = calculate_distance(centroids[clusterids[i]], 
                                                       op_centroids[clusterids[i]], 
                                                       centroids[clusterids[j]])
    
    # Convert to DataFrame for visualization
    distance_df = pd.DataFrame(distance_matrix, index=[f'c{clusterids[i]}' for i in range(k)],
                               columns=[f'c{clusterids[i]}' for i in range(k)])
    
    # Plot heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(distance_df, annot=True, fmt=".1f", cmap="coolwarm", linewidths=0.5)
    plt.title("Cluster Distance Heatmap")
    plt.show()

def plot_pca(centroids):
    """
    Plots a PCA projection of the cluster centroids in 2D.
    
    Parameters:
        centroids (dict): Dictionary of clusterId to pd.Series representing centroids.
    """
    k = len(centroids)  # Number of clusters
    
    # Convert centroids to NumPy array
    centroid_values = np.vstack([centroids[i].values for i in range(k)])
    
    # PCA Projection to 2D
    pca = PCA(n_components=2)
    centroids_pca = pca.fit_transform(centroid_values)
    
    # Plot PCA results
    plt.figure(figsize=(6, 5))
    plt.scatter(centroids_pca[:, 0], centroids_pca[:, 1], c=range(k), cmap='viridis', edgecolors='k', s=100)
    for i, txt in enumerate(range(k)):
        plt.annotate(f"Cluster {txt}", (centroids_pca[i, 0], centroids_pca[i, 1]), fontsize=10)
    plt.title("PCA Projection of Clusters")
    plt.xlabel("Principal Component 1")
    plt.ylabel("Principal Component 2")
    plt.grid(True)
    plt.show()