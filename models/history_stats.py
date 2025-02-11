
from models.trends_stats import TrendsStatsModel

class HistoryStatsModel(TrendsStatsModel):
    sql_template = "trends_stats"
    name = "history_stats"
    
    
    
    