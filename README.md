# audio-sync
Tool to help add &amp; synchronise additional audio tracks to video files.

Current state: Finds the offset between to audio files extracted from video files (ripped movies/tv). Files must be multi-channel audio for now (.dts/.ac3/.eac3/...)
Offset is returned in milliseconds.

streamlit app can be started with: streamlit run app.py

Usage example:
* Change FILE_DIR in app.py to where the video/audio files are located and atart the streamlit app. (should open a new browser tab)
* Select the video file where you'd like to add a new track to. Or if you already have an extracted audio file you like to use as a reference, select that.
* If you selected a video file in th eprevious step, select the audio track that shall be used as the reference for offset calculation.
* Do the same for the source file.
* Click the "Get Offset" button.
  * The Offset between both audio tracks will now be calculated and displayed if a suitable value can be found. It's possible that the tracks are from different source versions (DVD / Bluray) and that they have different lengths or even missing parts. In this case you'll notice a large standard deviation value.
* If the offset value is plausible: Use a muxing tool (like mkvtoolnix) to add the source file to the reference file's video with the calculated offset.
