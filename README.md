# audio-sync
Tool to help add &amp; synchronise additional audio tracks to video files.

Finds the offset between two selected audio tracks in two .mkv files (called reference and source). Can then merge the selected audio track from the source file into the reference file with the calculated offset.

Currently only works with .mkv files with multi-channel audio tracks. (not all audio codecs are 100% supported, still testing)

## How to start
Can be run from project terminal or docker.
* Start from project terminal
  * Change the file directories in app.py to where the video files are located and start the streamlit app with cmd: **streamlit run app.py** (should open a new browser tab)
* Start using docker-compose
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
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 4096M # ram limit example
```
## How to operate
Controlled via browser.
* Select the video file where you'd like to add a new track to.
  * Select which audio track you'd like to use as reference.
* Do the same for the source file.
* Click the "Get Offset" button.
  * The Offset between both audio tracks will now be calculated and displayed (if a suitable value can be found). It's possible that the tracks are from different source versions (DVD / Bluray) and that they have different lengths or even missing parts. In this case you'll notice a large standard deviation of the offset value. In this case, a simple synchronisation via offset probably won't work.
* If the offset value is plausible, select the "Mux to ref. video" button to add the selected audio track to the reference files video with the calculated offset. The finished file is exported to the output folder and named after the original file.
* Review the video for audio synchronicity and add to media folder manually.
