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

def validate_resolution(metadata, resolution=12):
    print('\nValidate resolution {}.'.format(resolution))

    def quantize_tick(tick, resolution_large, resolution_small):
        return round(tick // (resolution_large / resolution_small) * (resolution_large / resolution_small))

    def f_measure_pianoroll(output, target):
        output = output.astype(bool)
        target = target.astype(bool)

        TP = np.logical_and(output == True, target == True).sum()
        FP = np.logical_and(output == True, target == False).sum()
        FN = np.logical_and(output == False, target == True).sum()

        p = TP / (TP + FP + np.finfo(float).eps)
        r = TP / (TP + FN + np.finfo(float).eps)
        f = 2 * p * r / (p + r + np.finfo(float).eps)
        acc = TP / (TP + FP + FN + np.finfo(float).eps)
        
        return p, r, f, acc

    evals = []
    for ri, row in metadata.iterrows():
        print(ri+1, '/', len(metadata), end='\r')
        midi_data = pm.PrettyMIDI(os.path.join(row['folder'], row['MIDI_score']))
        pianoroll_orig = midi_data.get_piano_roll(pedal_threshold=128) > 0  # original pianoroll without pedal

        # quantize tick by resolution
        for inst in midi_data.instruments:
            short_notes_indexes = []
            for i, note in enumerate(inst.notes):
                
                note.start = midi_data.tick_to_time(quantize_tick(midi_data.time_to_tick(note.start), midi_data.resolution, resolution))
                note.end = midi_data.tick_to_time(quantize_tick(midi_data.time_to_tick(note.end), midi_data.resolution, resolution))
                if note.start >= note.end:
                    short_notes_indexes.append(i)
            
            for i in short_notes_indexes[::-1]:
                del inst.notes[i]
        pianoroll_quan = midi_data.get_piano_roll(pedal_threshold=128) > 0  # quantized pianoroll without pedal

        length = max(pianoroll_orig.shape[1], pianoroll_quan.shape[1])
        pianoroll_orig = np.concatenate([pianoroll_orig, np.zeros((128, length-pianoroll_orig.shape[1]), dtype=bool)], axis=1)
        pianoroll_quan = np.concatenate([pianoroll_quan, np.zeros((128, length-pianoroll_quan.shape[1]), dtype=bool)], axis=1)
        p, r, f, acc = f_measure_pianoroll(pianoroll_quan, pianoroll_orig)
        evals.append((p, r, f, acc))

    evals = list(zip(*evals))
    print('\nPrecision\tRecall\tF-measure\tAccuracy')
    print('{:.2f}\t\t{:.2f}\t{:.2f}\t\t{:.2f}'.format(np.mean(evals[0]), np.mean(evals[1]), np.mean(evals[2]), np.mean(evals[3])))

def check_beat_annotation_sorted(metadata):
    print('\nCheck is beat annotation sorted?')

    all_sorted = True
    for i, row in metadata.iterrows():
        print(i+1, '/', len(metadata), end='\r')

        beat_annotation_perfm = pd.read_csv(os.path.join(row['folder'], row['performance_beat_annotation']), header=None, sep='\t')
        beat_annotation_score = pd.read_csv(os.path.join(row['folder'], row['score_beat_annotation']), header=None, sep='\t')

        beats_perfm = np.array(beat_annotation_perfm[0])
        beats_score = np.array(beat_annotation_score[0])

        if min(beats_perfm[1:] - beats_perfm[:-1]) < 0:
            print('\n performance beats not sorted! performance_id: {}, aligned: {}'.format(row['performance_id'], row['aligned']))
            all_sorted = False
        if min(beats_score[1:] - beats_score[:-1]) < 0:
            print('\n score beats not sorted! performance_id: {}, aligned: {}'.format(row['performance_id'], row['aligned']))
            all_sorted = False

    if all_sorted:
        print('\nYes!')
    else:
        print('\nNope!')

if __name__ == '__main__':

    metadata_R = pd.read_csv('metadata_R.csv')
    metadata_S = pd.read_csv('metadata_S.csv')
    metadata = pd.concat([metadata_R, metadata_S], ignore_index=True)

    # all_files_exist(metadata)
    # MIDI_score_annotation_matched(metadata)
    # two_hand_parts(metadata)
    # check_polyphony(metadata)
    # validate_resolution(metadata, resolution=24)
    check_beat_annotation_sorted(metadata)

### Output:

# Two hand parts?
# 22 / 2189 Not two-hand: 0
# Nope. R_22 source: MAPS hand parts: 3
# 27 / 2189 Not two-hand: 1
# Nope. R_27 source: MAPS hand parts: 3
# 39 / 2189 Not two-hand: 2
# Nope. R_39 source: MAPS hand parts: 4
# 502 / 2189 Not two-hand: 3
# Nope. R_502 source: ASAP hand parts: 3
# 503 / 2189 Not two-hand: 4
# Nope. R_503 source: ASAP hand parts: 3
# 504 / 2189 Not two-hand: 5
# Nope. R_504 source: ASAP hand parts: 3
# 505 / 2189 Not two-hand: 6
# Nope. R_505 source: ASAP hand parts: 3
# 569 / 2189 Not two-hand: 7
# Nope. R_569 source: ASAP hand parts: 1
# 573 / 2189 Not two-hand: 8
# Nope. R_573 source: ASAP hand parts: 3
# 574 / 2189 Not two-hand: 9
# Nope. R_574 source: ASAP hand parts: 3
# 575 / 2189 Not two-hand: 10
# Nope. R_575 source: ASAP hand parts: 3
# 576 / 2189 Not two-hand: 11
# Nope. R_576 source: ASAP hand parts: 3
# 577 / 2189 Not two-hand: 12
# Nope. R_577 source: ASAP hand parts: 3
# 578 / 2189 Not two-hand: 13
# Nope. R_578 source: ASAP hand parts: 3
# 597 / 2189 Not two-hand: 14
# Nope. S_19 source: MAPS hand parts: 10
# 598 / 2189 Not two-hand: 15
# Nope. S_20 source: MAPS hand parts: 10
# 599 / 2189 Not two-hand: 16
# Nope. S_21 source: MAPS hand parts: 5
# 600 / 2189 Not two-hand: 17
# Nope. S_22 source: MAPS hand parts: 5
# 601 / 2189 Not two-hand: 18
# Nope. S_23 source: MAPS hand parts: 5
# 602 / 2189 Not two-hand: 19
# Nope. S_24 source: MAPS hand parts: 6
# 654 / 2189 Not two-hand: 20
# Nope. S_76 source: MAPS hand parts: 3
# 655 / 2189 Not two-hand: 21
# Nope. S_77 source: MAPS hand parts: 3
# 690 / 2189 Not two-hand: 22
# Nope. S_112 source: MAPS hand parts: 4
# 696 / 2189 Not two-hand: 23
# Nope. S_118 source: MAPS hand parts: 3
# 697 / 2189 Not two-hand: 24
# Nope. S_119 source: MAPS hand parts: 3
# 698 / 2189 Not two-hand: 25
# Nope. S_120 source: MAPS hand parts: 3
# 708 / 2189 Not two-hand: 26
# Nope. S_130 source: MAPS hand parts: 3
# 709 / 2189 Not two-hand: 27
# Nope. S_131 source: MAPS hand parts: 3
# 714 / 2189 Not two-hand: 28
# Nope. S_136 source: MAPS hand parts: 3
# 785 / 2189 Not two-hand: 29
# Nope. S_207 source: MAPS hand parts: 3
# 1671 / 2189 Not two-hand: 30
# Nope. S_1093 source: ASAP hand parts: 3
# 1672 / 2189 Not two-hand: 31
# Nope. S_1094 source: ASAP hand parts: 3
# 1673 / 2189 Not two-hand: 32
# Nope. S_1095 source: ASAP hand parts: 3
# 1674 / 2189 Not two-hand: 33
# Nope. S_1096 source: ASAP hand parts: 3
# 1675 / 2189 Not two-hand: 34
# Nope. S_1097 source: ASAP hand parts: 3
# 1676 / 2189 Not two-hand: 35
# Nope. S_1098 source: ASAP hand parts: 3
# 1677 / 2189 Not two-hand: 36
# Nope. S_1099 source: ASAP hand parts: 3
# 1678 / 2189 Not two-hand: 37
# Nope. S_1100 source: ASAP hand parts: 3
# 1679 / 2189 Not two-hand: 38
# Nope. S_1101 source: ASAP hand parts: 3
# 1680 / 2189 Not two-hand: 39
# Nope. S_1102 source: ASAP hand parts: 3
# 1681 / 2189 Not two-hand: 40
# Nope. S_1103 source: ASAP hand parts: 3
# 1728 / 2189 Not two-hand: 41
# Nope. S_1150 source: ASAP hand parts: 3
# 1729 / 2189 Not two-hand: 42
# Nope. S_1151 source: ASAP hand parts: 3
# 1730 / 2189 Not two-hand: 43
# Nope. S_1152 source: ASAP hand parts: 3
# 1731 / 2189 Not two-hand: 44
# Nope. S_1153 source: ASAP hand parts: 3
# 1732 / 2189 Not two-hand: 45
# Nope. S_1154 source: ASAP hand parts: 3
# 1733 / 2189 Not two-hand: 46
# Nope. S_1155 source: ASAP hand parts: 3
# 1734 / 2189 Not two-hand: 47
# Nope. S_1156 source: ASAP hand parts: 3
# 1816 / 2189 Not two-hand: 48
# Nope. S_1238 source: ASAP hand parts: 1
# 1843 / 2189 Not two-hand: 49
# Nope. S_1265 source: ASAP hand parts: 3
# 1844 / 2189 Not two-hand: 50
# Nope. S_1266 source: ASAP hand parts: 3
# 1845 / 2189 Not two-hand: 51
# Nope. S_1267 source: ASAP hand parts: 3
# 1846 / 2189 Not two-hand: 52
# Nope. S_1268 source: ASAP hand parts: 3
# 1847 / 2189 Not two-hand: 53
# Nope. S_1269 source: ASAP hand parts: 3
# 1848 / 2189 Not two-hand: 54
# Nope. S_1270 source: ASAP hand parts: 3
# 1849 / 2189 Not two-hand: 55
# Nope. S_1271 source: ASAP hand parts: 3
# 1850 / 2189 Not two-hand: 56
# Nope. S_1272 source: ASAP hand parts: 3
# 1851 / 2189 Not two-hand: 57
# Nope. S_1273 source: ASAP hand parts: 3
# 1852 / 2189 Not two-hand: 58
# Nope. S_1274 source: ASAP hand parts: 3
# 1867 / 2189 Not two-hand: 59
# Nope. S_1289 source: CPM hand parts: 6
# 1868 / 2189 Not two-hand: 60
# Nope. S_1290 source: CPM hand parts: 5
# 1869 / 2189 Not two-hand: 61
# Nope. S_1291 source: CPM hand parts: 6
# 1875 / 2189 Not two-hand: 62
# Nope. S_1297 source: CPM hand parts: 4
# 1881 / 2189 Not two-hand: 63
# Nope. S_1303 source: CPM hand parts: 3
# 1886 / 2189 Not two-hand: 64
# Nope. S_1308 source: CPM hand parts: 3
# 1908 / 2189 Not two-hand: 65
# Nope. S_1330 source: CPM hand parts: 3
# 1933 / 2189 Not two-hand: 66
# Nope. S_1355 source: CPM hand parts: 3
# 1948 / 2189 Not two-hand: 67
# Nope. S_1370 source: CPM hand parts: 3
# 1949 / 2189 Not two-hand: 68
# Nope. S_1371 source: CPM hand parts: 3
# 1969 / 2189 Not two-hand: 69
# Nope. S_1391 source: CPM hand parts: 3
# 2014 / 2189 Not two-hand: 70
# Nope. S_1436 source: CPM hand parts: 3
# 2043 / 2189 Not two-hand: 71
# Nope. S_1465 source: CPM hand parts: 4
# 2045 / 2189 Not two-hand: 72
# Nope. S_1467 source: CPM hand parts: 4
# 2050 / 2189 Not two-hand: 73
# Nope. S_1472 source: CPM hand parts: 4
# 2057 / 2189 Not two-hand: 74
# Nope. S_1479 source: CPM hand parts: 3
# 2059 / 2189 Not two-hand: 75
# Nope. S_1481 source: CPM hand parts: 3
# 2065 / 2189 Not two-hand: 76
# Nope. S_1487 source: CPM hand parts: 3
# 2076 / 2189 Not two-hand: 77
# Nope. S_1498 source: CPM hand parts: 3
# 2097 / 2189 Not two-hand: 78
# Nope. S_1519 source: CPM hand parts: 3
# 2104 / 2189 Not two-hand: 79
# Nope. S_1526 source: CPM hand parts: 4
# 2113 / 2189 Not two-hand: 80
# Nope. S_1535 source: CPM hand parts: 3
# 2114 / 2189 Not two-hand: 81
# Nope. S_1536 source: CPM hand parts: 3
# 2117 / 2189 Not two-hand: 82
# Nope. S_1539 source: CPM hand parts: 3
# 2189 / 2189 Not two-hand: 83
# Nope!

# Check polyphony level.
# 2189 / 2189
# Stat             Max     Mean    Medium
# with pedal       72      4.67    4.0
# no pedal         17      2.22    2.0

# Validate resolution 12.
# Precision       Recall  F-measure       Accuracy
# 0.99            0.87    0.92            0.86

# Validate resolution 16.
# Precision       Recall  F-measure       Accuracy
# 0.99            0.90    0.94            0.90

# Validate resolution 24.
# 2189 / 2189
# Precision       Recall  F-measure       Accuracy
# 1.00            0.94    0.96            0.93

# Check is beat annotation sorted?
# 2189 / 2189
# Yes!