import os
import subprocess
import pandas as pd
import time

from utilities import load_path


def prepare_batches():
    print('Copy performance midis to batches...')

    metadata_S = pd.read_csv('metadata_S.csv')
    for i, row in metadata_S.iterrows():
        print(i+1, '/', len(metadata_S), end='\r')

        if type(row['performance_audio_external']) == float:
            performance_audio = row['performance_audio']
            piano = performance_audio[:-4].split('_Kontakt_')[1]

            performance_MIDI_internal = os.path.join(load_path(row['folder']), row['performance_MIDI'])

            piano_folder = os.path.join('batches', piano)
            if not os.path.exists(piano_folder):
                os.makedirs(piano_folder)
            performance_MIDI_inbatch = os.path.join(piano_folder, row['performance_MIDI'])
            
            if not os.path.exists(performance_MIDI_inbatch):
                subprocess.check_output(['cp', performance_MIDI_internal, performance_MIDI_inbatch])
                time.sleep(0.02)
    print()


if __name__ == '__main__':
    
    prepare_batches()
