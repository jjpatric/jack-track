# Jack Track

Jack Track is a Python script designed to notify users when a song is repeated within the same day between 8AM-6PM for the Jack 96.9 radio contest. The script automates the process of recording songs played for each day and sending you a text when a repeat is detected so you can manually send in a contest entry.

I also included the song longs I captured during the contest so I can analyze what songs were played the most or least for my own curiosity.

## Features

- Log all played songs
- Sends texts via twilio when a repeated song is played
- Helps maximize your chances in the Jack 96.9 contest

## Getting Started

1. **Clone the repository**  
    ```bash
    git clone https://github.com/yourusername/jack-track.git
    cd jack-track
    ```

2. **Set up a virtual environment and install dependencies**  
    It's recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. **Configure your phone numbers and Twilio credentials**  
    Edit the `jack-track.py` file and add your Twilio account credentials and the phone numbers you want to use.

4. **Run the script**  
    Run:
    python jack-track.py
    ```

## Disclaimer

This project is not affiliated with or endorsed by Jack 96.9. It is an independent tool created for personal use. The contest rules specify no automated entries are allowed but I believe this tools is a loop-hole because it does not submit entries for you, it only prompts you to submit it manually when a repeat is played.
