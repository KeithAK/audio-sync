import librosa, os, ffmpeg, random
import numpy as np
from scipy.signal import correlate
from mkv_funcs import mkvinfo_json, parse_mkv_info
from pathlib import Path
from config import DEL_TMP_FILES, DIR_TMP, CONSTS

SR = 16000 # audio sample Rate
# some randomness involved here, will be removed after further testing
NR_OF_SAMPLES = int(np.random.choice(range(5, 11))) # nr. of samples spread across shortest audio file
SAMPLE_LEN = int(np.random.choice(range(60, 120))) # sample length in seconds
        
def extract_multiple_audio_segments(mkv_file_path: list[str], audio_track_id: list[int], timestamps: list, output_dir: str) -> list:
    """
    Extracts multiple segments from an audio track in an MKV file and saves them as WAV files.

    Args:
        - mkv_file_path (list[str]): Path to the MKV file.
        - audio_track_id (list[int]): The ID of the audio track to extract.
        - timestamps (list): List of tuples (start_time, duration) in seconds.
        - output_dir (str): Directory to save the output WAV files.

    Returns:
        - list: List of paths to the output WAV files.
    """
    output_paths = []
    for i, (start_time, duration) in enumerate(timestamps):
        # Define the output file path for each segment
        output_file_path = []
        output_file_path.append(str(Path(output_dir) / f"{Path(mkv_file_path[0]).stem}_track{audio_track_id[0]}_segment{i+1}.wav"))
        output_file_path.append(str(Path(output_dir) / f"{Path(mkv_file_path[1]).stem}_track{audio_track_id[1]}_segment{i+1}.wav"))
        output_paths.append(output_file_path)

        try:
            for i_mkv in range(len(mkv_file_path)):
                (
                    ffmpeg
                    .input(mkv_file_path[i_mkv], ss=start_time)
                    .output(
                        # input_stream,
                        output_paths[i][i_mkv],
                        map=f'0:{audio_track_id[i_mkv]+1}',      # Select the specified audio track
                        t=duration,                     # Set segment duration
                        af='pan=mono|c0=FL+FR+LFE+SL+SR', # Combine all non-center channels into one
                        c='pcm_s16le',                  # Set audio codec to PCM 16-bit (WAV format)
                        ac=1,                           # Set audio channels to mono
                        ar=CONSTS["sr"],                       # Set audio sample rate to 16000 Hz
                        loglevel='quiet'                # Supress terminal output
                    )
                    .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
                )
            
        except ffmpeg.Error as e:
            raise e

    return output_paths

def find_offset(file_paths: list[str], sel_audio_tracks: list[int]):
    file_ref_info = parse_mkv_info(mkvinfo_json(file_paths[0], DIR_TMP))
    file_src_info = parse_mkv_info(mkvinfo_json(file_paths[1], DIR_TMP))

    # STEP 1: get the shorter duration
    dur_ref = float(file_ref_info['duration_seconds'])
    if (Path(file_paths[1]).suffix == '.mkv'): # source file is a video file
        dur_src = float(file_src_info['duration_seconds'])

    else: # source file is an audio file
        try:
            dur_src = float(ffmpeg.probe(file_paths[1])["format"]["duration"])
        # wrap in an .mkv container
        except Exception:
            (
                ffmpeg
                .input(file_paths[1])
                .output(str(Path(file_paths[1]).with_suffix('.mkv')), f='matroska')
                .run(overwrite_output=True)
            )
            dur_src = float(ffmpeg.probe(str(Path(file_paths[1]).with_suffix('.mkv')))["format"]["duration"])

    dur_min = min(dur_ref, dur_src)

    # STEP 2 generate timestamps
    ts_starts = np.linspace(0, dur_min - CONSTS["max_smp_dur"], random.randint(CONSTS["min_nr_of_smp"], CONSTS["max_nr_of_smp"]))
    timestamps = []
    for i in range(len(ts_starts)):
        timestamps.append((float(ts_starts[i]), random.randint(CONSTS["min_smp_dur"], CONSTS["max_smp_dur"])))

    # STEP 3: Extract audio samples from both files without center channel as wav files
    smp_paths = extract_multiple_audio_segments(file_paths, sel_audio_tracks, timestamps, DIR_TMP)

    # STEP 4: Calculate offsets
    offsets = []
    for smp in range(len(smp_paths)):
        audio1, _ = librosa.load(smp_paths[smp][0], sr=CONSTS["sr"])
        audio2, _ = librosa.load(smp_paths[smp][1], sr=CONSTS["sr"])

        correlation = correlate(audio1, audio2, method='fft')
        offset_index = float(np.argmax(correlation))

        offsets.append((offset_index - len(audio1)) * 1000 / CONSTS["sr"])
        if DEL_TMP_FILES:
            [os.remove(path) for path in smp_paths[smp] if os.path.exists(path)]
    
    # STEP 5: median and standard deviation
    median = np.median(np.delete(offsets, [np.argmin(offsets), np.argmax(offsets)]))
    std_dev = np.std(np.delete(offsets, [np.argmin(offsets), np.argmax(offsets)]))
    
    return offsets, median, std_dev