# audio-sync
Tool to help add &amp; synchronise additional audio tracks to video files.

Current state: Finds the offset between to audio files extracted from video files (ripped movies/tv). Files must be multi-channel audio for now (.dts/.ac3/.eac3/...)
Offset is returned in milliseconds.

streamlit app can be started with: streamlit run app.py

Usage example:
* Extract an audio track from a movie file (original) of which you wish to add a new track to (reference)
* Extract the audio track that you wish to add to the original video from its video file (source)
* Run audio-sync with both files as inputs to receive offset, if any (handling may vary throughout project development)
* Use muxing tool (like mkvtoolnix) to add the source file to the reference file's video with the calculated offset.
