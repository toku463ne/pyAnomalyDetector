
def get_data_getter(data_source_config):
    if data_source_config['type'] == 'sample':
        from data_getter.sample_getter import SampleGetter
        return SampleGetter(data_source_config)
    else:
        raise ValueError('Invalid data source')