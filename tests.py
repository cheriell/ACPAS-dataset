import warnings
warnings.filterwarnings('ignore')
import os
import pandas as pd
import pretty_midi as pm
import numpy as np
import matplotlib.pyplot as plt
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
            print('\nNope.', row['performance_id'], 'source:', row['source'], 'split:', row['split'], 'hand parts:', len(midi_data.instruments))
            count_not_two_hand += 1

    if count_not_two_hand == 0:
        print('\nYes!')

def check_polyphony(metadata):
    print('\nCheck polyphony level.')

    polyphonys_with_pedal_list = []
    polyphonys_no_pedal_list = []
    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), end='\r')
        midi_data = pm.PrettyMIDI(os.path.join(row['folder'], row['performance_MIDI']))
        pianoroll_with_pedal = midi_data.get_piano_roll(pedal_threshold=64) > 0
        pianoroll_no_pedal = midi_data.get_piano_roll(pedal_threshold=128) > 0

        polyphonys_with_pedal = pianoroll_with_pedal.sum(axis=0)
        polyphonys_no_pedal = pianoroll_no_pedal.sum(axis=0)

        polyphonys_with_pedal_list.append(polyphonys_with_pedal)
        polyphonys_no_pedal_list.append(polyphonys_no_pedal)

    print()
    all_polyphonys_with_pedal = np.concatenate(polyphonys_with_pedal_list)
    all_polyphonys_no_pedal = np.concatenate(polyphonys_no_pedal_list)

    print('Stat', '\t\t', 'Max', '\t', 'Mean', '\t', 'Medium')
    print('with pedal', '\t', np.max(all_polyphonys_with_pedal), '\t', np.mean(all_polyphonys_with_pedal) // 0.01 / 100, '\t', np.median(all_polyphonys_with_pedal))
    print('no pedal', '\t', np.max(all_polyphonys_no_pedal), '\t', np.mean(all_polyphonys_no_pedal) // 0.01 / 100, '\t', np.median(all_polyphonys_no_pedal))

    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.hist(all_polyphonys_with_pedal)
    ax1.set_title('polyphony levels with pedal')
    ax2.hist(all_polyphonys_no_pedal)
    ax2.set_title('polyphony levels without pedal')
    fig.savefig('check_polyphony.pdf')

if __name__ == '__main__':

    metadata_R = pd.read_csv('metadata_R.csv')
    metadata_S = pd.read_csv('metadata_S.csv')
    metadata = pd.concat([metadata_R, metadata_S], ignore_index=True)

    # all_files_exist(metadata)
    # MIDI_score_annotation_matched(metadata)
    # two_hand_parts(metadata)
    check_polyphony(metadata)


### Output:

# Check polyphony level.
# 2189 / 2189
# Stat             Max     Mean    Medium
# with pedal       72      4.67    4.0
# no pedal         17      2.22    2.0