# getMusic

A quick implmentation of selenium, yt-dlp and streamlit for personal use. yt-dlp does not violate copyright policies here, though I'm simply using an already available library I wanted to stay on the safe side and not make it too public (hence the password lock).

Date: February 2023<br/>
Live site (locked with password): https://download-music.streamlit.app/

Here's a quick demo of the music being downloaded. We first enter the name of the song we want to download/listen to, then we select the video with corresponding title and durations to get a download link.

![Demo of the App](assets/musicDownloadDemo.gif)

## Tech Stack
- Libraries: Selenium, bs4, requests, yt-dlp, lxml
- How it works: Selenium and bs4 to scrape for the videos returned from youtube query with given song name input, then yt-dlp to download selected video in mp3 format

## How it works
Other than being abe to download specific songs, I also made it possible to batch download songs