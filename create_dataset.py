import os
import sys
import argparse
import math
import pandas as pd
import random
random.seed(42)
import subprocess
import time

from utilities import format_path, load_path, mkdir

Kontakt_Pianos_all = ['Gentleman_soft',
                    'Gentleman_hard', 
                    'Giant_soft', 
                    'Giant_hard',
                    'Grandeur_soft',
                    'Grandeur_hard', 
                    'Maverick_soft',
                    'Maverick_hard']
Kontakt_Pianos_train = Kontakt_Pianos_all[:6]

def get_distinct_pieces_dict():
    distinct_pieces = pd.read_csv('distinct_pieces.csv')
    distinct_pieces_dict = {
        'id2piece': {},
        'composer_ASAP_title2id': {},
        'composer_CPM_title2id': {},
    }

    for i, row in distinct_pieces.iterrows():
        distinct_pieces_dict['id2piece'][row['id']] = {
            'composer': row['composer'],
            'ASAP_title': row['ASAP_title'],
            'CPM_title': row['CPM_title'],
            'split': math.nan,  # no split for now.
        }
        if type(row['ASAP_title']) == str:
            distinct_pieces_dict['composer_ASAP_title2id']['_'.join([row['composer'], row['ASAP_title']])] = row['id']
        if type(row['CPM_title']) == str:
            distinct_pieces_dict['composer_CPM_title2id']['_'.join([row['composer'], row['CPM_title']])] = row['id']

    return distinct_pieces_dict

def update_distinct_pieces(distinct_pieces_dict):
    distinct_pieces = pd.read_csv('distinct_pieces.csv')
    for i, row in distinct_pieces.iterrows():
        distinct_pieces.loc[i, 'split'] = distinct_pieces_dict['id2piece'][row['id']]['split']
    distinct_pieces.to_csv('distinct_pieces.csv', index=False)

def get_CPM_metadata_dict(args):
    CPM_metadata = pd.read_csv(os.path.join(args.CPM, 'metadata.csv'))
    CPM_metadata_dict = {
        'short_name2title': {},
        'title2piece': {},
    }

    for i, row in CPM_metadata.iterrows():
        short_name = row['midi'].split('/')[-1][:-4]
        CPM_metadata_dict['short_name2title'][short_name] = row['title']
        CPM_metadata_dict['title2piece'][row['title']] = {
            'composer': row['composer'],
            'midi': row['midi'],
        }

    return CPM_metadata_dict

def create_real_recording_subset(distinct_pieces_dict, CPM_metadata_dict, args):
    print('Create Real recording subset...')

    metadata_R = pd.DataFrame(columns=[
        'performance_id',  # "R_{number}"
        'composer',  # composer (or "Christmas")
        'piece_id',  # "{number}"
        'title',  # title of the piece
        'source',  # "MAPS" or "ASAP"
        'performance_audio_external',  # path to the external performance audio
        'performance_MIDI_external',  # path to the external performance MIDI
        'MIDI_score_external',  # path to the external MIDI score
        'folder',  # folder to the audio and MIDI files
        'performance_audio',  # path to the performance audio
        'performance_MIDI',  # path to the performance MIDI
        'MIDI_score',  # path to the MIDI score
        'split',  # training/validation/testing
    ])
    performance_count = 0

    ## MAPS "ENSTDkCl" and "ENSTDkAm" subsets
    A_MAPS_items = os.listdir(args.A_MAPS)
    A_MAPS_items.sort()
    for item in A_MAPS_items:
        MAPS_subset = item[9:-4].split('_')[-1]
        if MAPS_subset in ['ENSTDkCl', 'ENSTDkAm']:

            # get metadata
            short_name = '_'.join(item[9:-4].split('_')[:-1])
            CPM_title = CPM_metadata_dict['short_name2title'][short_name]

            performance_id = 'R_' + str(performance_count + 1)
            composer = CPM_metadata_dict['title2piece'][CPM_title]['composer']
            piece_id = distinct_pieces_dict['composer_CPM_title2id']['_'.join([composer, CPM_title])]
            title = 'CPM_' + CPM_title
            source = 'MAPS'
            performance_audio_external = format_path(os.path.join('{MAPS}', MAPS_subset, 'MUS', item[:-4]+'.wav'))
            performance_MIDI_external = format_path(os.path.join('{A_MAPS}', item))
            MIDI_score_external = format_path(os.path.join('{A_MAPS}', item))  # same as performance MIDI
            folder = format_path(os.path.join('subset_R', composer, f'{piece_id}_{title}'.replace("'", '_')))
            performance_audio = f'{performance_id}_MAPS.wav'
            performance_MIDI = f'{performance_id}_A_MAPS_{short_name}_{MAPS_subset}.mid'
            MIDI_score = f'{performance_id}_A_MAPS_{short_name}_{MAPS_subset}.mid'  # same as performance MIDI
            split = 'testing'

            # update split in distinct_pieces_dict
            distinct_pieces_dict['id2piece'][piece_id]['split'] = split

            # update metadata_R
            metadata_R.loc[performance_count] = [
                performance_id,
                composer,
                piece_id,
                title,
                source,
                performance_audio_external,
                performance_MIDI_external,
                MIDI_score_external,
                folder,
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
            composer = row['composer']
            piece_id = distinct_pieces_dict['composer_ASAP_title2id']['_'.join([composer, ASAP_title])]
            title = 'ASAP_' + ASAP_title
            source = 'ASAP'
            performance_audio_external = format_path(os.path.join('{ASAP}', row['audio_performance']))
            performance_MIDI_external = format_path(os.path.join('{ASAP}', row['midi_performance']))
            MIDI_score_external = format_path(os.path.join('{ASAP}', row['midi_score']))
            folder = format_path(os.path.join('subset_R', composer, f'{piece_id}_{title}'.replace("'", '_')))
            performance_audio = f'{performance_id}_ASAP.wav'
            performance_MIDI = f'{performance_id}_ASAP.mid'
            MIDI_score = f'ASAP_{row["folder"].split("/")[-1]}.mid'
            split = distinct_pieces_dict['id2piece'][piece_id]['split']  # testing is the piece is already testing, update more testing later.

            # update metadata_R
            metadata_R.loc[performance_count] = [
                performance_id,
                composer,
                piece_id,
                title,
                source,
                performance_audio_external,
                performance_MIDI_external,
                MIDI_score_external,
                folder,
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
    ASAP_piece_id_testing_additional = set(random.sample(ASAP_piece_id_remaining, testing_amount - len(ASAP_piece_id_testing_cur)))
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
    # update split in distinct_pieces_dict
    for piece_id in distinct_pieces_dict['id2piece'].keys():
        if piece_id in ASAP_piece_id_testing_additional:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'testing'
        elif piece_id in ASAP_piece_id_validation:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'validation'
        elif piece_id in ASAP_piece_id_remaining:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'training'

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
    print('\ttotal:', (metadata_R['source'] == 'ASAP').sum())

    return distinct_pieces_dict, metadata_R
            
def create_synthetic_subset(distinct_pieces_dict, CPM_metadata_dict, args):
    print('Create Synthetic subset...')

    metadata_S = pd.DataFrame(columns=[
        'performance_id',  # "S_{number}"
        'composer',  # composer (or "Christmas")
        'piece_id',  # "{number}"
        'title',  # title of the piece
        'source',  # "MAPS", "ASAP" or "CPM"
        'performance_audio_external',  # path to the performance audio
        'performance_MIDI_external',  # path to the performance MIDI
        'MIDI_score_external',  # path to the MIDI score
        'folder',  # folder to the audio and MIDI files
        'performance_audio',  # path to the performance audio
        'performance_MIDI',  # path to the performance MIDI
        'MIDI_score',  # path to the MIDI score
        'split',  # training/validation/testing
    ])
    performance_count = 0

    ## MAPS Synthetic subsets
    A_MAPS_items = os.listdir(args.A_MAPS)
    A_MAPS_items.sort()
    for item in A_MAPS_items:
        MAPS_subset = item[9:-4].split('_')[-1]
        if MAPS_subset not in ['ENSTDkCl', 'ENSTDkAm']:

            # get metadata
            short_name = '_'.join(item[9:-4].split('_')[:-1])
            CPM_title = CPM_metadata_dict['short_name2title'][short_name]

            performance_id = 'S_' + str(performance_count + 1)
            composer = CPM_metadata_dict['title2piece'][CPM_title]['composer']
            piece_id = distinct_pieces_dict['composer_CPM_title2id']['_'.join([composer, CPM_title])]
            title = 'CPM_' + CPM_title
            source = 'MAPS'
            performance_audio_external = format_path(os.path.join('{MAPS}', MAPS_subset, 'MUS', item[:-4]+'.wav'))
            performance_MIDI_external = format_path(os.path.join('{A_MAPS}', item))
            MIDI_score_external = format_path(os.path.join('{A_MAPS}', item))  # same as performance MIDI
            folder = format_path(os.path.join('subset_S', composer, f'{piece_id}_{title}'.replace("'", '_')))
            performance_audio = f'{performance_id}_MAPS.wav'
            performance_MIDI = f'{performance_id}_A_MAPS_{short_name}_{MAPS_subset}.mid'
            MIDI_score = f'{performance_id}_A_MAPS_{short_name}_{MAPS_subset}.mid'  # same as performance MIDI
            split = distinct_pieces_dict['id2piece'][piece_id]['split']  # using the existing split first and update the empty ones later

            # update metadata_S
            metadata_S.loc[performance_count] = [
                performance_id,
                composer,
                piece_id,
                title,
                source,
                performance_audio_external,
                performance_MIDI_external,
                MIDI_score_external,
                folder,
                performance_audio,
                performance_MIDI,
                MIDI_score,
                split,
            ]
            performance_count += 1

    ## ASAP performance MIDIs
    metadata_ASAP = pd.read_csv(os.path.join(args.ASAP, 'metadata.csv'))
    for i, row in metadata_ASAP.iterrows():
        # get metadata
        ASAP_title = row['title']

        performance_id = 'S_' + str(performance_count + 1)
        composer = row['composer']
        piece_id = distinct_pieces_dict['composer_ASAP_title2id']['_'.join([composer, ASAP_title])]
        title = 'ASAP_' + ASAP_title
        source = 'ASAP'
        performance_audio_external = math.nan
        performance_MIDI_external = format_path(os.path.join('{ASAP}', row['midi_performance']))
        MIDI_score_external = format_path(os.path.join('{ASAP}', row['midi_score']))
        folder = format_path(os.path.join('subset_S', composer, f'{piece_id}_{title}'.replace("'", '_')))
        performance_audio = f'{performance_id}_Kontakt.wav'
        performance_MIDI = f'{performance_id}_ASAP.mid'
        MIDI_score = f'ASAP_{row["folder"].split("/")[-1]}.mid'
        split = distinct_pieces_dict['id2piece'][piece_id]['split']  # using the existing split first and update the empty ones later

        # update metadata_S
        metadata_S.loc[performance_count] = [
            performance_id,
            composer,
            piece_id,
            title,
            source,
            performance_audio_external,
            performance_MIDI_external,
            MIDI_score_external,
            folder,
            performance_audio,
            performance_MIDI,
            MIDI_score,
            split,
        ]
        performance_count += 1

    ## CPM performances
    for CPM_title, CPM_piece in CPM_metadata_dict['title2piece'].items():
        # get metadata
        performance_id = 'S_' + str(performance_count + 1)
        composer = CPM_piece['composer']
        piece_id = distinct_pieces_dict['composer_CPM_title2id']['_'.join([composer, CPM_title])]
        title = 'CPM_' + CPM_title
        source = 'CPM'
        performance_audio_external = math.nan
        performance_MIDI_external = format_path(os.path.join('{CPM}', CPM_piece['midi']))
        MIDI_score_external = format_path(os.path.join('{CPM}', CPM_piece['midi']))
        folder = format_path(os.path.join('subset_S', composer, f'{piece_id}_{title}'.replace("'", '_')))
        performance_audio = f'{performance_id}_Kontakt.wav'
        performance_MIDI = f'{performance_id}_CPM.mid'
        MIDI_score = f'{performance_id}_CPM.mid'  # same as performance midi
        split = distinct_pieces_dict['id2piece'][piece_id]['split']  # using the existing split first and update the empty ones later

        # update metadata_S
        metadata_S.loc[performance_count] = [
            performance_id,
            composer,
            piece_id,
            title,
            source,
            performance_audio_external,
            performance_MIDI_external,
            MIDI_score_external,
            folder,
            performance_audio,
            performance_MIDI,
            MIDI_score,
            split,
        ]
        performance_count += 1

    ## split into training/validation and testing
    piece_id_all = set(metadata_S.loc[:, 'piece_id'])
    # training/validation/testing amounts
    training_amount = len(piece_id_all) * 8 // 10
    validation_amount = len(piece_id_all) // 10
    testing_amount = len(piece_id_all) - training_amount - validation_amount

    # pieces already splitted
    piece_id_training_cur = set([piece_id for piece_id in piece_id_all if distinct_pieces_dict['id2piece'][piece_id]['split'] == 'training'])
    piece_id_validation_cur = set([piece_id for piece_id in piece_id_all if distinct_pieces_dict['id2piece'][piece_id]['split'] == 'validation'])
    piece_id_testing_cur = set([piece_id for piece_id in piece_id_all if distinct_pieces_dict['id2piece'][piece_id]['split'] == 'testing'])
    piece_id_remaining = piece_id_all - piece_id_training_cur - piece_id_validation_cur - piece_id_testing_cur
    # random select some other for testing
    if len(piece_id_testing_cur) < testing_amount:
        piece_id_testing_additional = set(random.sample(piece_id_remaining, testing_amount - len(piece_id_testing_cur)))
        piece_id_remaining -= piece_id_testing_additional
    else:
        piece_id_testing_additional = {}
    if len(piece_id_validation_cur) < validation_amount:
        piece_id_validation_additional = set(random.sample(piece_id_remaining, validation_amount - len(piece_id_validation_cur)))
        piece_id_remaining -= piece_id_validation_additional
    else:
        piece_id_validation_additional = {}
        
    # update split in metadata_S
    for i, row in metadata_S.iterrows():
        if type(row['split']) == float:
            if row['piece_id'] in piece_id_testing_additional:
                metadata_S.loc[i, 'split'] = 'testing'
            elif row['piece_id'] in piece_id_validation_additional:
                metadata_S.loc[i, 'split'] = 'validation'
            elif row['piece_id'] in piece_id_remaining:
                metadata_S.loc[i, 'split'] = 'training'
            else:
                print('check error!')
    # update split in distinct_pieces_dict
    for piece_id in distinct_pieces_dict['id2piece'].keys():
        if piece_id in piece_id_testing_additional:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'testing'
        elif piece_id in piece_id_validation_additional:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'validation'
        elif piece_id in piece_id_remaining:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'training'

    ## Allocate Kontakt Piano according to the training/validation/testing split
    for i, row in metadata_S.iterrows():
        if type(row['performance_audio_external']) == float:
            if row['split'] == 'testing':
                piano = random.choice(Kontakt_Pianos_all)
            else:
                piano = random.choice(Kontakt_Pianos_train)
            metadata_S.loc[i, 'performance_audio'] = row['performance_audio'][:-4] + '_' + piano + '.wav'

    ## subset statistics:
    print('\ttraining:', (metadata_S['split'] == 'training').sum())
    print('\tvalidation:', (metadata_S['split'] == 'validation').sum())
    print('\ttesting:', (metadata_S['split'] == 'testing').sum())
    print('\ttotal:', len(metadata_S))
    
    return distinct_pieces_dict, metadata_S

def copy_midi_files(metadata, subset, args):
    print('Copy midi files from external sources...')
    print(subset)

    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), end='\r')

        performance_MIDI_external = load_path(row['performance_MIDI_external']).format(A_MAPS=args.A_MAPS, CPM=args.CPM, ASAP=args.ASAP)
        MIDI_score_external = load_path(row['MIDI_score_external']).format(A_MAPS=args.A_MAPS, CPM=args.CPM, ASAP=args.ASAP)
        folder = load_path(row['folder'])
        performance_MIDI_internal = os.path.join(folder, row['performance_MIDI'])
        MIDI_score_internal = os.path.join(folder, row['MIDI_score'])
        
        mkdir(folder)
        if not os.path.exists(performance_MIDI_internal):
            subprocess.check_output(['cp', performance_MIDI_external, performance_MIDI_internal])
            time.sleep(0.02)
        if not os.path.exists(MIDI_score_internal):
            subprocess.check_output(['cp', MIDI_score_external, MIDI_score_internal])
            time.sleep(0.02)
    print()

def copy_audio_files(metadata, subset, args):
    print('Copy audio files from external sources...')
    print(subset)

    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), end='\r')

        if type(row['performance_audio_external']) == str:
            performance_audio_external = load_path(row['performance_audio_external']).format(MAPS=args.MAPS, ASAP=args.ASAP)
            folder = os.path.join('audio_files', load_path(row['folder']))
            performance_audio_internal = os.path.join(folder, row['performance_audio'])

            mkdir(folder)
            if not os.path.exists(performance_audio_internal):
                subprocess.check_output(['cp', performance_audio_external, performance_audio_internal])
                time.sleep(0.02)
    print()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--MAPS',
                        type=str,
                        default='/import/c4dm-01/MAPS_original',
                        help='Path to the MAPS dataset')
    parser.add_argument('--A_MAPS', 
                        type=str, 
                        default='C:\\Users\\Marco\\Downloads\\Datasets\\A-MAPS\\midi',
                        # default='/import/c4dm-datasets/A2S_transcription/A-MAPS_1.1/midi',
                        help='Path to the A_MAPS midi files')
    parser.add_argument('--CPM',
                        type=str,
                        default='C:\\Users\\Marco\\Downloads\\Datasets\\ClassicalPianoMIDI-dataset',
                        # default='/import/c4dm-datasets/A2S_transcription/working/ClassicalPianoMIDI-dataset',
                        help='Path to the Classical Piano MIDI dataset')
    parser.add_argument('--ASAP',
                        type=str,
                        default='C:\\Users\\Marco\\Downloads\\Datasets\\asap-dataset',
                        # default='/import/c4dm-datasets/ASAP_dataset/asap-dataset-1.1',
                        help='Path to the ASAP dataset')
    args = parser.parse_args()

    distinct_pieces_dict = get_distinct_pieces_dict()  # original distinct pieces are manually checked
    CPM_metadata_dict = get_CPM_metadata_dict(args)

    distinct_pieces_dict, metadata_R =  create_real_recording_subset(distinct_pieces_dict, CPM_metadata_dict, args)
    distinct_pieces_dict, metadata_S = create_synthetic_subset(distinct_pieces_dict, CPM_metadata_dict, args)

    metadata_R.to_csv('metadata_R.csv', index=False)
    metadata_S.to_csv('metadata_S.csv', index=False)
    
    update_distinct_pieces(distinct_pieces_dict)

    copy_midi_files(metadata_R, 'subset_R', args)
    copy_midi_files(metadata_S, 'subset_S', args)
    # copy_audio_files(metadata_R, 'subset_R', args)
    # copy_audio_files(metadata_S, 'subset_S', args)