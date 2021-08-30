
import pandas as pd


def print_statistics_R():
    print('\nReal recording subset statistics:')

    metadata_R = pd.read_csv('metadata_R.csv')
    statistics_R = pd.DataFrame(columns=[
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

    for source, split, metadata in [('MAPS', 'testing', metadata_R_MAPS),
                                    ('ASAP', 'training', metadata_R_ASAP_training),
                                    ('ASAP', 'validation', metadata_R_ASAP_validation),
                                    ('ASAP', 'testing', metadata_R_ASAP_testing),
                                    ('Total', '--', metadata_R)]:
        statistics_R = statistics_R.append({
            'Source': source,
            'Split': split,
            'Pieces': len(set(metadata['piece_id'])),
            'Performances': len(metadata),
            'Duration (hours)': metadata['duration'].sum() / 3600,
        }, ignore_index=True)
    print(statistics_R)

def print_statistics_S():
    print('\nSynthetic subset statistics:')

    metadata_S = pd.read_csv('metadata_S.csv')
    statistics_S = pd.DataFrame(columns=[
        'Split',
        'Pieces',
        'Performances',
        'Duration (hours)',
    ])
    metadata_S_training = metadata_S.loc[metadata_S['split'] == 'training']
    metadata_S_validation = metadata_S.loc[metadata_S['split'] == 'validation']
    metadata_S_testing = metadata_S.loc[metadata_S['split'] == 'testing']

    for split, metadata in [('training', metadata_S_training),
                            ('validation', metadata_S_validation),
                            ('testing', metadata_S_testing),
                            ('Total', metadata_S)]:
        statistics_S = statistics_S.append({
            'Split': split,
            'Pieces': len(set(metadata['piece_id'])),
            'Performances': len(metadata),
            'Duration (hours)': metadata['duration'].sum() / 3600,
        }, ignore_index=True)
    print(statistics_S)

if __name__ == '__main__':

    print_statistics_R()
    print_statistics_S()