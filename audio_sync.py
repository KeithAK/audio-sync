import subprocess, librosa, os, datetime, json
import numpy as np
from scipy.signal import correlate
from config import DEL_TMP_FILES

SR = 16000 # audio sample Rate
# some randomness involved here, will be removed after further testing
NR_OF_SAMPLES = int(np.random.choice(range(5, 11))) # nr. of samples spread across shortest audio file
SAMPLE_LEN = int(np.random.choice(range(60, 120))) # sample length in seconds

def get_audio_duration(file_path: str) -> float:
    """
    Retrieves the duration of an audio file. Uses librosa for compatible formats.
    For non-compatible formats, ffprobe is used after wrapping files in mkv first.

    Parameters:
    - file_path: str : Path to the audio file.

    Returns:
    - float : Duration of the file in seconds.
    """
    # Get the file extension
    _, ext = os.path.splitext(file_path)
    
    # List of file extensions that require get_truehd_duration
    custom_formats = [".thd", ".dts"]

    if ext.lower() in custom_formats:
        # Define a temporary MKV file path
        temp_mkv_path = file_path + ".mkv"
        
        try:
            # Step 1: Wrap the .TrueHD file in an MKV container using ffmpeg
            subprocess.run(
                ['ffmpeg', '-y', '-i', file_path, '-c', 'copy', temp_mkv_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            print(file_path)
            # Step 2: Use ffprobe to get duration of the MKV file
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error', '-show_entries',
                    'format=duration', '-of', 'json', temp_mkv_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Parse the duration from JSON output
            metadata = json.loads(result.stdout)
            duration = float(metadata["format"]["duration"])

            return duration

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg or ffprobe failed: {e.stderr}")
        except FileNotFoundError:
            raise FileNotFoundError("ffmpeg or ffprobe not found. Please ensure they are installed and accessible.")
        except KeyError:
            raise ValueError("Duration not found in ffprobe output.")
        finally:
            # Clean up the temporary MKV file
            if os.path.exists(temp_mkv_path):
                os.remove(temp_mkv_path)
    else:
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error', '-show_entries',
                    'format=duration', '-of', 'json', file_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Parse the duration from JSON output
            metadata = json.loads(result.stdout)
            duration = float(metadata["format"]["duration"])

            return duration
        except Exception as e:
            raise RuntimeError(f"Error: {e}")

def generate_timestamps(duration, num_timestamps=NR_OF_SAMPLES):
    """Generates an array of equally spaced timestamps across the given duration."""
    return np.linspace(0, duration, num_timestamps)

def detect_warp_or_stretch(offsets, std_threshold=100):
    """
    Detect if one file is warped or stretched relative to the other based on the
    standard deviation of the calculated offsets.
    """
    offsets_filt = np.delete(offsets, [np.argmin(offsets), np.argmax(offsets)])
    median = np.median(offsets_filt)
    std_dev = np.std(offsets_filt)
    
    # If the standard deviation exceeds the threshold, return True (files may be warped or stretched)
    if std_dev > std_threshold:
        print(f"Warning: Files may be warped/stretched. Offsets: {offsets}, std dev: {std_dev:.4f})")
        return offsets, median, std_dev
    else:
        print(f"File 2 has an offset of {round(median)}ms to file 1 (std dev = {std_dev:.4f}).")
        return offsets, median, std_dev

def extract_non_center_channels(audio_file, output_file, t_start:str, td_sample:str):
    """
    Extracts all audio channels except the center channel (channel 2) from a file using ffmpeg,
    and merges them into a mono track for analysis.
    """
    # Select channels 0, 1, 3, 4, 5 (all channels except center = channel 2)
    command = [
        'ffmpeg', '-ss', t_start, '-i', audio_file, '-t', td_sample,
        '-filter_complex', 'pan=mono|c0=FL+FR+LFE+SL+SR', 
        '-ac', '1', '-ar', str(SR), output_file
    ]
    if os.path.exists(output_file):
        os.remove(output_file)
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(output_file):
        print(result.stderr.decode())
        raise FileNotFoundError(f"Failed to create output file: {output_file}")
    
def find_offset(file1, file2):
    """
    Finds the best fitting offset value that would put file2 in sync with file1.  
    """
    if not os.path.exists(file1) & os.path.exists(file2):
        raise FileNotFoundError
    # generate timestamps spread across the shortest file
    duration1 = get_audio_duration(file1)
    duration2 = get_audio_duration(file2)
    dur_diff = abs(duration1-duration2)
    if dur_diff > (15 * 60): # over 10 minutes difference
        print('Audio most likely warped or from different cuts.')
        print(f'Duration file1: {datetime.timedelta(seconds=duration1)}, file2: {datetime.timedelta(seconds=duration2)}, difference: {datetime.timedelta(seconds=dur_diff)}')
        #raise Exception
        return 0, 0, 0
    shorter_duration = min(duration1, duration2) # Get the shorter duration
    t_sample = str(datetime.timedelta(seconds=SAMPLE_LEN))
    timestamps = generate_timestamps(shorter_duration - SAMPLE_LEN) # Generate 10 timestamps
    # Step 1: Extract audio from both .mka files to .wav files
    t_offsets_ms = []
    for i, t in enumerate(timestamps):
        file_out_1 = f'tmp/audio{i}_1.wav'
        file_out_2 = f'tmp/audio{i}_2.wav'

        t_start = str(datetime.timedelta(seconds=t))
        extract_non_center_channels(file1, file_out_1, t_start, t_sample)
        extract_non_center_channels(file2, file_out_2, t_start, t_sample)

        # Step 2: Load the extracted audio
        audio1, _ = librosa.load(file_out_1, sr=SR)
        audio2, _ = librosa.load(file_out_2, sr=SR)

        # Step 4: Compute cross-correlation
        correlation = correlate(audio1, audio2)

        # Step 5: Find and print the offset based on maximum correlation
        offset_index = float(np.argmax(correlation))
        t_offsets_ms.append((offset_index - len(audio1)) * 1000 / SR)
        if DEL_TMP_FILES:
            os.remove(file_out_1)
            os.remove(file_out_2)
    print(f'Offsets calculated from {NR_OF_SAMPLES} samples of {SAMPLE_LEN}s length.')
    offsets, median, std_dev = detect_warp_or_stretch(t_offsets_ms)
    return offsets, median, std_dev