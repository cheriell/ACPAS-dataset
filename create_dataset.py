import warnings
warnings.filterwarnings('ignore')
import os
import sys
import argparse
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
random.seed(42)
import subprocess
import time
import pretty_midi as pm
import mido
from collections import defaultdict
import functools

from utilities import format_path, load_path, mkdir

Kontakt_Pianos_all = [
    'Gentleman_soft',
    'Gentleman_hard', 
    'Giant_soft',
    'Giant_hard',
    'Grandeur_soft',
    'Grandeur_hard', 
    'Maverick_soft',
    'Maverick_hard',
]
Kontakt_Pianos_train = Kontakt_Pianos_all[:6]
metadata_columns = [
    'performance_id',  # "R_{number}"
    'composer',  # composer (or "Christmas")
    'piece_id',  # "{number}"
    'title',  # title of the piece
    'source',  # "MAPS", "ASAP" or "CPM"
    'performance_audio_external',  # path to the external performance audio
    'performance_MIDI_external',  # path to the external performance MIDI
    'MIDI_score_external',  # path to the external MIDI score
    'performance_beat_annotation_external',  # path to the external performance beat annotation
    'score_beat_annotation_external',  # path to the external score beat annotation
    'folder',  # folder to the audio, MIDI and annotation files
    'performance_audio',  # performance audio file
    'performance_MIDI',  # performance MIDI file
    'MIDI_score',  # MIDI score file
    'aligned',  # if the performance and score are aligned
    'performance_beat_annotation',  # performance beat annotation file
    'score_beat_annotation',  # score beat annotation file
    'duration',  # duration of the performance in seconds
    'split',  # train/validation/test
]

def get_distinct_pieces_dict(args):
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

    # allocate pieces in the MAESTRO test set to test
    MAESTRO_metadata = pd.read_csv(os.path.join(args.MAESTRO, 'maestro-v2.0.0.csv'))
    ASAP_metadata = pd.read_csv(os.path.join(args.ASAP, 'metadata.csv'))

    maestro_midi_filename2split = dict([(row['midi_filename'], row['split']) for i, row in MAESTRO_metadata.iterrows()])
    for i, row in ASAP_metadata.iterrows():
        ASAP_title = row['title']
        maestro_midi_filename = row['maestro_midi_performance']

        if type(maestro_midi_filename) != float:
            maestro_split = maestro_midi_filename2split[maestro_midi_filename[10:]]

            if maestro_split == 'test':
                piece_id = distinct_pieces_dict['composer_ASAP_title2id']['_'.join([row['composer'], row['title']])]
                distinct_pieces_dict['id2piece'][piece_id]['split'] = 'test'

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

def create_real_recording_subset(distinct_pieces_dict, 
                                CPM_metadata_dict, 
                                args):
    print('\nCreate Real recording subset...')

    metadata_R = pd.DataFrame(columns=metadata_columns)
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
            performance_beat_annotation_external = math.nan
            score_beat_annotation_external = math.nan
            folder = format_path(os.path.join('subset_R', composer, f'{piece_id}_{title}'.replace("'", '_')))
            performance_audio = f'{performance_id}_MAPS.wav'
            performance_MIDI = f'{performance_id}_A_MAPS_{short_name}_{MAPS_subset}.mid'
            MIDI_score = f'{performance_id}_A_MAPS_{short_name}_{MAPS_subset}.mid'  # same as performance MIDI
            aligned = True
            performance_beat_annotation = f'{performance_id}_A_MAPS_beat_annotation.csv'
            score_beat_annotation = f'{performance_id}_A_MAPS_beat_annotation.csv'  # same as performance beat annotation
            duration = math.nan
            split = 'test'

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
                performance_beat_annotation_external,
                score_beat_annotation_external,
                folder,
                performance_audio,
                performance_MIDI,
                MIDI_score,
                aligned,
                performance_beat_annotation,
                score_beat_annotation,
                duration,
                split,
            ]
            performance_count += 1

    ## ASAP real recording tuples
    metadata_ASAP = pd.read_csv(os.path.join(args.ASAP, 'metadata.csv'))
    for i, row in metadata_ASAP.iterrows():
        if type(row['audio_performance']) == str:
            
            # get metadata
            ASAP_title = row['title']
            ASAP_performance_annotations = pd.read_csv(os.path.join(args.ASAP, load_path(row['performance_annotations'])), sep='\t', header=None)
            ASAP_midi_score_annotations = pd.read_csv(os.path.join(args.ASAP, load_path(row['midi_score_annotations'])), sep='\t', header=None)

            performance_id = 'R_' + str(performance_count + 1)
            composer = row['composer']
            piece_id = distinct_pieces_dict['composer_ASAP_title2id']['_'.join([composer, ASAP_title])]
            title = 'ASAP_' + ASAP_title
            source = 'ASAP'
            performance_audio_external = format_path(os.path.join('{ASAP}', row['audio_performance']))
            performance_MIDI_external = format_path(os.path.join('{ASAP}', row['midi_performance']))
            MIDI_score_external = format_path(os.path.join('{ASAP}', row['midi_score']))
            performance_beat_annotation_external = format_path(os.path.join('{ASAP}', row['performance_annotations']))
            score_beat_annotation_external = format_path(os.path.join('{ASAP}', row['midi_score_annotations']))
            folder = format_path(os.path.join('subset_R', composer, f'{piece_id}_{title}'.replace("'", '_')))
            performance_audio = f'{performance_id}_ASAP.wav'
            performance_MIDI = f'{performance_id}_ASAP.mid'
            MIDI_score = f'ASAP_{row["folder"].split("/")[-1]}.mid'
            aligned = ';'.join(ASAP_performance_annotations[2]) == ';'.join(ASAP_midi_score_annotations[2])
            performance_beat_annotation = f'{performance_id}_ASAP_beat_annotation.csv'
            score_beat_annotation = f'{MIDI_score[:-4]}_beat_annotation.csv'
            duration = math.nan
            split = distinct_pieces_dict['id2piece'][piece_id]['split']  # use existing split here, update later

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
                performance_beat_annotation_external,
                score_beat_annotation_external,
                folder,
                performance_audio,
                performance_MIDI,
                MIDI_score,
                aligned,
                performance_beat_annotation,
                score_beat_annotation,
                duration,
                split,
            ]
            performance_count += 1

    ## udpate train/validation/test split for ASAP real recording performances
    # all pieces from ASAP
    ASAP_piece_id_all = set([row['piece_id'] for i, row in metadata_R.iterrows() if row['source'] == 'ASAP'])
    # train/validation/test amounts
    train_amount = len(ASAP_piece_id_all) * 8 // 10
    validation_amount = len(ASAP_piece_id_all) // 10
    test_amount = len(ASAP_piece_id_all) - train_amount - validation_amount

    # pieces already split to test
    ASAP_piece_id_test_cur = set([piece_id for piece_id in ASAP_piece_id_all if distinct_pieces_dict['id2piece'][piece_id]['split'] == 'test'])
    ASAP_piece_id_remaining = ASAP_piece_id_all - ASAP_piece_id_test_cur
    # random select some other pieces for test
    if test_amount > len(ASAP_piece_id_test_cur):
        ASAP_piece_id_test_additional = set(random.sample(ASAP_piece_id_remaining, test_amount - len(ASAP_piece_id_test_cur)))
        ASAP_piece_id_remaining -= ASAP_piece_id_test_additional
    else:
        ASAP_piece_id_test_additional = {}
    # random select pieces for validation
    ASAP_piece_id_validation = set(random.sample(ASAP_piece_id_remaining, validation_amount))
    ASAP_piece_id_remaining -= ASAP_piece_id_validation

    # update split in metadata_R
    for i, row in metadata_R.iterrows():
        if type(row['split']) == float:
            if row['piece_id'] in ASAP_piece_id_test_additional:
                metadata_R.loc[i, 'split'] = 'test'
            elif row['piece_id'] in ASAP_piece_id_validation:
                metadata_R.loc[i, 'split'] = 'validation'
            elif row['piece_id'] in ASAP_piece_id_remaining:
                metadata_R.loc[i, 'split'] = 'train'
            else:
                print('check error!')
    # update split in distinct_pieces_dict
    for piece_id in distinct_pieces_dict['id2piece'].keys():
        if piece_id in ASAP_piece_id_test_additional:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'test'
        elif piece_id in ASAP_piece_id_validation:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'validation'
        elif piece_id in ASAP_piece_id_remaining:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'train'

    return distinct_pieces_dict, metadata_R
            
def create_synthetic_subset(distinct_pieces_dict, 
                            CPM_metadata_dict, 
                            args):
    print('\nCreate Synthetic subset...')

    metadata_S = pd.DataFrame(columns=metadata_columns)
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
            performance_beat_annotation_external = math.nan
            score_beat_annotation_external = math.nan
            folder = format_path(os.path.join('subset_S', composer, f'{piece_id}_{title}'.replace("'", '_')))
            performance_audio = f'{performance_id}_MAPS.wav'
            performance_MIDI = f'{performance_id}_A_MAPS_{short_name}_{MAPS_subset}.mid'
            MIDI_score = f'{performance_id}_A_MAPS_{short_name}_{MAPS_subset}.mid'  # same as performance MIDI
            aligned = True
            performance_beat_annotation = f'{performance_id}_A_MAPS_beat_annotation.csv'
            score_beat_annotation = f'{performance_id}_A_MAPS_beat_annotation.csv'  # same as performance beat annotation
            duration = math.nan
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
                performance_beat_annotation_external,
                score_beat_annotation_external,
                folder,
                performance_audio,
                performance_MIDI,
                MIDI_score,
                aligned,
                performance_beat_annotation,
                score_beat_annotation,
                duration,
                split,
            ]
            performance_count += 1

    ## ASAP performance MIDIs
    metadata_ASAP = pd.read_csv(os.path.join(args.ASAP, 'metadata.csv'))
    for i, row in metadata_ASAP.iterrows():
        # get metadata
        ASAP_title = row['title']
        ASAP_performance_annotations = pd.read_csv(os.path.join(args.ASAP, load_path(row['performance_annotations'])), sep='\t', header=None)
        ASAP_midi_score_annotations = pd.read_csv(os.path.join(args.ASAP, load_path(row['midi_score_annotations'])), sep='\t', header=None)

        performance_id = 'S_' + str(performance_count + 1)
        composer = row['composer']
        piece_id = distinct_pieces_dict['composer_ASAP_title2id']['_'.join([composer, ASAP_title])]
        title = 'ASAP_' + ASAP_title
        source = 'ASAP'
        performance_audio_external = math.nan
        performance_MIDI_external = format_path(os.path.join('{ASAP}', row['midi_performance']))
        MIDI_score_external = format_path(os.path.join('{ASAP}', row['midi_score']))
        performance_beat_annotation_external = format_path(os.path.join('{ASAP}', row['performance_annotations']))
        score_beat_annotation_external = format_path(os.path.join('{ASAP}', row['midi_score_annotations']))
        folder = format_path(os.path.join('subset_S', composer, f'{piece_id}_{title}'.replace("'", '_')))
        performance_audio = f'{performance_id}_Kontakt.wav'
        performance_MIDI = f'{performance_id}_ASAP.mid'
        MIDI_score = f'ASAP_{row["folder"].split("/")[-1]}.mid'
        aligned = ';'.join(ASAP_performance_annotations[2]) == ';'.join(ASAP_midi_score_annotations[2])
        performance_beat_annotation = f'{performance_id}_ASAP_beat_annotation.csv'
        score_beat_annotation = f'{MIDI_score[:-4]}_beat_annotation.csv'
        duration = math.nan
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
            performance_beat_annotation_external,
            score_beat_annotation_external,
            folder,
            performance_audio,
            performance_MIDI,
            MIDI_score,
            aligned,
            performance_beat_annotation,
            score_beat_annotation,
            duration,
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
        MIDI_score_external = format_path(os.path.join('{CPM}', CPM_piece['midi']))  # same as performance MIDI
        performance_beat_annotation_external = math.nan
        score_beat_annotation_external = math.nan
        folder = format_path(os.path.join('subset_S', composer, f'{piece_id}_{title}'.replace("'", '_')))
        performance_audio = f'{performance_id}_Kontakt.wav'
        performance_MIDI = f'{performance_id}_CPM.mid'
        MIDI_score = f'{performance_id}_CPM.mid'  # same as performance midi
        aligned = True
        performance_beat_annotation = f'{performance_id}_CPM_beat_annotation.csv'
        score_beat_annotation = f'{performance_id}_CPM_beat_annotation.csv'  # same as performance beat annotation
        duration = math.nan
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
            performance_beat_annotation_external,
            score_beat_annotation_external,
            folder,
            performance_audio,
            performance_MIDI,
            MIDI_score,
            aligned,
            performance_beat_annotation,
            score_beat_annotation,
            duration,
            split,
        ]
        performance_count += 1

    ## split into train/validation and test
    piece_id_all = set(metadata_S.loc[:, 'piece_id'])
    # train/validation/test amounts
    train_amount = len(piece_id_all) * 8 // 10
    validation_amount = len(piece_id_all) // 10
    test_amount = len(piece_id_all) - train_amount - validation_amount

    # pieces already splitted
    piece_id_train_cur = set([piece_id for piece_id in piece_id_all if distinct_pieces_dict['id2piece'][piece_id]['split'] == 'train'])
    piece_id_validation_cur = set([piece_id for piece_id in piece_id_all if distinct_pieces_dict['id2piece'][piece_id]['split'] == 'validation'])
    piece_id_test_cur = set([piece_id for piece_id in piece_id_all if distinct_pieces_dict['id2piece'][piece_id]['split'] == 'test'])
    piece_id_remaining = piece_id_all - piece_id_train_cur - piece_id_validation_cur - piece_id_test_cur
    # random select some other for test
    if len(piece_id_test_cur) < test_amount:
        piece_id_test_additional = set(random.sample(piece_id_remaining, test_amount - len(piece_id_test_cur)))
        piece_id_remaining -= piece_id_test_additional
    else:
        piece_id_test_additional = {}
    if len(piece_id_validation_cur) < validation_amount:
        piece_id_validation_additional = set(random.sample(piece_id_remaining, validation_amount - len(piece_id_validation_cur)))
        piece_id_remaining -= piece_id_validation_additional
    else:
        piece_id_validation_additional = {}
        
    # update split in metadata_S
    for i, row in metadata_S.iterrows():
        if type(row['split']) == float:
            if row['piece_id'] in piece_id_test_additional:
                metadata_S.loc[i, 'split'] = 'test'
            elif row['piece_id'] in piece_id_validation_additional:
                metadata_S.loc[i, 'split'] = 'validation'
            elif row['piece_id'] in piece_id_remaining:
                metadata_S.loc[i, 'split'] = 'train'
            else:
                print('check error!')
    # update split in distinct_pieces_dict
    for piece_id in distinct_pieces_dict['id2piece'].keys():
        if piece_id in piece_id_test_additional:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'test'
        elif piece_id in piece_id_validation_additional:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'validation'
        elif piece_id in piece_id_remaining:
            distinct_pieces_dict['id2piece'][piece_id]['split'] = 'train'

    ## Allocate Kontakt Piano according to the train/validation/test split
    for i, row in metadata_S.iterrows():
        if type(row['performance_audio_external']) == float:
            if row['split'] == 'test':
                piano = random.choice(Kontakt_Pianos_all)
            else:
                piano = random.choice(Kontakt_Pianos_train)
            metadata_S.loc[i, 'performance_audio'] = row['performance_audio'][:-4] + '_' + piano + '.wav'
    
    return distinct_pieces_dict, metadata_S

def copy_midi_files(metadata, subset, args):
    print('\nCopy midi files from external sources...', subset)

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

def update_performance_durations(metadata, subset):
    print('\nUpdate performance durations...', subset)

    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), end='\r')

        performance_MIDI_internal = os.path.join(load_path(row['folder']), row['performance_MIDI'])
        midi_data = pm.PrettyMIDI(performance_MIDI_internal)
        duration = midi_data.get_end_time()

        metadata.loc[i, 'duration'] = duration
    print()

    return metadata

def get_beat_annotations(metadata, subset, args):
    print('\nGet beat annotations...', subset)

    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), end='\r')

        performance_beat_annotation_internal = os.path.join(load_path(row['folder']), row['performance_beat_annotation'])
        score_beat_annotation_internal = os.path.join(load_path(row['folder']), row['score_beat_annotation'])

        if not os.path.exists(performance_beat_annotation_internal) or not os.path.exists(score_beat_annotation_internal):

            if row['source'] == 'ASAP':  # copy annotation files
                performance_beat_annotation_external = load_path(row['performance_beat_annotation_external']).format(ASAP=args.ASAP)
                score_beat_annotation_external = load_path(row['score_beat_annotation_external']).format(ASAP=args.ASAP)

                performance_beat_annotation = pd.read_csv(performance_beat_annotation_external, sep='\t', header=None)[[1, 2]]
                score_beat_annotation = pd.read_csv(score_beat_annotation_external, sep='\t', header=None)[[1, 2]]

                performance_beat_annotation.to_csv(performance_beat_annotation_internal, sep='\t', header=None, index=False)
                score_beat_annotation.to_csv(score_beat_annotation_internal, sep='\t', header=None, index=False)

            else:  # generate annotation files (performance MIDI and MIDI score are the same)
                MIDI_file = os.path.join(load_path(row['folder']), row['performance_MIDI'])
                midi_data = pm.PrettyMIDI(MIDI_file)

                beats = midi_data.get_beats()
                downbeats_set = set(midi_data.get_downbeats())
                time2timesig_change = defaultdict(str, dict([(ts.time, f'{ts.numerator}/{ts.denominator}') for ts in midi_data.time_signature_changes]))
                key_sharps2midoname = ['C',
                    'G', 'D', 'A', 'E', 'B', 'F#', 'C#m', 'G#m', 'D#m', 'Bbm', 'Fm',
                    'Gm', 'Dm', 'Am', 'Em', 'Bm', 'F#m', 'Db', 'Ab', 'Eb', 'Bb', 'F',
                ]
                key_num2midoname = [
                    'C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B',
                    'Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am',
                    'Bbm', 'Bm'
                ]
                def key_num2sharps(key_number):
                    s = key_sharps2midoname.index(key_num2midoname[key_number])
                    if s > 11:
                        s -= len(key_sharps2midoname)
                    return s
                time2keysig_change = defaultdict(str, dict([(ks.time, str(key_num2sharps(ks.key_number))) for ks in midi_data.key_signature_changes]))

                labels = []
                for beat in beats:
                    beat_label = 'b' if beat not in downbeats_set else 'db'
                    time_label = time2timesig_change[beat]
                    key_label = time2keysig_change[beat]
                    if key_label:
                        label = ','.join([beat_label, time_label, key_label])
                    elif time_label:
                        label = ','.join([beat_label, time_label])
                    else:
                        label = beat_label
                    labels.append(label)
                
                annotation_df = pd.DataFrame({1: list(beats), 2: labels})
                annotation_df.to_csv(performance_beat_annotation_internal, sep='\t', header=None, index=False)

    print()

def copy_audio_files(metadata, subset, args):
    print('\nCopy audio files from external sources...', subset)

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

def update_ASAP_score_annotations(metadata, subset, args):
    print('\nUpdate ASAP score annotations...', subset)

    def write_midi_with_tickmap(midi_data, tick2new, score_beat_annotations, beat_ticks, filename='test.mid'):
        
        def event_compare(event1, event2):
            secondary_sort = {
                'set_tempo': lambda e: (1 * 256 * 256),
                'time_signature': lambda e: (2 * 256 * 256),
                'key_signature': lambda e: (3 * 256 * 256),
                'lyrics': lambda e: (4 * 256 * 256),
                'text_events' :lambda e: (5 * 256 * 256),
                'program_change': lambda e: (6 * 256 * 256),
                'pitchwheel': lambda e: ((7 * 256 * 256) + e.pitch),
                'control_change': lambda e: (
                    (8 * 256 * 256) + (e.control * 256) + e.value),
                'note_off': lambda e: ((9 * 256 * 256) + (e.note * 256)),
                'note_on': lambda e: (
                    (10 * 256 * 256) + (e.note * 256) + e.velocity) if e.velocity > 0 
                    else ((9 * 256 * 256) + (e.note * 256)),
                'end_of_track': lambda e: (11 * 256 * 256)
            }
            if event1.time == event2.time and event1.type in secondary_sort and event2.type in secondary_sort:
                return secondary_sort[event1.type](event1) - secondary_sort[event2.type](event2)
            return event1.time - event2.time

        mid = mido.MidiFile(ticks_per_beat=midi_data.resolution)
        
        # track 0 with timing information
        timing_track = mido.MidiTrack()
        # add time signatures & key signatures
        time_signature_changes = [(row[0], row[2].split(',')[1]) for i, row in score_beat_annotations.iterrows() if len(row[2].split(',')) > 1 and row[2].split(',')[1] != '']
        for ts in time_signature_changes:
            timing_track.append(mido.MetaMessage('time_signature',
                                                time=int(tick2new[midi_data.time_to_tick(ts[0])]),
                                                numerator=int(ts[1].split('/')[0]),
                                                denominator=int(ts[1].split('/')[1])))
        key_sharps2name = ['C',
            'G', 'D', 'A', 'E', 'B', 'F#', 'C#m', 'G#m', 'D#m', 'Bbm', 'Fm',
            'Gm', 'Dm', 'Am', 'Em', 'Bm', 'F#m', 'Db', 'Ab', 'Eb', 'Bb', 'F',
        ]
        key_signature_changes = [(row[0], row[2].split(',')[2]) for i, row in score_beat_annotations.iterrows() if len(row[2].split(',')) == 3]
        for ks in key_signature_changes:
            timing_track.append(mido.MetaMessage('key_signature',
                                                time=int(tick2new[midi_data.time_to_tick(ks[0])]),
                                                key=key_sharps2name[int(ks[1])]))
        # add tempo changes
        for beat_index in range(len(beat_ticks)-1):
            gap_in_second = midi_data.tick_to_time(beat_ticks[beat_index+1]) - midi_data.tick_to_time(beat_ticks[beat_index])
            gap_in_ticknew = tick2new[beat_ticks[beat_index+1]] - tick2new[beat_ticks[beat_index]]
            tempo = gap_in_second * 1e6 / (gap_in_ticknew / midi_data.resolution)
            timing_track.append(mido.MetaMessage('set_tempo', 
                                                time=int(tick2new[beat_ticks[beat_index]]),
                                                tempo=int(tempo)))
        # sort events
        timing_track.sort(key=functools.cmp_to_key(event_compare))
        # add end of track event
        timing_track.append(mido.MetaMessage('end_of_track', time=timing_track[-1].time+1))
        # add track
        mid.tracks.append(timing_track)

        # add tracks
        channels = list(range(16))
        channels.remove(9)
        for ii, instrument in enumerate(midi_data.instruments):
            track = mido.MidiTrack()
            channel = channels[ii % len(channels)]
            # set the program number
            track.append(mido.Message('program_change', 
                                        time=0, 
                                        program=instrument.program,
                                        channel=channel))
            # add note events
            for note in instrument.notes:
                track.append(mido.Message('note_on', 
                                        time=int(tick2new[midi_data.time_to_tick(note.start)]),
                                        channel=channel,
                                        note=note.pitch,
                                        velocity=note.velocity))
                track.append(mido.Message('note_on',
                                        time=int(tick2new[midi_data.time_to_tick(note.end)]),
                                        channel=channel,
                                        note=note.pitch,
                                        velocity=0))
            # add control change events
            for cc in instrument.control_changes:
                track.append(mido.Message('control_change',
                                        time=int(tick2new[midi_data.time_to_tick(cc.time)]),
                                        channel=channel,
                                        control=cc.number,
                                        value=cc.value))
            # sort all the events
            track = sorted(track, key=functools.cmp_to_key(event_compare))
            # add end of track event
            track.append(mido.MetaMessage('end_of_track', time=track[-1].time+1))
            # add track
            mid.tracks.append(track)

        # ticks from absolute to relative
        for track in mid.tracks:
            tick = 0
            for event in track:
                event.time -= tick
                tick += event.time

        mid.save(filename=filename)

    updated = set()

    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), end='\r')

        if row['source'] == 'ASAP':
            if row['MIDI_score_external'] not in updated:
                # keep track of updated ones
                updated.add(row['MIDI_score_external'])

                # udpate annotations in MIDI_score
                MIDI_score_file = load_path(row['MIDI_score_external']).format(ASAP=args.ASAP)
                score_beat_annotation_file = load_path(row['score_beat_annotation_external']).format(ASAP=args.ASAP)

                midi_data = pm.PrettyMIDI(MIDI_score_file)
                score_beat_annotations = pd.read_csv(score_beat_annotation_file, header=None, sep='\t')

                # get ticks for beats in original MIDI_score
                beat_ticks = [midi_data.time_to_tick(beat) for beat in score_beat_annotations[0]]
                # add 0. for start, although tick 0 may not be a beat
                if beat_ticks[0] != 0.:
                    beat_ticks = [0] + beat_ticks
                # fill up missing beats in the beginning
                if beat_ticks[1] / (beat_ticks[2] - beat_ticks[1]) > 1.5:
                    ticks_insert = []
                    gap = beat_ticks[2] - beat_ticks[1]
                    tick_insert = beat_ticks[1] - gap
                    while tick_insert > gap * 0.2:
                        ticks_insert = [tick_insert] + ticks_insert
                        tick_insert -= gap
                    beat_ticks = [beat_ticks[0]] + ticks_insert + beat_ticks[1:]
                # add missing beats in the end
                max_tick = midi_data.time_to_tick(midi_data.get_end_time())
                gap = beat_ticks[-1] - beat_ticks[-2]
                while beat_ticks[-1] < max_tick:
                    beat_ticks.append(beat_ticks[-1] + gap)

                # get tick to new tick mapping
                tick2new = np.zeros(beat_ticks[-1]+1)  # float for now, round to int later
                tick2new[:beat_ticks[1]+1] = np.linspace(start=0, 
                                                        stop=midi_data.resolution * beat_ticks[1] / (beat_ticks[2] - beat_ticks[1]), 
                                                        num=beat_ticks[1]+1)
                for beat_index in range(1, len(beat_ticks)-1):
                    tick2new[beat_ticks[beat_index]:beat_ticks[beat_index+1]+1] = np.linspace(start=tick2new[beat_ticks[beat_index]], 
                                                        stop=tick2new[beat_ticks[beat_index]]+midi_data.resolution, 
                                                        num=beat_ticks[beat_index+1]-beat_ticks[beat_index]+1)
                
                # write midi events to MIDI object
                MIDI_score_file = os.path.join(load_path(row['folder']), row['MIDI_score'])
                write_midi_with_tickmap(midi_data, tick2new, score_beat_annotations, beat_ticks, filename=MIDI_score_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--MAPS',
                        type=str,
                        default='/import/c4dm-01/MAPS_original',
                        help='Path to the MAPS dataset')
    parser.add_argument('--A_MAPS', 
                        type=str, 
                        # default='C:\\Users\\Marco\\Downloads\\Datasets\\A-MAPS\\midi',
                        default='/import/c4dm-datasets/A2S_transcription/working/A-MAPS_1.1/midi',
                        help='Path to the A_MAPS midi files')
    parser.add_argument('--CPM',
                        type=str,
                        # default='C:\\Users\\Marco\\Downloads\\Datasets\\ClassicalPianoMIDI-dataset',
                        default='/import/c4dm-datasets/A2S_transcription/working/ClassicalPianoMIDI-dataset',
                        help='Path to the Classical Piano MIDI dataset')
    parser.add_argument('--ASAP',
                        type=str,
                        # default='C:\\Users\\Marco\\Downloads\\Datasets\\asap-dataset',
                        default='/import/c4dm-datasets/ASAP_dataset/asap-dataset-1.1',
                        help='Path to the ASAP dataset')
    parser.add_argument('--MAESTRO',
                        type=str,
                        # default='C:\\Users\\Marco\\Downloads\\Datasets\\maestro-v2.0.0',
                        default='/import/c4dm-datasets/maestro-v2.0.0',
                        help='Path to the MAESTRO-v2.0.0 dataset')
    args = parser.parse_args()

    # CPM_metadata_dict = get_CPM_metadata_dict(args)
    # distinct_pieces_dict = get_distinct_pieces_dict(args)  # original distinct pieces are manually checked

    # distinct_pieces_dict, metadata_R =  create_real_recording_subset(distinct_pieces_dict, 
    #                                                                 CPM_metadata_dict, 
    #                                                                 args)
    # distinct_pieces_dict, metadata_S = create_synthetic_subset(distinct_pieces_dict, 
    #                                                             CPM_metadata_dict, 
    #                                                             args)
    # update_distinct_pieces(distinct_pieces_dict)

    # ## get performance MIDIs and MIDI scores
    # copy_midi_files(metadata_R, 'Real recording subset', args)
    # copy_midi_files(metadata_S, 'Synthetic subset', args)

    # ## get durations and update metadata
    # metadata_R = update_performance_durations(metadata_R, 'Real recoding subset')
    # metadata_S = update_performance_durations(metadata_S, 'Synthetic subset')

    # ## save metadata
    # metadata_R.to_csv('metadata_R.csv', index=False)
    # metadata_S.to_csv('metadata_S.csv', index=False)

    # ## get beat annotations
    # get_beat_annotations(metadata_R, 'Real recording subset', args)
    # get_beat_annotations(metadata_S, 'Synthetic subset', args)

    # ## get performance audios
    metadata_R = pd.read_csv('metadata_R.csv')
    metadata_S = pd.read_csv('metadata_S.csv')
    copy_audio_files(metadata_R, 'Real recording subset', args)
    copy_audio_files(metadata_S, 'Synthetic subset', args)
    # # TODO: synthesize Kontakt audio files in reaper

    # ## update beat annotations in MIDI_score files
    # update_ASAP_score_annotations(metadata_R, 'Real recording subset', args)
    # update_ASAP_score_annotations(metadata_S, 'Synthetic subset', args)


