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
from itertools import combinations

from scipy.spatial.distance import pdist, squareform, correlation
from typing import Dict, Tuple
import numpy as np
import pandas as pd

def run_dbscan(
    charts: Dict[int, pd.Series],
    chart_stats: Dict[int, pd.Series],
    sigma: float = 3.0,
    jaccard_eps: float = 0.1,
    corr_eps: float = 0.4,
    min_samples: int = 2,
) -> Tuple[Dict[int, int], Dict[int, pd.Series], Dict[int, pd.Series]]:
    """
    Classify charts using DBSCAN with Correlation Distance.

    Parameters:
        charts (dict): Dictionary of itemId to chart data.
        eps (float): Maximum distance between two samples for them to be considered as in the same neighborhood.
        min_samples (int): Minimum number of samples in a neighborhood to form a core point.

    Returns:
        Tuple[Dict[int, int], Dict[int, pd.Series]]: Clusters and centroids.
    """
    distance_matrix = compute_jaccard_distance_matrix(charts, chart_stats, sigma=sigma)
    matrix_size = (distance_matrix.max().max() - distance_matrix.min().min())
    # Ensure the distance matrix values are normalized between 0 and 1
    if matrix_size > 1:
        distance_matrix = (distance_matrix - distance_matrix.min().min()) / matrix_size
    
    # Convert chart data to a NumPy array
    data = np.array([chart.values for chart in charts.values()])

    # Run DBSCAN with precomputed distance matrix
    db = DBSCAN(eps=jaccard_eps, min_samples=min_samples, metric='precomputed').fit(distance_matrix)

    # chart_ids per labels
    db_groups = {}
    chart_ids = list(charts.keys())
    for i, label in enumerate(db.labels_):
        if label not in db_groups:
            db_groups[label] = []
        db_groups[label].append(chart_ids[i])

    clusters = {chart_id: db.labels_[i] for i, chart_id in enumerate(charts.keys())}
    max_cluster_id = max(db_groups.keys())

    # classify each db_group by DBSCAN using correlation distance
    for label, group in db_groups.items():
        # Skip noise points
        if label == -1:
            continue

        # Skip groups with only one chart
        if len(group) < 2:
            continue

        # Calculate the distance matrix for the group
        group_distance_matrix = compute_correlation_distance_matrix({chart_id: charts[chart_id] for chart_id in group})
        matrix_size = (distance_matrix.max().max() - distance_matrix.min().min())
        # Ensure the distance matrix values are normalized between 0 and 1
        if matrix_size > 1:
            group_distance_matrix = (group_distance_matrix - group_distance_matrix.min().min()) / matrix_size
        
        # Run DBSCAN on the group
        db_group = DBSCAN(eps=corr_eps, min_samples=min_samples, metric='precomputed').fit(group_distance_matrix)
        # Update labels for the group
        for i, chart_id in enumerate(group):
            clusters[chart_id] = max_cluster_id + db_group.labels_[i] + 1
        max_cluster_id = max(clusters.values())
    
    
    # Extract centroids (mean of points in each cluster)
    centroids = {}
    for cluster_id in set(db.labels_):
        if cluster_id == -1:  # Skip noise points
            continue
        cluster_points = data[np.array(list(clusters.values())) == cluster_id]
        centroids[cluster_id] = np.mean(cluster_points, axis=0)

    return clusters, centroids, charts


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


def calculate_k(charts: Dict[int, pd.Series], distance_matrix: pd.DataFrame, threshold: float) -> int:
    """
    Calculate the number of clusters using determined distance threshold.
    """
    assigned_chart_ids = set()
    n_groups = 0

    for chart_id in charts.keys():
        if chart_id in assigned_chart_ids:
            continue

        n_groups += 1
        assigned_chart_ids.add(chart_id)

        for other_chart_id in charts.keys():
            if other_chart_id in assigned_chart_ids:
                continue

            distance = distance_matrix.loc[chart_id, other_chart_id]
            if distance < threshold:
                assigned_chart_ids.add(other_chart_id)
    return n_groups



def run_kmeans(
    charts: Dict[int, pd.Series],
    chart_stats: Dict[int, pd.Series],
    threshold: float,
    max_iterations: int,
    alpha: float = 0.7,
    sigma: float = 3.0,
) -> Tuple[Dict[int, int], Dict[int, pd.Series], Dict[int, pd.Series]]:
    
    # isolate charts with std = 0
    charts = {chart_id: chart for chart_id, chart in charts.items() if chart.std() > 0}

    distance_matrix = compute_combined_distance_matrix(charts, chart_stats, alpha=alpha, sigma=sigma)
    k = calculate_k(charts, distance_matrix, threshold)
    if k == 0:
        return {}, {}
    if k == 1:
        return {chart_id: 0 for chart_id in charts.keys()}, {0: charts[list(charts.keys())[0]]}

    #data = np.array([list(chart) for chart in charts.values()])
    km = KMeans(n_clusters=k, max_iter=max_iterations, tol=1e-4, random_state=42, algorithm='lloyd')
    #distance_matrix = squareform(pdist(data, metric='correlation'))
    #distance_matrix = np.nan_to_num(distance_matrix, nan=0.0)
    # Fit the KMeans model
    km.fit(distance_matrix)

    # Extract clusters and centroids
    clusters = {chart_id: km.labels_[i] for i, chart_id in enumerate(charts.keys())}
    centroids = {i: centroid for i, centroid in enumerate(km.cluster_centers_)}

    return clusters, centroids, charts

def reassign_charts(charts: Dict[int, pd.Series], 
                    clusters: Dict[int, int], 
                    centroids: Dict[int, pd.Series],
                    threshold: float) -> Dict[int, int]:
    """
    check all charts and calculate the distance to the centroids and if the distance is less than the threshold
    then assign the chart to the cluster with clusterid = -1 
    """
    for chart_id, cluster_id in clusters.items():
        if cluster_id == -1:
            continue
        dist = correlation_distance(charts[chart_id], centroids[cluster_id])
        if dist < threshold:
            clusters[chart_id] = -1

    # check if charts in clusterid = -1 belong to other clusters
    for chart_id, cluster_id in clusters.items():
        if cluster_id != -1:
            continue
        min_dist = float('inf')
        min_cluster_id = -1
        for centroid_id, centroid in centroids.items():
            dist = correlation_distance(charts[chart_id], centroid)
            if dist < min_dist and dist < threshold:
                min_dist = dist
                min_cluster_id = centroid_id
        clusters[chart_id] = min_cluster_id

    return clusters
   


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


def compute_anomaly_indicators(charts: dict, charts_stats: dict, z_thresh: float = 3.0) -> dict:
    """Returns {itemid: binary anomaly indicator (0/1 Series)}"""
    indicators = {}
    for itemid, series in charts.items():
        z_mean = charts_stats[itemid]['mean']
        z_std = charts_stats[itemid]['std']
        if z_std == 0:
            z = 0
        else:
            z = (series - z_mean) / z_std
        indicators[itemid] = (z.abs() > z_thresh).astype(int)
    return indicators

def jaccard_distance(a: pd.Series, b: pd.Series) -> float:
    """Compute Jaccard distance between two binary pd.Series"""
    intersection = ((a == 1) & (b == 1)).sum()
    union = ((a == 1) | (b == 1)).sum()
    return 1.0 if union == 0 else 1 - intersection / union

def correlation_distance(a: pd.Series, b: pd.Series) -> float:
    """Compute 1 - Pearson correlation between two time series"""
    astd = a.std()
    bstd = b.std()
    if astd == 0 or bstd == 0:
        return 1.0
    return 1 - a.corr(b)


def compute_combined_distance_matrix(charts: dict, chart_stats: dict, 
                                     alpha: float = 0.2,
                                     sigma: float = 3.0) -> pd.DataFrame:
    itemids = list(charts.keys())
    N = len(itemids)

    # Step 1: Precompute anomaly indicators
    indicators = compute_anomaly_indicators(charts, chart_stats, z_thresh=sigma)

    # Step 2: Initialize distance matrix
    dist_matrix = np.zeros((N, N))

    for i, j in combinations(range(N), 2):
        id_i, id_j = itemids[i], itemids[j]
        s_i, s_j = charts[id_i], charts[id_j]
        a_i, a_j = indicators[id_i], indicators[id_j]

        d_time = jaccard_distance(a_i, a_j)
        d_shape = correlation_distance(s_i, s_j)
        combined = alpha * d_time + (1 - alpha) * d_shape

        dist_matrix[i, j] = dist_matrix[j, i] = combined

    return pd.DataFrame(dist_matrix, index=itemids, columns=itemids)


def compute_jaccard_distance_matrix(charts: dict, charts_stats: dict, 
                                    sigma: float = 3.0) -> pd.DataFrame:
    itemids = list(charts.keys())
    N = len(itemids)

    # Step 1: Precompute anomaly indicators
    indicators = compute_anomaly_indicators(charts, charts_stats, z_thresh=sigma)

    # Step 2: Initialize distance matrix
    dist_matrix = np.zeros((N, N))

    for i, j in combinations(range(N), 2):
        id_i, id_j = itemids[i], itemids[j]
        a_i, a_j = indicators[id_i], indicators[id_j]

        d_shape = jaccard_distance(a_i, a_j)
        dist_matrix[i, j] = dist_matrix[j, i] = d_shape

    return pd.DataFrame(dist_matrix, index=itemids, columns=itemids)


def compute_correlation_distance_matrix(charts: dict) -> pd.DataFrame:
    itemids = list(charts.keys())
    N = len(itemids)

    # Step 1: Initialize distance matrix
    dist_matrix = np.zeros((N, N))

    for i, j in combinations(range(N), 2):
        id_i, id_j = itemids[i], itemids[j]
        s_i, s_j = charts[id_i], charts[id_j]

        d_shape = correlation_distance(s_i, s_j)
        dist_matrix[i, j] = dist_matrix[j, i] = d_shape

    return pd.DataFrame(dist_matrix, index=itemids, columns=itemids)


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
    if csv_path.endswith('.gz'):
        with gzip.open(csv_path, 'rt', encoding='utf-8') as f:
            data = pd.read_csv(f)
    else:
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
    score = silhouette_score(data_array, label_array, metric='correlation')
    return score