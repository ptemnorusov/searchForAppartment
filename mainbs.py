import os
import requests
from bs4 import BeautifulSoup
import telebot
from urllib.parse import urljoin
import time
import json

from keys import BOT_TOKEN
from keys import CHAT_ID
from keys import searchURL
from keys import searchURLDomain
from keys import CDNLink


bot = telebot.TeleBot(BOT_TOKEN)


def load_discovered_links():
    if os.path.exists(DISCOVERED_LINKS_FILE):
        try:
            with open(DISCOVERED_LINKS_FILE, "r") as f:
                content = f.read().strip()  # Read the file content and strip any extra whitespace
                if content:  # If the file is not empty
                    links = json.loads(content)
                    return set(links)  # Convert to a set to avoid duplicates
                else:
                    return set()  # Return an empty set if the file is empty
        except json.JSONDecodeError:
            print("Error: JSON file is not properly formatted.")
            return set()  # Return an empty set if the file is corrupted
    return set()  # Return an empty set if the file doesn't exist


def save_discovered_links(discovered_links):
    with open(DISCOVERED_LINKS_FILE, "w") as f:
        json.dump(list(discovered_links), f)


def saveAndSentAd(url):
    folder_name = url.split('/')[-1]

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Get the webpage content
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    time.sleep(5)

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the required information
    title = soup.select_one('h1[data-cy="adPageAdTitle"]').text.strip()
    price = soup.select_one('strong[data-cy="adPageHeaderPrice"]').text.strip()
    description = soup.select_one('div[data-cy="adPageAdDescription"]').text.strip()
    address = soup.select_one('div.css-70qvj9.e42rcgs0 > a').text.strip()

    images = []
    for img_tag in soup.find_all('img'):
        img_src = img_tag.get('src')
        if img_src and img_src.startswith(CDNLink):
            images.append(img_src)
 

    # Save images to the specified folder
    image_paths = []
    for index, img_url in enumerate(images):
        img_data = requests.get(img_url).content
        img_name = f"{folder_name}/image_{index + 1}.jpg"
        with open(img_name, 'wb') as handler:
            handler.write(img_data)
        image_paths.append(img_name)
        if index > 2:
            break

    # Prepare the message to be sent
    message = f"""Ad:{title} \nPrice: {price} \nAddress: {address} \nDescription: {description}\nLink: {url}"""

    try:
        # Send the message to the Telegram bot
        bot.send_message(CHAT_ID, message)

        # Send all images to the Telegram bot
        for image_path in image_paths:
            try:
                with open(image_path, 'rb') as img_file:
                    bot.send_photo(CHAT_ID, img_file)
                time.sleep(1)
                print(f"Image {image_path} sent successfully.")
            except Exception as e:
                print(f"Error sending image {image_path}: {e}")
                return  # Stop the function if there's an error sending any image

        print("Data and images sent successfully.")
    except Exception as e:
        print(f"Error sending message or images: {e}")


def extract_new_links():
    try:
        # Send a GET request to fetch the HTML content of the page
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(searchURL, headers=headers)
        response.raise_for_status()  # Check for any request errors
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all anchor tags with href starting with '/ro/oferta/'
        offer_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('/ro/oferta/')]

        offer_links = list(set(offer_links))

        # Filter out links that have already been discovered
        new_links = [searchURLDomain + link for link in offer_links if link not in discovered_links]
        print(f"New links: {new_links}")
        print(f"Discovered links: {discovered_links}")

        # Add new links to the set and print them
        for link in new_links:
            print(f"New link found: {link}. Sending the info to TG")
            try:
                saveAndSentAd(link)
            except:
                print("Failed to send the link.")
            discovered_links.add(link)
            time.sleep(60)
        
        save_discovered_links(discovered_links)
        


    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")


def refresh_page():
    while True:
        print("Checking for new links...")
        try:
            extract_new_links()
        except:
            pass
        time.sleep(60)  # Wait for 60 seconds before the next check



discovered_links = load_discovered_links()
DISCOVERED_LINKS_FILE = "discovered_links.json"


# Start the link extraction and refresh loop
if __name__ == "__main__":
    refresh_page()