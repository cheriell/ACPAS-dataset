
import pandas as pd


def print_statistics():

    metadata_R = pd.read_csv('metadata_R.csv')
    metadata_S = pd.read_csv('metadata_S.csv')

    statistics = pd.DataFrame(columns=[
        'Subset',
        'Source',
        'Split',
        'Pieces',
        'Performances',
        'Duration (hours)',
    ])
    metadata_R_MAPS = metadata_R.loc[metadata_R['source'] == 'MAPS']
    metadata_R_ASAP = metadata_R.loc[metadata_R['source'] == 'ASAP']

    metadata_R_ASAP_training = metadata_R_ASAP.loc[metadata_R_ASAP['split'] == 'training']
    metadata_R_ASAP_validation = metadata_R_ASAP.loc[metadata_R_ASAP['split'] == 'validation']
    metadata_R_ASAP_testing = metadata_R_ASAP.loc[metadata_R_ASAP['split'] == 'testing']

    metadata_S_training = metadata_S.loc[metadata_S['split'] == 'training']
    metadata_S_validation = metadata_S.loc[metadata_S['split'] == 'validation']
    metadata_S_testing = metadata_S.loc[metadata_S['split'] == 'testing']

    metadata_all = pd.concat([metadata_R, metadata_S], ignore_index=True)

    for subset, source, split, metadata in [('Real recording', 'MAPS', 'testing', metadata_R_MAPS),
                                            ('Real recording', 'ASAP', 'training', metadata_R_ASAP_training),
                                            ('Real recording', 'ASAP', 'validation', metadata_R_ASAP_validation),
                                            ('Real recording', 'ASAP', 'testing', metadata_R_ASAP_testing),
                                            ('Real recording', 'Total', '--', metadata_R),
                                            ('Synthetic', '--', 'training', metadata_S_training),
                                            ('Synthetic', '--', 'validation', metadata_S_validation),
                                            ('Synthetic', '--', 'testing', metadata_S_testing),
                                            ('Synthetic', '--', 'Total', metadata_S),
                                            ('Total', '--', '--', metadata_all)]:
        statistics = statistics.append({
            'Subset': subset,
            'Source': source,
            'Split': split,
            'Pieces': len(set(metadata['piece_id'])),
            'Performances': len(metadata),
            'Duration (hours)': metadata['duration'].sum() / 3600,
        }, ignore_index=True)
    
    print(statistics)

if __name__ == '__main__':

    print_statistics()