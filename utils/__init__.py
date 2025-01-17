from datetime import datetime


# converts string to epoch time
def str2epoch(datestr: str, format: str) -> int:
    dt = datetime.strptime(datestr, format)
    epoch_time = int(dt.timestamp())
    return epoch_time

