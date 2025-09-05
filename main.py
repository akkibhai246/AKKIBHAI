import time
import requests
import random
import os
from datetime import datetime, timedelta, timezone
from threading import Thread, Event
from flask import Flask, send_from_directory
from flask import Flask, request, render_template_string
import json
import sys
from platform import system
import os
import subprocess
import http.server
import threading


app = Flask(__name__)

app.debug = True

@app.route("/")
def home():
    return "Service running!"

def keep_awake():
    url = "https://akkibhai.onrender.com"
    while True:
        try:
            requests.get(url)
            print("Pinged self to stay awake.")
        except Exception as e:
            print("Ping failed:", e)
        time.sleep(300)  # every 5 min

user_agents = [
    'Mozilla/5.0 (Linux; Android 14; 22101316|Build/Up1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.111 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36'
]

stop_events = {}
pause_events = {}
threads = {}


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        
def get_kolkata_time():
    kolkata_offset = timedelta(hours=5, minutes=30)
    kolkata_time = datetime.now(timezone.utc) + kolkata_offset
    return kolkata_time.strftime('%d-%m-%Y %I:%M:%S %p IST')


def send_messages(tokens, Convo_ids, Post_ids, hater_names, messages, sender_names,
                  delay, batch_count, batch_delay, loop_delay, task_id):
    stop_event = stop_events[task_id]
    pause_event = pause_events[task_id]

    token_index = 0
    convo_index = 0
    post_index = 0
    msg_index = 0  # for cycling through messages

    token_count = len(tokens)
    convo_count = len(Convo_ids) if Convo_ids else 0
    post_count = len(Post_ids) if Post_ids else 0

    invalid_tokens = set()
    last_checked = {}
    retry_after = 60  # seconds

    while not stop_event.is_set():
        # current token
        access_token = tokens[token_index % token_count]
        token_no = (token_index % token_count) + 1

        # skip if invalid
        if access_token in invalid_tokens:
            if time.time() - last_checked.get(access_token, 0) >= retry_after:
                try:
                    res = requests.get(f"https://graph.facebook.com/me?access_token={access_token}")
                    if res.status_code == 200 and 'id' in res.json():
                        print(f"\033[96m[4KK1-H3R3✔] Token recovered: {access_token[:10]}...")
                        invalid_tokens.remove(access_token)
                    else:
                        last_checked[access_token] = time.time()
                        token_index += 1
                        continue
                except:
                    last_checked[access_token] = time.time()
                    token_index += 1
                    continue
            else:
                token_index += 1
                continue

        # send batch_count messages with current token
        for _ in range(batch_count):
            if stop_event.is_set():
                break
            pause_event.wait()

            # pick next message (cycle if end reached)
            msg = messages[msg_index % len(messages)]
            msg_index += 1

            hater = random.choice(hater_names).strip() if hater_names else ""
            sender = random.choice(sender_names).strip() if sender_names else ""
            full_msg = f"{hater} {msg.strip()}\n{sender}".strip()
            event_time = get_kolkata_time()

            headers = {
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.1746.57'
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.1958.29'
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0 Unique/93.7.2506.7'
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0 Unique/97.7.6972.67',
    'Accept': 'text/html,application/xhtml+xml,application/xml,application/json;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.Google.com'
            }

            try:
                # convo send
                if Convo_ids:
                    convo_id = Convo_ids[convo_index % convo_count]
                    convo_index += 1
                    url = f"https://graph.facebook.com/v14.0/t_{convo_id}/"
                    parameters = {'access_token': access_token, 'message': full_msg}
                    response = requests.post(url, json=parameters, headers=headers)
                    if response.status_code == 200:
                        print(f"\033 (4KK1-H3R3)[92m[{event_time}] Token {token_no} sent: {full_msg}")
                    elif response.status_code in [400, 401, 403]:
                        print(f"\033 (4KK1-H3R3)[91m[✖] Token {token_no} failed: {response.text}")
                        invalid_tokens.add(access_token)
                        last_checked[access_token] = time.time()
                        break  # stop this batch early

                # post send
                if Post_ids:
                    post_id = Post_ids[post_index % post_count].strip()
                    post_index += 1
                    url = f"https://graph.facebook.com/v14.0/{post_id}/comments"
                    parameters = {'access_token': access_token, 'message': full_msg}
                    response = requests.post(url, json=parameters, headers=headers)
                    if response.status_code == 200:
                        print(f"\033[92m (4KK1-H3R3)[{event_time}] Token {token_no} commented: {full_msg}")
                    elif response.status_code in [400, 401, 403]:
                        print(f"\033 (4KK1-H3R3)[91m[✖] Token {token_no} failed: {response.text}")
                        invalid_tokens.add(access_token)
                        last_checked[access_token] = time.time()
                        break  # stop this batch early

                if delay > 0:
                    time.sleep(delay)

            except Exception as e:
                print(f"\033(4KK1-H3R3)[91m[!!] Exception for token {token_no}: {str(e)}")
                break

        # batch done → wait batch_delay
        if batch_delay > 0:
            time.sleep(batch_delay)

        # move to next token
        token_index += 1

        # after one full round of all tokens → loop_delay
        if token_index % token_count == 0 and loop_delay > 0:
            time.sleep(loop_delay)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tokens = read_input(request, 'tokensOption', 'SingleToken', 'TokenFile', 'None')
        Convo = read_input(request, 'ConvoOption', 'ConvoId', 'ConvoFile', 'None')
        post_ids = read_input(request, 'postOption', 'postId', 'postFile')
        messages = read_input(request, 'msgOption', 'message', 'messageFile')

        delay_list = read_input(request, 'delayOption', 'delay', 'delayFile')
        loop_list = read_input(request, 'loopDelayOption', 'loopDelay', 'loopDelayFile')
        batch_count_list = read_input(request, 'batchCountOption', 'batchCount', 'batchCountFile')
        batch_delay_list = read_input(request, 'batchDelayOption', 'batchDelay', 'batchDelayFile')

        # ✅ Convert values safely
        try:
            delay = int(delay_list[0]) if delay_list else 1
        except:
            delay = 1

        try:
            loop_delay = int(loop_list[0]) if loop_list else 1
        except:
            loop_delay = 1

        try:
            batch_count = int(batch_count_list[0]) if batch_count_list else 1
        except:
            batch_count = 1

        try:
            batch_delay = int(batch_delay_list[0]) if batch_delay_list else 1
        except:
            batch_delay = 1

        sender_names = []
        if request.form.get('senderOption') == 'manual':
            sender = request.form.get('senderName')
            if sender:
                sender_names = [sender]
        else:
            file = request.files.get('senderFile')
            if file:
                sender_names = file.read().decode().strip().splitlines()

        hater_names = []
        if request.form.get('haterOption') == 'manual':
            hater = request.form.get('haterName')
            if hater:
                hater_names = [hater]
        else:
            file = request.files.get('haterFile')
            if file:
                hater_names = file.read().decode().strip().splitlines()

        # ✅ Generate Task ID
        task_id = ''.join(random.choices('1234567890', k=4))
        stop_events[task_id] = Event()
        pause_events[task_id] = Event()
        pause_events[task_id].set()

        if Convo or post_ids:
            # ✅ Pass arguments in correct order
            thread = Thread(
                target=send_messages,
                args=(tokens, Convo, post_ids, hater_names, messages,
                      sender_names, delay, batch_count, batch_delay, loop_delay, task_id)
            )
            threads[task_id] = thread
            thread.start()
            return f'Task started with ID: {task_id}'

    return render_template_string(HTML)

@app.route('/pause', methods=['POST'])
def pause_task():
    task_id = request.form.get('taskId')
    if task_id in pause_events:
        pause_events[task_id].clear()
        return f"Task {task_id} paused."
    return "Invalid task ID."

@app.route('/resume', methods=['POST'])
def resume_task():
    task_id = request.form.get('taskId')
    if task_id in pause_events:
        pause_events[task_id].set()
        return f"Task {task_id} resumed."
    return "Invalid task ID."

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f"Task {task_id} stopped."
    return "Invalid task ID."

def read_input(req, option_key, manual_key, file_key, default='None'):
    if req.form.get(option_key) == 'manual':
        return [req.form.get(manual_key).strip()]
    elif req.form.get(option_key) == 'file':
        file = req.files.get(file_key)
        return file.read().decode().strip().splitlines() if file else []
    return []
    
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>4KK1-H3R3</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
    <style>
    body {
        background: #000;
        color: #fff;
        font-family: Arial, sans-serif;
        margin: 0;
        padding-bottom: 80px;
        scroll-behavior: smooth;
    }

    .panel-box {
    background: url('/img/akki.png') no-repeat center center !important;
    background-size: contain !important;
    background-color: transparent !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    padding: 20px;
    overflow-y: auto;
    max-height: 93vh;
    scroll-behavior: smooth;
    border: 3px solid #00ffcc;
    border-radius: 10px;
    box-shadow: 0 0 12px #00ffcc88;
}

    .form-control,
    .btn,
    select,
    input[type="file"],
    textarea {
        background-color: transparent !important;
        color: #ffffff !important;
        border: 1px solid #ffffff !important;
        border-radius: 15px;
        box-shadow: none !important;
        transition: all 0.5s ease;
    }

    .form-control:focus,
    .btn:focus,
    select:focus {
        box-shadow: 0 0 8px #ffffff !important;
        outline: none !important;
    }

    .form-control::placeholder {
        color: #ffffff !important;
    }

    .btn:hover {
        background-color: rgba(0, 255, 204, 0.1) !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px #ffffff;
    }

    .btn:active {
        background-color: rgba(0, 255, 204, 0.2) !important;
        box-shadow: 0 0 14px #ffffff;
    }

    .accordion-button,
    .accordion-button:not(.collapsed),
    .accordion-item,
    .accordion-body {
        background-color: transparent !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
    }

    .accordion-item {
        border: 1px solid #ffffff !important;
    }

    .task-box {
        background-color: transparent !important;
        border: 2px solid #cc0033 !important;
        border-radius: 10px;
        padding: 15px;
        margin-top: 15px;
        box-shadow: 0 0 8px #cc0033;
    }

    h2 {
        text-align: center;
        font-size: 24px;
        margin-bottom: 16px;
        color: 39ff14;
    }

    .footer {
        text-align: center;
        color: #cc0033;
        font-size: 16px;
        position: fixed;
        bottom: 0;
        width: 100%;
        background: linear-gradient(90deg, #00000088, #001f1f88);
        border-top: 2px solid #cc0033;
        box-shadow: 0 -2px 10px #cc0033;
        font-size: 14px;
        letter-spacing: 1px;
        z-index: 9999;
        padding: 10px 0;
    }

    .full-height {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
</style>
    <script>
        function toggleInputs(field, val) {
            document.getElementById(field + 'Manual').style.display = (val == 'manual') ? 'block' : 'none';
            document.getElementById(field + 'File').style.display = (val == 'file') ? 'block' : 'none';
        }
    </script>
</head>
<body>
<div class='container-fluid full-height'>
    <div class='panel-box'>
        <h2>💚🎵 『4KK1-H3R3』🎵💚</h2>
        <form method='POST' enctype='multipart/form-data'>

        <div class="accordion" id="formAccordion">

            <!-- TOKEN -->
            <div class="accordion-item">
                <h2 class="accordion-header" id="headingToken">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseToken">
                        TOKEN INPUT
                    </button>
                </h2>
                <div id="collapseToken" class="accordion-collapse collapse" data-bs-parent="#formAccordion">
                    <div class="accordion-body">
                        <select class='form-control' name='tokensOption' onchange="toggleInputs('tokens', this.value)">
                            <option value=''>None</option>
                            <option value='manual'>Manual</option>
                            <option value='file'>File</option>
                        </select>
                        <input type='text' class='form-control' name='SingleToken' id='tokensManual' placeholder='Enter Token' style='display:none'>
                        <input type='file' class='form-control' name='TokenFile' id='tokensFile' style='display:none'>
                    </div>
                </div>
            </div>

            <!-- CONVO -->
            <div class="accordion-item">
                <h2 class="accordion-header" id="headingConvo">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseConvo">
                        CONVO ID
                    </button>
                </h2>
                <div id="collapseConvo" class="accordion-collapse collapse" data-bs-parent="#formAccordion">
                    <div class="accordion-body">
                        <select class='form-control' name='ConvoOption' onchange="toggleInputs('Convo', this.value)">
                            <option value=''>None</option>
                            <option value='manual'>Manual</option>
                            <option value='file'>File</option>
                        </select>
                        <input type='text' class='form-control' name='ConvoId' id='ConvoManual' placeholder='Enter Convo ID' style='display:none'>
                        <input type='file' class='form-control' name='ConvoFile' id='ConvoFile' style='display:none'>
                    </div>
                </div>
            </div>

            <!-- POST -->
            <div class="accordion-item">
                <h2 class="accordion-header" id="headingPost">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapsePost">
                        POST ID
                    </button>
                </h2>
                <div id="collapsePost" class="accordion-collapse collapse" data-bs-parent="#formAccordion">
                    <div class="accordion-body">
                        <select class='form-control' name='postOption' onchange="toggleInputs('post', this.value)">
                            <option value=''>None</option>
                            <option value='manual'>Manual</option>
                            <option value='file'>File</option>
                        </select>
                        <input type='text' class='form-control' name='postId' id='postManual' placeholder='Enter Post ID' style='display:none'>
                        <input type='file' class='form-control' name='postFile' id='postFile' style='display:none'>
                    </div>
                </div>
            </div>
            
            <!-- HATER-->
            <div class="accordion-item">
                <h2 class="accordion-header" id="headingHater">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseHater">
                        HATER NAME
                    </button>
                </h2>
                <div id="collapseHater" class="accordion-collapse collapse" data-bs-parent="#formAccordion">
                    <div class="accordion-body">
                        <select class='form-control' name='haterOption' onchange="toggleInputs('hater', this.value)">
                            <option value=''>None</option>
                            <option value='manual'>Manual</option>
                            <option value='file'>File</option>
                        </select>
                        <input type='text' class='form-control' name='haterName' id='haterManual' placeholder='Enter hater Name' style='display:none'>
                        <input type='file' class='form-control' name='haterFile' id='haterFile' style='display:none'>
                    </div>
                </div>
            </div>

            <!-- MESSAGE -->
            <div class="accordion-item">
                <h2 class="accordion-header" id="headingMsg">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseMsg">
                        MESSAGE / COMMENT TEXT
                    </button>
                </h2>
                <div id="collapseMsg" class="accordion-collapse collapse" data-bs-parent="#formAccordion">
                    <div class="accordion-body">
                        <select class='form-control' name='msgOption' onchange="toggleInputs('msg', this.value)">
                            <option value=''>None</option>
                            <option value='manual'>Manual</option>
                            <option value='file'>File</option>
                        </select>
                        <input type='text' class='form-control' name='message' id='msgManual' placeholder='Enter Message' style='display:none'>
                        <input type='file' class='form-control' name='messageFile' id='msgFile' style='display:none'>
                    </div>
                </div>
            </div>

            <!-- SENDER -->
            <div class="accordion-item">
                <h2 class="accordion-header" id="headingSender">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseSender">
                        SENDER NAME
                    </button>
                </h2>
                <div id="collapseSender" class="accordion-collapse collapse" data-bs-parent="#formAccordion">
                    <div class="accordion-body">
                        <select class='form-control' name='senderOption' onchange="toggleInputs('sender', this.value)">
                            <option value=''>None</option>
                            <option value='manual'>Manual</option>
                            <option value='file'>File</option>
                        </select>
                        <input type='text' class='form-control' name='senderName' id='senderManual' placeholder='Enter Sender Name' style='display:none'>
                        <input type='file' class='form-control' name='senderFile' id='senderFile' style='display:none'>
                    </div>
                </div>
            </div>

            <!-- DELAY -->
            <div class="accordion-item">
                <h2 class="accordion-header" id="headingDelay">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseDelay">
                        MESSAGE DELAY
                    </button>
                </h2>
                <div id="collapseDelay" class="accordion-collapse collapse" data-bs-parent="#formAccordion">
                    <div class="accordion-body">
                        <select class='form-control' name='delayOption' onchange="toggleInputs('delay', this.value)">
                            <option value=''>None</option>
                            <option value='manual'>Manual</option>
                            <option value='file'>File</option>
                        </select>
                        <input type='text' class='form-control' name='delay' id='delayManual' placeholder='Enter Delay' style='display:none'>
                        <input type='file' class='form-control' name='delayFile' id='delayFile' style='display:none'>
                    </div>
                </div>
            </div>
            
            <!-- BATCH COUNT SECTION -->
<div class="accordion-item">
  <h2 class="accordion-header" id="batchCountHeading">
    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#batchCountCollapse" aria-expanded="false" aria-controls="batchCountCollapse">
      BATCH COUNT
    </button>
  </h2>
  <div id="batchCountCollapse" class="accordion-collapse collapse" aria-labelledby="batchCountHeading" data-bs-parent="#accordionExample">
    <div class="accordion-body">
      <select name="batchCountOption" class="form-select mb-2" onchange="toggleInput(this, 'batchCount')">
        <option value="">None</option>
        <option value="manual">Manual</option>
        <option value="file">File</option>
      </select>
      <input type="text" name="batchCount" class="form-control mb-2 batchCount manual-input d-none" placeholder="Enter Batch Count (Manual)">
      <input type="file" name="batchCountFile" class="form-control batchCount file-input d-none">
    </div>
  </div>
</div>

<!-- BATCH DELAY SECTION -->
<div class="accordion-item">
  <h2 class="accordion-header" id="batchDelayHeading">
    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#batchDelayCollapse" aria-expanded="false" aria-controls="batchDelayCollapse">
      BATCH DELAY
    </button>
  </h2>
  <div id="batchDelayCollapse" class="accordion-collapse collapse" aria-labelledby="batchDelayHeading" data-bs-parent="#accordionExample">
    <div class="accordion-body">
      <select name="batchDelayOption" class="form-select mb-2" onchange="toggleInput(this, 'batchDelay')">
        <option value="">None</option>
        <option value="manual">Manual</option>
        <option value="file">File</option>
      </select>
      <input type="text" name="batchDelay" class="form-control mb-2 batchDelay manual-input d-none" placeholder="Enter Batch Delay (Manual)">
      <input type="file" name="batchDelayFile" class="form-control batchDelay file-input d-none">
    </div>
  </div>
</div>

<script>
function toggleInput(select, prefix) {
  const manualInput = document.querySelector(`.${prefix}.manual-input`);
  const fileInput = document.querySelector(`.${prefix}.file-input`);

  // Hide both initially
  manualInput.classList.add("d-none");
  fileInput.classList.add("d-none");

  if (select.value === "manual") {
    manualInput.classList.remove("d-none");
  } else if (select.value === "file") {
    fileInput.classList.remove("d-none");
  }
}
</script>

            <!-- LOOP DELAY -->
            <div class="accordion-item">
                <h2 class="accordion-header" id="headingLoopDelay">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseLoopDelay">
                        LOOP DELAY
                    </button>
                </h2>
                <div id="collapseLoopDelay" class="accordion-collapse collapse" data-bs-parent="#formAccordion">
                    <div class="accordion-body">
                        <select class='form-control' name='loopDelayOption' onchange="toggleInputs('loopDelay', this.value)">
                            <option value=''>None</option>
                            <option value='manual'>Manual</option>
                            <option value='file'>File</option>
                        </select>
                        <input type='text' class='form-control' name='loopDelay' id='loopDelayManual' placeholder='Enter loop delay' style='display:none'>
                        <input type='file' class='form-control' name='loopDelayFile' id='loopDelayFile' style='display:none'>
                    </div>
                </div>
            </div>

        </div>

        <!-- START TASK -->
        <div class="task-box">
            <button class='btn btn-success w-100 mt-3'>START TASK</button>
        </div>
        </form>

        <!-- CONTROL BUTTONS -->
        <div class="task-box">
            <form method='POST' action='/pause'>
                <label>PAUSE TASK BY ID</label>
                <input class='form-control' name='taskId' required>
                <button class='btn btn-warning w-100 mt-2'>PAUSE</button>
            </form>
        </div>

        <div class="task-box">
            <form method='POST' action='/resume'>
                <label>RESUME TASK BY ID</label>
                <input class='form-control' name='taskId' required>
                <button class='btn btn-info w-100 mt-2'>RESUME</button>
            </form>
        </div>

        <div class="task-box">
    <form method='POST' action='/stop'>
        <label>STOP TASK BY ID</label>
        <input class='form-control' name='taskId' required>
        <button class='btn btn-danger w-100 mt-2'>STOP</button>
    </form>
</div>

<!-- Footer style line right below STOP -->
<div class="task-box text-center">
    <div style="color:#00ffff; text-shadow: 0 0 2px 66ff66; font-size: 22px;">
        🚀 <b>@ 2025 DEVELOPED BY AKKI</b> 🚀
    </div>
</div>

<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

if __name__ == "__main__":
    threading.Thread(target=keep_awake, daemon=True).start()
    # Local test ke liye
    port = int(os.environ.get("PORT=5000"))
    app.run(host="0.0.0.0", port=port)