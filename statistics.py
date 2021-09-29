import os
import pandas as pd
import pretty_midi as pm
import librosa
import json


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

def statistics_other_datasets():
    MAPS = '/import/c4dm-01/MAPS_original'
    A_MAPS = '/import/c4dm-datasets/A2S_transcription/working/A-MAPS_1.1/midi/'
    ASAP = '/import/c4dm-datasets/ASAP_dataset/asap-dataset-1.1'

    print('MAPS dataset:')
    n, duration = 0, 0
    MAPS_subsets = [f for f in os.listdir(MAPS) if os.path.isdir(os.path.join(MAPS, f))]
    for subset in MAPS_subsets:
        for item in os.listdir(os.path.join(MAPS, subset, 'MUS')):
            if item[-4:] == '.wav':
                y, fs = librosa.load(os.path.join(MAPS, subset, 'MUS', item))
                n += 1
                duration += len(y) / fs
                print(n, end='\r')
    print('\n, n:', n, 'duration:', duration / 3600)

    print('A-MAPS dataset:')
    n, duration = 0, 0
    for item in os.listdir(A_MAPS):
        midi_data = pm.PrettyMIDI(os.path.join(A_MAPS, item))
        n += 1
        duration += midi_data.get_end_time()
        print(n, end='\r')
    print('\n n:', n, 'duration:', duration / 3600)

    print('ASAP dataset:')
    n, duration = 0, 0
    n_audio, duration_audio = 0, 0
    metadata = pd.read_csv(os.path.join(ASAP, 'metadata.csv'))
    for i, row in metadata.iterrows():
        midi_data = pm.PrettyMIDI(os.path.join(ASAP, row['midi_performance']))
        d = midi_data.get_end_time()
        n += 1
        duration += d
        if type(row['maestro_audio_performance']) == str:
            n_audio += 1
            duration_audio += d
        print(i+1, '/', len(metadata), end='\r')
    print('\n n:', n, 'duration:', duration / 3600)
    print('n_audio:', n_audio, 'duration_audio:', duration_audio / 3600)


if __name__ == '__main__':

    # print_statistics()
    statistics_other_datasets()