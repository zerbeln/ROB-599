ROB599: Philosophy and Ethics of Robotics, HW1
Written by: Geoff Hollinger, 1/17/18
Updated: 1/15/20

The file simulator.m provides a simulator for military operations scenarios.

The testSimulator.m runs 100 trials of the simulator given parameters:

scenario,tau,displayOn

After running, it displays averages of: warfighters killed, civilians killed, 
combatants killed. 

The scenario parameter can take on three values: 

1 = peacekeeping, few combatants
2 = peacekeeping, guerilla forces
3 = active war zone, few civilians, many combatants

Tau = uncertainty threshold for lethal action (between 0 and 1)

displayOn = 1, display GUI
displayOn = 0, display off

%The colors of various agents are displayed as such in the simulator:

c_sensor = [0,1,0]; %green, sensor asset
c_lethal = [0.49,0.18,0.56]; %purple, lethal asset
c_human = [0,0,1]; %blue, human warfighter (on your team)
c_unknown = [0,0,0]; %black, unknown (not on your team, civilian or enemy)
c_enemy = [1,0,0]; % red, enemy as determined by tau

Note: a civilian will turn from black to red when it is positively identified as a combatant (certainty above tau). A civilian will remain black regardless of how certain we are it is a civilian. The sensor vehicles and lethal vehicles know the locations of all vehicles/warfighters and the locations/certainty of all combatants/civilians at all times.

The lethal vehicle will disable a combatant if its certainty is above tau and it is with range 10 (currently fixed).

A combatant will disable a human warfighter if it is within range 10.

You will need to program the sensor model and behaviors for the lethal assets and the sensor assets as described in HW1.pdf to protect your human warfighters.
