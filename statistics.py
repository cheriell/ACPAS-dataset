
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

    metadata_R_ASAP_train = metadata_R_ASAP.loc[metadata_R_ASAP['split'] == 'train']
    metadata_R_ASAP_validation = metadata_R_ASAP.loc[metadata_R_ASAP['split'] == 'validation']
    metadata_R_ASAP_test = metadata_R_ASAP.loc[metadata_R_ASAP['split'] == 'test']

    metadata_S_train = metadata_S.loc[metadata_S['split'] == 'train']
    metadata_S_validation = metadata_S.loc[metadata_S['split'] == 'validation']
    metadata_S_test = metadata_S.loc[metadata_S['split'] == 'test']

    metadata_all_train = pd.concat([metadata_R_ASAP_train, metadata_S_train], ignore_index=True)
    metadata_all_validation = pd.concat([metadata_R_ASAP_validation, metadata_S_validation], ignore_index=True)
    metadata_all_test = pd.concat([metadata_R_MAPS, metadata_R_ASAP_test, metadata_S_test], ignore_index=True)
    metadata_all = pd.concat([metadata_R, metadata_S], ignore_index=True)

    for subset, source, split, metadata in [('Real recording', 'MAPS', 'test', metadata_R_MAPS),
                                            ('Real recording', 'ASAP', 'train', metadata_R_ASAP_train),
                                            ('Real recording', 'ASAP', 'validation', metadata_R_ASAP_validation),
                                            ('Real recording', 'ASAP', 'test', metadata_R_ASAP_test),
                                            ('Real recording', 'Total', '--', metadata_R),
                                            ('Synthetic', '--', 'train', metadata_S_train),
                                            ('Synthetic', '--', 'validation', metadata_S_validation),
                                            ('Synthetic', '--', 'test', metadata_S_test),
                                            ('Synthetic', '--', 'Total', metadata_S),
                                            ('Both', '--', 'train', metadata_all_train),
                                            ('Both', '--', 'validation', metadata_all_validation),
                                            ('Both', '--', 'test', metadata_all_test),
                                            ('Both', '--', 'Total', metadata_all)]:
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