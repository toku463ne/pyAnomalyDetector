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

- Initialize or update trends data:
    Get `trends` from the data source and save the following values to `anomdec.trends_stats` table.  
	  - sum: sum of values
      - sqr_sum: sum of square of values
      - count: count of values
      - t_mean: average
      - t_std: standard deviation
  
- Data Conversion:
    Convert `history` from the data source into the `anomdec.history` table.  
    Data will drop into a single interval defined in the config file.  
  
  
- 1st detection:
    - calculate h_mean: the mean of each items in the `anomdec.history` table
    - calculate lambda1: (h_mean - t_mean)/t_std  of each items
    - if lambda1 > lambda1_threshold, store the item in the dict variable latest_items
    
- 2nd detection:
  for items in latest_items variable
	- Get `trends` from the data source filtering by
		lambda2: (value - t_mean)/std > lambda2_threshold
	- calculate t2_mean, t2_std of the filtered values
    - calculate lambda3: (h_mean - t2_mean)/t2_std
	- if lambda3 > lambda3_threshold, store the item in the dict variable latest_items
	
- Normalize recent history:
    - For item in latest_items:
      - Normalize item data in `anomdec.history` so that max=1 and min=-0

- Summarize recent data:
    - classify the normalized data by a customized k-means algorithm  

- View the result
	- Show all items filtered by 2nd detection somehow (zabbix dashboard etc)  
  
- Alarming:
	- If there are items from multiple hosts in the same k-means group, send an alarm.
    

  
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
  
