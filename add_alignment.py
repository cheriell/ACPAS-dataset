###############################################################################
# This is the script to run for
# updating the dataset from v1.0 to v1.1
# 
# Updates:
# - Add performance-to-score alignment annotations for the ASAP pieces, using
#   the alignment toolbox in:
#       Eita Nakamura, Kazuyoshi Yoshii, Haruhiro Katayose
#       Performance Error Detection and Post-Processing for Fast and Accurate Symbolic Music Alignment
#       In Proc. ISMIR, pp. 347-353, 2017.
###############################################################################

from ctypes import alignment
import pandas as pd
import pretty_midi as pm
import numpy as np
import subprocess
from pathlib import Path


AlignmentTool = './../../tools/AlignmentTool/MIDIToMIDIAlign.sh'
resolution = 480
tolerance = 0.05


def segment_MIDI(row):
    print('>>> Segment MIDI files for performance: ' + row['performance_id'])
    annot_perfm_file = Path(row['folder'], row['performance_annotation'])
    annot_score_file = Path(row['folder'], row['score_annotation'])
    MIDI_perfm_file = Path(row['folder'], row['performance_MIDI'])
    MIDI_score_file = Path(row['folder'], row['MIDI_score'])

    annot_perfm = pd.read_csv(str(annot_perfm_file), sep='\t', header=None)
    annot_score = pd.read_csv(str(annot_score_file), sep='\t', header=None)
    MIDI_perfm = pm.PrettyMIDI(str(MIDI_perfm_file))
    MIDI_score = pm.PrettyMIDI(str(MIDI_score_file))

    beats_perfm = annot_perfm[0].tolist()
    beats_score = annot_score[0].tolist()
    cutpoints_perfm = np.array([-1] + beats_perfm + [MIDI_perfm.get_end_time()+1])
    cutpoints_score = np.array([-1] + beats_score + [MIDI_score.get_end_time()+1])
    N_segments = len(cutpoints_score) - 1
    
    perfm_midis = [pm.PrettyMIDI(resolution=resolution) for _ in range(N_segments)]
    score_midis = [pm.PrettyMIDI(resolution=resolution) for _ in range(N_segments)]

    print('Cut MIDI score')
    for inst_idx, inst in enumerate(MIDI_score.instruments):
        for seg_idx in range(N_segments):
            score_midis[seg_idx].instruments.append(pm.Instrument(program=inst.program, is_drum=inst.is_drum))

        for note in inst.notes:
            seg_idx = np.min(np.where(cutpoints_score >= note.start)) - 1

            # Move resolution ticks rightward
            start_tick = int(MIDI_score.time_to_tick(note.start) / MIDI_score.resolution * resolution + resolution)
            end_tick = int(MIDI_score.time_to_tick(note.end) / MIDI_score.resolution * resolution + resolution)

            score_midis[seg_idx].instruments[inst_idx].notes.append(pm.Note(
                pitch=note.pitch,
                start=score_midis[seg_idx].tick_to_time(start_tick),
                end=score_midis[seg_idx].tick_to_time(end_tick),
                velocity=note.velocity,
            ))

    print('Cut MIDI performance')
    for seg_idx in range(N_segments):
        perfm_midis[seg_idx].instruments.append(pm.Instrument(program=1, is_drum=False))

    for inst in MIDI_perfm.instruments:
        for note in inst.notes:
            seg_idx = np.min(np.where(cutpoints_perfm - note.start >= -tolerance)) - 1

            # Move resolution ticks rightward
            start = note.start + perfm_midis[seg_idx].tick_to_time(resolution)
            end = note.end + perfm_midis[seg_idx].tick_to_time(resolution)

            perfm_midis[seg_idx].instruments[0].notes.append(pm.Note(
                pitch=note.pitch,
                start=start,
                end=end,
                velocity=note.velocity,
            ))
    
    print('Write MIDI segments')
    for seg_idx in range(N_segments):
        print(f'write: {seg_idx}/{N_segments}', end='\r')
        
        # Add some notes in the beginning of each segment to help the alignment algorithm
        for p in range(4):
            perfm_midis[seg_idx].instruments[0].notes.append(pm.Note(
                pitch=p+60, 
                start=perfm_midis[seg_idx].tick_to_time(p*resolution//4), 
                end=perfm_midis[seg_idx].tick_to_time(p*resolution//4+resolution//4), 
                velocity=100)
            )
            score_midis[seg_idx].instruments[0].notes.append(pm.Note(
                pitch=p+60, 
                start=score_midis[seg_idx].tick_to_time(p*resolution//4),
                end=score_midis[seg_idx].tick_to_time(p*resolution//4+resolution//4),
                velocity=100)
            )

        # Write to MIDI files
        Path('temps', row['performance_id']).mkdir(exist_ok=True, parents=True)
        perfm_midi_file = str(Path('temps', row['performance_id'], 'perfm_seg_' + str(seg_idx) + '.mid'))
        score_midi_file = str(Path('temps', row['performance_id'], 'score_seg_' + str(seg_idx) + '.mid'))
        perfm_midis[seg_idx].write(perfm_midi_file)
        score_midis[seg_idx].write(score_midi_file)

def create_alignment_annotation(row):
    print('>>> Create alignment annotations for performance: ' + row['performance_id'])
    annot_perfm_file = Path(row['folder'], row['performance_annotation'])
    annot_perfm = pd.read_csv(str(annot_perfm_file), sep='\t', header=None)
    N_segments = len(annot_perfm) + 1

    # reference resolution ticks time shift applied when creating the segmented MIDI files
    ref_midi_data = pm.PrettyMIDI(resolution=resolution)
    ref_resolution_time = ref_midi_data.tick_to_time(resolution)

    alignment_annotation = pd.DataFrame(columns=['onset_perfm', 'pitch_perfm', 'velocity_perfm', 'onset_score', 'pitch_score', 'velocity_score'], data=[])
    alignment_annotation_file = Path(row['folder'], f'{row["performance_id"]}_{row["source"]}_align_annot.csv')

    for seg_idx in range(N_segments):
        print(f'align: {seg_idx}/{N_segments}', end='\r')
        perfm_midi_file = str(Path('temps', row['performance_id'], 'perfm_seg_' + str(seg_idx) + '.mid'))
        score_midi_file = str(Path('temps', row['performance_id'], 'score_seg_' + str(seg_idx) + '.mid'))

        # Align
        subprocess.check_output([AlignmentTool, score_midi_file[:-4], perfm_midi_file[:-4]])
        if Path('corresp.txt').exists():
            results_file = open('corresp.txt', 'r')
            results = results_file.readlines()[1:]

            for line in results:
                alignID, alignOntime, alignSitch, alignPitch, alignOnvel, refID, refOntime, refSitch, refPitch, refOnvel, _ = line.split('\t')
                alignOntime = float(alignOntime)
                alignPitch = int(alignPitch)
                alignOnvel = int(alignOnvel)
                refOntime = float(refOntime)
                refPitch = int(refPitch)
                refOnvel = int(refOnvel)

                if alignID == '*' or refID == '*' or alignOntime in ref_resolution_time * np.arange(4) / 4:
                    continue

                # Get original note
                perfm_pitch = alignPitch
                perfm_start = alignOntime - ref_resolution_time
                perfm_vel = alignOnvel
                score_pitch = refPitch
                score_start = refOntime - ref_resolution_time
                score_vel = refOnvel

                alignment_annotation.loc[len(alignment_annotation)] = [perfm_start, perfm_pitch, perfm_vel, score_start, score_pitch, score_vel]

        else:
            print('\nWARNING: alignment failed')
            print(f'Performance MIDI file: {perfm_midi_file}')
            print(f'Score MIDI file: {score_midi_file}')
            input('Press Enter to continue...')
    print()

    alignment_annotation.to_csv(str(alignment_annotation_file), sep=',', index=False, header=True)

def alignment_statistics(row):
    print('>>> Calculate alignment statistics for performance: ' + row['performance_id'])

    print('Get alignment statistics')
    MIDI_perfm_file = Path(row['folder'], row['performance_MIDI'])
    MIDI_score_file = Path(row['folder'], row['MIDI_score'])
    alignment_annotation_file = Path(row['folder'], f'{row["performance_id"]}_{row["source"]}_align_annot.csv')

    MIDI_perfm = pm.PrettyMIDI(str(MIDI_perfm_file))
    MIDI_score = pm.PrettyMIDI(str(MIDI_score_file))
    alignment_annotation = pd.read_csv(str(alignment_annotation_file), sep=',')

    N_notes_perfm = np.sum([len(instr.notes) for instr in MIDI_perfm.instruments])
    N_notes_score = np.sum([len(instr.notes) for instr in MIDI_score.instruments])
    N_notes_aligned = len(alignment_annotation)

    print(f'N_notes_perfm: {N_notes_perfm}')
    print(f'N_notes_score: {N_notes_score}')
    print(f'N_notes_aligned: {N_notes_aligned}')
    print(f'N_notes_aligned/N_notes_perfm: {N_notes_aligned/N_notes_perfm}')
    print(f'N_notes_aligned/N_notes_score: {N_notes_aligned/N_notes_score}')

    return {
        'performance_id': row['performance_id'],
        'aligned_notes_ratio_perfm': N_notes_aligned/N_notes_perfm,
        'aligned_notes_ratio_score': N_notes_aligned/N_notes_score,
    }

def update_metadata(metadata_R, metadata_S, stats):
    print('>>> Update metadata')

    if stats['performance_id'][0] == 'R':
        idx = metadata_R.index[metadata_R['performance_id'] == stats['performance_id']].tolist()[0]
        metadata_R.loc[idx, 'alignment_annotation'] = f'{stats["performance_id"]}_ASAP_align_annot.csv'
        metadata_R.loc[idx, 'aligned_notes_ratio_perfm'] = stats['aligned_notes_ratio_perfm']
        metadata_R.loc[idx, 'aligned_notes_ratio_score'] = stats['aligned_notes_ratio_score']
    elif stats['performance_id'][0] == 'S':
        idx = metadata_S.index[metadata_S['performance_id'] == stats['performance_id']].tolist()[0]
        metadata_S.loc[idx, 'alignment_annotation'] = f'{stats["performance_id"]}_ASAP_align_annot.csv'
        metadata_S.loc[idx, 'aligned_notes_ratio_perfm'] = stats['aligned_notes_ratio_perfm']
        metadata_S.loc[idx, 'aligned_notes_ratio_score'] = stats['aligned_notes_ratio_score']

if __name__ == "__main__":
    metadata_R = pd.read_csv('metadata_R.csv')
    metadata_S = pd.read_csv('metadata_S.csv')
    metadata = pd.concat([metadata_R, metadata_S], ignore_index=True)

    # Add new columns to metadata for alignment statistics
    for col in ['alignment_annotation', 'aligned_notes_ratio_perfm', 'aligned_notes_ratio_score']:
        metadata_R[col] = -1
        metadata_S[col] = -1

    for i, row in metadata.iterrows():
        if row['source'] == 'ASAP' and row['aligned'] == True:
            print('Processing performance: ' + row['performance_id'] + ' (' + str(i+1) + '/' + str(len(metadata)) + ')')

            segment_MIDI(row)
            create_alignment_annotation(row) # be careful we cannot use multiprocessing here, since we save the alignmentTool output to the same file.
            stats = alignment_statistics(row)
            update_metadata(metadata_R, metadata_S, stats)

    # Clean temporary files & save updated metadata
    subprocess.check_output(['rm', '-rf', 'temps'])
    metadata_R.to_csv('metadata_R_v1.1.csv', sep=',', index=False, header=True)
    metadata_S.to_csv('metadata_S_v1.1.csv', sep=',', index=False, header=True)