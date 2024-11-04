# audio-sync
Tool to help add &amp; synchronise additional audio tracks to video files.

Finds the offset between two selected audio tracks in two .mkv files (called reference and source). Can then merge the selected audio track from the source file into the reference file with the calculated offset.

streamlit app can be started with command: **streamlit run app.py**

Usage example:
* Change the file directories in app.py to where the video files are located. (Docker usage guide coming soon)
* start the streamlit app. (should open a new browser tab)
* Select the video file where you'd like to add a new track to.
  * Select which audio track you'd like to use as reference.
* Do the same for the source file.
* Click the "Get Offset" button.
  * The Offset between both audio tracks will now be calculated and displayed (if a suitable value can be found). It's possible that the tracks are from different source versions (DVD / Bluray) and that they have different lengths or even missing parts. In this case you'll notice a large standard deviation value. In this case, a simple synchronisation via offset won't work.
* If the offset value is plausible, select the "Mux to ref. video" button to add the selected audio track to the reference files video with the calculated offset.
