import tkinter as tk
import multiprocessing
import random
import time
import threading

# CONFIGURATION
N = 12
GROUP_SIZE = 3
RUN_TIME = 60
UPDATE_INTERVAL = 0.5

# ==== Generate Conflict Groups ====
def generate_conflict_groups(n, group_size):
    groups = []
    used = set()
    for i in range(n):
        if i not in used:
            group = [i]
            for j in range(i + 1, n):
                if j not in used and len(group) < group_size:
                    group.append(j)
            groups.append(group)
            used.update(group)
    return groups

conflict_groups = generate_conflict_groups(N, GROUP_SIZE)

# ==== Street Process ====
def street_process(street_id, ctrl_pipe, data_queue):
    cars_waiting = random.randint(1, 5)
    allowed_to_pass = False

    while True:
        if ctrl_pipe.poll():
            msg = ctrl_pipe.recv()
            if msg == "EXIT":
                break
            elif msg == "GO":
                allowed_to_pass = True
            elif msg == "WAIT":
                allowed_to_pass = False

        if allowed_to_pass and cars_waiting > 0:
            cars_to_pass = min(2, cars_waiting)
            cars_waiting -= cars_to_pass
            time.sleep(0.5)

        # Random new car arrival (even if light is red)
        if random.random() < 0.3:
            cars_waiting += 1

        # Send update to GUI
        data_queue.put((street_id, cars_waiting))
        time.sleep(1)

# ==== Traffic GUI ====
class TrafficGUI:
    def __init__(self, root, num_streets, data_queue, control_pipes):
        self.root = root
        self.num_streets = num_streets
        self.data_queue = data_queue
        self.control_pipes = control_pipes
        self.street_labels = []
        self.car_labels = []
        self.car_counts = [0] * num_streets
        self.green_group = []
        self.remaining_time = 0
        self.create_ui()
        self.poll_data()

    def create_ui(self):
        self.root.title("Distributed Traffic Simulation GUI")
        for i in range(self.num_streets):
            frame = tk.Frame(self.root, padx=10, pady=5)
            frame.grid(row=i, column=0, sticky='w')
            tk.Label(frame, text=f"Street {i}", width=12).pack(side='left')
            car_label = tk.Label(frame, text="Cars: 0", width=10)
            car_label.pack(side='left')
            light_label = tk.Label(frame, text="RED", bg='red', fg='white', width=6)
            light_label.pack(side='left')
            self.car_labels.append(car_label)
            self.street_labels.append(light_label)

        self.timer_label = tk.Label(self.root, text="Time Remaining: 0s", font=('Arial', 12, 'bold'))
        self.timer_label.grid(row=self.num_streets, column=0, pady=10)

    def poll_data(self):
        while not self.data_queue.empty():
            sid, cars = self.data_queue.get()
            self.car_counts[sid] = cars
            self.car_labels[sid].config(text=f"Cars: {cars}")

        for i in range(self.num_streets):
            if i in self.green_group:
                self.street_labels[i].config(text="GREEN", bg='green')
            else:
                self.street_labels[i].config(text="RED", bg='red')

        self.timer_label.config(text=f"Time Remaining: {self.remaining_time}s")
        self.root.after(int(UPDATE_INTERVAL * 1000), self.poll_data)

# ==== Controller Logic (corrected) ====
def controller_loop(pipes, data_queue, gui):
    start_time = time.time()
    group_index = 0

    while time.time() - start_time < RUN_TIME:
        green_group = conflict_groups[group_index]
        gui.green_group = green_group

        # Send control messages once per group switch
        for i in range(N):
            if i in green_group:
                pipes[i].send("GO")
            else:
                pipes[i].send("WAIT")

        # Countdown 5 seconds for the group
        for t in range(5, 0, -1):
            gui.remaining_time = t
            time.sleep(1)

        # Move to next group
        group_index = (group_index + 1) % len(conflict_groups)

    # End of simulation
    for pipe in pipes:
        pipe.send("EXIT")

# ==== Main Launcher ====
def run_distributed_gui():
    data_queue = multiprocessing.Queue()
    pipes = []
    processes = []

    for i in range(N):
        parent_conn, child_conn = multiprocessing.Pipe()
        p = multiprocessing.Process(target=street_process, args=(i, child_conn, data_queue))
        p.start()
        pipes.append(parent_conn)
        processes.append(p)

    root = tk.Tk()
    gui = TrafficGUI(root, N, data_queue, pipes)
    threading.Thread(target=controller_loop, args=(pipes, data_queue, gui), daemon=True).start()
    root.mainloop()

    for p in processes:
        p.join()

if __name__ == "__main__":
    run_distributed_gui()
