"""
ROB 599 Robotics and Society, HW 1
Code translated from Matlab assignment implementation by Connor Yates
Updated: 2020-01-23

Simulator for military operations scenarios

Three scenarios provided:
Scenario 1: peacekeeping, few combatants
Scenario 2: peacekeeping, guerrilla forces
Scenario 3: active war zone, few civilians, many combatants

Parameters are set by the calling __init__() function. After that object is created, calling the .run() method will
execute the simulaiton for the configured scenario.

Display parameters:
    c_enemy: default color red, enemies as determined by tau value
    c_sensor: default green, shows sensor assets
    c_lethal: default purple, lethal asset
    c_human: default blue, human warfighter
    c_unknown: default black, unknown (civialian or enemy)
"""
import numpy as np
from random import random
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from os import path
import math

class Simulator:
    def __init__(self, scenario, tau, displayOn=False, output_img_dir="", greedy=True):
        """
        Simulation class used for this assignment. The main method to call is .run(), which executes all the functions
        in the correct order. This assignment has you place code in four different functions, boldly noted with an
        all-caps TODO YOUR CODE HERE

        :param scenario: int, should be 1 2 or 3. Will throw a ValueError if not one of those values
        :param tau: the classification threshold for
        :param displayOn: whether or not to render the images and save them to disk. (SLOW)
        :param output_img_dir: to save images in an optional folder, to make the displaying easier and less messy
        """
        if not (0 <= tau <= 1):
            raise ValueError("tau must be a float in [0, 1]")
        self.tau = tau
        self.endTime = 50
        self.displayOn = displayOn
        self.output_img_dir = output_img_dir

        # world parameters
        self.xy_size = 50
        self.lethal_radius = 10
        self.scene = scenario

        # agent counts in each category
        self.num_sensors = 2
        self.num_lethal = 2
        self.num_humans = 4
        self.num_unknown = 4

        # User defined agent parameters:
        self.sensor_max_step_size = 2.0
        self.lethal_max_step_size = 2.0
        self.use_greedy = greedy
        self.sensor_range = 10.0

        # starting locations
        self.sensor_loc = np.random.randint(0, self.xy_size, [self.num_sensors, 2])
        self.lethal_loc = np.random.randint(0, self.xy_size, [self.num_lethal, 2])
        self.human_loc = np.random.randint(0, self.xy_size, [self.num_humans, 2])
        self.unknown_loc = np.random.randint(0, self.xy_size, [self.num_unknown, 2])

        # is each warfighter alive (bool)
        self.human_alive = np.full(self.num_humans, True)

        # create random goal locations for each human to reach
        self.human_goal = np.random.randint(0, self.xy_size, [self.num_humans, 2])

        # create the initial maximally uninformed prior for each certainty of combatant
        # could change this based on the scenario if you wanted to
        if scenario == 1:
            self.unknown_estimates = np.full(self.num_unknown, 0.5)
        elif scenario == 2:
            self.unknown_estimates = np.full(self.num_unknown, 0.5)
        else:
            self.unknown_estimates = np.full(self.num_unknown, 0.5)

        # Set the ground truth for each scenario
        self.unknown_ground_truth = [None]*self.num_unknown
        # Peacekeeping, 10% combatants
        if scenario == 1:
            for i in range(self.num_unknown):
                if random() > 0.1:
                    self.unknown_ground_truth[i] = "civilian"
                else:
                    self.unknown_ground_truth[i] = "combatant"

        # Guerrilla forces, 30% combatants
        elif scenario == 2:
            for i in range(self.num_unknown):
                if random() > 0.3:
                    self.unknown_ground_truth[i] = "civilian"
                else:
                    self.unknown_ground_truth[i] = "combatant"

        # Active war zone, 80% combatants
        elif scenario == 3:
            for i in range(self.num_unknown):
                if random() > 0.8:
                    self.unknown_ground_truth[i] = "civilian"
                else:
                    self.unknown_ground_truth[i] = "combatant"

        else:
            raise(ValueError("Scenario number not recognized"))

        # lastly, set the alive markers for unknowns and their location goals
        self.unknown_alive = np.full(self.num_unknown, True)
        self.unknown_goal = np.random.randint(0, self.xy_size, [self.num_unknown, 2])

    def run(self):
        """
        Main function to call. Executes the simulation for the specified number of timesteps and returns statistics
        on the number of each category killed and how many of each agent type there was.
        :return: 6-tuple of ints:
                 num_combatants_killed, num_warfighters_killed, num_civilians_killed
                 num_combatants, num_warfighters, num_civilians
        :raises: ValueError if it somehow finds an unknown label of 'combatant' or 'civilian' in the unknown list.
        """
        for t in range(self.endTime):
            pass
            # update agent locations

            self.updateSensorLocations()
            self.updateLethalLocations()
            self.updateHumanLocations()
            self.updateUnknownLocations()

            # update estimates of combatant versus noncombatant
            self.updateCombatantEstimate()

            # update lethal actions (combatants against humans and lethal robots against combatants)
            self.updateLethalActions()

            # draw world if display is on
            if self.displayOn:
                self.render_world(t, self.output_img_dir)

        # print(self.unknown_estimates)
        # print(self.unknown_ground_truth)

        # Calculate final statistics for the simulation
        num_combatants_killed = 0
        num_civilians_killed = 0
        num_combatants = 0
        num_civilians = 0
        for u in range(self.num_unknown):
            if self.unknown_ground_truth[u] == "combatant":
                num_combatants += 1
                if not self.unknown_alive[u]:
                    num_combatants_killed += 1
            elif self.unknown_ground_truth[u] == "civilian":
                num_civilians += 1
                if not self.unknown_alive[u]:
                    num_civilians_killed += 1
            else:
                raise ValueError("A value other than 'combatant' or 'civilian' made its way into self.unknown_ground_truth.")
        num_warfighters_killed = 0
        for w in range(self.num_humans):
            if not self.human_alive[w]:
                num_warfighters_killed += 1

        return num_combatants_killed, num_warfighters_killed, num_civilians_killed, \
               num_combatants, self.num_humans, num_civilians

    def render_world(self, t, output_dir):
        """
        Creates an image using matplotlib of the current state of the world, which is saved to disk.

        :param t: Which timestep is being recorded, to differentiate the filenames for each frame.
        :param ouput_dir: joined with the filename to create the full path to save images.
        :return: None
        """
        enemy = ("red", "X")
        sensor = ("green", '^')
        lethal = ("purple", "v")
        human = ("blue", 'o')
        unknown = ("black", 'D')
        fig = plt.figure()
        ax = fig.gca()
        ax.set_xlim([0, self.xy_size])
        ax.set_ylim([0, self.xy_size])

        ax.scatter(self.sensor_loc[:, 0], self.sensor_loc[:, 1], color=sensor[0], marker=sensor[1], label="Sensor")
        ax.scatter(self.lethal_loc[:, 0], self.lethal_loc[:, 1], color=lethal[0], marker=lethal[1], label="Lethal")
        for h in range(self.num_humans):
            if self.human_alive[h]:
                ax.scatter(self.human_loc[h, 0], self.human_loc[h, 1], color=human[0], marker=human[1], label='Human Warfighter')
        for u in range(self.num_unknown):
            if self.unknown_alive[u]:
                if self.unknown_estimates[u] > self.tau:
                    ax.scatter(self.unknown_loc[u, 0], self.unknown_loc[u, 1], color=enemy[0], marker=enemy[1], label="Enemy Combatant")
                else:
                    ax.scatter(self.unknown_loc[u, 0], self.unknown_loc[u, 1], color=unknown[0], marker=unknown[1], label="Unknown")
        # below is some crazy code to make the legend nice
        legend_elements = [Line2D([0], [0], color='w', markerfacecolor=enemy[0], marker=enemy[1], markersize=10,
                                  label='Enemy Combatant'),
                           Line2D([0], [0], color='w', markerfacecolor=sensor[0], marker=sensor[1], markersize=10,
                                  label='Sensors'),
                           Line2D([0], [0], color='w', markerfacecolor=lethal[0], marker=lethal[1], markersize=10,
                                  label='Lethals'),
                           Line2D([0], [0], color='w', markerfacecolor=human[0], marker=human[1], markersize=10,
                                  label='Warfighters'),
                           Line2D([0], [0], color='w', markerfacecolor=unknown[0], marker=unknown[1], markersize=10,
                                  label='Unknowns')
                           ]
        legend = ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3)
        plt.savefig(fname=path.join(output_dir, "frame_{:03}.png".format(t)), bbox='tight', bbox_extra_artists=[legend])
        plt.close(fig)


    def getDistancesForSensors(self, sense_id):
        """
        Calculates distances between all objects and sensors for use in policies
        :param sense_id:
        :return:
        """
        unk_distances = np.zeros(self.num_unknown)  # Unknown to sensor
        wf_distances = np.zeros(self.num_humans)  # Human to sensor
        leth_distances = np.zeros(self.num_lethal)  # Lethal to sensor
        unk_wf_distances = np.zeros((self.num_unknown, self.num_humans))  # Unknown to Human

        x_sense = self.sensor_loc[sense_id, 0]
        y_sense = self.sensor_loc[sense_id, 1]

        # Distance between unknown and sensor as well as unknowns and warfighters
        for unk_id in range(self.num_unknown):
            if self.unknown_alive[unk_id]:
                x_targ = self.unknown_loc[unk_id, 0]
                y_targ = self.unknown_loc[unk_id, 1]
                x_dist = x_targ - x_sense
                y_dist = y_targ - y_sense
                unk_distances[unk_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                if unk_distances[unk_id] == 0.0:
                    unk_distances[unk_id] = 0.1

                for wf_id in range(self.num_humans):
                    if self.human_alive[wf_id]:
                        x_hum = self.human_loc[wf_id, 0]
                        y_hum = self.human_loc[wf_id, 1]
                        x_dist = x_hum - x_targ
                        y_dist = y_hum - y_targ
                        unk_wf_distances[unk_id, wf_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                        if unk_wf_distances[unk_id, wf_id] == 0.0:
                            unk_wf_distances[unk_id, wf_id] = 0.1
                    else:
                        unk_wf_distances[unk_id, wf_id] = 1000.00  # Human is dead
            else:  # Unknwon is dead
                unk_distances[unk_id] = 1000.00
                for wf_id in range(self.num_humans):
                    unk_wf_distances[unk_id, wf_id] = 1000.00

        # Distance between warfighters and sensor
        for wf_id in range(self.num_humans):
            if self.human_alive[wf_id]:
                x_wf = self.human_loc[wf_id, 0]
                y_wf = self.human_loc[wf_id, 1]
                x_dist = x_wf - x_sense
                y_dist = y_wf - y_sense
                wf_distances[wf_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                if wf_distances[wf_id] == 0.0:
                    wf_distances[wf_id] = 0.1
            else:  # Human is dead
                wf_distances[wf_id] = 1000.00

        # Distance between lethal robots and sensor
        for leth_id in range(self.num_sensors):
            x_leth = self.lethal_loc[leth_id, 0]
            y_leth = self.lethal_loc[leth_id, 1]
            x_dist = x_leth - x_sense
            y_dist = y_leth - y_sense
            leth_distances[leth_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
            if leth_distances[leth_id] == 0.0:
                leth_distances[leth_id] = 0.1

        return unk_distances, wf_distances, leth_distances, unk_wf_distances

    def sensorGreedyMove(self, sense_id):
        """
        Sensor platforms move greedily towards the closest target with uncertainty below threshold
        :return:
        """
        distances = np.zeros(self.num_unknown)
        x_sens = self.sensor_loc[sense_id, 0]
        y_sens = self.sensor_loc[sense_id, 1]

        for unk_id in range(self.num_unknown):
            if self.unknown_alive[unk_id] and self.unknown_estimates[unk_id] <= self.tau:
                x_unk = self.unknown_loc[unk_id, 0]
                y_unk = self.unknown_loc[unk_id, 1]
                x_dist = x_unk - x_sens
                y_dist = y_unk - y_sens
                distances[unk_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                if distances[unk_id] == 0.0:
                    distances[unk_id] = 0.5
            else:
                distances[unk_id] = 1000.00

        targ_id = np.argmin(distances)
        if distances[targ_id] < 1000.0:
            x_targ = self.unknown_loc[targ_id, 0]
            y_targ = self.unknown_loc[targ_id, 1]
            dx = ((x_targ - x_sens) / distances[targ_id])*self.sensor_max_step_size
            dy = ((y_targ - y_sens) / distances[targ_id])*self.sensor_max_step_size
            self.sensor_loc[sense_id, 0] += dx
            self.sensor_loc[sense_id, 1] += dy

    def sensorPolicyS1(self, sense_id):
        """
        Sensor platforms move according to policy
        :return:
        """

        x_sense = self.sensor_loc[sense_id, 0]
        y_sense = self.sensor_loc[sense_id, 1]
        unk_distances, wf_distances, leth_distances, unk_wf_distances = self.getDistancesForSensors(sense_id)

        if sense_id == 0:
            action_count = 0
            # Move towards unknown which is closest to a warfighter
            for unk_id in range(self.num_unknown):
                absolute_min = np.min(unk_wf_distances)
                min_dist = np.min(unk_wf_distances[unk_id, :])
                if min_dist == absolute_min and min_dist < 6.0:  # Move towards unknown if it is close to a warfighter
                    targ_id = np.argmin(unk_wf_distances[unk_id, :])
                    x_targ = self.unknown_loc[targ_id, 0]
                    y_targ = self.unknown_loc[targ_id, 1]
                    dx = ((x_targ - x_sense) / min_dist) * self.sensor_max_step_size
                    dy = ((y_targ - y_sense) / min_dist) * self.sensor_max_step_size
                    self.sensor_loc[sense_id, 0] += dx
                    self.sensor_loc[sense_id, 1] += dy
                    action_count += 1
                    break

            # Move towards closest warfighter
            min_wf_id = np.argmin(wf_distances)
            if wf_distances[min_wf_id] < 1000.00 and action_count == 0:
                x_targ = self.human_loc[min_wf_id, 0]
                y_targ = self.human_loc[min_wf_id, 1]
                dx = ((x_targ - x_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                dy = ((y_targ - y_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                self.sensor_loc[sense_id, 0] += dx
                self.sensor_loc[sense_id, 1] += dy
        else:
            action_count = 0
            # Move towards unknown currently suspected of being a combatant
            for unk_id in range(self.num_unknown):
                if self.unknown_estimates[unk_id] > self.tau and self.unknown_alive[unk_id]:
                    x_targ = self.unknown_loc[unk_id, 0]
                    y_targ = self.unknown_loc[unk_id, 1]
                    dx = ((x_targ - x_sense) / unk_distances[unk_id]) * self.sensor_max_step_size
                    dy = ((y_targ - y_sense) / unk_distances[unk_id]) * self.sensor_max_step_size
                    self.sensor_loc[sense_id, 0] += dx
                    self.sensor_loc[sense_id, 1] += dy
                    action_count += 1
                    break

            # Move towards closest warfighter
            min_wf_id = np.argmin(wf_distances)
            if wf_distances[min_wf_id] < 1000.00 and action_count == 0:
                x_targ = self.human_loc[min_wf_id, 0]
                y_targ = self.human_loc[min_wf_id, 1]
                dx = ((x_targ - x_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                dy = ((y_targ - y_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                self.sensor_loc[sense_id, 0] += dx
                self.sensor_loc[sense_id, 1] += dy

    def sensorPolicyS2(self, sense_id):
        x_sense = self.sensor_loc[sense_id, 0]
        y_sense = self.sensor_loc[sense_id, 1]
        unk_distances, wf_distances, leth_distances, unk_wf_distances = self.getDistancesForSensors(sense_id)

        if sense_id == 0:
            action_count = 0
            # Move towards unknown which is closest to a warfighter
            for unk_id in range(self.num_unknown):
                absolute_min = np.min(unk_wf_distances)
                min_dist = np.min(unk_wf_distances[unk_id, :])
                if min_dist == absolute_min and min_dist < 6.0:  # Move towards unknown if it is close to a warfighter
                    targ_id = np.argmin(unk_wf_distances[unk_id, :])
                    x_targ = self.unknown_loc[targ_id, 0]
                    y_targ = self.unknown_loc[targ_id, 1]
                    dx = ((x_targ - x_sense) / min_dist) * self.sensor_max_step_size
                    dy = ((y_targ - y_sense) / min_dist) * self.sensor_max_step_size
                    self.sensor_loc[sense_id, 0] += dx
                    self.sensor_loc[sense_id, 1] += dy
                    action_count += 1
                    break

            # Move towards closest warfighter
            min_wf_id = np.argmin(wf_distances)
            if wf_distances[min_wf_id] < 1000.00 and action_count == 0:
                x_targ = self.human_loc[min_wf_id, 0]
                y_targ = self.human_loc[min_wf_id, 1]
                dx = ((x_targ - x_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                dy = ((y_targ - y_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                self.sensor_loc[sense_id, 0] += dx
                self.sensor_loc[sense_id, 1] += dy
        else:
            action_count = 0
            # Move towards unknown currently suspected of being a combatant
            for unk_id in range(self.num_unknown):
                if self.unknown_estimates[unk_id] > self.tau and self.unknown_alive[unk_id]:
                    x_targ = self.unknown_loc[unk_id, 0]
                    y_targ = self.unknown_loc[unk_id, 1]
                    dx = ((x_targ - x_sense) / unk_distances[unk_id]) * self.sensor_max_step_size
                    dy = ((y_targ - y_sense) / unk_distances[unk_id]) * self.sensor_max_step_size
                    self.sensor_loc[sense_id, 0] += dx
                    self.sensor_loc[sense_id, 1] += dy
                    action_count += 1
                    break

            # Move towards closest warfighter
            min_wf_id = np.argmin(wf_distances)
            if wf_distances[min_wf_id] < 1000.00 and action_count == 0:
                x_targ = self.human_loc[min_wf_id, 0]
                y_targ = self.human_loc[min_wf_id, 1]
                dx = ((x_targ - x_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                dy = ((y_targ - y_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                self.sensor_loc[sense_id, 0] += dx
                self.sensor_loc[sense_id, 1] += dy

    def sensorPolicyS3(self, sense_id):

        if sense_id == 0:
            self.sensorGreedyMove(sense_id)
        else:
            x_sense = self.sensor_loc[sense_id, 0]
            y_sense = self.sensor_loc[sense_id, 1]
            unk_distances, wf_distances, leth_distances, unk_wf_distances = self.getDistancesForSensors(sense_id)

            action_count = 0
            for unk_id in range(self.num_unknown):
                min_unk_wf_dist = np.min(unk_wf_distances[unk_id, :])
                if min_unk_wf_dist < 10.0:  # Move towards unknown if it is too close to a warfighter
                    targ_id = np.argmin(unk_wf_distances[unk_id, :])
                    x_targ = self.unknown_loc[targ_id, 0]
                    y_targ = self.unknown_loc[targ_id, 1]
                    dx = ((x_targ - x_sense) / min_unk_wf_dist) * self.sensor_max_step_size
                    dy = ((y_targ - y_sense) / min_unk_wf_dist) * self.sensor_max_step_size
                    self.sensor_loc[sense_id, 0] += dx
                    self.sensor_loc[sense_id, 1] += dy
                    action_count += 1
                    break
                if self.unknown_estimates[unk_id] < self.tau and self.unknown_alive[unk_id] and unk_distances[unk_id] > 10.0:
                    assert (action_count == 0)
                    x_targ = self.unknown_loc[unk_id, 0]
                    y_targ = self.unknown_loc[unk_id, 1]
                    dx = ((x_targ - x_sense) / unk_distances[unk_id]) * self.sensor_max_step_size
                    dy = ((y_targ - y_sense) / unk_distances[unk_id]) * self.sensor_max_step_size
                    self.sensor_loc[sense_id, 0] += dx
                    self.sensor_loc[sense_id, 1] += dy
                    action_count += 1
                    break

            min_wf_id = np.argmin(wf_distances)
            if wf_distances[min_wf_id] < 1000.00 and action_count == 0:
                x_targ = self.human_loc[min_wf_id, 0]
                y_targ = self.human_loc[min_wf_id, 1]
                dx = ((x_targ - x_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                dy = ((y_targ - y_sense) / wf_distances[min_wf_id]) * self.sensor_max_step_size
                self.sensor_loc[sense_id, 0] += dx
                self.sensor_loc[sense_id, 1] += dy

    def updateSensorLocations(self):
        """
        Fill in with algorithm from problem 3c or 3d
        This function controls how sensor robots move
        :return:
        """

        for sense_id in range(self.num_sensors):
            if self.use_greedy:
                self.sensorGreedyMove(sense_id)
            elif self.scene == 1:
                self.sensorPolicyS1(sense_id)
            elif self.scene == 2:
                self.sensorPolicyS2(sense_id)
            else:
                self.sensorPolicyS3(sense_id)

    def getDistancesForLethals(self, leth_id):
        """
        Calculates distances between all objects and lethal robots for use in policies
        :param leth_id:
        :return:
        """

        x_leth = self.lethal_loc[leth_id, 0]
        y_leth = self.lethal_loc[leth_id, 1]
        unk_distances = np.zeros(self.num_unknown)  # Unknown to lethal
        wf_distances = np.zeros(self.num_humans)  # Human to lethal
        sensor_distances = np.zeros(self.num_sensors)  # Sensor to lethal
        unk_wf_distances = np.zeros((self.num_unknown, self.num_humans))  # Unknown to Human

        # Distance between unknowns and lethal robots and unknowns and warfighters
        for unk_id in range(self.num_unknown):
            if self.unknown_alive[unk_id]:
                x_targ = self.unknown_loc[unk_id, 0]
                y_targ = self.unknown_loc[unk_id, 1]
                x_dist = x_targ - x_leth
                y_dist = y_targ - y_leth
                unk_distances[unk_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                if unk_distances[unk_id] == 0.0:
                    unk_distances[unk_id] = 0.1

                for wf_id in range(self.num_humans):
                    if self.human_alive[wf_id]:
                        x_hum = self.human_loc[wf_id, 0]
                        y_hum = self.human_loc[wf_id, 1]
                        x_dist = x_hum - x_targ
                        y_dist = y_hum - y_targ
                        unk_wf_distances[unk_id, wf_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                        if unk_wf_distances[unk_id, wf_id] == 0.0:
                            unk_wf_distances[unk_id, wf_id] = 0.1
                    else:
                        unk_wf_distances[unk_id, wf_id] = 1000.00  # Human is dead
            else:
                unk_distances[unk_id] = 1000.00
                for wf_id in range(self.num_humans):
                    unk_wf_distances[unk_id, wf_id] = 1000.00

        # Distance between warfighters and lethal robots
        for wf_id in range(self.num_humans):
            if self.human_alive[wf_id]:
                x_wf = self.human_loc[wf_id, 0]
                y_wf = self.human_loc[wf_id, 1]
                x_dist = x_wf - x_leth
                y_dist = y_wf - y_leth
                wf_distances[wf_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                if wf_distances[wf_id] == 0.0:
                    wf_distances[wf_id] = 0.1
            else:
                wf_distances[wf_id] = 1000.00

        # Distance between sensors and lethal robots
        for sens_id in range(self.num_sensors):
            x_sense = self.sensor_loc[sens_id, 0]
            y_sense = self.sensor_loc[sens_id, 1]
            x_dist = x_sense - x_leth
            y_dist = y_sense - y_leth
            sensor_distances[sens_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
            if sensor_distances[sens_id] == 0.0:
                sensor_distances[sens_id] = 0.1

        return unk_distances, wf_distances, sensor_distances, unk_wf_distances


    def lethalGreedyMove(self, leth_id):
        """
        Lethal platforms move greedily towards the closest target with uncertainty above threshold
        :return:
        """
        distances = np.zeros(self.num_unknown)
        x_leth = self.lethal_loc[leth_id, 0]
        y_leth = self.lethal_loc[leth_id, 1]

        for unk_id in range(self.num_unknown):
            if self.unknown_alive[unk_id] and self.unknown_estimates[unk_id] > self.tau:
                x_unk = self.unknown_loc[unk_id, 0]
                y_unk = self.unknown_loc[unk_id, 1]
                x_dist = x_unk - x_leth
                y_dist = y_unk - y_leth
                distances[unk_id] = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                if distances[unk_id] == 0.0:
                    distances[unk_id] = 0.5
            else:
                distances[unk_id] = 1000.00

        targ_id = np.argmin(distances)
        if distances[targ_id] < 1000.00:  # Move towards closest combatant
            x_targ = self.unknown_loc[targ_id, 0]
            y_targ = self.unknown_loc[targ_id, 1]
            dx = ((x_targ - x_leth)/distances[targ_id])*self.lethal_max_step_size
            dy = ((y_targ - y_leth)/distances[targ_id])*self.lethal_max_step_size
            self.lethal_loc[leth_id, 0] += dx
            self.lethal_loc[leth_id, 1] += dy


    def lethalPolicyS1(self, leth_id):
        """
        Lethal platforms move according to policy
        :return:
        """

        x_leth = self.lethal_loc[leth_id, 0]
        y_leth = self.lethal_loc[leth_id, 1]
        unk_distances, wf_distances, sensor_distances, unk_wf_distances = self.getDistancesForLethals(leth_id)

        action_count = 0
        for targ_id in range(self.num_unknown):  # Move towards identified combatant
            if self.unknown_estimates[targ_id] > self.tau and self.unknown_alive[targ_id]:
                x_targ = self.unknown_loc[targ_id, 0]
                y_targ = self.unknown_loc[targ_id, 1]
                dx = ((x_targ - x_leth) / unk_distances[targ_id]) * self.lethal_max_step_size
                dy = ((y_targ - y_leth) / unk_distances[targ_id]) * self.lethal_max_step_size
                self.lethal_loc[leth_id, 0] += dx
                self.lethal_loc[leth_id, 1] += dy
                action_count += 1
                break

        min_wf_id = np.argmin(wf_distances)
        if wf_distances[min_wf_id] < 1000.00 and action_count == 0:  # Follow closest warfighter
            x_targ = self.human_loc[min_wf_id, 0]
            y_targ = self.human_loc[min_wf_id, 1]
            dx = ((x_targ - x_leth) / wf_distances[min_wf_id]) * self.lethal_max_step_size
            dy = ((y_targ - y_leth) / wf_distances[min_wf_id]) * self.lethal_max_step_size
            self.lethal_loc[leth_id, 0] += dx
            self.lethal_loc[leth_id, 1] += dy


    def lethalPolicyS2(self, leth_id):
        """
        Lethal platforms move according to policy
        :return:
        """

        x_leth = self.lethal_loc[leth_id, 0]
        y_leth = self.lethal_loc[leth_id, 1]
        unk_distances, wf_distances, sensor_distances, unk_wf_distances = self.getDistancesForLethals(leth_id)

        action_count = 0
        for targ_id in range(self.num_unknown):  # Move towards identified combatant
            if self.unknown_estimates[targ_id] > self.tau and self.unknown_alive[targ_id]:
                x_targ = self.unknown_loc[targ_id, 0]
                y_targ = self.unknown_loc[targ_id, 1]
                dx = ((x_targ - x_leth) / unk_distances[targ_id]) * self.lethal_max_step_size
                dy = ((y_targ - y_leth) / unk_distances[targ_id]) * self.lethal_max_step_size
                self.lethal_loc[leth_id, 0] += dx
                self.lethal_loc[leth_id, 1] += dy
                action_count += 1
                break

        min_wf_id = np.argmin(wf_distances)
        if wf_distances[min_wf_id] < 1000.00 and action_count == 0:  # Follow closest warfighter
            x_targ = self.human_loc[min_wf_id, 0]
            y_targ = self.human_loc[min_wf_id, 1]
            dx = ((x_targ - x_leth) / wf_distances[min_wf_id]) * self.lethal_max_step_size
            dy = ((y_targ - y_leth) / wf_distances[min_wf_id]) * self.lethal_max_step_size
            self.lethal_loc[leth_id, 0] += dx
            self.lethal_loc[leth_id, 1] += dy


    def lethalPolicyS3(self, leth_id):
        """
                Lethal platforms move according to policy
                :return:
                """

        x_leth = self.lethal_loc[leth_id, 0]
        y_leth = self.lethal_loc[leth_id, 1]
        unk_distances, wf_distances, sensor_distances, unk_wf_distances = self.getDistancesForLethals(leth_id)

        min_unk_id = np.argmin(unk_distances)  # Closest unknown
        min_wf_id = np.argmin(wf_distances)  # Closest warfighter

        action_count = 0
        for targ_id in range(self.num_unknown):
            min_unk_wf_dist = np.min(unk_wf_distances[targ_id, :])
            if min_unk_wf_dist < 10.0:  # Move towards unknown if it is too close to a warfighter
                targ_id = np.argmin(unk_wf_distances[targ_id, :])
                x_targ = self.unknown_loc[targ_id, 0]
                y_targ = self.unknown_loc[targ_id, 1]
                dx = ((x_targ - x_leth) / min_unk_wf_dist) * self.sensor_max_step_size
                dy = ((y_targ - y_leth) / min_unk_wf_dist) * self.sensor_max_step_size
                self.sensor_loc[leth_id, 0] += dx
                self.sensor_loc[leth_id, 1] += dy
                action_count += 1
                break
            elif self.unknown_estimates[targ_id] > self.tau and self.unknown_alive[targ_id]:
                x_targ = self.unknown_loc[targ_id, 0]
                y_targ = self.unknown_loc[targ_id, 1]
                dx = ((x_targ - x_leth) / unk_distances[targ_id]) * self.lethal_max_step_size
                dy = ((y_targ - y_leth) / unk_distances[targ_id]) * self.lethal_max_step_size
                self.lethal_loc[leth_id, 0] += dx
                self.lethal_loc[leth_id, 1] += dy
                action_count += 1
                break

        if action_count == 0:
            if unk_distances[min_unk_id] < 1000.00 and leth_id == 0:  # Lethal 1 move to closest unknown
                x_targ = self.unknown_loc[min_unk_id, 0]
                y_targ = self.unknown_loc[min_unk_id, 1]
                dx = ((x_targ - x_leth) / unk_distances[min_unk_id]) * self.lethal_max_step_size
                dy = ((y_targ - y_leth) / unk_distances[min_unk_id]) * self.lethal_max_step_size
                self.lethal_loc[leth_id, 0] += dx
                self.lethal_loc[leth_id, 1] += dy
            elif wf_distances[min_wf_id] < 1000.00 and leth_id == 1:  # Lethal 2 move to closest warfighter
                x_targ = self.human_loc[min_wf_id, 0]
                y_targ = self.human_loc[min_wf_id, 1]
                dx = ((x_targ - x_leth) / wf_distances[min_wf_id]) * self.lethal_max_step_size
                dy = ((y_targ - y_leth) / wf_distances[min_wf_id]) * self.lethal_max_step_size
                self.lethal_loc[leth_id, 0] += dx
                self.lethal_loc[leth_id, 1] += dy
            else:  # Move to closest sensor
                min_sense_id = np.argmin(sensor_distances)
                x_targ = self.sensor_loc[min_sense_id, 0]
                y_targ = self.sensor_loc[min_sense_id, 1]
                dx = ((x_targ - x_leth) / sensor_distances[min_sense_id]) * self.lethal_max_step_size
                dy = ((y_targ - y_leth) / sensor_distances[min_sense_id]) * self.lethal_max_step_size
                self.lethal_loc[leth_id, 0] += dx
                self.lethal_loc[leth_id, 1] += dy


    def updateLethalLocations(self):  # How lethal robots move
        """
        Fill in with the algorithm from problem 3c or 3d
        This function controls how lethal robots move
        :return:
        """

        for leth_id in range(self.num_lethal):
            if self.use_greedy:
                self.lethalGreedyMove(leth_id)
            elif self.scene == 1:
                self.lethalPolicyS1(leth_id)
            elif self.scene == 2:
                self.lethalPolicyS2(leth_id)
            else:
                self.lethalPolicyS3(leth_id)


    def updateHumanLocations(self):
        """
        Updates the locations of all human (non-controllable) warfighters.
        They move toward random goals in an 8-connected grid. Once a goal is sufficiently reached,
        a new goal is assigned.
        :return:
        """
        for i in range(self.num_humans):
            if self.human_alive[i]:
                # conditionally generate new goal if prev goal reached
                if np.linalg.norm(self.human_loc[i] - self.human_goal[i], 2) < 4:
                    self.human_goal[i] = np.random.randint(0, self.xy_size, self.human_loc[i].shape)
                self.human_loc[i] += np.sign(self.human_goal[i] - self.human_loc[i])


    def updateUnknownLocations(self):
        """
        Updates the locations of combats and civilians
        :return: None
        """
        for i in range(self.num_unknown):
            if self.unknown_alive[i]:
                if self.unknown_ground_truth == "combatant":
                    # Combatants move towards human warfighters
                    minDistance = np.inf
                    closestWarfighter = None
                    for j in range(self.num_humans):
                        if self.human_alive:
                            distance = np.linalg.norm(self.unknown_loc[i] - self.human_loc[j], 2)
                            if distance < minDistance:
                                minDistance = distance
                                closestWarfighter = j
                    if closestWarfighter is not None:
                        self.unknown_loc[i] += np.sign(self.human_loc[closestWarfighter] - self.unknown_loc[i])
                else:
                    # Move civilian toward goal or generate new goal
                    if np.linalg.norm(self.unknown_loc[i] - self.unknown_goal[i], 2) < 4:
                        self.unknown_goal[i] = np.random.randint(0, self.xy_size, self.unknown_goal[i].shape)
                    self.unknown_loc[i] += np.sign(self.unknown_goal[i] - self.unknown_loc[i])


    def calcEuclideanDistanceSensors(self):
        """
        Calculates the euclidean distance between sensors and unknowns
        :return:
        """
        sensor_target_distances = np.zeros((self.num_sensors, self.num_unknown))
        for sen_id in range(self.num_sensors):
            sensor_x = self.sensor_loc[sen_id, 0]
            sensor_y = self.sensor_loc[sen_id, 1]

            for targ_id in range(self.num_unknown):
                target_x = self.unknown_loc[targ_id, 0]
                target_y = self.unknown_loc[targ_id, 1]
                x_dist = target_x - sensor_x
                y_dist = target_y - sensor_y
                eucl_dist = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                sensor_target_distances[sen_id, targ_id] = eucl_dist

        return sensor_target_distances


    def simSensor(self, unk_id, falseNegativeRate, falsePositiveRate):

        x = random()
        if self.unknown_ground_truth[unk_id] == "combatant":
            if x > falseNegativeRate:  # Probability that a combatant is identified as a civ
                return 1
            else:
                return 0
        else:
            if x > falsePositiveRate:  # Probability that a civ is identified as a combatant
                return 0
            else:
                return 1


    def updateCombatantEstimate(self):
        """
        # Fill in with the model from problem 3a
        # Should be different for different scenarios
        Use the self.simSensor() function to generate positive and negative measurements
        """
        distances = self.calcEuclideanDistanceSensors()

        p_fp = 0.0001  # Probability that a civ is identified as a combatant
        for unk_id in range(self.num_unknown):
            if self.unknown_alive[unk_id]:
                dist = np.min(distances[:, unk_id])  # Uses the shortest distance (most confident reading)
                if dist <= 0.0:
                    dist = 0.01
                if dist < self.sensor_range:  # Only updates estimate if sensor is within range
                    p_fn = 1 - math.exp(-dist / self.sensor_range)  # Probability that a combatant is identified as a civ
                    measurement = self.simSensor(unk_id, p_fn, p_fp)

                    p_com = self.unknown_estimates[unk_id]
                    p_civ = 1 - p_com

                    if measurement == 0:  # Sensor reads a civ
                        if self.unknown_estimates[unk_id] <= self.tau:  # I believe this is a civ
                            assert (self.unknown_estimates[unk_id] <= self.tau)
                            p_s0 = ((1 - p_fp) * p_civ) + (p_fn * p_com)  # Prob of civ and true neg, Prob of com and false neg
                            self.unknown_estimates[unk_id] = (1 - p_fp)*p_civ / p_s0

                        else:  # I believe this is a combatant
                            assert (self.unknown_estimates[unk_id] > self.tau)
                            p_s0 = ((1 - p_fp) * p_civ) + (p_fn * p_com)  # Prob of civ and true neg, Prob of com and false neg
                            self.unknown_estimates[unk_id] = p_fn * p_com / p_s0

                    else:  # Sensor reads a combatant
                        if self.unknown_estimates[unk_id] <= self.tau:  # I believe this is a civ
                            assert (self.unknown_estimates[unk_id] <= self.tau)
                            p_s1 = (p_fp * p_civ) + ((1 - p_fn) * p_com)  # prob of civ and false pos, prob of com and true pos
                            self.unknown_estimates[unk_id] = p_fp * p_civ / p_s1

                        else:  # I believe this is a combatant
                            assert (self.unknown_estimates[unk_id] > self.tau)
                            p_s1 = (p_fp * p_civ) + ((1 - p_fn) * p_com)  # prob of civ and false pos, prob of com and true pos
                            self.unknown_estimates[unk_id] = (1 - p_fn) * p_com / p_s1

                    assert(self.unknown_estimates[unk_id] >= 0.0)
                    assert(self.unknown_estimates[unk_id] <= 1.0)


    def calcEuclideanDistanceLethal(self):
        """
        Calculates the euclidean distance between sensors and unknowns
        :return:
        """
        lethal_target_distances = np.zeros((self.num_sensors, self.num_unknown))
        for leth_id in range(self.num_sensors):
            sensor_x = self.lethal_loc[leth_id, 0]
            sensor_y = self.lethal_loc[leth_id, 1]

            for targ_id in range(self.num_unknown):
                target_x = self.unknown_loc[targ_id, 0]
                target_y = self.unknown_loc[targ_id, 1]
                x_dist = target_x - sensor_x
                y_dist = target_y - sensor_y
                eucl_dist = math.sqrt((x_dist*x_dist) + (y_dist*y_dist))
                lethal_target_distances[leth_id, targ_id] = eucl_dist

        return lethal_target_distances


    def updateLethalActions(self):
        """
        This function determines if human warfighters are "disabled" by combatants
        :return:
        """
        for i in range(self.num_humans):
            for j in range(self.num_unknown):
                if (self.unknown_ground_truth[j] == "combatant") and self.unknown_alive[j]:
                    distance = np.linalg.norm(self.unknown_loc[j]-self.human_loc[i], 2)
                    if distance < self.lethal_radius:
                        self.human_alive[i] = False

        # Below determine if combatants are disabled by our lethal assets
        # Fill in with behaviorist architecture from problem 1

        distances = self.calcEuclideanDistanceLethal()

        for leth_id in range(self.num_lethal):
            for unk_id in range(self.num_unknown):
                if distances[leth_id, unk_id] <= self.lethal_radius and self.unknown_estimates[unk_id] > self.tau:
                    if self.scene == 3:
                        self.unknown_alive[unk_id] = False  # Give em the stabbo
                    elif (self.unknown_estimates[unk_id] - self.unknown_estimates[unk_id]*0.01) > self.tau:
                        self.unknown_alive[unk_id] = False  # Give em the stabbo


if __name__ == '__main__':
    # Basic testing code for each different scenario. Mainly used for debugging development purposes.
    # See test_simulator for a better example use-case for this code.
    for s in (1, 2, 3):
        print("Testing scenario {}".format(s))
        sim = Simulator(s, 0.2)
        combatants, warfighters, civs, num_combat, num_warfighters, num_civ = sim.run()
        print("Stats on this round:")
        print("\tWarfighters: Killed {} out of {}".format(warfighters, sim.num_humans))
        print("\tCombatants:  Killed {} out of {}".format(combatants, num_combat))
        print("\tCivilians:   Killed {} out of {}".format(civs, num_civ))

    print("Testing bad scenario number 0")
    try:
        sim = Simulator(0, 0.2)
    except ValueError as e:
        print("Caught:", e)

    print("Testing bad tau:")
    try:
        sim = Simulator(1, -1)
    except ValueError as e:
        print("Caught:", e)
    try:
        sim = Simulator(1, 10)
    except ValueError as e:
        print("Caught:", e)

    print("test rendering")
    sim = Simulator(3, 0.8, True, output_img_dir='images/')
    combatants, warfighters, civs, num_combat, num_warfighters, num_civ = sim.run()
