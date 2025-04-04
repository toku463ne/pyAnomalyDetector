from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import gzip
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import utils.normalizer as normalizer
from sklearn.cluster import OPTICS

from scipy.spatial.distance import pdist, squareform, correlation
from typing import Dict, Tuple
import numpy as np
import pandas as pd

def run_dbscan(
    charts: Dict[int, pd.Series],
    eps: float = 0.5,
    min_samples: int = 5,
) -> Tuple[Dict[int, int], Dict[int, pd.Series]]:
    """
    Classify charts using DBSCAN with Correlation Distance.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        eps (float): Maximum distance between two samples for them to be considered as in the same neighborhood.
        min_samples (int): Minimum number of samples in a neighborhood to form a core point.

    Returns:
        Tuple[Dict[int, int], Dict[int, pd.Series]]: Clusters and centroids.
    """
    # Convert chart data to a NumPy array
    data = np.array([chart.values for chart in charts.values()])

    # Compute pairwise correlation distances
    try:
        distance_matrix = squareform(pdist(data, metric='correlation'))
    except ValueError as e:
        raise ValueError("Error computing the distance matrix. Ensure the input data is valid and non-empty.") from e

    # Run DBSCAN with precomputed distance matrix
    db = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed').fit(distance_matrix)

    # Extract clusters
    clusters = {chart_id: db.labels_[i] for i, chart_id in enumerate(charts.keys())}

    # Extract centroids (mean of points in each cluster)
    centroids = {}
    for cluster_id in set(db.labels_):
        if cluster_id == -1:  # Skip noise points
            continue
        cluster_points = data[np.array(list(clusters.values())) == cluster_id]
        centroids[cluster_id] = np.mean(cluster_points, axis=0)

    return clusters, centroids


def run_optics(
    charts: Dict[int, pd.Series],
    min_samples: int = 5,
    max_eps: float = np.inf,
) -> Tuple[Dict[int, int], Dict[int, pd.Series]]:
    """
    Classify charts using OPTICS.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        min_samples (int): Minimum number of samples in a neighborhood to form a core point.
        max_eps (float): Maximum distance between two samples for them to be considered as in the same neighborhood.

    data = np.array([list(chart) for chart in charts.values()])
    if np.isnan(data).any():
        raise ValueError("Input data contains NaN values. Please check your input charts for missing or invalid values.")
        Tuple[Dict[int, int], Dict[int, pd.Series]]: Clusters and centroids.
    """
    data = np.array([list(chart) for chart in charts.values()])
    optics = OPTICS(min_samples=min_samples, max_eps=max_eps, metric='euclidean').fit(data)

    # Extract clusters
    clusters = {chart_id: optics.labels_[i] for i, chart_id in enumerate(charts.keys())}

    # Extract centroids (mean of points in each cluster)
    centroids = {}
    for cluster_id in set(optics.labels_):
        if cluster_id == -1:  # Skip noise points
            continue
        cluster_points = data[np.array(list(clusters.values())) == cluster_id]
        centroids[cluster_id] = np.mean(cluster_points, axis=0)

    return clusters, centroids


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

            distance = pdist([chart.values, other_chart.values], metric='correlation')[0]
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
    km = KMeans(n_clusters=k, max_iter=max_iterations, tol=1e-4, random_state=42, algorithm='lloyd')
    distance_matrix = squareform(pdist(data, metric='correlation'))
    distance_matrix = np.nan_to_num(distance_matrix, nan=0.0)
    # Fit the KMeans model
    km.fit(distance_matrix)

    # Extract clusters and centroids
    clusters = {chart_id: km.labels_[i] for i, chart_id in enumerate(charts.keys())}
    centroids = {i: centroid for i, centroid in enumerate(km.cluster_centers_)}

    return clusters, centroids

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
    d1 = np.linalg.norm(chart1 - chart2) 
    d2 = np.linalg.norm(op_chart1 - chart2) 
    return min(d1, d2) / np.sqrt(len(chart1))


def save_centroids(centroids, filename="centroids.json.gz"):
    """
    Saves centroids to a compressed JSON file.
    """
    centroids_dict = {key: value.tolist() for key, value in centroids.items()}
    with gzip.open(filename, 'wt', encoding='utf-8') as f:
        json.dump(centroids_dict, f)

def save_cluster_metrics(cluster_metrics, filename="cluster_metrics.json.gz"):
    """
    Saves cluster metrics to a compressed JSON file.
    """
    with gzip.open(filename, 'wt', encoding='utf-8') as f:
        json.dump(cluster_metrics, f)

def load_centroids(filename="centroids.json.gz"):
    """
    Loads centroids from a compressed JSON file.
    """
    with gzip.open(filename, 'rt', encoding='utf-8') as f:
        centroids_dict = json.load(f)
    return {int(key): pd.Series(value) for key, value in centroids_dict.items()}

def load_csv_metrics(csv_path: str, base_clocks: List[int], chart_ids: List[int] = []) -> Dict[int, pd.Series]:
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
    data = normalizer.normalize_metric_df(data)

    charts = {}

    # Get unique chart ids
    if len(chart_ids) == 0:
        chart_ids = data['itemid'].unique().astype(int).tolist()
    charts = {}
    for itemId in chart_ids:
        #charts[itemId] = history_df[history_df['itemid'] == itemId]['value'].reset_index(drop=True)
        clocks = data[data['itemid'] == itemId]['clock'].tolist()
        values = data[data['itemid'] == itemId]['value'].tolist()
        if len(values) > 0:
            values = normalizer.fit_to_base_clocks(base_clocks, clocks, values)
            charts[itemId] = pd.Series(values)
            # normalize charts[itemId] 

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

def evaluate_clusters(data: Dict[int, pd.Series], labels: Dict[int, int]) -> float:
    """
    Evaluate the quality of clusters using the Silhouette Score.

    Parameters:
        data (dict): Dictionary of itemId to chart data.
        labels (dict): Dictionary of itemId to clusterId.

    Returns:
        float: Silhouette Score for the clustering.
    """
    # Convert data and labels to NumPy arrays
    data_array = np.array([data[item_id].values for item_id in data.keys()])
    label_array = np.array([labels[item_id] for item_id in data.keys()])
    
    # Compute Silhouette Score
    score = silhouette_score(data_array, label_array, metric='euclidean')
    return score