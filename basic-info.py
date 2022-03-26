import json
import os
import sys
import re

# check for and collect JSON files
def checkpath(thispath):
    if os.path.isfile(thispath):
        if not thispath.endswith('.json'):
            print("Sorry, kein JSON.")
            return []
        else: return [thispath]
    if os.path.isdir(thispath):
        jsons = []
        for root, dirs, files in os.walk(thispath):
            for name in files:
                if (name.endswith(".json")) and not (re.search(r"(.*)RECYCLE(.*)", root) != None):
                    jsons.append(os.path.join(root, name))
    else: 
        print("Sorry, kein existierender Pfad.")
        return []
    return jsons
        
# call checkpath until we got some files or break
def getfilelist(whichpath):
    currentlist = checkpath(whichpath)
    while len(currentlist) == 0:
        print("\nKein JSON gefunden. \nAnderen Pfad durchsuchen?")
        newpath = str(input("Pfad: "))
        if len(newpath) > 0: currentlist = checkpath(newpath)
        else: sys.exit('Keine Eingabe, beendet.')
    return currentlist

# get a list of dict keys for a given value
def get_key(whichdict, val):
    allkeys = 'unbekannt'
    for key, value in whichdict.items():
        if val == value:
            if (allkeys == 'unbekannt'): allkeys = key
            else: allkeys = ', '.join((str(allkeys), str(key)))
    return allkeys

#
def analyse (file):
    #Open JSON file if it exists, return as dict
    file_exists = os.path.exists(file)
    if not file_exists:
        print(f"FEHLER beim Öffnen der Datei {file}. Übersprungen.")
        return 0
    else:
        f = open(file, "r", encoding='utf-8')
    chat = json.load(f)
    
    #roughly check if it is in fact a Telegram export
    if not 'messages' in chat: 
        print(f"\n\nFEHLER: Kein Telegram JSON. Überspringe {file}.")
        return 0
    differentuser = {}
    vips = {'unbekannt': 'unbekannt'}
    links = {}
    messagecount = {'posts': 0, 'photos': 0, 'videos': 0, 'voice': 0}

    print('\n\n-------------------------------\nKANALNAME:', chat['name'], '\n-------------------------------')
    for msg in chat['messages']:
        #interessante user aus den systemmeldungen filtern
        if msg['type'] == "service":
            if 'action' in msg:
                if msg['action'] == "create_channel": vips[msg['actor_id']] = 'creator'
                if msg['action'] == "migrate_from_group": vips[msg['actor_id']] = 'creator'
                if (msg['action'] == "pin_message") and not (msg['actor_id'] in vips):
                    vips[msg['actor_id']] = 'moderator'
                    
        #nun die nachrichten durchgehen
        if msg['type'] == "message":
            messagecount['posts'] += 1
            #wenn der nutzer nicht bekannt ist, aufnehmen
            if not msg['from_id'] in differentuser:
                differentuser[msg['from_id']] = [0, msg['from']]
            #benutzer bekommt einen punkt für slytherin
            differentuser[msg['from_id']][0]+=1
            if 'photo' in msg: messagecount['photos'] += 1
            if ('mediatype' in msg) and (msg['mediatype'] == 'video_file'): messagecount['videos'] += 1
            if ('mediatype' in msg) and (msg['mediatype'] == 'voice_message'): messagecount['voice'] += 1
            #wenn die nachricht eine liste ist
            if type(msg['text']) == type([]):
                for element in msg['text']:
                    #und das element in der liste ein dict ist
                    if type(element) == type({}):
                        #und das dict ein link objekt ist
                        if element['type'] == "link":
                            #wird dieser hinzugefügt, sofern er nicht bereits existiert
                            if not element["text"] in links:
                                links[element['text']] = 0
                            #und wird ebenfalls hochgezählt
                            links[element['text']]+=1

    #textausgabe der ergebnisse
    ersteller = get_key(vips,'creator')
    print(f"\nKanalersteller: {ersteller}", f"({differentuser.get(ersteller)[1]})" if ((ersteller != 'unbekannt') and (ersteller in differentuser)) else "")
    print(f"Moderatoren: {get_key(vips,'moderator')}")
    print(f"\n{messagecount.get('posts')} einzelne Posts von {len(differentuser)} verschiedenen Account(s).")
    print(f"Es wurden {len(links)} Links, {messagecount.get('photos')} Fotos, {messagecount.get('videos')} Videos und {messagecount.get('voice')} Sprachnachrichten gepostet.")
    print("\nHöchste Partizipation:")
    #dict auseinandernehmen, sortieren nach punkten, letzte 5 einträge(=höchste zahlen) anzeigen
    for user in sorted(differentuser.items(), key=lambda x: x[1][0])[-5:]:
        print(f"{user[0]} ({user[1][1]}): {user[1][0]} Nachrichten")

    print(f"\nAm häufigsten verlinkt:")
    #same, same but different
    for link in sorted(links.items(), key=lambda x: x[1])[-5:]:
        print(f"{link[0]}: {link[1]} mal")

    # Closing file
    f.close()



# main
decision = 'n'
jsons = getfilelist(os.getcwd())
while decision == 'n':
    print(f"\n{len(jsons)} JSONs gefunden.")
    decision = str(input("(F)ortfahren oder (n)euen Pfad? "))
    if decision != 'n': break
    newpath = str(input("Pfad: "))
    jsons = getfilelist(newpath)

for file in jsons: analyse(file)

