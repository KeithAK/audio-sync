# audio-sync
Tool to help add &amp; synchronise additional audio tracks to video files.

Finds the offset between two selected audio tracks in two .mkv files (called reference and source). Can then merge the selected audio track from the source file into the reference file with the calculated offset.

streamlit app can be started with command: **streamlit run app.py**

Usage example:
* Change the file directories in app.py to where the video files are located. 
  * start the streamlit app. (should open a new browser tab)
  * Or use docker-compose
* Select the video file where you'd like to add a new track to.
  * Select which audio track you'd like to use as reference.
* Do the same for the source file.
* Click the "Get Offset" button.
  * The Offset between both audio tracks will now be calculated and displayed (if a suitable value can be found). It's possible that the tracks are from different source versions (DVD / Bluray) and that they have different lengths or even missing parts. In this case you'll notice a large standard deviation value. In this case, a simple synchronisation via offset won't work.
* If the offset value is plausible, select the "Mux to ref. video" button to add the selected audio track to the reference files video with the calculated offset.

**docker-compose**
```yaml
services:
  audio-sync:
    image: keithak/audio-sync:latest
    ports:
      - "5656:5656"  # Map Streamlit’s default port to host
    volumes:
      - MOVIE_DIR_HERE:/data/movies # Link local movies directory
      - TV_DIR_HERE:/data/tv # Link local tv directory
      - SOURCE_DIR_HERE:/data/src # Link local src directory
      - OUTPUT_DIR_HERE:/data/output  # Link local output directory
      - TEMP_DIR_HERE:/data/tmp # Link local temp directory, preferably ssd or ramdisk
```
