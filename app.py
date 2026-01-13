from flask import Flask, request, session, url_for, jsonify
import csv
import random

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'


# --- Python Helper Functions (Unchanged) ---

def load_songs():
    songs = []
    with open("tracks.csv", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                row["bpm"] = int(row["bpm"].strip())
                row["duration"] = int(row["duration"].strip())
                row["energy"] = int(row["energy"].strip())
                songs.append(row)
            except ValueError:
                print(f"Skipping invalid row due to conversion error in data: {row}")
                continue
    return songs


def filter_songs(songs, task, genre_choice):
    filtered = []
    for song in songs:
        bpm = song["bpm"]
        lyrics = song["lyrics"]
        energy = song["energy"]
        genre = song["genre"]
        if genre_choice != "any" and genre != genre_choice: continue
        if task == "focus":
            if energy <= 4 and lyrics in ["no", "min"] and genre in ["lofi", "ambient"]: filtered.append(song)
        elif task == "study":
            if energy <= 6 and genre not in ["metal"]: filtered.append(song)
        elif task == "coding":
            if 4 <= energy <= 6 and lyrics != "yes" and genre in ["lofi", "ambient", "hip-hop"]: filtered.append(song)
        elif task == "deep":
            if energy <= 3 and lyrics == "no" and genre in ["ambient", "lofi"]: filtered.append(song)
        elif task == "chill":
            if energy <= 6: filtered.append(song)
        elif task == "workout":
            if energy >= 7 and genre in ["rock", "metal", "hip-hop", "pop"]: filtered.append(song)
    random.shuffle(filtered)
    return filtered


def build_playlist(songs, max_minutes):
    max_seconds = max_minutes * 60
    total_time = 0
    playlist = []
    for song in songs:
        if total_time + song["duration"] <= max_seconds:
            playlist.append(song)
            total_time += song["duration"]
        else:
            break
    return playlist


@app.route("/save_theme", methods=["POST"])
def save_theme():
    theme_key = request.json.get('theme')
    if theme_key:
        session['theme'] = theme_key
        return jsonify({'status': 'success', 'theme': theme_key})
    return jsonify({'status': 'error'}), 400


@app.route("/", methods=["GET", "POST"])
def home():
    playlist_html = ""
    task = "focus"
    time_minutes = 60
    genre_choice = "any"

    themes = {
        'sakura': url_for('static', filename='images/sakura.gif'),
        'cafe': url_for('static', filename='images/cafe.gif'),
        'lofi_girl': url_for('static', filename='images/lofi girl.gif'),
        'train': url_for('static', filename='images/train.gif')
    }

    current_theme_key = session.get('theme', 'sakura')
    current_background_url = themes[current_theme_key]

    if request.method == "POST":
        task = request.form["task"]
        time_minutes = int(request.form["time"])
        genre_choice = request.form["genre"]

        songs = load_songs()
        filtered = filter_songs(songs, task, genre_choice)
        playlist = build_playlist(filtered, time_minutes)

        playlist_html = "<h2>Recommended Playlist</h2><ul>"
        for song in playlist:
            playlist_html += (
                f"<li>{song['title']} — {song['artist']} "
                f"({song['duration'] // 60}:{song['duration'] % 60:02d})</li>"
            )
        playlist_html += "</ul>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Focus Productivity App</title>
        <style>
            body {{
                font-family: sans-serif;
                background: url('{current_background_url}') no-repeat center center fixed; 
                background-size: cover; 
                background-color: #121212; 
                color: #ffffff;
                padding: 50px 20px 20px 20px; 
                transition: background-image 0.5s ease-in-out; 
            }}
            .container {{
                max-width: 800px; 
                margin: 0px auto; 
                padding: 20px;
                background-color: rgba(0, 0, 0, 0.6); 
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.8);
            }}
            .section-separator {{ margin-top: 40px; }}
            .menu-toggle {{ position: fixed; top: 15px; left: 15px; z-index: 200; background: none; border: none; color: white; font-size: 30px; cursor: pointer; }}
            .sidebar {{ height: 100%; width: 0; position: fixed; z-index: 150; top: 0; left: 0; background-color: #111; overflow-x: hidden; transition: 0.5s; padding-top: 60px; box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
            .sidebar.open {{ width: 300px; padding-left: 20px; padding-right: 20px; }}
            .sidebar h3 {{ color: #1DB954; margin-top: 20px; }}
            .sidebar-image {{ width: 80px; height: 80px; margin: 5px; cursor: pointer; border-radius: 5px; border: 2px solid transparent; transition: border 0.3s; object-fit: cover; }}
            .sidebar-image:hover {{ border-color: #1DB954; }}
            .task-input-group {{ display: flex; margin-bottom: 10px; }}
            .task-input {{ flex-grow: 1; padding: 8px; background-color: #333; border: none; color: white; }}
            .add-task-btn {{ padding: 8px; background-color: #1DB954; border: none; cursor: pointer; }}
            .task-item {{ padding: 8px 0; border-bottom: 1px solid #444; display: flex; align-items: center; justify-content: space-between; }}
            .task-checkbox {{ margin-right: 10px; }}
            .task-done label {{ text-decoration: line-through; color: #888; }}

            /* General styles for containers/buttons, excluding inputs/selects now */
            .timer-container, ul li, form button, #timer-control-btn {{ background-color: rgba(40, 40, 40, 0.8); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; padding: 12px; }}

            /* --- NEW: Specific styling for all inputs and selects (Pomodoro & Music sections) --- */
            form select, form input[type="number"], .timer-input {{
                width: 100%;
                padding: 12px; /* Standardized size */
                margin-top: 5px;
                border-radius: 8px; /* Consistent border radius */
                box-sizing: border-box;
                appearance: none;
                background-color: #94a3b8; /* Soft blue/gray opaque background */
                border: 1px solid #94a3b8; 
                color: #000000; /* Black text for contrast */
                font-size: 1rem;
            }}
            /* --- END NEW STYLES --- */

            form button {{ background-color: #1DB954; border: none; }}
            .timer-display-group {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 15px; }}
            #timer-display {{ font-size: 4rem; font-weight: bold; color: #1DB954; flex-grow: 1; text-align: center; }}
            #timer-control-btn {{ background-color: #1DB954; border: none; cursor: pointer; font-size: 1.2rem; padding: 15px 20px; width: auto; }}
            .timer-inputs-group {{ display: flex; gap: 10px; }}
        </style>
    </head>
    <body>

        <!-- Hamburger Menu Button -->
        <button class="menu-toggle" onclick="toggleSidebar()">☰</button>

        <!-- Sidebar Menu -->
        <div class="sidebar" id="sidebar-menu">
            <h3>Backgrounds</h3>
            <div id="background-options">
                <img src="{themes['sakura']}" class="sidebar-image" onclick="setNewBackground('sakura', '{themes['sakura']}')" alt="Sakura theme">
                <img src="{themes['cafe']}" class="sidebar-image" onclick="setNewBackground('cafe', '{themes['cafe']}')" alt="Cafe theme">
                <img src="{themes['lofi_girl']}" class="sidebar-image" onclick="setNewBackground('lofi_girl', '{themes['lofi_girl']}')" alt="Lofi Girl theme">
                <img src="{themes['train']}" class="sidebar-image" onclick="setNewBackground('train', '{themes['train']}')" alt="Train theme">
            </div>

            <h3>Tasks</h3>
            <div class="task-input-group">
                <input type="text" id="new-task-input" class="task-input" placeholder="Add a new task...">
                <button onclick="addTask()" class="add-task-btn">+</button>
            </div>
            <div id="task-list">
                <!-- Tasks injected here by JS -->
            </div>
        </div>

        <div class="container">
            <h1>Focus Productivity App</h1>

            <!-- SECTION 1: POMODORO -->
            <h2>Pomodoro</h2>
            <div class="timer-container">
                <div id="timer-status">Set your times below 👇</div>

                <div class="timer-display-group">
                    <div id="timer-display">00:00</div>
                    <button id="timer-control-btn">Start Timer</button>
                </div>

                <div class="timer-inputs-group">
                    <div>
                        <label>Focus (min):</label>
                        <input type="number" id="focus-time-input" class="timer-input" value="25" min="1">
                    </div>
                    <div>
                        <label>Break (min):</label>
                        <input type="number" id="break-time-input" class="timer-input" value="5" min="1">
                    </div>
                </div>
            </div>

            <!-- SECTION 2: MUSIC -->
            <h2 class="section-separator">Music</h2>
            <form method="post">
                <label>Task:</label>
                <select name="task">
                    <option value="focus">Focus</option>
                    <option value="study">Study</option>
                    <option value="coding">Coding</option>
                    <option value="deep">Deep Work</option>
                    <option value="chill">Chill</option>
                    <option value="workout">Workout</option>
                </select>

                <label>Genre:</label>
                <select name="genre">
                    <option value="any">Any</option>
                    <option value="lofi">Lofi</option>
                    <option value="ambient">Ambient</option>
                    <option value="rock">Rock</option>
                    <option value="metal">Metal</option>
                    <option value="hip-hop">Hip-Hop</option>
                    <option value="pop">Pop</option>
                </select>

                <label>Time (minutes):</label>
                <input type="number" name="time" required value="{time_minutes}">

                <button type="submit">Generate Playlist</button>
            </form>

            {playlist_html}
        </div>


        <!-- JavaScript Logic -->
        <script>
            function toggleSidebar() {{
                const sidebar = document.getElementById('sidebar-menu');
                sidebar.classList.toggle('open');
            }}

            function setNewBackground(themeKey, imageUrl) {{
                document.body.style.backgroundImage = `url('${{imageUrl}}')`;
                fetch('/save_theme', {{
                    method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ theme: themeKey }})
                }}).then(response => response.json())
                  .then(data => console.log('Theme saved:', data.theme))
                  .catch(error => console.error('Error saving theme:', error));
            }}

            let tasks = JSON.parse(localStorage.getItem('focusTasks')) || [];

            function renderTasks() {{
                const taskList = document.getElementById('task-list');
                taskList.innerHTML = '';
                tasks.forEach((task, index) => {{
                    const taskItem = document.createElement('div');
                    taskItem.classList.add('task-item');
                    if (task.done) taskItem.classList.add('task-done');
                    taskItem.innerHTML = '<div>' +
                            `<input type="checkbox" class="task-checkbox" ${{task.done ? 'checked' : ''}} onclick="toggleTaskDone(${{index}})">` +
                            `<label>${{task.text}}</label>` +
                        '</div>' +
                        `<button onclick="deleteTask(${{index}})">X</button>`;
                    taskList.appendChild(taskItem);
                }});
                localStorage.setItem('focusTasks', JSON.stringify(tasks));
            }}

            function addTask() {{
                const input = document.getElementById('new-task-input');
                const text = input.value.trim();
                if (text) {{
                    tasks.push({{ text: text, done: false }});
                    input.value = '';
                    renderTasks();
                }}
            }}

            function toggleTaskDone(index) {{
                tasks[index].done = !tasks[index].done;
                renderTasks();
            }}

            function deleteTask(index) {{
                tasks.splice(index, 1);
                renderTasks();
            }}

            window.onload = renderTasks;

            const timerDisplay = document.getElementById('timer-display');
            const timerStatus = document.getElementById('timer-status');
            const controlButton = document.getElementById('timer-control-btn');
            const focusInput = document.getElementById('focus-time-input');
            const breakInput = document.getElementById('break-time-input');

            let countdown; let isRunning = false; let isFocusTime = true;

            function updateDisplay(secondsRemaining) {{
                const minutes = Math.floor(secondsRemaining / 60);
                const seconds = secondsRemaining % 60;
                timerDisplay.textContent = `${{minutes < 10 ? '0' : ''}}${{minutes}}:${{seconds < 10 ? '0' : ''}}${{seconds}}`;
            }}

            function startTimerCycle() {{
                if (isRunning) return;
                isRunning = true;
                controlButton.textContent = "Stop"; 
                const focusTimeSeconds = parseInt(focusInput.value) * 60;
                const breakTimeSeconds = parseInt(breakInput.value) * 60;
                let timeRemaining = isFocusTime ? focusTimeSeconds : breakTimeSeconds;
                timerStatus.textContent = isFocusTime ? "Focus Time 🧠" : "Break Time ☕";
                countdown = setInterval(() => {{
                    timeRemaining--;
                    updateDisplay(timeRemaining);
                    if (timeRemaining <= 0) {{
                        clearInterval(countdown);
                        isRunning = false;
                        isFocusTime = !isFocusTime; 
                        startTimerCycle(); 
                    }}
                }}, 1000);
            }}

            function stopTimer() {{
                clearInterval(countdown);
                isRunning = false;
                controlButton.textContent = "Start Timer";
                timerStatus.textContent = "Timer Stopped";
                updateDisplay(0); 
            }}

            controlButton.addEventListener('click', () => {{
                if (isRunning) {{
                    stopTimer();
                }} else {{
                    startTimerCycle();
                }}
            }});
            updateDisplay(parseInt(focusInput.value) * 60);
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)
