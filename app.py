import os, glob
import streamlit as st
import pandas as pd
from pathlib import Path, PurePath
from datetime import timedelta
from mkv_funcs import mkvinfo_json, parse_mkv_info, mux_src_to_ref_offset
from audio_sync import find_offset
from typing import List, Tuple

DIR_INPUTS_REF = ['/data/movies', '/data/tv']
DIR_INPUT_SRC = '/data/src'
DIR_OUTPUT = '/data/output'
DIR_TMP = '/data/tmp'

def file_selector(file_tag: str, dir: str, ignore_folders: list[str]) -> str:
    """
    Draws a streamlit file selector as a dropdown
    Args:
        - file_tag (str): Tag the files role. Used for display purposes.
        - dir (str): Directory of the files to be selected from.
        - ignore_folders (list): List of folder names to ignore when displaying files.
    Returns:
        - str: The full path of the selected file.
    """
    file_paths = sorted(glob.glob(f'{dir}/**/*.mkv', recursive = True))

    # Filter out files in ignored folders
    filtered_files = [path for path in file_paths if PurePath(path).parent.name not in ignore_folders]
    
    # Display only the basename of each file in the dropdown
    display_names = [PurePath(path).name for path in filtered_files]

    # Show the selectbox with display names, and get the selected file's full path
    selected_display_name = st.selectbox(f'Select the {file_tag} file', display_names)
    if selected_display_name:
        # Find the full path of the selected file by matching the basename
        sel_file_path = next(path for path in filtered_files if PurePath(path).name == selected_display_name)
        return sel_file_path

def disp_tbl(data: List[Tuple]):
    """
    Displays a table in Streamlit using specified column headers and data.
    Args:
        - data (List[Tuple]): A list of tuples, where each tuple represents a row of data.
    """
    df = pd.DataFrame(data)
    st.dataframe(df.set_index(df.columns[0]))

# Select base directory of reference file
dir_sel = st.radio('Base directory of reference file:', DIR_INPUTS_REF)

# Selection reference file
if dir_sel:
    file_ref = file_selector(file_tag='reference', dir=dir_sel, ignore_folders=['Featurettes'])
if (file_ref != '') & (Path(file_ref).suffix == '.mkv'):
    file_ref_info = parse_mkv_info(mkvinfo_json(file_ref, DIR_TMP))
    vid_duration = file_ref_info
    audio_tracks_ref = file_ref_info['audio_tracks']
    duration_ref = str(timedelta(seconds=file_ref_info['duration_seconds'])).split(".")[0]
    st.session_state['audio_tracks_ref'] = audio_tracks_ref
    # display the file stats
    disp_tbl([{"Duration": duration_ref, "Fps": file_ref_info["fps"]}])
    st.write('Audio tracks:')
    disp_tbl(audio_tracks_ref)
    if len(audio_tracks_ref) > 1:
        # Select audio track
        track_ids = [t['track_id'] for t in audio_tracks_ref]
        track_id_sel_ref = int(st.radio('Select which audio track to use as reference', track_ids))-1
        # Get index of selected track
        for i in range(len(audio_tracks_ref)):
            if track_id_sel_ref+1 == audio_tracks_ref[i]['track_id']:
                track_sel_idx_ref = i
    else:
        track_id_sel_ref = 0
        track_sel_idx_ref = 0

# Selection source file
file_src = file_selector(file_tag='source', dir= DIR_INPUT_SRC, ignore_folders=['Featurettes'])
if (file_src != '') & (Path(file_src).suffix == '.mkv'):
    file_src_info = parse_mkv_info(mkvinfo_json(file_src, DIR_TMP))
    audio_tracks_src = file_src_info['audio_tracks']
    duration_src = str(timedelta(seconds=file_src_info['duration_seconds'])).split(".")[0]
    st.session_state['audio_tracks_src'] = audio_tracks_src
    # display the file stats
    disp_tbl([{"Duration": duration_src, "Fps": file_src_info["fps"]}])
    st.write('Audio tracks:')
    disp_tbl(audio_tracks_src)
    if len(audio_tracks_src) > 1:
        # Select audio track
        track_ids = [t['track_id'] for t in audio_tracks_src]
        track_id_sel_src = int(st.radio('Select which audio track to use as source', track_ids))-1
        # Get index of selected track
        for i in range(len(audio_tracks_src)):
            if track_id_sel_src+1 == audio_tracks_src[i]['track_id']:
                track_sel_idx_src = i
    else:
        track_id_sel_src = 0
        track_sel_idx_src = 0

if st.button('Get offset'):
    offsets, median, std_dev = find_offset([file_ref, file_src], [track_id_sel_ref, track_id_sel_src])

    if median:
        st.write(f'Offsets: {offsets}')
        st.write(f'Median offset after trimming max. and min. value: {round(median)}ms')
        st.write(f'Standard deviation: {std_dev:.1f}ms')
        st.session_state['offset'] = int(round(median))

if st.button('Mux source audio track to reference video'):
    file_muxed = mux_src_to_ref_offset(file_ref, file_src, track_id_sel_src+1, st.session_state['offset'], DIR_OUTPUT)
    if file_muxed:
        st.write(f'Audio track {track_id_sel_src+1} from *{os.path.basename(file_src)}* successfully merged into *{os.path.basename(file_ref)}* with an offset of {st.session_state['offset']}ms and exported to *{file_muxed}*')