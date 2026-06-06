import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk
import threading
import time
import math

# ══════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════
BAUD = 9600

# ══════════════════════════════════════════
# SERIAL STATE
# ══════════════════════════════════════════
ser         = None
connected   = False
direction   = "STOP"
speed_level = 0
speed_pct   = 0

# ══════════════════════════════════════════
# SEND COMMAND
# ══════════════════════════════════════════
def send(cmd):
    global ser, connected
    if connected and ser:
        try:
            ser.write((cmd + '\n').encode())
        except:
            pass

# ══════════════════════════════════════════
# READ SERIAL (background thread)
# ══════════════════════════════════════════
def read_loop():
    global direction, speed_level, speed_pct
    while True:
        try:
            if ser and ser.in_waiting:
                line = ser.readline().decode().strip()
                # Format: S:CW:3:60
                if line.startswith('S:'):
                    parts = line.split(':')
                    if len(parts) == 4:
                        direction   = parts[1]
                        speed_level = int(parts[2])
                        speed_pct   = int(parts[3])
                        update_gui()
        except:
            pass
        time.sleep(0.01)

# ══════════════════════════════════════════
# CONNECT
# ══════════════════════════════════════════
def connect():
    global ser, connected
    port = port_var.get()
    try:
        ser = serial.Serial(port, BAUD, timeout=1)
        connected = True
        conn_btn.config(text="Disconnect",
                        bg='#f38ba8')
        status_var.set(f"Connected on {port} ✅")
        threading.Thread(target=read_loop,
                         daemon=True).start()
    except Exception as e:
        status_var.set(f"Error: {e}")

def disconnect():
    global ser, connected
    if ser:
        ser.close()
    connected = False
    conn_btn.config(text="Connect", bg='#89b4fa')
    status_var.set("Disconnected")

def toggle_connect():
    if connected:
        disconnect()
    else:
        connect()

def refresh_ports():
    ports = [p.device for p in
             serial.tools.list_ports.comports()]
    port_menu['values'] = ports
    if ports:
        port_var.set(ports[0])

# ══════════════════════════════════════════
# SPEEDOMETER CANVAS
# ══════════════════════════════════════════
def draw_speedometer(canvas, pct, direction):
    canvas.delete("all")
    cx, cy, r = 120, 110, 90

    # Background arc
    canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                      start=0, extent=180,
                      style='arc',
                      outline='#313244', width=18)

    # Color arc based on speed
    color = '#a6e3a1' if pct < 40 else \
            '#f9e2af' if pct < 75 else '#f38ba8'

    if pct > 0:
        canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                          start=180,
                          extent=-(pct * 180 / 100),
                          style='arc',
                          outline=color, width=18)

    # Needle
    angle_deg = 180 - (pct * 180 / 100)
    angle_rad = math.radians(angle_deg)
    nx = cx + (r - 10) * math.cos(angle_rad)
    ny = cy - (r - 10) * math.sin(angle_rad)
    canvas.create_line(cx, cy, nx, ny,
                       fill='white', width=3)
    canvas.create_oval(cx-6, cy-6, cx+6, cy+6,
                       fill='white')

    # Speed % text
    canvas.create_text(cx, cy + 25,
                       text=f"{pct}%",
                       fill='white',
                       font=('Courier', 18, 'bold'))

    # Direction text
    dir_color = '#89b4fa' if direction == 'CW'  else \
                '#f38ba8' if direction == 'CCW' else \
                '#6c7086'
    canvas.create_text(cx, cy + 50,
                       text=direction,
                       fill=dir_color,
                       font=('Courier', 13, 'bold'))

# ══════════════════════════════════════════
# UPDATE GUI FROM DATA
# ══════════════════════════════════════════
def update_gui():
    draw_speedometer(speed_canvas, speed_pct, direction)

    # Speed bar
    speed_bar['value'] = speed_pct

    # Level indicators
    for i, dot in enumerate(level_dots):
        if i < speed_level:
            dot.config(bg='#a6e3a1')
        else:
            dot.config(bg='#313244')

    # Direction indicator
    cw_btn.config( bg='#89b4fa' if direction == 'CW'
                   else '#313244')
    ccw_btn.config(bg='#f38ba8' if direction == 'CCW'
                   else '#313244')

# ══════════════════════════════════════════
# KEYBOARD CONTROLS
# ══════════════════════════════════════════
def key_press(event):
    k = event.keysym
    if   k == 'Right': send('CW')
    elif k == 'Left':  send('CCW')
    elif k == 'Up':    send('UP')
    elif k == 'Down':  send('DN')
    elif k == 'space': send('STP')
    elif k in ('r','R'): send('RST')

# ══════════════════════════════════════════
# BUILD GUI
# ══════════════════════════════════════════
BG  = '#1e1e2e'
BTN = '#313244'
TXT = '#cdd6f4'
ACC = '#89b4fa'

root = tk.Tk()
root.title("🎮 Servo UART Controller")
root.geometry("480x580")
root.configure(bg=BG)
root.resizable(False, False)

# ── Title ──
tk.Label(root, text="🎮  Servo Controller",
         bg=BG, fg=ACC,
         font=('Courier', 16, 'bold')).pack(pady=8)

# ── Connection bar ──
conn_frame = tk.Frame(root, bg=BG)
conn_frame.pack(fill='x', padx=16, pady=4)

port_var = tk.StringVar()
port_menu = ttk.Combobox(conn_frame,
                          textvariable=port_var,
                          width=16)
port_menu.pack(side='left', padx=4)

tk.Button(conn_frame, text="🔄",
          bg=BTN, fg=TXT,
          command=refresh_ports).pack(side='left')

conn_btn = tk.Button(conn_frame,
                     text="Connect",
                     bg=ACC, fg=BG,
                     font=('Courier', 10, 'bold'),
                     width=12,
                     command=toggle_connect)
conn_btn.pack(side='left', padx=8)

status_var = tk.StringVar(value="Not connected")
tk.Label(root, textvariable=status_var,
         bg=BG, fg='#a6e3a1',
         font=('Courier', 9)).pack()

# ── Speedometer ──
speed_canvas = tk.Canvas(root, width=240,
                          height=160, bg=BG,
                          highlightthickness=0)
speed_canvas.pack(pady=4)
draw_speedometer(speed_canvas, 0, "STOP")

# ── Speed progress bar ──
style = ttk.Style()
style.theme_use('clam')
style.configure("green.Horizontal.TProgressbar",
                troughcolor=BTN,
                background='#a6e3a1')
speed_bar = ttk.Progressbar(root, length=300,
                              maximum=100,
    style="green.Horizontal.TProgressbar")
speed_bar.pack(pady=4)

# ── Speed level dots ──
dots_frame = tk.Frame(root, bg=BG)
dots_frame.pack(pady=4)
tk.Label(dots_frame, text="Speed: ",
         bg=BG, fg=TXT,
         font=('Courier', 10)).pack(side='left')
level_dots = []
for i in range(5):
    d = tk.Label(dots_frame, text="●",
                 bg=BTN, fg=BTN,
                 font=('Courier', 14),
                 width=2)
    d.pack(side='left', padx=2)
    level_dots.append(d)

# ── Control buttons ──
ctrl_frame = tk.Frame(root, bg=BG)
ctrl_frame.pack(pady=10)

btn_s = dict(font=('Courier', 11, 'bold'),
             width=8, height=2,
             bg=BTN, fg=TXT)

tk.Button(ctrl_frame, text="▲ UP",   **btn_s,
          command=lambda: send('UP')).grid(
          row=0, column=1, padx=4, pady=4)

ccw_btn = tk.Button(ctrl_frame, text="◄ CCW", **btn_s,
                     command=lambda: send('CCW'))
ccw_btn.grid(row=1, column=0, padx=4, pady=4)

tk.Button(ctrl_frame, text="■ STOP",
          font=('Courier', 11, 'bold'),
          width=8, height=2,
          bg='#f38ba8', fg=BG,
          command=lambda: send('STP')).grid(
          row=1, column=1, padx=4, pady=4)

cw_btn = tk.Button(ctrl_frame, text="CW ►", **btn_s,
                    command=lambda: send('CW'))
cw_btn.grid(row=1, column=2, padx=4, pady=4)

tk.Button(ctrl_frame, text="▼ DN",   **btn_s,
          command=lambda: send('DN')).grid(
          row=2, column=1, padx=4, pady=4)

tk.Button(root, text="↺  RESET",
          bg='#fab387', fg=BG,
          font=('Courier', 10, 'bold'),
          width=24,
          command=lambda: send('RST')).pack(pady=4)

# ── Keyboard hint ──
tk.Label(root,
         text="← CW/CCW →  |  ↑↓ Speed  "
              "|  Space Stop  |  R Reset",
         bg=BG, fg='#585b70',
         font=('Courier', 8)).pack(pady=4)

# ── Keyboard bind ──
root.bind('<KeyPress>', key_press)
root.focus_set()

# Init ports
refresh_ports()

root.mainloop()
