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

- This dataset is created for Audio-to-Score Transcription, however, the voice information in the MIDI socres is not checked and it's suggested not to use it as ground truth annotation.
- there are 83 performances in total whose hand part is not equal to 2 (range from 1 to 10 parts).
- 30 performances are not aligned with the corresponding score. This is because of some errors made during the performance.

## Test output

Two hand parts?
22 / 2189 Not two-hand: 0
Nope. R_22 source: MAPS hand parts: 3
27 / 2189 Not two-hand: 1
Nope. R_27 source: MAPS hand parts: 3
39 / 2189 Not two-hand: 2
Nope. R_39 source: MAPS hand parts: 4
502 / 2189 Not two-hand: 3
Nope. R_502 source: ASAP hand parts: 3
503 / 2189 Not two-hand: 4
Nope. R_503 source: ASAP hand parts: 3
504 / 2189 Not two-hand: 5
Nope. R_504 source: ASAP hand parts: 3
505 / 2189 Not two-hand: 6
Nope. R_505 source: ASAP hand parts: 3
569 / 2189 Not two-hand: 7
Nope. R_569 source: ASAP hand parts: 1
573 / 2189 Not two-hand: 8
Nope. R_573 source: ASAP hand parts: 3
574 / 2189 Not two-hand: 9
Nope. R_574 source: ASAP hand parts: 3
575 / 2189 Not two-hand: 10
Nope. R_575 source: ASAP hand parts: 3
576 / 2189 Not two-hand: 11
Nope. R_576 source: ASAP hand parts: 3
577 / 2189 Not two-hand: 12
Nope. R_577 source: ASAP hand parts: 3
578 / 2189 Not two-hand: 13
Nope. R_578 source: ASAP hand parts: 3
597 / 2189 Not two-hand: 14
Nope. S_19 source: MAPS hand parts: 10
598 / 2189 Not two-hand: 15
Nope. S_20 source: MAPS hand parts: 10
599 / 2189 Not two-hand: 16
Nope. S_21 source: MAPS hand parts: 5
600 / 2189 Not two-hand: 17
Nope. S_22 source: MAPS hand parts: 5
601 / 2189 Not two-hand: 18
Nope. S_23 source: MAPS hand parts: 5
602 / 2189 Not two-hand: 19
Nope. S_24 source: MAPS hand parts: 6
654 / 2189 Not two-hand: 20
Nope. S_76 source: MAPS hand parts: 3
655 / 2189 Not two-hand: 21
Nope. S_77 source: MAPS hand parts: 3
690 / 2189 Not two-hand: 22
Nope. S_112 source: MAPS hand parts: 4
696 / 2189 Not two-hand: 23
Nope. S_118 source: MAPS hand parts: 3
697 / 2189 Not two-hand: 24
Nope. S_119 source: MAPS hand parts: 3
698 / 2189 Not two-hand: 25
Nope. S_120 source: MAPS hand parts: 3
708 / 2189 Not two-hand: 26
Nope. S_130 source: MAPS hand parts: 3
709 / 2189 Not two-hand: 27
Nope. S_131 source: MAPS hand parts: 3
714 / 2189 Not two-hand: 28
Nope. S_136 source: MAPS hand parts: 3
785 / 2189 Not two-hand: 29
Nope. S_207 source: MAPS hand parts: 3
1671 / 2189 Not two-hand: 30
Nope. S_1093 source: ASAP hand parts: 3
1672 / 2189 Not two-hand: 31
Nope. S_1094 source: ASAP hand parts: 3
1673 / 2189 Not two-hand: 32
Nope. S_1095 source: ASAP hand parts: 3
1674 / 2189 Not two-hand: 33
Nope. S_1096 source: ASAP hand parts: 3
1675 / 2189 Not two-hand: 34
Nope. S_1097 source: ASAP hand parts: 3
1676 / 2189 Not two-hand: 35
Nope. S_1098 source: ASAP hand parts: 3
1677 / 2189 Not two-hand: 36
Nope. S_1099 source: ASAP hand parts: 3
1678 / 2189 Not two-hand: 37
Nope. S_1100 source: ASAP hand parts: 3
1679 / 2189 Not two-hand: 38
Nope. S_1101 source: ASAP hand parts: 3
1680 / 2189 Not two-hand: 39
Nope. S_1102 source: ASAP hand parts: 3
1681 / 2189 Not two-hand: 40
Nope. S_1103 source: ASAP hand parts: 3
1728 / 2189 Not two-hand: 41
Nope. S_1150 source: ASAP hand parts: 3
1729 / 2189 Not two-hand: 42
Nope. S_1151 source: ASAP hand parts: 3
1730 / 2189 Not two-hand: 43
Nope. S_1152 source: ASAP hand parts: 3
1731 / 2189 Not two-hand: 44
Nope. S_1153 source: ASAP hand parts: 3
1732 / 2189 Not two-hand: 45
Nope. S_1154 source: ASAP hand parts: 3
1733 / 2189 Not two-hand: 46
Nope. S_1155 source: ASAP hand parts: 3
1734 / 2189 Not two-hand: 47
Nope. S_1156 source: ASAP hand parts: 3
1816 / 2189 Not two-hand: 48
Nope. S_1238 source: ASAP hand parts: 1
1843 / 2189 Not two-hand: 49
Nope. S_1265 source: ASAP hand parts: 3
1844 / 2189 Not two-hand: 50
Nope. S_1266 source: ASAP hand parts: 3
1845 / 2189 Not two-hand: 51
Nope. S_1267 source: ASAP hand parts: 3
1846 / 2189 Not two-hand: 52
Nope. S_1268 source: ASAP hand parts: 3
1847 / 2189 Not two-hand: 53
Nope. S_1269 source: ASAP hand parts: 3
1848 / 2189 Not two-hand: 54
Nope. S_1270 source: ASAP hand parts: 3
1849 / 2189 Not two-hand: 55
Nope. S_1271 source: ASAP hand parts: 3
1850 / 2189 Not two-hand: 56
Nope. S_1272 source: ASAP hand parts: 3
1851 / 2189 Not two-hand: 57
Nope. S_1273 source: ASAP hand parts: 3
1852 / 2189 Not two-hand: 58
Nope. S_1274 source: ASAP hand parts: 3
1867 / 2189 Not two-hand: 59
Nope. S_1289 source: CPM hand parts: 6
1868 / 2189 Not two-hand: 60
Nope. S_1290 source: CPM hand parts: 5
1869 / 2189 Not two-hand: 61
Nope. S_1291 source: CPM hand parts: 6
1875 / 2189 Not two-hand: 62
Nope. S_1297 source: CPM hand parts: 4
1881 / 2189 Not two-hand: 63
Nope. S_1303 source: CPM hand parts: 3
1886 / 2189 Not two-hand: 64
Nope. S_1308 source: CPM hand parts: 3
1908 / 2189 Not two-hand: 65
Nope. S_1330 source: CPM hand parts: 3
1933 / 2189 Not two-hand: 66
Nope. S_1355 source: CPM hand parts: 3
1948 / 2189 Not two-hand: 67
Nope. S_1370 source: CPM hand parts: 3
1949 / 2189 Not two-hand: 68
Nope. S_1371 source: CPM hand parts: 3
1969 / 2189 Not two-hand: 69
Nope. S_1391 source: CPM hand parts: 3
2014 / 2189 Not two-hand: 70
Nope. S_1436 source: CPM hand parts: 3
2043 / 2189 Not two-hand: 71
Nope. S_1465 source: CPM hand parts: 4
2045 / 2189 Not two-hand: 72
Nope. S_1467 source: CPM hand parts: 4
2050 / 2189 Not two-hand: 73
Nope. S_1472 source: CPM hand parts: 4
2057 / 2189 Not two-hand: 74
Nope. S_1479 source: CPM hand parts: 3
2059 / 2189 Not two-hand: 75
Nope. S_1481 source: CPM hand parts: 3
2065 / 2189 Not two-hand: 76
Nope. S_1487 source: CPM hand parts: 3
2076 / 2189 Not two-hand: 77
Nope. S_1498 source: CPM hand parts: 3
2097 / 2189 Not two-hand: 78
Nope. S_1519 source: CPM hand parts: 3
2104 / 2189 Not two-hand: 79
Nope. S_1526 source: CPM hand parts: 4
2113 / 2189 Not two-hand: 80
Nope. S_1535 source: CPM hand parts: 3
2114 / 2189 Not two-hand: 81
Nope. S_1536 source: CPM hand parts: 3
2117 / 2189 Not two-hand: 82
Nope. S_1539 source: CPM hand parts: 3
2189 / 2189 Not two-hand: 83
Nope!