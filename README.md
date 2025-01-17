# pyAnomalyDetector

## Setup
**Prepare postgresql server**


**Execute the setup script**
```bash
./setup.sh
```

## Setup postgresql for admin
```sql
CREATE DATABASE anomdec;
CREATE USER anomdec_adm WITH ENCRYPTED PASSWORD 'anomdec_pass';
GRANT ALL PRIVILEGES ON DATABASE anomdec TO anomdec_adm;
```

## Algorithm
- load config:
load `default.yml` and an additional config file if provided

- Initialize data (only the first time):
    Convert `trends` from the data source into the `anomdec.trends` table.
  
- Data Conversion:
    Convert `history` from the data source into the `anomdec.trends`, `anomdec.history` table.
    Data will drop into a single interval defined in the config file.
  
- Trend statistics:
    Calculate statistics per item and store them in the `anomdec.trends_stats` table.
      - sum: sum of values
      - sqr_sum: sum of square of values
      - count: count of values
      - start: start epoch
      - end: end epoch
      - t_mean: average
      - t_std: standard deviation
      - last_update: last updated epoch
  
- 1st detection:
    - calculate h_mean: the mean of each items in the `anomdec.history` table
    - calculate lambda1: (h_mean - t_mean)/t_std  of each items
    - if lambda1 > lambda1_threshold, store the item in the dict variable latest_items
    
- Normalize recent history:
    - For item in latest_items:
      - Normalize item data in `anomdec.history` table the way below:
        - Calculate (value - t_mean)/t_std
        - If the absolute value goes over lambda2_max, change it so that the absolute value be lambda2_max
        - If the absolute value goes under lamba1_threshold, set it as zero

- Summarize recent data:
    - If the item has cache and the pattern matches, rule out the item
    - classify the normalized data by a customized k-means algorithm  
    - calculate score: the sum of data in the same class 
    - Save the topN scores and save it to `anomdec.scores` table.
        - epoch: the current epoch time
        - count: the number of members in the cluster
        - score: the score
    - Remove the scores older than trends_retention
  
- Cache abnormal patterns
    - shift data so that the beginning of the abnormal data comes first
    - keep it per item for history_retention

- Final detection:
    - Calculate statistics of the score in `anomdec.scores` table
    - If the new score is over lambda3_threshold then detect the score as abnormal

  
## File Structure

To implement the algorithm described, you can structure your Python files as follows:

```
pyAnomalyDetector/
│
├── config/
│   ├── __init__.py
│   └── default.yml
│
├── data/
│   ├── __init__.py
│   └── data_source.py
│
├── models/
│   ├── __init__.py
│   ├── trends.py
│   ├── history.py
│   ├── trends_stats.py
│   └── scores.py
│
├── scripts/
│   ├── __init__.py
│   ├── setup_db.py
│   └── data_conversion.py
│
├── utils/
│   ├── __init__.py
│   ├── config_loader.py
│   └── statistics.py
│
├── detection/
│   ├── __init__.py
│   ├── first_detection.py
│   ├── normalize_data.py
│   ├── summarize_data.py
│   └── final_detection.py
│
├── main.py
└── README.md
```

### Description of Files

- `config/`: Contains configuration files and loaders.
    - `default.yml`: Default configuration file.
    - `config_loader.py`: Utility to load configuration files.

- `data/`: Handles data source operations.
    - `data_source.py`: Functions to fetch and preprocess data from the source.

- `models/`: Contains database models and operations.
    - `trends.py`: Model and operations for `anomdec.trends` table.
    - `history.py`: Model and operations for `anomdec.history` table.
    - `trends_stats.py`: Model and operations for `anomdec.trends_stats` table.
    - `scores.py`: Model and operations for `anomdec.scores` table.

- `scripts/`: Contains setup and data conversion scripts.
    - `setup_db.py`: Script to set up the PostgreSQL database.
    - `data_conversion.py`: Script to convert data into the required format.

- `utils/`: Utility functions and helpers.
    - `statistics.py`: Functions to calculate statistics.

- `detection/`: Contains detection algorithms.
    - `first_detection.py`: Implementation of the first detection algorithm.
    - `normalize_data.py`: Functions to normalize recent data.
    - `summarize_data.py`: Functions to summarize recent data.
    - `final_detection.py`: Implementation of the final detection algorithm.

- `main.py`: Entry point of the application.

This structure will help you organize your code and make it easier to maintain and extend. 
  
