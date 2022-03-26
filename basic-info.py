import json
import os
import sys
import re

# check for and collect JSON files
def checkpath(thispath):
    # if path points at a file, check if it is actually a JSON
    if os.path.isfile(thispath):
        if not thispath.endswith('.json'):
            print("Sorry, not a JSON.")
            return []
        else: return [thispath]
    # if path points to a folder, search it and subfolders for JSON files
    if os.path.isdir(thispath):
        jsons = []
        for root, dirs, files in os.walk(thispath):
            for name in files:
                # if we have a JSON file and it is not in a recycle bin, add it to our file list
                if (name.endswith(".json")) and not (re.search(r"(.*)RECYCLE(.*)", root) != None):
                    jsons.append(os.path.join(root, name))
    else: 
        print("Sorry, not an existing path.")
        return []
    return jsons
        
# call checkpath until we got some files or break
def getfilelist(whichpath):
    currentlist = checkpath(whichpath)
    while len(currentlist) == 0:
        print("\nNo JSON fiel found. \nSearch a different path?")
        newpath = str(input("Path: "))
        if len(newpath) > 0: currentlist = checkpath(newpath)
        else: sys.exit('No input, terminating.')
    return currentlist

# get a list of dict keys for a given value
def get_key(whichdict, val):
    allkeys = 'unknown'
    for key, value in whichdict.items():
        if val == value:
            if (allkeys == 'unknown'): allkeys = key
            else: allkeys = ', '.join((str(allkeys), str(key)))
    return allkeys

# do basic analysis for a given JSON
def analyse (file):
    #Open JSON file if it exists, return as dict
    file_exists = os.path.exists(file)
    if not file_exists:
        print(f"FAILED opening {file}. Skipped.")
        return 0
    else:
        f = open(file, "r", encoding='utf-8')
    chat = json.load(f)
    
    #roughly check if it is in fact a Telegram export
    if not 'messages' in chat: 
        print(f"\n\nFAILED: No Telegram export JSON. Skipping {file}.")
        return 0

    # prepare our storages for users, privileged users, links and counters of message types
    differentuser = {}
    vips = {'unknown': 'unknown'}
    links = {}
    messagecount = {'posts': 0, 'photos': 0, 'videos': 0, 'voice': 0}

    print('\n\n-------------------------------\nCHANNEL NAME:', chat['name'], '\n-------------------------------')
    for msg in chat['messages']:
        #filter interesting users from service messages
        if msg['type'] == "service":
            if 'action' in msg:
                if msg['action'] == "create_channel": vips[msg['actor_id']] = 'creator'
                # we might want to differentiate between channel and group creators later, but for now we treat them the same
                if msg['action'] == "migrate_from_group": vips[msg['actor_id']] = 'creator'
                if (msg['action'] == "pin_message") and not (msg['actor_id'] in vips):
                    vips[msg['actor_id']] = 'moderator'
                    
        #now go through the actual messages
        if msg['type'] == "message":
            messagecount['posts'] += 1
            #if a user is new to us we add them to our dict
            if not msg['from_id'] in differentuser: differentuser[msg['from_id']] = [0, msg['from']]
            #and give them a point for every single message
            differentuser[msg['from_id']][0]+=1
            # we also count different types of messages
            if 'photo' in msg: messagecount['photos'] += 1
            if ('mediatype' in msg) and (msg['mediatype'] == 'video_file'): messagecount['videos'] += 1
            if ('mediatype' in msg) and (msg['mediatype'] == 'voice_message'): messagecount['voice'] += 1
            #if the message text is a list
            if type(msg['text']) == type([]):
                for element in msg['text']:
                    #if element is a dict and it contains a link
                    if (type(element) == type({})) and (element['type'] == "link"):
                            #store it, if it's new
                            if not element["text"] in links: links[element['text']] = 0
                            #increase link counter
                            links[element['text']]+=1

    #print our results
    creator = get_key(vips,'creator')
    print(f"\nChannel/group creator: {creator}", f"({differentuser.get(creator)[1]})" if ((creator != 'unknown') and (creator in differentuser)) else "")
    print(f"Moderator(s): {get_key(vips,'moderator')}")
    print(f"\n{messagecount.get('posts')} posts by {len(differentuser)} account(s).")
    print(f"{len(links)} links, {messagecount.get('photos')} photos, {messagecount.get('videos')} videos and {messagecount.get('voice')} voice messages.")
    print("\nMost active user(s):")
    #sort our dict entries and display highest 5
    for user in sorted(differentuser.items(), key=lambda x: x[1][0], reverse=True)[0:5]:
        print(f"{user[0]} ({user[1][1]}): {user[1][0]} messages")

    print(f"\nMost linked to:")
    #same, same but different
    for link in sorted(links.items(), key=lambda x: x[1], reverse=True)[0:5]:
        print(f"{link[0]}: {link[1]} time(s)")

    # closing file
    f.close()



# main
decision = 'n'
jsons = getfilelist(os.getcwd())
while decision == 'n':
    print(f"\nFound {len(jsons)} JSONs.")
    decision = str(input("(C)ontinue or (n)ew path? "))
    if decision != 'n': break
    newpath = str(input("Path: "))
    jsons = getfilelist(newpath)

for file in jsons: analyse(file)

