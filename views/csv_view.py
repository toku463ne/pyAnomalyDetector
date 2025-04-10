import matplotlib.pyplot as plt
import pandas as pd
import math

from views.view import View

class CsvViews(View):
    def __init__(self, config):
        self.history_file_path = config['history_file_path']
        self.trends_file_path = config['trends_file_path']
        self.startep = config.get('startep',0)
        self.endep = config.get('endep',0)


    def show(self, anomaly_data: pd.DataFrame):
        target_itemids = anomaly_data['itemid'].unique()
        trends = pd.read_csv(self.trends_file_path)
        history = pd.read_csv(self.history_file_path)

        # filter trends and history by startep and endep
        if self.startep != 0:
            trends = trends[trends['clock'] >= self.startep]
            history = history[history['clock'] >= self.startep]
        if self.endep != 0:
            trends = trends[trends['clock'] <= self.endep]
            history = history[history['clock'] <= self.endep]

        # concat trends and history
        data = pd.concat([trends, history])


        itemids = data['itemid'].unique()
        # limit to target_itemids
        itemids = [itemid for itemid in itemids if itemid in target_itemids]

        if len(itemids) > 30:
            itemids = itemids[:30]

        nrows = math.ceil(len(itemids) / 3) 
        fig, axs = plt.subplots(nrows, 3, figsize=(20, 3 * nrows))
        if nrows == 1:
            axs = axs.flatten()  # Flatten axs if it's a single row

        for i, itemid in enumerate(itemids):
            if nrows == 1:
                ax = axs[i % 3]
            else:
                ax = axs[i // 3, i % 3]
            ax.set_title(f'itemid: {itemid}')
            # convert clock to datetime
            data['clock'] = pd.to_datetime(data['clock'], unit='s')
            # show datatime in vertical way
            ax.xaxis_date()
            fig.autofmt_xdate()

            if len(data[data['itemid'] == itemid]['clock']) == 0:
                continue
            
            # show value_avg, value_min, value_max, value in the same graph
            ax.plot(data[data['itemid'] == itemid]['clock'], data[data['itemid'] == itemid]['value_avg'])
            ax.plot(data[data['itemid'] == itemid]['clock'], data[data['itemid'] == itemid]['value_min'])
            ax.plot(data[data['itemid'] == itemid]['clock'], data[data['itemid'] == itemid]['value_max'])
            ax.plot(data[data['itemid'] == itemid]['clock'], data[data['itemid'] == itemid]['value'])
            
            ax.plot(data[data['itemid'] == itemid]['clock'], data[data['itemid'] == itemid]['value'])

        plt.tight_layout()
        plt.show()
        

    def check_conn(self):
        return True