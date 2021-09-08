import warnings
warnings.filterwarnings('ignore')
import os
import pandas as pd
import pretty_midi as pm
from collections import defaultdict



def all_files_exist(metadata):
    print('\nAll file exists?')
    for i, row in metadata.iterrows():
        performance_audio = os.path.join('audio_files', row['folder'], row['performance_audio'])
        performance_MIDI = os.path.join(row['folder'], row['performance_MIDI'])
        MIDI_score = os.path.join(row['folder'], row['MIDI_score'])
        performance_beat_annotation = os.path.join(row['folder'], row['performance_beat_annotation'])
        score_beat_annotation = os.path.join(row['folder'], row['score_beat_annotation'])

        for f in [performance_audio, 
                performance_MIDI,
                MIDI_score,
                performance_beat_annotation,
                score_beat_annotation]:
            if not os.path.exists(f):
                print('Nope.', row['performance_id'])
                return
    print('Yes!')

def MIDI_score_annotation_matched(metadata):
    print('\nMIDI score annotation matched?')
    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), end='\r')
        if row['source'] == 'ASAP':
            # raw annotation
            score_annotation = pd.read_csv(os.path.join(row['folder'], row['score_beat_annotation']), header=None, delimiter='\t')

            # beats from MIDI_score
            MIDI_score_file = os.path.join(row['folder'], row['MIDI_score'])
            midi_data = pm.PrettyMIDI(MIDI_score_file)
            beats = midi_data.get_beats()
            
            for beat in score_annotation.loc[:,0]:
                if min(abs(beats - beat)) > 0.01:
                    print('\nNope.', row['performance_id'])
                    return
    print('Yes!')

def two_hand_parts(metadata):
    print('\nTwo hand parts?')
    count_not_two_hand = 0
    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), 'Not two-hand count:', count_not_two_hand, end='\r')
        MIDI_score_file = os.path.join(row['folder'], row['MIDI_score'])
        midi_data = pm.PrettyMIDI(MIDI_score_file)

        if len(midi_data.instruments) != 2:
            print('\nNope.', row['performance_id'], 'source:', row['source'], 'hand parts:', len(midi_data.instruments))
            count_not_two_hand += 1

    if count_not_two_hand == 0:
        print('\nYes!')


if __name__ == '__main__':

    metadata_R = pd.read_csv('metadata_R.csv')
    metadata_S = pd.read_csv('metadata_S.csv')
    metadata = pd.concat([metadata_R, metadata_S], ignore_index=True)

    all_files_exist(metadata)
    MIDI_score_annotation_matched(metadata)
    two_hand_parts(metadata)