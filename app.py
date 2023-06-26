import time
import streamlit as st
import cachetools
from utils import *
import shutil

def get_github_username(url):
    """
    Get the GitHub username from the URL.

    Args:
      url: The GitHub URL.

    Returns:
      The GitHub username.
    """

    match = re.match(r"https://github.com/(.*)", url)
    if match:
        return match.group(1)
    else:
        return None

def is_url(string):
    # Regular expression pattern to match a URL
    url_pattern = re.compile(
        r"^(https?://)?([A-Za-z0-9\-]+\.){1,}[A-Za-z]{2,}(:\d{1,5})?(/.*)?$"
    )
    return bool(re.match(url_pattern, string))    

def main():
    st.title("Github Automated Analysis")
    username = (st.text_input("Enter the GitHub URL or username:"))
    if st.button('Analyse'):
        if is_url(username):
            username = get_github_username(username)
        print(username)
        text = run(username)
        text = st.markdown(text)
    



if __name__ == "__main__":
    main()

