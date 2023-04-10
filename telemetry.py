import json

from f1_22_telemetry.listener import TelemetryListener
from f1_22_telemetry.appendices import TRACK_IDS

import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import queue
import time
import math

telemetry_queue = queue.Queue()
ui_update_interval = 50 # ms
telelmetry_update_interval = 500 # ms
max_data_points = 100
map_scale_factor = 0.25

# Enable bits of the UI:
enable_throttle_graph = True
enable_brake_graph = True
enable_speed_graph = True
enable_map = True
    
def format_lap_time(lap_time):
    msec=lap_time%1000
    seconds=math.floor((lap_time/1000)%60)
    minutes=math.floor((lap_time/(1000*60))%60)
    return (f"{minutes:0.0f}:{seconds:0.0f}.{msec}") #TODO: fix times are rounded up

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        #self.wm_state('zoomed')
        #self.overrideredirect(True)
        #self.attributes('-topmost', True)

        #left_frame = tk.Frame(self, width=200, height=400, bg='grey')
        #left_frame.grid(row=0,column=0)

        #right_frame = tk.Frame(self, width=200, height=400, bg='grey')
        #right_frame.grid(row=0,column=1)

        self.current_lap_number = 0

        # Speed Graph
        if enable_speed_graph:
            self.speed_x_data = list(range(0,max_data_points))
            self.speed_y_data = [0] * max_data_points

            speed_f = Figure(figsize=(5,5), dpi=100)
            speed_a = speed_f.add_subplot(111)
            self.speed_plot = speed_a.plot(self.speed_x_data, self.speed_y_data)[0]  # get the line object
            speed_a.set_ylim(0, 350)
            self.speed_canvas = FigureCanvasTkAgg(speed_f, self)
            self.speed_canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Throttle Graph
        if enable_throttle_graph:
            self.throttle_x_data = list(range(0,max_data_points))
            self.throttle_y_data = [0] * max_data_points

            throttle_f = Figure(figsize=(5,5), dpi=100)
            self.throttle_a = throttle_f.add_subplot(111)
            self.throttle_plot = self.throttle_a.plot(self.throttle_x_data, self.throttle_y_data, color="green")[0]  # get the line object
            self.throttle_a.set_ylim(-10, 110)
            #self.throttle_a.fill_between(self.throttle_x_data, self.throttle_y_data, color='green')
            self.throttle_canvas = FigureCanvasTkAgg(throttle_f, self)
            self.throttle_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Brake Graph
        if enable_brake_graph:
            self.brake_x_data = list(range(0,max_data_points))
            self.brake_y_data = [0] * max_data_points

            brake_f = Figure(figsize=(5,5), dpi=100)
            self.brake_a = brake_f.add_subplot(111)
            self.brake_plot = self.brake_a.plot(self.brake_x_data, self.brake_y_data, color="red")[0]  # get the line object
            self.brake_a.set_ylim(-10, 110)
            #self.brake_a.fill_between(self.throttle_x_data, self.throttle_y_data, color='green')
            self.brake_canvas = FigureCanvasTkAgg(brake_f, self)
            self.brake_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Track Map
        if enable_map:
            self.map = tk.Canvas(self,width=400, height=400)
            self.map.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(text="F1 22 - Test").pack()

        self.tk_speed = tk.StringVar()
        self.tk_speed.set("--- KPH")
        tk.Label(textvariable=self.tk_speed).pack()

        self.tk_throttle = tk.StringVar()
        self.tk_throttle.set("Throttle: ---%")
        tk.Label(textvariable=self.tk_throttle).pack()

        self.tk_brake = tk.StringVar()
        self.tk_brake.set("Brake: ---%")
        tk.Label(textvariable=self.tk_brake).pack()

        self.tk_track = tk.StringVar()
        self.tk_track.set("Track: Unknown")
        tk.Label(textvariable=self.tk_track).pack()

        self.tk_lap_0 = tk.StringVar()
        self.tk_lap_0.set("Lap -1: ---")
        tk.Label(textvariable=self.tk_lap_0).pack()

        self.tk_lap_1 = tk.StringVar()
        self.tk_lap_1.set("Lap -2: ---")
        tk.Label(textvariable=self.tk_lap_1).pack()

        self.tk_lap_2 = tk.StringVar()
        self.tk_lap_2.set("Lap -3: ---")
        tk.Label(textvariable=self.tk_lap_2).pack()

        self.tk_lap_3 = tk.StringVar()
        self.tk_lap_3.set("Lap -4: ---")
        tk.Label(textvariable=self.tk_lap_3).pack()

        self.tk_lap_4 = tk.StringVar()
        self.tk_lap_4.set("Lap -5: ---")
        tk.Label(textvariable=self.tk_lap_4).pack()
        
        self.after(ui_update_interval, self.update_ui_telemetry)

        #tk.Button(self, text="Run unthreaded", command=self.startF1Server_unthreaded).pack()
        tk.Button(self, text="Run threaded", command=self.startF1Server_threaded).pack()

        self.tk_thread_status = tk.StringVar()
        self.tk_thread_status.set("Not Listening")
        tk.Label(textvariable=self.tk_thread_status).pack()

        self.after(1000, self.check_thread_status)

        self.telemetry_thread = Thread(target=startF1Server,daemon=True)

    def startF1Server_unthreaded(self):
        startF1Server()

    def startF1Server_threaded(self):
        self.telemetry_thread.start()
    
    def check_thread_status(self):
        if self.telemetry_thread.is_alive():
            self.tk_thread_status.set("Listening")
        else:
            self.tk_thread_status.set("Not Listening")
        self.after(1000, self.check_thread_status)


    def update_ui_telemetry(self):
        ui_update_start = time.time()
        try:
            message = telemetry_queue.get(block=False)
            # If we're getting too far out of sync drop the packet and grab the next one till we're close enough
            while message is not None and message["update_time"] < time.time() - 1:
                message = telemetry_queue.get(block=False)
                print(f"Dropped packet from queue: {time.time()}")
        except queue.Empty:
            # let's try again later
            self.after(ui_update_interval, self.update_ui_telemetry)
            #print(f"Queue Empty: {time.time()}")
            return
        #print(f"Updating UI with Telemetry: {time.time()}")

        #print('update_ui_telemetry got', message)
        if message is not None:
            #print(json.loads(message))
            self.tk_speed.set(f"{message['speed']}KPH")
            self.tk_throttle.set(f"Throttle: {message['throttle']*100:0.0f}%")
            self.tk_brake.set(f"Brake: {message['brake']*100:0.0f}%")
            if message['track_id'] != -1:
                self.tk_track.set(f"Track: {TRACK_IDS[message['track_id']]}")
            else:
                self.tk_track.set(f"Track: Unknown")

            # Only update the times when on a new lap to speed up UI updates 
            if self.current_lap_number != message['lap_number']:
                self.tk_lap_0.set(f"Lap -1: {format_lap_time(message['last_laps'][4]['time'])} { ('I','V')[message['last_laps'][4]['valid']] }")
                self.tk_lap_1.set(f"Lap -2: {format_lap_time(message['last_laps'][3]['time'])} { ('I','V')[message['last_laps'][3]['valid']] }")
                self.tk_lap_2.set(f"Lap -3: {format_lap_time(message['last_laps'][2]['time'])} { ('I','V')[message['last_laps'][2]['valid']] }")
                self.tk_lap_3.set(f"Lap -4: {format_lap_time(message['last_laps'][1]['time'])} { ('I','V')[message['last_laps'][1]['valid']] }")
                self.tk_lap_4.set(f"Lap -5: {format_lap_time(message['last_laps'][0]['time'])} { ('I','V')[message['last_laps'][0]['valid']] }")
                self.current_lap_number = message['lap_number']

            # Update Speed Graph
            if enable_speed_graph:
                self.speed_y_data.append(message['speed'])
                # remove oldest data point
                self.speed_y_data = self.speed_y_data[1:]
                #  update plot data
                self.speed_plot.set_ydata(self.speed_y_data)
                self.speed_canvas.draw_idle()  # redraw plot

            # Update Throttle Graph
            if enable_throttle_graph:
                self.throttle_y_data.append(message['throttle']*100)
                # remove oldest data point
                self.throttle_y_data = self.throttle_y_data[1:]
                #  update plot data
                #self.throttle_canvas.clear()
                self.throttle_plot.set_ydata(self.throttle_y_data)
                #self.throttle_a.fill_between(self.throttle_x_data, self.throttle_y_data, color='green')
                self.throttle_canvas.draw_idle()  # redraw plot

            # Update Brake Graph
            if enable_brake_graph:
                self.brake_y_data.append(message['brake']*100)
                # remove oldest data point
                self.brake_y_data = self.brake_y_data[1:]
                #  update plot data
                #self.brake_canvas.clear()
                self.brake_plot.set_ydata(self.brake_y_data)
                #self.brake_a.fill_between(self.brake_x_data, self.brake_y_data, color='red')
                self.brake_canvas.draw_idle()  # redraw plot

            # Update Track Map
            if enable_map:
                mapped_x = message["loc_x"] * map_scale_factor + 200
                mapped_y = message["loc_y"] * map_scale_factor + 200
                mapped_z = message["loc_z"] * map_scale_factor + 200
                #self.map.create_oval(mapped_x-5,mapped_z-5,mapped_x+5,mapped_z+5,fill="blue", outline="blue")
                pointer_size = 20
                break_colur = f'#{int(message["brake"]*100):02x}{0:02x}{0:02x}'
                throttle_colur = f'#{0:02x}{0:02x}{int(message["throttle"]*100):02x}'
                self.map.create_arc(mapped_x-pointer_size,mapped_z-pointer_size,mapped_x+pointer_size,mapped_z+pointer_size,fill=break_colur, outline=throttle_colur, start=(math.degrees(message["yaw"])-15)+90, extent=45)
                #print(f'Orig: { message["loc_x"] }x,{ message["loc_y"] }y,{ message["loc_z"] }z, Mapped: {mapped_x}x,{mapped_y}y,{mapped_z}z,')


            #print(f"UI Update took {time.time() - ui_update_start}")
            self.after(ui_update_interval, self.update_ui_telemetry)


def _get_listener():
    try:
        print('Starting listener on 0.0.0.0:20777')
        return TelemetryListener(host="0.0.0.0")
    except OSError as exception:
        print(f'Unable to setup connection: {exception.args[1]}')
        print('Failed to open connector, stopping.')
        exit(127)

def startF1Server():
    listener = _get_listener()
    
    session_time = 0
    speed = 0
    throttle = 0.0
    brake = 0.0
    drs = 0
    last_laps = [{'time': 0, 'valid': True},{'time': 0, 'valid': True},{'time': 0, 'valid': True},{'time': 0, 'valid': True},{'time': 0, 'valid': True}]
    loc_x = 0.0
    loc_y = 0.0
    loc_z = 0.0
    yaw = 0.0
    last_ui_update = time.time()
    track_id = -1
    game_paused = 1
    lap_number = 0

    while True:
        packet = listener.get()

        if (packet.header.packet_id == 0): #PacketMotionData
            session_time = packet.header.session_time
            loc_x = packet.car_motion_data[0].world_position_x
            loc_y = packet.car_motion_data[0].world_position_y
            loc_z = packet.car_motion_data[0].world_position_z
            yaw = packet.car_motion_data[0].yaw
        
        if (packet.header.packet_id == 1): #PacketSessionData
            session_time = packet.header.session_time
            #print(json.dumps(packet.to_dict(), indent=4, sort_keys=True))
            #"formula": 0, # 0 = F1 Modern, 1 = F1 Classic, 2 = F2, 3 = F1 Generic, 4 = Beta, 5 = Supercars, 6 = Esports, 7 = F2 2021
            #"game_mode": 5,
            track_id = packet.track_id
            game_paused = packet.game_paused
        
        #if (packet.header.packet_id == 2): #PacketLapData
        #    session_time = packet.header.session_time
        #    lap_number = packet.current_lap_num

        if (packet.header.packet_id == 6): #PacketCarTelemetryData
            session_time = packet.header.session_time
            #print(json.dumps(packet.to_dict(), indent=4, sort_keys=True))
            #print("Speed = " + str(packet.car_telemetry_data[0].speed))
            #speed.set(str(packet.car_telemetry_data[0].speed) + " KPH")
            speed = packet.car_telemetry_data[0].speed
            throttle = packet.car_telemetry_data[0].throttle
            brake = packet.car_telemetry_data[0].brake
            drs = packet.car_telemetry_data[0].drs
        
        if (packet.header.packet_id == 11 and packet.car_idx == 0): #PacketSessionHistoryData
            session_time = packet.header.session_time
            #if packet.lap_history_data[1].lap_time_in_ms != 0:
            #    print(json.dumps(packet.to_dict(), indent=4, sort_keys=True))
            #print("Last 5 Laps time:" + 
            #      str(packet.lap_history_data[0].lap_time_in_ms/1000) + ", " + 
            #      str(packet.lap_history_data[1].lap_time_in_ms/1000) + ", " + 
            #      str(packet.lap_history_data[2].lap_time_in_ms/1000) + ", " + 
            #      str(packet.lap_history_data[3].lap_time_in_ms/1000) + ", " + 
            #      str(packet.lap_history_data[4].lap_time_in_ms/1000) + ", ")
            num_laps = packet.num_laps
            if num_laps > 99: # Max 100 laps of data, this is going to be fun to test...
                num_laps = 99
            if num_laps < 5:
                num_laps = 6
            last_laps[0]['time'] = packet.lap_history_data[num_laps-6].lap_time_in_ms
            last_laps[0]['valid'] = bool(packet.lap_history_data[num_laps-6].lap_valid_bit_flags & 0b0001)
            last_laps[1]['time'] = packet.lap_history_data[num_laps-5].lap_time_in_ms
            last_laps[1]['valid'] = bool(packet.lap_history_data[num_laps-5].lap_valid_bit_flags & 0b0001)
            last_laps[2]['time'] = packet.lap_history_data[num_laps-4].lap_time_in_ms
            last_laps[2]['valid'] = bool(packet.lap_history_data[num_laps-4].lap_valid_bit_flags & 0b0001)
            last_laps[3]['time'] = packet.lap_history_data[num_laps-3].lap_time_in_ms
            last_laps[3]['valid'] = bool(packet.lap_history_data[num_laps-3].lap_valid_bit_flags & 0b0001)
            last_laps[4]['time'] = packet.lap_history_data[num_laps-2].lap_time_in_ms
            last_laps[4]['valid'] = bool(packet.lap_history_data[num_laps-2].lap_valid_bit_flags & 0b0001)
            print(f"{packet.lap_history_data[num_laps-2].lap_valid_bit_flags:>08b}, {packet.lap_history_data[num_laps-3].lap_valid_bit_flags:>08b}, {packet.lap_history_data[num_laps-4].lap_valid_bit_flags:>08b}, {packet.lap_history_data[num_laps-5].lap_valid_bit_flags:>08b}, {packet.lap_history_data[num_laps-6].lap_valid_bit_flags:>08b}")
            print(f"{last_laps[0]['valid']!s:^5}, {last_laps[1]['valid']!s:^5}, {last_laps[2]['valid']!s:^5}, {last_laps[3]['valid']!s:^5}, {last_laps[4]['valid']!s:^5}")
            lap_number = packet.num_laps
            #print(f"Lap {lap_number}")
        
        #print(f"{speed}KPH, {last_laps[0]/1000}s, {last_laps[1]/1000}s, {last_laps[2]/1000}s, {last_laps[3]/1000}s, {last_laps[4]/1000}s, {throttle*100:0.0f}%, {brake*100:0.0f}%, {drs}, {loc_x:0.2f}x, {loc_y:0.2f}y")

        if last_ui_update < time.time() - (telelmetry_update_interval / 1000):
            last_ui_update = time.time()
            update = {
                "session_time": session_time,
                "speed": speed,
                "last_laps": [
                    last_laps[0],
                    last_laps[1],
                    last_laps[2],
                    last_laps[3],
                    last_laps[4],
                ],
                "throttle": throttle,
                "brake": brake,
                "drs": drs,
                "loc_x": loc_x,
                "loc_y": loc_y,
                "loc_z": loc_z,
                "yaw": yaw,
                "track_id": track_id,
                "game_paused": game_paused,
                "lap_number": lap_number,
                "update_time": last_ui_update
            }
            #print(json.dumps(update, indent=4, sort_keys=True))
            telemetry_queue.put(update)

if __name__ == '__main__':
    App().mainloop()
