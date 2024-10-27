import subprocess, os, re
from typing import List, Tuple

def list_audio_tracks(mkv_file_path: str) -> List[Tuple[str, str]]:
    """
    Lists all audio track IDs and their languages from a given .mkv file.

    Parameters:
    - mkv_file_path: str : Path to the .mkv file.

    Returns:
    - List[Tuple[str, str]] : A list of tuples, each containing the track ID and language code.
    """
    try:
        # Run mkvinfo command to get metadata information
        result = subprocess.run(['mkvinfo', mkv_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #print(result.stdout)
        # Check if mkvinfo ran without issues
        if result.returncode != 0:
            raise RuntimeError(f"Error in executing mkvinfo: {result.stderr}")

        audio_tracks = []
        track_id = None
        track_type = None
        language = None
        for line in result.stdout.splitlines():
            # Detect track ID
            if 'Track number:' in line:
                track_id = re.search(r'Track number: (\d+)', line)
                if track_id:
                    track_id = track_id.group(1)
            
            # Detect audio track with language
            elif 'Track type:' in line:
                track_type = line.split(':', 1)[1].strip()
            
            elif 'Language:' in line:
                language = line.split(':', 1)[1].strip()

            elif 'Codec ID:' in line:
                codec = line.split(':', 1)[1].replace(" A_","",1).lower()
            
            # If both track ID and language are found, store and reset
            elif track_id and track_type=='audio' and language and codec:
                audio_tracks.append((str(int(track_id)-1), language, codec))
                track_id = None
                track_type = None
                language = None
                codec = None

        return audio_tracks
    
    except FileNotFoundError:
        raise FileNotFoundError("mkvinfo not found. Please ensure mkvtoolnix is installed and mkvinfo is accessible.")
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")


def extract_audio_track(mkv_file_path: str, track_id: int, output_codec: str = 'aac', output_dir: str = "tmp") -> str:
    """
    Extracts a specified audio track from an .mkv file using mkvextract.

    Parameters:
    - mkv_file_path: str : Path to the .mkv file.
    - track_id: int : ID of the audio track to extract.
    - output_codec: str : Audio codec of the output file. 
    - output_dir: str : Directory where the extracted file will be saved (default is current directory).

    Returns:
    - str : Path to the extracted audio file.
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Determine output file name and path
    output_file_path = os.path.join(output_dir, f"track_{track_id}.{output_codec}")  # Defaulting to .aac; update if needed

    try:
        # Execute mkvextract command
        result = subprocess.run(
            ['mkvextract', 'tracks', mkv_file_path, f'{track_id}:{output_file_path}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Check for errors in mkvextract execution
        if result.returncode != 0:
            raise RuntimeError(f"mkvextract failed: {result.stderr}")
        
        print(f"Track {track_id} extracted successfully to {output_file_path}")
        return output_file_path

    except FileNotFoundError:
        raise FileNotFoundError("mkvextract not found. Please ensure mkvtoolnix is installed and mkvextract is accessible.")
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")


if __name__ == "__main__":
    FILE = 'tmp/'
    audio_tracks = list_audio_tracks(FILE)
    print('')
    print(audio_tracks)
    track_id_sel = int(input("Extract which track ID? "))-1 #track id for mkv extract and merge is n-1
    track_id = audio_tracks[track_id_sel][0]
    codec = audio_tracks[track_id_sel][2]

    extract_audio_track(FILE, track_id, codec)