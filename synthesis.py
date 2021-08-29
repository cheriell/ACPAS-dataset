import os
import argparse
import pandas as pd
import time
import pretty_midi as pm

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
            
            # rewrite midi files so they can be directly processed by reaper batch converter.
            if not os.path.exists(performance_MIDI_inbatch):
                midi_data_internal = pm.PrettyMIDI(performance_MIDI_internal)
                midi_data_inbatch = pm.PrettyMIDI()
                midi_data_inbatch.instruments.append(pm.Instrument(program=0, name='Piano'))

                for inst in midi_data_internal.instruments:
                    for note in inst.notes:
                        note_inbatch = pm.Note(velocity=note.velocity,
                                                pitch=note.pitch,
                                                start=note.start,
                                                end=note.end)
                        midi_data_inbatch.instruments[0].notes.append(note_inbatch)
                
                midi_data_inbatch.write(performance_MIDI_inbatch)
                time.sleep(0.02)
    print()

def copy_audio_files():
    print('Copy synthesized audio files to dataset...')



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--step',
                        type=int,
                        help='Select step. 1: prepare batches, 2: copy audio files')
    args = parser.parse_args()
    
    if args.step == 1:
        prepare_batches()
    elif args.step == 2:
        copy_audio_files()
    else:
        raise ValueError('Input Error! Check help!')