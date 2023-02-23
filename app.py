import streamlit as st

st.title("Download Music :D")
st.write("Choose between downloading a single song where you will be able to select the exact song you'd like or batch \
         downloading songs which wil default to the first result of the query from YouTube.")

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
def get_binary_file_downloader_html(bin_file, song_title):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{song_title}">Download {song_title}</a>'
    return href

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
    soup = BeautifulSoup(html, "html.parser")

    videos_soup = soup.find_all("a", id="video-title")
    videos = []

    for video in videos_soup[:5]: # only get top 5 results
        title = video["title"]
        link = "https://www.youtube.com" + video["href"]

        if "shorts" not in title:
            videos.append((title, link))

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
    }

    # set provide the path using --ffmpeg-location
    # ydl_opts['ffmpeg_location'] = r'C:\ffmpeg\bin\ffmpeg.exe'
    ydl_opts['ffmpeg_location'] = r"/usr/bin/ffmpeg"
    ydl_opts['outtmpl'] = 'song'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])

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
            options = searchYouTube(search)

            # get only the first item in the list of tuples
            options_titles = [(None, "Select a song (disabled)")]
            # add numbers from 0 to list as a tuple
            options_titles.extend(list(enumerate([option[0] for option in options])))
            st.session_state['options_titles'] = options_titles
            st.session_state['options'] = options
        else:
            st.write("Retrieving search results...")
            st.write("Getting Songs...")
            options_titles = st.session_state['options_titles']
            options = st.session_state['options']

        # display options and get user input
        # TOOD: ait for input, start from no selection :") AHAHA
        choice = st.selectbox("Choose a song (default selected first one)", options_titles)
        st.session_state['songSelection'] = choice
        print(choice[0])

        if choice[0] is not None and is_checkbox_filled():
            # download song
            st.write("Downloading song...")
            downloadYTFromLink(options[choice[0]][1], options[choice[0]][0])

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
            downloadYTFromLink(options[0][1], options[0][0])