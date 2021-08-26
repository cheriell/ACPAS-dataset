import pandas as pd

A_MAPS_FOLDER = '~/Downloads/A-MAPS'


metadata_distinct_pieces = pd.read_csv('metadata_distinct_pieces.csv')

SongID2ASAPTitle, SongID2CPMTitle = {}, {}
ASAPTitle2SongID, CPMTitle2SongID = {}, {}

for i, row in metadata_distinct_pieces.iterrows():
    SongID2ASAPTitle
