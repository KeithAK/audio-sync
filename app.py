import os
import streamlit as st
from audio_sync import test_correlation

FILE_DIR = 'path to files for selection'

def file_selector(file_tag:str, folder_path=FILE_DIR):
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox(f'Select the {file_tag} file', filenames)
    return os.path.join(folder_path, selected_filename)

file_ref = file_selector(file_tag='reference')
st.write('You selected `%s`' % file_ref)

file_src = file_selector(file_tag='source')
st.write('You selected `%s`' % file_src)

if st.button('Get offset'):
    median, std_dev = test_correlation(file_ref, file_src)
    if median:
        st.write(f'Offset: {round(median)}ms, SD: {std_dev:.1f}ms')