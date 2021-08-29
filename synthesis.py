import os
import argparse
import pandas as pd
import time
import pretty_midi as pm
import subprocess

from utilities import load_path, mkdir


def prepare_batches():
    print('Copy performance midis to batches...')

    metadata_S = pd.read_csv('metadata_S.csv')
    for i, row in metadata_S.iterrows():
        print(i+1, '/', len(metadata_S), end='\r')

        if type(row['performance_audio_external']) == float:
            performance_audio = row['performance_audio']
            piano = performance_audio[:-4].split('_Kontakt_')[1]

            performance_MIDI_internal = os.path.join(load_path(row['folder']), row['performance_MIDI'])
            performance_MIDI_inbatch = os.path.join('batches', piano, row['performance_MIDI'])
            
            # rewrite midi files so they can be directly processed by reaper batch converter.
            if not os.path.exists(performance_MIDI_inbatch):
                mkdir(os.path.split(performance_MIDI_inbatch)[0])

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

def distribute_audio_files():
    print('Distribute synthesized audio files into dataset...')

    metadata_S = pd.read_csv('metadata_S.csv')
    for i, row in metadata_S.iterrows():
        print(i+1, '/', len(metadata_S), end='\r')

        if type(row['performance_audio_external']) == float:
            performance_audio = row['performance_audio']
            piano = performance_audio[:-4].split('_Kontakt_')[1]

            performance_audio_internal = os.path.join('audio_files', load_path(row['folder']), performance_audio)
            performance_audio_inbatch = os.path.join('batches', piano, row['performance_MIDI'][:-4]+'.wav')

            if not os.path.exists(performance_audio_internal):
                mkdir(os.path.split(performance_audio_internal)[0])
                subprocess.check_output(['mv', performance_audio_inbatch, performance_audio_internal])
                time.sleep(0.02)
    print()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--step',
                        type=int,
                        help='Select step. 1: prepare batches, 2: distribute audio files')
    args = parser.parse_args()
    
    if args.step == 1:
        prepare_batches()
    elif args.step == 2:
        distribute_audio_files()
    else:
        raise ValueError('Input Error! Check help!')