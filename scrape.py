import json
import os
import requests
import time

secrets = open('secrets.json', 'r')
objSecrets = json.load(secrets)
API_KEY = objSecrets['api_key']
AUTH_KEY = objSecrets['auth_key']
TORR_PASS = objSecrets['torr_pass']
secrets.close()

HEADER = {"x-api-key": API_KEY}

API_URL = 'https://gazellegames.net/api.php'
TORR_URL = 'https://gazellegames.net/torrents.php?action=download&id='
REQUEST_STRING = '?request='
SEARCH_STRING = REQUEST_STRING + 'search&search_type=torrents'
TORRENT_STRING = REQUEST_STRING + 'torrentgroup&'

SPECIAL_EDITIONS = ["redump", "nointro", "no-intro", "no intro"]
USA_REGIONS = ["USA", "NTSC"]
EUR_REGIONS = ["Europe", "PAL", "PAL-E"]
JPN_REGIONS = ["Japan", "NTSC-J"]

def generate_list(console_torrents):
    torrents_to_fetch = []
    for group, groupData in console_torrents.items():
        if('Torrents' in groupData.keys() and groupData['Torrents'] != []):
            for torrent, torrentData in groupData['Torrents'].items():
                if torrentData['RemasterTitle'] != "" and any(type in torrentData['RemasterTitle'].lower() for type in SPECIAL_EDITIONS):
                    if(targetRegion != ""):
                        if( any(torrentData['Region'] in type for type in targetRegion) ):
                            torrents_to_fetch.append(torrentData['ID'])
                    else:
                        torrents_to_fetch.append(torrentData['ID'])
    
    print(f"Number of torrents to fetch: {len(torrents_to_fetch)}")
    return torrents_to_fetch

def fetch_pages(session):
    final_torrents = []
    target_page = 1

    # do-while isn't in python, so we will just have to make a mangled loop.
    constructed_request = API_URL + SEARCH_STRING + "&page=" + str(target_page) + "&artistname=" + targetConsole
    console_torrents = session.get(constructed_request, headers=HEADER)
    console_torrents = json.loads(console_torrents.text)

    while(console_torrents['response'] != []):
        console_torrents = console_torrents['response']
        final_torrents += generate_list(console_torrents)
        
        target_page += 1
        print(f"Fetching page {target_page}")
        constructed_request = constructed_request = API_URL + SEARCH_STRING + "&page=" + str(target_page) + "&artistname=" + targetConsole
        time.sleep(2.1) # We are capped at 5 requests per 10 seconds, so sleep such that we cannot exceed that.
        console_torrents = session.get(constructed_request, headers=HEADER)
        console_torrents = json.loads(console_torrents.text)


    print(f"Num of final torrents to fetch: {len(final_torrents)}")
    return final_torrents

def download_torrents(torrent_ids, session):
    directory = (f"./{targetConsole}/")
    if(not os.path.exists(directory)):
        os.makedirs(directory)

    for index, id in enumerate(torrent_ids):
        print(f"Downloading Torrent {index + 1} out of {len(torrent_ids)}")
        torrent_url = TORR_URL + id + "&authkey=" +  AUTH_KEY + "&torrent_pass=" + TORR_PASS
        torrent = session.get(torrent_url)
        torr_file = open( (directory + id + '.torrent'), 'wb')
        torr_file.write(torrent.content)
        torr_file.close()
        time.sleep(2.1) # We are hitting the website and not the API anymore, but I don't know if we'll get rate limited. Let's just be nice about it.



targetConsole = input("Target Console: ")
targetRegion = input("Target Region (Japan, Europe, USA, empty for All): ")
if(targetRegion == "Japan"):
    targetRegion = JPN_REGIONS
elif(targetRegion == "Europe"):
    targetRegion = EUR_REGIONS
elif(targetRegion == "USA"):
    targetRegion = USA_REGIONS

print(f"Target Region: {targetRegion}")
print(f"Target Console: {targetConsole}")

session = requests.Session()
download_torrents( fetch_pages(session), session )
