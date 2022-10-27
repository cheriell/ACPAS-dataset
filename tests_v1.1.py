import pretty_midi as pm
import pandas as pd
import os

ASAP = "/import/c4dm-05/ll307/datasets/asap-dataset-master"

###############################################################################
# QUESTION: Does ASAP scores have tempo change or not?
# CONCLUSION: there can be tempo changes in the middle of a score!
###############################################################################
def test_tempo_change():
    metadata_S = pd.read_csv('metadata_S.csv')
    metadata_R = pd.read_csv('metadata_R.csv')
    metadata = pd.concat([metadata_S, metadata_R], ignore_index=True)

    for i, row in metadata.iterrows():
        print(i, 'of', len(metadata), end='\r')
        if row['source'] != 'ASAP':
            continue
        
        midi_file = row['MIDI_score_external'].format(ASAP=ASAP)
        midi_data = pm.PrettyMIDI(midi_file)
        tempo_change_time, tempi = midi_data.get_tempo_changes()
        if len(tempo_change_time) > 1:
            print()
            print(row['MIDI_score_external'])
            print(tempo_change_time)
            print(tempi)
            print()

test_tempo_change()
