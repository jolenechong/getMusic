import streamlit as st
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Music Downloader", page_icon="🎵")

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

import json

def get_from_local_storage(k):
    v = st_javascript(
        f"JSON.parse(localStorage.getItem('{k}'));"
    )
    return v or {}


def set_to_local_storage(k, v):
    jdata = json.dumps(v)
    st_javascript(
        f"localStorage.setItem('{k}', JSON.stringify({jdata}));"
    )

if get_from_local_storage("password_correct"):
    # skip pw checking
    authenticated = True
else:
    authenticated = check_password()

if authenticated:
    set_to_local_storage("password_correct", True)
    
    st.title("Download Music :D")
    st.write("Choose between downloading a single song where you will be able to select the exact song you'd like or batch \
            downloading songs which wil default to the first result of the query from YouTube. Videos over 10mins long will \
            not be downloaded due to long load times.")
    st.write("")
    st.write("**Disclaimer**: This app is not affiliated with YouTube in any way. This app should only be used for personal \
            use and not for commercial use, downloaded content should not be uploaded. This app is not responsible for \
            any misuse or liabilities. By using this app, you agree to the above disclaimer.")
    st.write("**Note:** This app is still in development and may not work as expected. Please report any bugs to the \
            [GitHub repo](https://github.com/jolenechong/getMusic).")

    # set some spacing
    st.write("")
    st.write("")

    # helpers
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    import yt_dlp
    import base64
    from datetime import timedelta
    import re

    def get_binary_file_downloader_html(bin_file, song_title):
        with open(bin_file, 'rb') as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{song_title}.mp3">Download {song_title}</a>'
        return href

    def getDuration(label):
        match = re.search(r'\b(\d+ minutes?, \d+ seconds)\b', label)
        if match:
            duration = match.group(1).split(", ")

            if len(duration) > 2:
                # there is an hour component which we will not be including for music videos due to long load times
                # hours = int(duration[0].split(" ")[0])
                # minutes = int(duration[1].split(" ")[0])
                # seconds = int(duration[2].split(" ")[0])
                return None
            else:
                minutes = int(duration[0].split(" ")[0])
                seconds = int(duration[1].split(" ")[0])

                # ensure under 10mins
                if minutes < 10:
                    # Create timedelta object
                    duration = timedelta(minutes=minutes, seconds=seconds)

                    # Format as "MM:SS" string
                    duration_formatted = duration - timedelta(microseconds=duration.microseconds)
                    duration_str = str(duration_formatted)[2:]
                    return duration_str

    def searchYouTube(search):
        search = search.replace(" ", "+")

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)

        url = f"https://www.youtube.com/results?search_query={search}"
        driver.get(url)

        try:
            element_present = EC.presence_of_element_located((By.ID, "video-title"))
            WebDriverWait(driver, 10).until(element_present)
        except:
            st.write("Timed out waiting for page to load")
            return []
        
        st.write("Getting songs...")

        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")

        videos_soup = soup.find_all("a", id="video-title")
        durations = [video['aria-label'] for video in videos_soup][:5]
        durations = [getDuration(duration) for duration in durations]
        print(durations)
        # get links and titles of videos
        videos = []

        for idx, video in enumerate(videos_soup[:5]): # only get top 5 results
            title = video["title"]
            link = "https://www.youtube.com" + video["href"]

            if "shorts" not in title:
                videos.append((title, durations[idx], link))

        driver.quit()

        return videos

    def downloadYTFromLink(link, song_title):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # 'geo_verification_proxy': 'http://proxy-server-singapore:8080', # TODO: need to replace this with a proxy server
        }

        # set provide the path using --ffmpeg-location
        # ydl_opts['ffmpeg_location'] = r'C:\ffmpeg\bin\ffmpeg.exe'
        ydl_opts['ffmpeg_location'] = r"/usr/bin/ffmpeg"
        ydl_opts['outtmpl'] = 'song'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.cache.remove()
                ydl.download([link])
        except:
            st.write("Error downloading song, try another link/song")
            return

        # send song to user
        st.audio("song.mp3")

        # allow user to download music file
        st.markdown(get_binary_file_downloader_html("song.mp3", song_title), unsafe_allow_html=True)



    # ui
    downloadMusic, batchDownload = st.tabs(["Download Song", "Batch Download"])

    def is_checkbox_filled():
        if 'songSelection' in st.session_state.keys() and st.session_state['songSelection']:
            return True
        else:
            return False

    with downloadMusic:
        st.subheader("Download Song (select result from query)")

        with st.form("search_form"):
            search = st.text_input("Search for a song")
            submit_button = st.form_submit_button("Get Relevant Songs")

        if submit_button or is_checkbox_filled():
            if not is_checkbox_filled():
                st.write("Retrieving search results...")
                options = searchYouTube(search) # title, duration, link
                options.insert(0, ("Select a song (disabled)", None, None))
                options = [(idx, option[0], option[1], option[2]) for idx, option in enumerate(options)]

                # get only the first item in the list of tuples
                options_titles = ["Select a song (disabled)"]
                # add numbers from 0 and 1 to list as a tuple, skip first one
                options_titles.extend([f"{idx+1}. {option[2]} ({option[1]})" for idx, option in enumerate(options[1:])])

                st.session_state['options_titles'] = options_titles
                st.session_state['options'] = options
            else:
                st.write("Retrieving search results...")
                st.write("Getting Songs...")
                options_titles = st.session_state['options_titles']
                options = st.session_state['options']

            print(options)
            print(options_titles)
            
            # display options and get user input
            choice = st.selectbox(
                "Choose a song",
                options,
                format_func=lambda x: options_titles[x[0]]
            )
            print(choice)

            # TODO: fix >10mins songs arnt rlly ignored (they arnt, it only shows None for the timing)

            st.session_state['songSelection'] = choice
            print(choice[0])

            if choice[0] !=0 and is_checkbox_filled():
                # download song
                st.write("Getting song... (wait for a download button to appear :D)")
                downloadYTFromLink(options[choice[0]][2], options[choice[0]][0])

    with batchDownload:
        st.subheader("Batch Download (defaults to first result of query)")

        getSongs = st.text_input("Songs to download (separate by comma)")

        if st.button("Get Songs"):
            songs = getSongs.split(",")

            for song in songs:
                st.write("Retrieving search results...")
                options = searchYouTube(song)

                # download song
                st.write("Downloading song...")
                downloadYTFromLink(options[0][2], options[0][0])