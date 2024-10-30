import os
import streamlit as st
from pathlib import Path
from mkv_funcs import list_audio_tracks, extract_audio_track, mux_src_to_ref_offset
from audio_sync import find_offset

FILE_DIR = 'imp'
if not os.path.exists(FILE_DIR):
    os.mkdir(FILE_DIR)

def file_selector(file_tag:str, folder_path=FILE_DIR):
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox(f'Select the {file_tag} file', filenames)
    return os.path.join(folder_path, selected_filename)

file_ref = file_selector(file_tag='reference')
st.write('You selected `%s`' % file_ref)
if Path(file_ref).suffix == '.mkv':
    audio_tracks_ref = list_audio_tracks(file_ref)
    track_ids = [t[0] for t in audio_tracks_ref]
    st.write(audio_tracks_ref)
    track_id_sel_ref = int(st.radio('Select which audio track to use as reference', track_ids))-1
    st.session_state['audio_tracks_ref'] = audio_tracks_ref

file_src = file_selector(file_tag='source')
st.write('You selected `%s`' % file_src)
if Path(file_src).suffix == '.mkv':
    audio_tracks_src = list_audio_tracks(file_src)
    track_ids = [t[0] for t in audio_tracks_src]
    st.write(audio_tracks_src)
    track_id_sel_src = int(st.radio('Select which audio track to use as source', track_ids))-1
    st.session_state['audio_tracks_src'] = audio_tracks_src

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