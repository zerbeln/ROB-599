%ROB599: Philosophy and Ethics of Robotics, HW1
%Written by: Geoff Hollinger, 1/17/18
%Updated: 1/17/18

%test script to run multiple trials of military operations scenarios

function testSimulator(scenario,tau,displayOn)

for i = 1:100
    [warfightersKilled(i),combatantsKilled(i),civiliansKilled(i)] = simulator(scenario,tau,displayOn);
end
averageWarfightersKilled = mean(warfightersKilled)
averageCombatantsKilled = mean(combatantsKilled)
averageCiviliansKilled = mean(civiliansKilled)
end