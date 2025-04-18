import threading
import time
import random


# ==== CONFIGURATION ====
N = 15  #streets
GROUP_SIZE = 3  
RUN_TIME = 40 

#GENERATE CONFLICT GROUPS 
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

# TRAFFIC CONTROLLE
class TrafficController:
    def __init__(self, groups):
        self.groups = groups
        self.current_index = 0
        self.lock = threading.Lock()

    def is_green(self, street_id):
        return street_id in self.groups[self.current_index]

    def next_group(self):
        with self.lock:
            self.current_index = (self.current_index + 1) % len(self.groups)

# STREET THREAD
class Street(threading.Thread):
    def __init__(self, street_id, controller):
        super().__init__()
        self.street_id = street_id
        self.controller = controller
        self.cars_waiting = random.randint(1, 5)
        self.running = True
        self.lock = threading.Lock()
        self.total_passed = 0
        self.total_arrived = self.cars_waiting
        self.empty_announced = False

    def run(self):
        while self.running:
            if self.controller.is_green(self.street_id):
                with self.lock:
                    if self.cars_waiting == 0:
                        if not self.empty_announced:
                            print(f"Street {self.street_id} is empty.")
                            self.empty_announced = True  
                    else:
                        cars_to_pass = min(2, self.cars_waiting)
                        for _ in range(cars_to_pass):
                            print(f"Street {self.street_id}: car passed!")
                            self.cars_waiting -= 1
                            self.total_passed += 1
                            time.sleep(0.5)
                        self.empty_announced = False  
            else:
                time.sleep(0.1)


    def add_car(self):
        with self.lock:
            self.cars_waiting += 1
            self.total_arrived += 1
            print(f"Street {self.street_id}: car arrived. Waiting = {self.cars_waiting}")

#SIMULATION SETUP
controller = TrafficController(conflict_groups)
streets = [Street(i, controller) for i in range(N)]

for street in streets:
    street.start()

# SIMULATION LOOP 
start_time = time.time()
try:
    while time.time() - start_time < RUN_TIME:
        current_group = conflict_groups[controller.current_index]
        green_time = random.randint(3, 7)
        print(f"\n== GREEN for group {current_group} for {green_time} seconds ==")

        # Simulate random car arrivals
        for _ in range(random.randint(1, N // 2)):
            random.choice(streets).add_car()

        time.sleep(green_time)
        controller.next_group()

finally:
    for s in streets:
        s.running = False
    for s in streets:
        s.join()

#FINAL SUMMARY
print("\nSimulation ended.\n== Summary ==")
for s in streets:
    print(f"Street {s.street_id}: Total Arrived = {s.total_arrived}, Passed = {s.total_passed}, Waiting = {s.cars_waiting}")
