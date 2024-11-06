import subprocess, os, re, json
from typing import List, Tuple
from config import DEL_TMP_FILES

def mkvinfo_json(file_path: str, output_dir: str = ".") -> str:
    """
    Uses mkvmerge to retrieve metadata in JSON format from an .mkv file and saves it as a JSON file.

    Parameters:
    - file_path: str : Path to the .mkv file.
    - output_dir: str : Directory to save the JSON file (default is current directory).

    Returns:
    - str : Path to the created JSON file.
    """
    try:
        # Run mkvmerge with JSON output
        result = subprocess.run(
            ['mkvmerge', '-J', file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        # Check if mkvmerge ran successfully
        if result.returncode != 0:
            raise RuntimeError(f"mkvmerge failed: {result.stderr}")
        
        # Parse the JSON output from mkvmerge
        metadata = json.loads(result.stdout)
        
        # Define the output JSON file path
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        json_file_path = os.path.join(output_dir, f"{base_name}_mkvmerge.json")

        # Write metadata to JSON file
        with open(json_file_path, "w") as json_file:
            json.dump(metadata, json_file, indent=4)
        
        return json_file_path

    except FileNotFoundError:
        raise FileNotFoundError("mkvmerge not found. Please ensure mkvtoolnix is installed and mkvmerge is accessible.")
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")
    
def parse_mkv_info(json_file_path: str) -> dict:
    """
    Parses specific metadata from an mkvmerge JSON output file.

    Parameters:
    - json_file_path: str : Path to the JSON file containing mkvmerge output.

    Returns:
    - dict : Parsed information including file name, title, duration, and audio track details.
    """
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Extract general metadata
    file_name = data.get("file_name", "N/A")
    title = data.get("container", {}).get("properties", {}).get("title", "N/A")
    duration_ns = data.get("container", {}).get("properties", {}).get("duration", 0)
    duration_seconds = duration_ns / 1_000_000_000  # Convert nanoseconds to seconds

    # Extract audio track information
    audio_tracks = []
    for track in data.get("tracks", []):
        if track.get("type") == "audio":
            audio_info = {
                "track_id": track.get("id"),
                "codec": track.get("codec"),
                "language": track.get("properties", {}).get("language", "N/A"),
                "track_name": track.get("properties", {}).get("track_name", "N/A")
            }
            audio_tracks.append(audio_info)
    
    # Create a result dictionary
    result = {
        "file_name": file_name,
        "title": title,
        "duration_seconds": duration_seconds,
        "audio_tracks": audio_tracks
    }
    if DEL_TMP_FILES:
        os.remove(json_file_path)
    return result

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


def extract_audio_track(mkv_file_path: str, audio_track: List[Tuple[str, str]], output_dir: str) -> str:
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
    base_name = os.path.splitext(os.path.basename(mkv_file_path))[0]
    # Dictionary mapping codec names to file extensions
    codec_extension_map = {
        "AC-3": "ac3",
        "E-AC-3": "eac3",
        "TrueHD": "thd",
        "DTS-HD Master Audio": "dts",
        "DTS": "dts",
        "AAC": "aac",
        "MP3": "mp3",
        "FLAC": "flac",
        "Vorbis": "ogg",
        "PCM": "wav",
        "Opus": "opus",
    }
    codec = codec_extension_map[audio_track['codec']]
    output_file_path = os.path.join(output_dir, f"{base_name}_track{audio_track['track_id']}_{audio_track['language']}.{codec}")  # Defaulting to .aac; update if needed

    try:
        # Execute mkvextract command
        result = subprocess.run(
            ['mkvextract', 'tracks', mkv_file_path, f'{audio_track['track_id']}:{output_file_path}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Check for errors in mkvextract execution
        if result.returncode != 0:
            raise RuntimeError(f"mkvextract failed: {result.stderr}")
        
        print(f"Track {audio_track['track_id']} extracted successfully to {output_file_path}")
        return output_file_path

    except FileNotFoundError:
        raise FileNotFoundError("mkvextract not found. Please ensure mkvtoolnix is installed and mkvextract is accessible.")
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")

def mux_src_to_ref_offset(file_path_ref_vid: str, file_path_src_vid: str, src_track_id: str, offset_src_to_ref: int, path_output: str) -> str:
    """
    Merges an audio file from one video file into another video file using mkvmerge, with the audio offset and no "default" flag.

    Parameters:
    - file_path_ref_vid: str : Path to the reference video file.
    - file_path_src_vid: str : Path to the source video file.
    - src_track_id: str : Track ID to merge
    - offset_src_to_ref: int : Offset in milliseconds from source to reference.
    - path_output: str : Directory where the merged file will be saved.

    Returns:
    - str : Path to the created merged video file.
    """
    # Extract base filename for output
    base_name = os.path.splitext(os.path.basename(file_path_ref_vid))[0]
    output_file_path = os.path.join(path_output, f"{base_name}.mkv")
    # Construct mkvmerge command
    mkvmerge_command = [
        'mkvmerge',
        '-o', output_file_path, # Output file path
        file_path_ref_vid,      # Reference video file with original audio tracks
        '--no-video',           # Only merge audio
        '--no-subtitles',       # Only merge audio
        '--audio-tracks', f'{src_track_id}',    # Track ID to merge
        '--track-name', f'{src_track_id}:',     # Ensure no custom track name is set for the audio
        '--default-track-flag', '0',    # Remove the "default" flag from the audio track
        '--sync', f'{src_track_id}:{offset_src_to_ref}',    # Apply offset to the audio track
        file_path_src_vid   # Source video file to merge
    ]
    try:
        # Run the mkvmerge command
        result = subprocess.run(mkvmerge_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if mkvmerge executed successfully
        if result.returncode != 0:
            raise RuntimeError(f"mkvmerge failed: {result.stderr}")
        print(f"Merged file created successfully at: {output_file_path}")

        return output_file_path

    except FileNotFoundError:
        raise FileNotFoundError("mkvmerge not found. Please ensure mkvtoolnix is installed and mkvmerge is accessible.")
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")