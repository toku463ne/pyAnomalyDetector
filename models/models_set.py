

#from models.trends import TrendsModel
from models.trends_stats import TrendsStatsModel
from models.history import HistoryModel
#from models.history_stats import HistoryStatsModel
from models.trends_updates import TrendsUpdatesModel
from models.history_updates import HistoryUpdatesModel
from models.recent_anomalies import RecentAnomalyModel
from models.anomalies import AnomaliesModel
from db.postgresql import PostgreSqlDB
import utils.config_loader as config_loader


class ModelsSet:
    def __init__(self, data_source_name):
        self.data_source_name = data_source_name
        #self.trends = TrendsModel(data_source_name)
        self.create_schema()
        self.trends_stats = TrendsStatsModel(data_source_name)
        self.history = HistoryModel(data_source_name)
        self.history_updates = HistoryUpdatesModel(data_source_name)
        self.trends_updates = TrendsUpdatesModel(data_source_name)
        self.anomalies = AnomaliesModel(data_source_name)
        self.recent_anomalies = RecentAnomalyModel(data_source_name)

    # create schema with name of data_source_name 
    def create_schema(self):
        db = PostgreSqlDB(config_loader.conf["admdb"])
        db.create_schema(self.data_source_name)


    def initialize(self):
        #self.trends.truncate()
        self.trends_stats.truncate()
        self.history.truncate()
        #self.history_stats.truncate()
        self.history_updates.truncate()
        self.trends_updates.truncate()
        self.recent_anomalies.truncate()
        self.anomalies.truncate()

    def check_conn(self) -> bool:
        for m in [self.trends_stats, 
                  self.history, 
                  self.history_updates, 
                  self.trends_updates, 
                  self.recent_anomalies, 
                  self.anomalies]:
            if not m.check_conn():
                return False
        return True