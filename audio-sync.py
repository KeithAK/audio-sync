import subprocess, librosa, os, json, datetime
import numpy as np
from scipy.signal import correlate

FILE1 = 'reference.ac3'
FILE2 = 'source.ac3'
SR = 16000 # audio sample Rate
# some randomness involved here, will be removed after further testing
NR_OF_SAMPLES = int(np.random.choice(range(5, 10))) # nr. of samples spread across shortest audio file
SAMPLE_LEN = int(np.random.choice(range(60, 240))) # sample length in seconds

def get_audio_duration(file_path):
    """Uses ffprobe to get the duration of an audio file."""
    command = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'json', file_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    
    # Parse the JSON output from ffprobe
    metadata = json.loads(output)
    return float(metadata['format']['duration'])

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
        return True
    else:
        print(f"File 2 has an offset of {round(median)}ms to file 1 (std dev = {std_dev:.4f}).")
        return False

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


def load_audio(file_path):
    """Loads audio as a waveform using librosa."""
    audio, sr = librosa.load(file_path, sr=SR)
    return audio, sr

def test_correlation(file1, file2):
    if not os.path.exists(file1) & os.path.exists(file2):
        return print('File not found.')
    # generate timestamps spread across the shortest file
    duration1 = get_audio_duration(file1)
    duration2 = get_audio_duration(file2)
    dur_diff = abs(duration1-duration2)
    if dur_diff > 15*60:
        print('Audio most likely warped or from different cuts.')
        print(f'Duration file1: {datetime.timedelta(seconds=duration1)}, file2: {datetime.timedelta(seconds=duration2)}, difference: {datetime.timedelta(seconds=dur_diff)}')
        return 0
    shorter_duration = min(duration1, duration2) # Get the shorter duration
    t_sample = str(datetime.timedelta(seconds=SAMPLE_LEN))
    timestamps = generate_timestamps(shorter_duration - SAMPLE_LEN) # Generate 10 timestamps
    # Step 1: Extract audio from both .mka files to .wav files
    t_offsets_ms = []
    for i, t in enumerate(timestamps):
        #print()
        t_start = str(datetime.timedelta(seconds=t))
        extract_non_center_channels(file1, 'audio1.wav', t_start, t_sample)
        extract_non_center_channels(file2, 'audio2.wav', t_start, t_sample)

        # Step 2: Load the extracted audio
        audio1, sr1 = load_audio('audio1.wav')
        audio2, sr2 = load_audio('audio2.wav')

        # Step 4: Compute cross-correlation
        correlation = correlate(audio1, audio2)

        # Step 5: Find and print the offset based on maximum correlation
        offset_index = float(np.argmax(correlation))
        t_offsets_ms.append((offset_index - len(audio1)) * 1000 / sr1)
        #print(f"Timestamp: {i}, delay of track 2: {t_offset_ms[i]:.2f} ms")
    print(f'Offsets calculated from {NR_OF_SAMPLES} samples of {SAMPLE_LEN}s length.')
    detect_warp_or_stretch(t_offsets_ms)

if __name__ == "__main__":
    # Replace with paths to your .mka files
    test_correlation(FILE1, FILE2)