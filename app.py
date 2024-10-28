import os
import streamlit as st
from pathlib import Path
from mkv_funcs import list_audio_tracks, extract_audio_track
from audio_sync import find_offset

FILE_DIR = 'tmp'

def file_selector(file_tag:str, folder_path=FILE_DIR):
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox(f'Select the {file_tag} file', filenames)
    return os.path.join(folder_path, selected_filename)

file_ref = file_selector(file_tag='reference')
st.write('You selected `%s`' % file_ref)
if Path(file_ref).suffix == '.mkv':
    audio_tracks = list_audio_tracks(file_ref)
    track_ids = [t[0] for t in audio_tracks]
    st.write(audio_tracks)
    track_id_sel_ref = int(st.radio('Select which audio track to use as reference', track_ids))-1
    st.write(track_id_sel_ref)

file_src = file_selector(file_tag='source')
st.write('You selected `%s`' % file_src)
if Path(file_src).suffix == '.mkv':
    audio_tracks = list_audio_tracks(file_src)
    track_ids = [t[0] for t in audio_tracks]
    st.write(audio_tracks)
    track_id_sel_src = int(st.radio('Select which audio track to use as source', track_ids))-1
    st.write(track_id_sel_src)

if st.button('Get offset'):
    file_ref = extract_audio_track(file_ref, audio_tracks[track_id_sel_ref][0], audio_tracks[track_id_sel_ref][2])
    st.write(file_ref)
    offsets, median, std_dev = find_offset(file_ref, file_src)
    if median:
        st.write(f'Offsets: {offsets}')
        st.write(f'Median offset after trimming max. and min. value: {round(median)}ms')
        st.write(f'Standard deviation: {std_dev:.1f}ms')
