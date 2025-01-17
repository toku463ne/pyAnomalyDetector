
import utils.config_loader as config_loader
import data_processing.trends_stats as trends_stats
from models.models_set import ModelsSet




def update_stats(config_file: str, 
                endep: int, diff_startep: int =0, 
                item_names: list[str] = [], 
                host_names: list[str] = [], 
                group_names: list[str] = [],
                initialize: bool = False):
    config_loader.load_config(config_file)
    conf = config_loader.conf
    data_sources = conf['data_sources']
    
    # don't include the very last epoch
    endep -= 1

    # update stats
    for data_source in data_sources:
        oldstartep: int = 0
        startep: int = 0
        diff_startep: int = 0
        ms = ModelsSet(data_source["name"])
    
        if diff_startep == 0:
            diff_startep = ms.trends_updates.get_endep()

        oldstartep = ms.trends_updates.get_startep()

        # get old epoch from trends_interval and trends_retention
        trends_interval = conf['trends_interval']
        trends_retention = conf['trends_retention']
        startep = endep - trends_interval * trends_retention
        if diff_startep == 0:
            diff_startep = startep
        trends_stats.update_trends_stats(data_source, startep, diff_startep, endep, 
                                         oldstartep, 
                                         item_names=item_names, host_names=host_names, group_names=group_names,
                                         initialize=initialize)

        ms.trends_updates.upsert_updates(startep, endep)


if __name__ == "__main__":
    # read arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')
    parser.add_argument('--start', type=int, help='Start epoch. Data will be initialized if start is given.')
    parser.add_argument('--end', type=int, help='End epoch.')

    