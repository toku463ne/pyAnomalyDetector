import matplotlib.pyplot as plt
import pandas as pd

from views.view import View

class CsvViews(View):
    def __init__(self, config):
        self.history_file_path = config['history_file_path']
        self.trends_file_path = config['trends_file_path']


    def show(self, data_conf):
        itemids = data_conf['anomaly_itemIds2']
        trends = pd.read_csv(self.trends_file_path)
        history = pd.read_csv(self.history_file_path)

        # concat trends and history
        data = pd.concat([trends, history])


        """
        data: pandas.DataFrame with columns: 'itemid', 'clock', 'value'
        plots data per itemid 
        3 * 10 graphs as maximum in the given order
        """

        itemids = data['itemid'].unique()
        itemids = itemids[:30]

        fig, axs = plt.subplots(10, 3, figsize=(20, 20))

        for i, itemid in enumerate(itemids):
            ax = axs[i // 3, i % 3]
            ax.set_title(f'itemid: {itemid}')
            # convert clock to datetime
            data['clock'] = pd.to_datetime(data['clock'], unit='s')
            # show datatime in vertical way
            ax.xaxis_date()
            fig.autofmt_xdate()
            
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