# pyAnomalyDetector
Detects anomalies in time series metric data, such as from Zabbix or log files.   
Log data are expected to be the output of [goLogAnalyzer](https://github.com/toku463ne/goLogAnalyzer).  
By default, the tool checks for anomalies in the most recent 3 hours by comparing them to data from the past 14 days.  
For the detected anomalies we provide visualization by the following ways:
- Web UI (by [Streamlit](https://streamlit.io/))
- Zabbix dashboard
- JSON output  
  
  
An item is considered "anomalous" if it meets all of the following conditions:
- **Detect1:**  
    The average of recent data exceeds the historical mean by more than `detect1_lambda_threshold` times the standard deviation.  
    If `item_conds` is defined, items are filtered according to these conditions.

- **Detect2:**  
    The difference between adjacent values in a time series is unusually large compared to historical variation—specifically, if it exceeds `detect2_lambda_threshold` times the historical standard deviation.

- **Detect3:**  
    Calculate the average of the maximum and minimum values for each trend.   
    If the recent data is above or below `detect3_lambda_threshold`, it is considered anomalous.  
    Additionally, compute the maximum and minimum averages for each sliding window of past trend data.   
    If the recent average is greater or smaller than these, it is flagged as anomalous.
  
## Setup
**Prepare the PostgreSQL server somewhere**
  
**Set up PostgreSQL for admin**  
Used for management and data caching.  
```sql
CREATE DATABASE anomdec;
CREATE DATABASE anomdec_test; -- optional: for unit tests
CREATE USER anomdec WITH ENCRYPTED PASSWORD 'You password';
GRANT ALL PRIVILEGES ON DATABASE anomdec TO anomdec;
GRANT ALL PRIVILEGES ON DATABASE anomdec_test TO anomdec; -- optional: for unit tests
```  
  
Only for testing: Create database in a MySQL table
```sql
CREATE DATABASE anomdec_test; -- optional: for unit tests
CREATE USER 'anomdec'@'localhost' IDENTIFIED BY 'anomdec_pass';
GRANT ALL PRIVILEGES ON anomdec_test.* TO 'anomdec'@'localhost';
```

**Configure streamlit (optional)**  
If you use streamlit, edit streamlit parameters in `scripts/setup.env` as necessary.  
  
**Run the setup script**  
This will setup python virtualenv and install necessary packages.
```bash
scripts/setup.sh
```


## How to use
### Prepare yaml file
Refer to [sample](samples/unified.yml) and prepare a yaml file for your envinronment.  
The yaml file could be jinja format.  

If you don't want to include sensitive data like passwords in the yaml file, you could include them in a secret file.
Configure environment variable `ANOMDEC_SECRET_PATH` to specify the secret file path in yaml format too.
```bash
export ANOMDEC_SECRET_PATH=/path/to/your/secretfile.yml
```
  
If you use samples/unified.yml the secret file may look like
```yaml
ZABBIX_API_URL: http://localhost/zabbix
ZABBIX_API_USER: your_zabbix_api_user
ZABBIX_API_PASSWORD: your_zabbix_api_pass
ZABBIX_PSQL_DB_HOST: localhost
ZABBIX_PSQL_DB_NAME: your_zabbix_psql_database
ZABBIX_PSQL_DB_USER: your_zabbix_psql_user
ZABBIX_PSQL_DB_PASSWORD: your_zabbix_psql_user
ZABBIX_MYSQL_DB_HOST: localhost
ZABBIX_MYSQL_DB_NAME: your_zabbix_mysql_database
ZABBIX_MYSQL_DB_USER: your_zabbix_mysql_user
ZABBIX_MYSQL_DB_PASSWORD: your_zabbix_mysql_user
ADM_DB_HOST: localhost
ADM_DB_DB_NAME: anomdec
ADM_DB_PASSWORD: anomdec_pass
ADM_DB_SCHEMA: public
LOGAN_BASE_URL: http://localhost/loganal
```

### Collect trend data
The first step is to prepare trend statics table in the postgresql.  
Execute below once of twice a day.
```bash
scripts/run_daily_trends_stats.sh -c config.yaml
```  
  
### Detect anomaly
Execute below to detect anomaly.
```bash
scripts/run_hourly_detection.sh config.yaml $HOME/anomdec/report.json
```  
