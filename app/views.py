from app import app
from flask import render_template, request, redirect, url_for, session
import sys
sys.path.insert(0, "mygpoclient") #gpo won't work without this
import mygpoclient
from mygpoclient import simple, api, public, feeds
import datetime

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

@app.route('/going-somewhere')
def going_somewhere():
    return render_template('going-somewhere.html')

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
