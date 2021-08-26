# Aligned Classical Piano Audio and Score (ACPAS) dataset

**ACPAS** is a dataset with aigned audio and scores for classical piano music. For each performance, we provide the corresponding **performance audio** (real recording or synthesized), **performance MIDI**, and **MIDI score**, together with **rhythm and key annotations**.

The dataset data is partly collected from a list of Automatic Music Transcription (AMT) datasets, and partly synthesized using [Native Instrument Kontakt Player](https://www.native-instruments.com/en/products/komplete/samplers/kontakt-6-player/).

List of source AMT datasets:
- MIDI Aligned Piano Sounds (MAPS) dataset
- [A-MAPS dataset](http://c4dm.eecs.qmul.ac.uk/ycart/a-maps.html)
- [Classical Piano MIDI Page](http://www.piano-midi.de/)
- [Aligned Scores and Performances (ASAP) dataset](https://github.com/fosfrancesco/asap-dataset)
- [MAESTRO dataset](https://magenta.tensorflow.org/datasets/maestro)

In this document, we describe a piece of music composition as a **music piece**, a version of music score to the composition as a **music score**, and a music performance to a specific music score as a **music performance**. Thus, one music piece can have multiple versions of music scores (due to e.g. different repeats), and one music score can be mapped to multiple versions of music performances.

Due to different sources of data, the performances can be human performances (from the ASAP dataset) or hand-crafted tempos and dynamics to sound like human performances (from MAPS dataset and Classical Piano MIDI Page).

## Dataset Structure

**ACPAS** dataset is composed of two subsets:
- **Real recording subset**
- **Synthetic subset**

### Real recording subset

This subset covers performances with real recordings from the MAPS "ENSTDkCl" and "ENSTDkAm" subsets and the MAESTRO dataset, in total (60+520=)**580 performances**. The corresponding MIDI scores and annotations are from the A-MAPS dataset and the ASAP dataset.

Among the 580 performance, the 60 perforamnces from the MAPS dataset are for testing only. This is to keep inline with test data in other AMT works. The 520 performances from the MAESTRO dataset are divided into training and testing in a way where there is no overlap on music pieces between the training and testing sets.


