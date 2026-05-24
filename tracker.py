import asyncio
import json
import os
import subprocess
import time
import google.generativeai as genai
from twikit import Client

# === CONFIGURATION ===
TWITTER_USER = "HistoricalAcco1"
TWITTER_EMAIL = "histacco@gmail.com"
TWITTER_PASS = "2002Ulas"
TWITTER_LIST_ID = "2058624212386845028 " # The ID from your Twitter list URL
GEMINI_API_KEY = "AIzaSyCE_tfY3rbLk8j6fFqfk7jTS8XpX3ZjM0o"

# Automatically detects the exact folder this script is sitting in on your laptop
GITHUB_REPO_PATH = os.path.dirname(os.path.abspath(__file__))

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})

client = Client('en-US')

async def check_tweets():
    print("[*] Logging into Twitter...")
    try:
        client.load_cookies('cookies.json')
    except:
        await client.login(auth_info_1=TWITTER_USER, auth_info_2=TWITTER_EMAIL, password=TWITTER_PASS)
        client.save_cookies('cookies.json')

    print(f"[*] Fetching List ID: {TWITTER_LIST_ID}")
    
    try:
        twitter_list = await client.get_list(TWITTER_LIST_ID)
        tweets = await twitter_list.get_tweets()
    except Exception as e:
        print(f"[!] Error fetching list: {e}")
        return

    # Ensure we are in the correct directory for Git operations
    os.chdir(GITHUB_REPO_PATH)
    
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
    else:
        existing_data = []

    existing_ids = [item.get('tweet_id') for item in existing_data]
    new_events_found = False

    for tweet in tweets:
        if tweet.id in existing_ids:
            continue
            
        print(f"[*] Analyzing new tweet from {tweet.user.name}...")
        
        prompt = f"""
        Analyze this text from a CHP provincial Twitter account. 
        Is it announcing a specific upcoming public protest, rally, mobilization, or press statement?
        If yes, extract the details. Do not include past events.
        
        Text: "{tweet.text}"
        
        Return STRICTLY in this JSON format:
        {{
            "is_event": true or false,
            "province": "Name of province or null",
            "date": "Date of event or null",
            "time": "Time of event or null",
            "location": "Specific gathering location or null",
            "topic": "What the event is about or null"
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            
            if result.get('is_event') == True:
                print(f"[!] EVENT FOUND: {result.get('province')} - {result.get('topic')}")
                result['tweet_id'] = tweet.id
                result['source_url'] = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                existing_data.append(result)
                new_events_found = True
        except Exception as e:
            print(f"[!] AI processing error: {e}")

    if new_events_found:
        print("[*] Saving to JSON and pushing to GitHub...")
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
        subprocess.run(['git', 'add', 'data.json'])
        subprocess.run(['git', 'commit', '-m', 'Automated event update'])
        subprocess.run(['git', 'push'])
        print("[+] Live website updated successfully.")
    else:
        print("[*] No new events found.")

def main():
    print("[*] Starting tracker loop...")
    while True:
        try:
            asyncio.run(check_tweets())
        except Exception as e:
            print(f"[!] Critical loop error: {e}")
        
        print("[*] Sleeping for 5 minutes...")
        time.sleep(300)

if __name__ == "__main__":
    main()
