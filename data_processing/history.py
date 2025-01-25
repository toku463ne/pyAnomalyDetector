from typing import List

import utils.config_loader as config_loader
import data_getter
from models.models_set import ModelsSet
import utils.normalizer as normalizer


def _update_history_batch(dg, ms: ModelsSet, itemIds: List[int], 
            base_clocks: List[int], oldep: int):
    # update history data
    hist_df = dg.get_history_data(startep=base_clocks[0], endep=base_clocks[-1], itemIds=itemIds)
    if hist_df.empty:
        return 

    for itemId in itemIds:
        item_hist_df = hist_df[hist_df['itemid'] == itemId]
        if item_hist_df.empty:
            continue

        values = normalizer.fit_to_base_clocks(
            base_clocks, 
            item_hist_df['clock'].tolist(), 
            item_hist_df['value'].tolist())
        ms.history.upsert([itemId]*len(base_clocks), base_clocks, values)

    if oldep > 0:
        # delete old history data
        ms.history.remove_old_data(oldep)


def update_history(data_source, itemIds: List[int], base_clocks: List[int], oldep: int):
    batch_size = config_loader.conf["batch_size"]
    dg = data_getter.get_data_getter(data_source)
    ms = ModelsSet(data_source["name"])
    #itemIds = dg.get_itemIds(itemIds=itemIds)

    for i in range(0, len(itemIds), batch_size):
        batch_itemIds = itemIds[i:i+batch_size]
        # update history
        _update_history_batch(dg, ms, batch_itemIds, base_clocks, oldep)
        
        

    