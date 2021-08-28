import os
import argparse
import pandas as pd
from collections import defaultdict
import random
random.seed(42)


def get_distinct_pieces_dict():
    distinct_pieces = pd.read_csv('metadata/distinct_pieces.csv')
    distinct_pieces_dict = {
        'id2piece': {},
        'ASAP_title2id': {},
        'CPM_title2id': {},
    }

    for i, row in distinct_pieces.iterrows():
        distinct_pieces_dict['id2piece'][row['id']] = {
            'composer': row['composer'],
            'ASAP_title': row['ASAP_title'],
            'CPM_title': row['CPM_title'],
            'split': row['split'],
        }
        distinct_pieces_dict['ASAP_title2id'][row['ASAP_title']] = row['id']
        distinct_pieces_dict['CPM_title2id'][row['CPM_title']] = row['id']

    return distinct_pieces_dict

def get_CPM_metadata_dict(args):
    CPM_metadata = pd.read_csv(os.path.join(args.CPM, 'metadata.csv'))
    CPM_metadata_dict = {
        'short_name2title': {},
        'title2composer': {},
    }

    for i, row in CPM_metadata.iterrows():
        short_name = row['midi'].split('/')[-1][:-4]
        CPM_metadata_dict['short_name2title'][short_name] = row['title']
        CPM_metadata_dict['title2composer'][row['title']] = row['composer']

    return CPM_metadata_dict

def create_real_recording_subset(distinct_pieces_dict, CPM_metadata_dict, args):
    print('Create Real recording subset...')

    metadata_R = pd.DataFrame(columns=[
        'performance_id',  # "R_{number}"
        'piece_id',  # "{number}"
        'composer',  # composer (or "Christmas")
        'title',  # title of the piece
        'source',  # "MAPS" or "ASAP"
        'performance_audio',  # path to the performance audio
        'performance_MIDI',  # path to the performance MIDI
        'MIDI_score',  # path to the MIDI score
        'split',  # training/validation/testing
    ])
    performance_count = 0

    ## MAPS "ENSTDkCl" and "ENSTDkAm" subsets
    for item in os.listdir(args.A_MAPS):
        MAPS_subset = item[9:-4].split('_')[-1]
        if MAPS_subset in ['ENSTDkCl', 'ENSTDkAm']:

            # get metadata
            short_name = '_'.join(item[9:-4].split('_')[:-1])
            CPM_title = CPM_metadata_dict['short_name2title'][short_name]

            performance_id = 'R_' + str(performance_count + 1)
            piece_id = distinct_pieces_dict['CPM_title2id'][CPM_title]
            composer = CPM_metadata_dict['title2composer'][CPM_title]
            title = 'CPM_' + CPM_title
            source = 'MAPS'
            performance_audio = os.path.join('{MAPS}', MAPS_subset, 'MUS', item[:-4]+'.wav')
            performance_MIDI = os.path.join('{MAPS}', MAPS_subset, 'MUS', item)
            MIDI_score = os.path.join('{A_MAPS}', item)
            split = 'testing'

            # update split in distinct_pieces_dict
            distinct_pieces_dict['id2piece'][piece_id]['split'] = split

            # update metadata_R
            metadata_R.loc[performance_count] = [
                performance_id,
                piece_id,
                composer,
                title,
                source,
                performance_audio,
                performance_MIDI,
                MIDI_score,
                split,
            ]
            performance_count += 1

    ## ASAP real recording tuples
    metadata_ASAP = pd.read_csv(os.path.join(args.ASAP, 'metadata.csv'))
    for i, row in metadata_ASAP.iterrows():
        if type(row['audio_performance']) == str:
            
            # get metadata
            ASAP_title = row['title']

            performance_id = 'R_' + str(performance_count + 1)
            piece_id = distinct_pieces_dict['ASAP_title2id'][ASAP_title]
            composer = row['composer']
            title = 'ASAP_' + ASAP_title
            source = 'ASAP'
            performance_audio = os.path.join('{ASAP}', row['audio_performance'])
            performance_MIDI = os.path.join('{ASAP}', row['midi_performance'])
            MIDI_score = os.path.join('{ASAP}', row['midi_score'])
            split = distinct_pieces_dict['id2piece'][piece_id]['split']  # testing is the piece is already testing, update more testing later.

            # update metadata_R
            metadata_R.loc[performance_count] = [
                performance_id,
                piece_id,
                composer,
                title,
                source,
                performance_audio,
                performance_MIDI,
                MIDI_score,
                split,
            ]
            performance_count += 1

    ## udpate training/validation/testing split for ASAP real recording performances
    # all pieces from ASAP
    ASAP_piece_id_all = set([row['piece_id'] for i, row in metadata_R.iterrows() if row['source'] == 'ASAP'])
    # training/validation/testing amounts
    training_amount = len(ASAP_piece_id_all) * 8 // 10
    validation_amount = len(ASAP_piece_id_all) // 10
    testing_amount = len(ASAP_piece_id_all) - training_amount - validation_amount

    # pieces already split to testing
    ASAP_piece_id_testing_cur = set([piece_id for piece_id in ASAP_piece_id_all if distinct_pieces_dict['id2piece'][piece_id]['split'] == 'testing'])
    ASAP_piece_id_remaining = ASAP_piece_id_all - ASAP_piece_id_testing_cur
    # random select some other pieces for testing
    ASAP_piece_id_testing_additional = set(random.sample(list(ASAP_piece_id_remaining), testing_amount - len(ASAP_piece_id_testing_cur)))
    ASAP_piece_id_remaining -= ASAP_piece_id_testing_additional
    # random select pieces for validation
    ASAP_piece_id_validation = set(random.sample(ASAP_piece_id_remaining, validation_amount))
    ASAP_piece_id_remaining -= ASAP_piece_id_validation

    # update split in metadata_R
    for i, row in metadata_R.iterrows():
        if type(row['split']) == float:
            if row['piece_id'] in ASAP_piece_id_testing_additional:
                metadata_R.loc[i, 'split'] = 'testing'
            elif row['piece_id'] in ASAP_piece_id_validation:
                metadata_R.loc[i, 'split'] = 'validation'
            elif row['piece_id'] in ASAP_piece_id_remaining:
                metadata_R.loc[i, 'split'] = 'training'
            else:
                print('check error!')

    ## subset statistics
    # MAPS
    print('- from MAPS:')
    print('\ttesting:', (metadata_R['source'] == 'MAPS').sum())
    # ASAP
    performance_training_amount = 0
    performance_validation_amount = 0
    performance_testing_amount = 0
    for i, row in metadata_R.iterrows():
        if row['source'] == 'ASAP':
            if row['split'] == 'training':
                performance_training_amount += 1
            elif row['split'] == 'validation':
                performance_validation_amount += 1
            elif row['split'] == 'testing':
                performance_testing_amount += 1
            else:
                print('check error!')
    print('- from ASAP:')
    print('\ttraining:', performance_training_amount)
    print('\tvalidation:', performance_validation_amount)
    print('\ttesting:', performance_testing_amount)

    metadata_R.to_csv('metadata/metadata_R.csv', index=False)
            




if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--A_MAPS', 
                        type=str, 
                        default='C:\\Users\\Marco\\Downloads\\Datasets\\A-MAPS\\midi',
                        help='Path to the A_MAPS midi files')
    parser.add_argument('--CPM',
                        type=str,
                        default='C:\\Users\\Marco\\Downloads\\Datasets\\ClassicalPianoMIDI-dataset',
                        help='Path to the Classical Piano MIDI dataset')
    parser.add_argument('--ASAP',
                        type=str,
                        default='C:\\Users\\Marco\\Downloads\\Datasets\\asap-dataset',
                        help='Path to the ASAP dataset')
    args = parser.parse_args()

    distinct_pieces_dict = get_distinct_pieces_dict()
    CPM_metadata_dict = get_CPM_metadata_dict(args)

    create_real_recording_subset(distinct_pieces_dict, CPM_metadata_dict, args)