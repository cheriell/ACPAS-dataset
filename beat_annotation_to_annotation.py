import pandas as pd
import os
import subprocess
import time

# beat_annotation.csv to annotation.tsv

metadata_R = pd.read_csv('metadata_R.csv')
metadata_S = pd.read_csv('metadata_S.csv')
metadata = pd.concat([metadata_R, metadata_S], ignore_index=True)

for i, row in metadata.iterrows():
    print(i+1, '/', len(metadata), end='\r')
    annotation_file_perfm = '\\'.join(row['folder'].split('/') + [row['performance_beat_annotation']])
    annotation_file_score = '\\'.join(row['folder'].split('/') + [row['score_beat_annotation']])
    
    if os.path.exists(annotation_file_perfm):
        subprocess.check_output(['mv', annotation_file_perfm, annotation_file_perfm[:-19]+'annotation.tsv'])
    if os.path.exists(annotation_file_score):
        subprocess.check_output(['mv', annotation_file_score, annotation_file_score[:-19]+'annotation.tsv'])
    # time.sleep(0.05)