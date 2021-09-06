# Aligned Classical Piano Audio and Score (ACPAS) dataset

**ACPAS** is a dataset with aigned audio and scores for classical piano music. For each performance, we provide the corresponding **performance audio** (real recording or synthesized), **performance MIDI**, and **MIDI score**, together with **rhythm and key annotations**.

The dataset data is partly collected from a list of Automatic Music Transcription (AMT) datasets, and partly synthesized using [Native Instrument Kontakt Player](https://www.native-instruments.com/en/products/komplete/samplers/kontakt-6-player/).

List of source AMT datasets:
- MIDI Aligned Piano Sounds (MAPS) dataset
- [A-MAPS dataset](http://c4dm.eecs.qmul.ac.uk/ycart/a-maps.html)
- [Classical Piano MIDI (CPM) dataset](http://www.piano-midi.de/)
- [Aligned Scores and Performances (ASAP) dataset](https://github.com/fosfrancesco/asap-dataset)

In this document, we describe a piece of music composition as a **music piece**, a version of music score to the composition as a **music score**, and a music performance to a specific music score as a **music performance**. Thus, one music piece can have multiple versions of music scores (due to e.g. different repeats), and one music score can be mapped to multiple versions of music performances.

Due to different sources of data, the performances can be human performances (from the ASAP dataset) or hand-crafted tempos and dynamics to sound like human performances (from MAPS dataset and Classical Piano MIDI Page).

## Dataset Contents

**ACPAS** dataset is composed of a **Real recording subset** and a **Synthetic subset**.

### Real recording subset

This subset covers performances with real recordings from the MAPS "ENSTDkCl" and "ENSTDkAm" subsets and the MAESTRO dataset, in total **578 performances**. The corresponding MIDI scores and annotations are from the A-MAPS dataset and the ASAP dataset.

### Synthetic subset

This subset covers performances with synthetic audios from the following three sources, in total **1611 performances**:

1. Performance audio and MIDI from the MAPS synthetic subsets, and MIDI score from the A-MAPS dataset.
2. MIDI performance and score from the ASAP dataset, and audio files synthesized from performance MIDIs using [Native Instrument Kontakt Player](https://www.native-instruments.com/en/products/komplete/samplers/kontakt-6-player/).
3. MIDI performance and score from the CPM dataset, and audio files synthesized from performance MIDIs using Native Instrument Kontakt Player.

We make use of four different piano models provided in the Native Instrument Kontakt Player, and tune the piano font to be soft or hard. This end up with 8 different piano fonts. During synthesis, we add some level of reverberation to simulate real recordings. We reserve one piano model (both soft and hard fonts) to only be used for testing only. The other three piano models (6 fonts) are used for both training/validaton and testing sets.

## Dataset Statistics

The dataset is splitted into train/validation/test in a way that there is no overlap between pieces over the whole dataset. To keep in line with the MAPS and MAESTRO train/test split, we reserve all the MAPS real recording pieces and the testing pieces in MAESTRO-v2.0.0 to the test split. However, the training/validation split is randomly selected.

Below are the basic statistics of this dataset:

|     Subset     | Source |    Split   | Distinct Pieces | Performances | Duration (hours) |
|:--------------:|:------:|:----------:|:---------------:|:------------:|:----------------:|
| Real recording |  MAPS  |    test    |        52       |      59      |     4.277917     |
| Real recording |  ASAP  |    train   |        109      |      368     |     32.737423    |
| Real recording |  ASAP  | validation |        17       |      49      |     2.524508     |
| Real recording |  ASAP  |    test    |        44       |      102     |     9.420974     |
| Real recording |  Both  |    Total   |        215      |      578     |     48.960822    |
|                |        |            |                 |              |                  |
|    Synthetic   |   --   |    train   |        359      |     1155     |     94.958975    |
|    Synthetic   |   --   | validation |        49       |      135     |     8.669080     |
|    Synthetic   |   --   |    test    |        89       |      321     |     27.178842    |
|    Synthetic   |   --   |    Total   |        497      |     1611     |    130.806897    |
|                |        |            |                 |              |                  |
|      Both      |   --   |    train   |        359      |     1523     |    127.696398    |
|      Both      |   --   | validation |        49       |      184     |     11.193588    |
|      Both      |   --   |    test    |        89       |      482     |     40.877733    |
|      Both      |   --   |    Total   |        497      |     2189     |    179.767718    |

## Metadata

The dataset metadata is provided in three files:

- `distinct_pieces.csv` is a list of distinct pieces in this dataset, together with the allocated train/vadlidation/test split.
- `metadata_R.csv` provides the metadata for all the performances in the Real recording subset.
- `metadata_S.csv` provides the metadata for all the perofrmances in the Synthetic subset.

The parameters in the two `metadata_X.csv` file are:

- `performance_id`: The ID of the performance in this dataset. Performances from the Real recording subset have IDs starting with `R_` and those from the Synthetic subset have IDs starting with `S_`.
- `composer`: composer of the music piece.
- `piece_id`: ID of the corresponding music piece, this is in line with the piece ID provided in `distinct_pieces.csv`.
- `title`: title of the music pieces, in line with the title in `distinct_pieces.csv`.
- `source`: the source dataset of the performance, can be "MAPS", "ASAP" or "CPM".
- `performance_audio_external`: path to the performance audio in the source dataset.
- `performance_MIDI_external`: path to the performance MIDI in the source dataset.
- `MIDI_score_external`: path to the MIDI score in the source dataset.
- `performance_beat_annotation_external`: path to the performance beat annotation in the source dataset.
- `score_beat_annotation_external`: path to the score beat annotation in the source dataset.
- `folder`: folder to the audio, MIDI and annotation files.
- `performance_audio`: performance audio file.
- `performance_MIDI`: performance MIDI file.
- `MIDI_score`: MIDI score file.
- `aligned`: True if the performance and score are aligned.
- `performance_beat_annotation`:  performance beat annotation file.
- `score_beat_annotation`:  # score beat annotation file.
- `duration`: duration of the performance in seconds.
- `split`: train/validation/test split.

The corresponding files are provided in the following locations:

- `audio_files/{folder}/{performance_audio}`
- `{folder}/{performance_MIDI}`
- `{folder}/{MIDI_score}`
- `{folder}/{performance_beat_annotation}`
- `{folder}/{score_beat_annotation}`

## Reminders

This dataset is created for Audio-to-Score Transcription, however, the voice information in the MIDI socres is not checked and it's suggested not to use it as ground truth annotation.