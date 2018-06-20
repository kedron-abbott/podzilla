from app import app
from flask import render_template, request, redirect, url_for, session
import sys
sys.path.insert(0, "mygpoclient") #gpo won't work without this for me
import mygpoclient
from mygpoclient import simple, api, public, feeds
import datetime
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
http = urllib3.PoolManager()

# LOGGING IN:
# SUMMARY: log into using your gPodder account info.
# HOW:
# 1. Type in your username and password from your gPodder account
#     a) If invalid, you will be asked to try again
# 2. Upon submittion of login info, you will be redirected to either
# the dashboard or the select devices page
#     a) If you have 2+ devices, you will be asked to select one. Options
#     are available via dropdown menu, and you will see the device name and
#     how many subscriptions that device has
#     b) If you have 1 device, it will default to that one. No need to select devices
#     c) If you have 0 devices, Podzilla will create one for you with your username.
#     It will not have any subscriptions
#     d) You can go into Account to change device at anytime
#pages
@app.route('/')

@app.route('/login')
def login():
    logout()
    title = "Login"
    return render_template('login.html', title = title)

@app.route('/select-device', methods = ['POST', 'GET'])
def select_device():
    session['status'] = None
    session['device_id'] = None
    if not session['username']:
        username = request.form.getlist('username')[0]
        session['username'] = username
        password = request.form.getlist('password')[0]
        session['password'] = password
    else:
        username = session['username']
        password = session['password']
    try:
        api_client = api.MygPodderClient(username, password)
        devices = api_client.get_devices()
        title = "Devices"
        if len(devices) == 0:
            session['device_id'] = username + "s-device" #no device. Made one for ya. No subs tho :(
            return redirect(url_for('dashboard'))
        if len(devices) == 1:
            session['device_id'] = devices[0].device_id #only one device. Defaults to that. Easy peasysession.
            return redirect(url_for('dashboard'))
        return render_template('select-devices.html', devices = devices, title = title)
    except:
        login()
        title = "login"
        status = "attempt"
        return render_template('login.html', title = title, status = status)



@app.route('/dashboard', methods = ['POST', 'GET'])
def dashboard():
    if not session.get('device_id'):
        device_id = request.form.get('chosen_device')
    else:
        device_id = session.get('device_id')
    username = session['username']
    session['device_id'] = device_id
    return render_template('dashboard.html', username = username)

# ACCOUNT:
# SUMMARY: check status of account or change device
# HOW:
# 1. User will see:
#   a) username associated to current account that's logged in
#   b) device currently being used to gather subscription data
#   c) how many podcasts they're subscribed to from that device
# 2. User will have the option to:
#   a) View their subscriptions
#   b) logout of current account
#   c) change the device used to gather subscriptions
#     1. note: if user only has 1 device, user will be directed to dashboard instead
#     of the device-select page
@app.route('/account')
def account():
    username = session['username']
    password = session['password']
    device_id = session['device_id']
    api_client = api.MygPodderClient(username, password)
    devices = api_client.get_devices()
    for dev in devices:
        if dev.device_id == device_id:
            num_subs = dev.subscriptions
            break
    return render_template('account.html', device_id = device_id, username = username, num_subs = num_subs)

# SUBSCRIPTIONS & BROWSE:
# SUMMARY: view podcasts that user is subscribed to or search for new ones
# HOW:
# 1. User will see the following info per subscription:
#   a) Title
#   b) Description
#   c) Number of podcasts
# HOW[BROWSE]:
# 1. You can also see the top podcasts and the top tags
#     a) selecting a podcasts will take you to their site
#     b) selecting a tag will show you top podcasts within that tag
@app.route('/subscriptions')
def subscriptions():
    username = session['username']
    password = session['password']
    device_id = session['device_id']
    client = simple.SimpleClient(username, password)
    links = client.get_subscriptions(device_id)
    pub_client = public.PublicClient()
    subscriptions = []
    for link in links:
        subscriptions.append(pub_client.get_podcast_data(link))
    subscriptions = shortenDescriptions(subscriptions) #some descriptions are way too long
    return render_template('subscriptions.html', subscriptions = subscriptions)

@app.route('/browse')
def browse():
    client = public.PublicClient()
    toplist = client.get_toplist(9)
    toplist = shortenDescriptions(toplist)
    top_tags = client.get_toptags()
    return render_template('browse.html', toplist = toplist, top_tags = top_tags)

@app.route('/results', methods = ['POST', 'GET'])
def results():
    if request.form.get('tag'):
        search_term = request.form.get('tag')
    else:
        search_term = request.form.getlist('search_term')[0]
    client = public.PublicClient()
    search_results = client.search_podcasts(search_term)
    search_results = shortenDescriptions(search_results)
    return render_template('results.html', search_results = search_results, search_term = search_term)


# GOING SOMEWHERE:
# SUMMARY: Find podcasts to listen to that fit your travel time!
# HOW:
# 1. Type in your departure and destination locations
# 2. Podzilla will determine the travel time (default by car)
#     a) It takes your locations and plugs them into a url that returns a json object
#     powered by the Google Maps & Distance Matrix APIs
#         1. If the location is not valid, you are asked to retry
#         2. FOR EXAMPLE: 'Gryphon Coffee' is not valid, but 'Gryphon Coffee Shop' is
#         3. You can input places, cities, addresses, etc.
#     b) It takes that data and stores it in an object (map_obj)
# 3. User will be redirected to a results page ('/traveling')
# 4. This page will show user podcasts that fit within their travel time
#     a) Suggestions are pulled from their subscription list by parsing through
#     xml data and comparing the duration of recent episodes
#         1. If their subscription list is < 5, Podzilla pulls from toplists instead

@app.route('/going-somewhere')
def going_somewhere():
    return render_template('going-somewhere.html')

@app.route('/traveling', methods = ['POST', 'GET'])
def traveling():
    departure = request.form.getlist('departure')[0]
    session['departure'] = departure
    destination = request.form.getlist('destination')[0]
    session['destination'] = destination
    map_url = getMapURL(departure, destination)
    map_obj = gatherMapData(map_url)
    return render_template('traveling.html', time_text = map_obj.duration_text, destination = destination, departure = departure)

class map(object):
    duration_text = ""
    duration_value = 0
    distance_text = ""
    distance_value = 0

    # The class "constructor" - It's actually an initializer
    def __init__(self, duration_text, duration_value, distance_text, distance_value):
        self.duration_text = duration_text
        self.duration_value = duration_value
        self.distance_text = distance_text
        self.distance_value = distance_value

def gatherMapData(url):
    try:
        response = http.request('GET', url)
        data = response.data
        info = json.loads(data)
        duration_text = info['rows'][0]['elements'][0]['duration']['text']
        duration_value = info['rows'][0]['elements'][0]['duration']['value']
        distance_text = info['rows'][0]['elements'][0]['distance']['text']
        distance_value = info['rows'][0]['elements'][0]['distance']['value']
        map_obj = map(duration_text, duration_value, distance_text, distance_value)
        return map_obj
    except KeyError:
        map_obj = map("no", 100, "no", 200)
def getMapURL(departure, destination):
    one = departure.strip().replace(" ", "+")
    two = destination.strip().replace(" ", "+")
    base = 'https://maps.googleapis.com/maps/api/distancematrix/json?origins='
    url = base + one + "&destinations=" + two
    return url

def logout():
    session['device_id'] = None
    session['username'] = None
    session['password'] = None

def shortenDescriptions(subscriptions):
    for item in subscriptions:
        str = item.description
        if len(str) >= 290:
            str = str[0:291]
            sentenceEnd = max(str.rfind(i) for i in ".!?") + 1
            str = str[0:sentenceEnd]
        item.description = str
    return subscriptions
