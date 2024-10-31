import os, glob
import streamlit as st
import pandas as pd
from pathlib import Path, PurePath
from mkv_funcs import list_audio_tracks, extract_audio_track, mux_src_to_ref_offset
from audio_sync import find_offset
from typing import List, Tuple

FILE_DIR = '/Volumes/data/media/movies_backup/'
TBL_COL = ['Track ID','Language','Codec']

def file_selector(file_tag:str):
    file_paths = sorted(glob.glob(f'{FILE_DIR}/**/*.mkv', recursive = True))
    files_with_dir = []
    files_with_dir2 = []
    for i in range(len(file_paths)):
        files_with_dir.append(PurePath(file_paths[i]))
        files_with_dir2.append(os.path.join(files_with_dir[i].parent.name, files_with_dir[i].name))
    sel_file = st.selectbox(f'Select the {file_tag} file', files_with_dir2)
    sel_file_idx = files_with_dir2.index(sel_file)
    sel_file_path = file_paths[sel_file_idx]
    return sel_file_path

def disp_tbl(columns: List[str], data: List[Tuple]):
    """
    Displays a table in Streamlit using specified column headers and data.

    Parameters:
    - columns (List[str]): A list of column headers.
    - data (List[Tuple]): A list of tuples, where each tuple represents a row of data.
    """
    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df.set_index(df.columns[0]))

# Selection reference file
file_ref = file_selector(file_tag='reference')
if Path(file_ref).suffix == '.mkv':
    audio_tracks_ref = list_audio_tracks(file_ref)
    st.session_state['audio_tracks_ref'] = audio_tracks_ref
    # display the audio tracks in a table
    disp_tbl(TBL_COL, audio_tracks_ref)
    if len(audio_tracks_ref) > 1:
        # Select audio track
        track_ids = [t[0] for t in audio_tracks_ref]
        track_id_sel_ref = int(st.radio('Select which audio track to use as reference', track_ids))-1
    else:
        track_id_sel_ref = 0

# Selection source file
file_src = file_selector(file_tag='source')
if Path(file_src).suffix == '.mkv':
    audio_tracks_src = list_audio_tracks(file_src)
    st.session_state['audio_tracks_src'] = audio_tracks_src
    # display the audio tracks in a table
    disp_tbl(TBL_COL, audio_tracks_src)
    if len(audio_tracks_src) > 1:
        # Select audio track
        track_ids = [t[0] for t in audio_tracks_src]
        track_id_sel_src = int(st.radio('Select which audio track to use as source', track_ids))-1
    else:
        track_id_sel_src = 0

if st.button('Get offset'):
    audio_tracks_ref = st.session_state['audio_tracks_ref']
    audio_tracks_src = st.session_state['audio_tracks_src']
    file_ref_audio = extract_audio_track(file_ref, audio_tracks_ref[track_id_sel_ref][0], audio_tracks_ref[track_id_sel_ref][1], audio_tracks_ref[track_id_sel_ref][2])
    file_src_audio = extract_audio_track(file_src, audio_tracks_src[track_id_sel_src][0], audio_tracks_src[track_id_sel_src][1], audio_tracks_src[track_id_sel_src][2])
    offsets, median, std_dev = find_offset(file_ref_audio, file_src_audio)
    if median:
        st.write(f'Offsets: {offsets}')
        st.write(f'Median offset after trimming max. and min. value: {round(median)}ms')
        st.write(f'Standard deviation: {std_dev:.1f}ms')
        st.session_state['offset'] = int(round(median))

if st.button('Mux source audio track to reference video'):
    file_muxed = mux_src_to_ref_offset(file_ref, file_src, track_id_sel_src+1, st.session_state['offset'], 'exp')
    if file_muxed:
        st.write(f'Audio track {track_id_sel_src+1} from {file_src} successfully merged into {file_ref} with an offset of {st.session_state['offset']}ms and exported to {file_muxed}')