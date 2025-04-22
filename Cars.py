
import multiprocessing
import time
import random

# ==== CONFIGURATION ====
N = 6  # Number of streets
GROUP_SIZE = 2
RUN_TIME = 30  # Seconds

# ==== Generate conflict-free groups ====
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
def street_process(street_id, controller_pipe, car_queue, status_queue):
    cars_waiting = random.randint(1, 5)
    total_passed = 0
    total_arrived = cars_waiting
    empty_announced = False

    while True:
        msg = controller_pipe.recv()
        if msg == "EXIT":
            break
        elif msg == "GO":
            if cars_waiting == 0:
                if not empty_announced:
                    print(f"Street {street_id} is empty.")
                    empty_announced = True
            else:
                cars_to_pass = min(2, cars_waiting)
                for _ in range(cars_to_pass):
                    print(f"Street {street_id}: car passed!")
                    cars_waiting -= 1
                    total_passed += 1
                    time.sleep(0.5)
                empty_announced = False

        # Check for new car arrivals
        while not car_queue.empty():
            car_queue.get()
            cars_waiting += 1
            total_arrived += 1
            print(f"Street {street_id}: car arrived. Waiting = {cars_waiting}")

    status_queue.put((street_id, total_arrived, total_passed, cars_waiting))

# ==== Main Simulation ====
def run_simulation():
    processes = []
    pipes = []
    car_queues = []
    status_queue = multiprocessing.Queue()

    # Setup all streets
    for i in range(N):
        parent_conn, child_conn = multiprocessing.Pipe()
        car_queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=street_process, args=(i, child_conn, car_queue, status_queue))
        processes.append(p)
        pipes.append(parent_conn)
        car_queues.append(car_queue)
        p.start()

    start_time = time.time()
    try:
        while time.time() - start_time < RUN_TIME:
            current_index = int(((time.time() - start_time) // 5) % len(conflict_groups))
            current_group = conflict_groups[current_index]
            print(f"\n== GREEN for group {current_group} ==")

            # Send "GO" to streets in the group
            for i in range(N):
                if i in current_group:
                    pipes[i].send("GO")
                else:
                    pipes[i].send("WAIT")

            # Random car arrivals
            for _ in range(random.randint(1, N // 2)):
                random.choice(car_queues).put("CAR")

            time.sleep(5)

    finally:
        # Clean shutdown
        for pipe in pipes:
            pipe.send("EXIT")
        for p in processes:
            p.join()

        print("\nSimulation ended.\n== Summary ==")
        while not status_queue.empty():
            sid, arrived, passed, waiting = status_queue.get()
            print(f"Street {sid}: Total Arrived = {arrived}, Passed = {passed}, Waiting = {waiting}")

if __name__ == "__main__":
    run_simulation()
