"""
ROB 599 Robotics and Society, HW 1
Code translated from Matlab assignment implementation by Connor Yates
Updated: 2020-01-23

Example testing using the simulator provided. This file instantiate the simulator, calls it, and collects data on it.
"""
from simulator import Simulator
import numpy as np

trials = 100
data = np.zeros((trials, 6))
for t in range(trials):
    sim = Simulator(1, 0.5)
    combatants_killed, warfighters_killed, civ_killed, num_combatants, num_warfighters, num_civ = sim.run()
    data[t, :] = [combatants_killed, warfighters_killed, civ_killed, num_combatants, num_warfighters, num_civ]

print("Final average values:")
print("\tAverage combatants killed: {}/{}".format(np.average(data[:, 0]), np.average(data[:, 3])))
print("\tAverage warfighters killed: {}/{}".format(np.average(data[:, 1]), np.average(data[:, 4])))
print("\tAverage civ killed: {}/{}".format(np.average(data[:, 2]), np.average(data[:, 5])))

print("Running for visualization...")
sim = Simulator(1, 0.5, displayOn=True, output_img_dir='imgs')
_ = sim.run()
print("Done.")
