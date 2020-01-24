%ROB599: Philosophy and Ethics of Robotics, HW1
%Written by: Geoff Hollinger, 1/17/18
%Updated: 1/17/18

%simulator for military operations scenarios

%Scenario 1 = peacekeeping, few combatants
%Scenario 2 = peacekeeping, guerilla forces
%Scenario 3 = active war zone, few civilians, many combatants

%Tau = uncertainty threshold for lethal action (between 0 and 1)

%displayOn = 1, display GUI
%displayOn = 0, display off

%color of various agents
%c_enemy = [1,0,0]; % red, enemy as determined by tau
%c_sensor = [0,1,0]; %green, sensor asset
%c_lethal = [0.49,0.18,0.56]; %purple, lethal asset
%c_human = [0,0,1]; %blue, human warfighter
%c_unknown = [0,0,0]; %black, unknown (civilian or enemy)

function [totalWarfightersDisabled,totalCombatantsDisabled,totalCiviliansDisabled] = simulator(scenario,tau,displayOn)

world = initializeWorld(scenario);

%threshold for lethal action, should change based on answer to Problem 2,
%passed as argument to main function
world.tau = tau;

%end time of simulation, can leave at 50
endTime = 50;

for curTime = 1:endTime
    
    %update agent locations
    world = updateSensorLocations(world);
    world = updateLethalLocations(world);
    world = updateHumanLocations(world);
    world = updateUnknownLocations(world);
    
    %update estimate of combatant versus noncombatant
    world = updateCombatantEstimate(world);
    
    %update lethal actions (combatants against humans and lethal robots
    %against combatants)
    world = updateLethalActions(world);
    
    %draw the world if display is on
    if displayOn == 1
        drawWorld(world);
    end
end

%calculate statistics
numCombatantsKilled = 0;
numCiviliansKilled = 0;
numCombatants = 0;
numCivilians = 0;
for i = 1:world.numUnknown
    if world.unknown.combatant(i) == 2
        numCombatants = numCombatants + 1;
    else
        numCivilians = numCivilians + 1;
    end
    if world.unknown.alive(i) == 0
        if world.unknown.combatant(i) == 2
            numCombatantsKilled = numCombatantsKilled + 1;
        else
            numCiviliansKilled = numCiviliansKilled + 1;
        end
    end
end
numWarfightersKilled = 0;
for i = 1:world.numHumans
    if world.humans.alive(i) == 0
        numWarfightersKilled = numWarfightersKilled + 1;
    end
end

totalCombatantsDisabled = numCombatantsKilled;
totalWarfightersDisabled = numWarfightersKilled;
totalCiviliansDisabled = numCiviliansKilled;

end

function newWorld = updateCombatantEstimate(world)
    newWorld = world;
    %FILL IN WITH MODEL FROM PROBLEM 3a
    %SHOULD BE DIFFERENT FOR DIFFERENT SCENARIOS
    %Should use the simSensor() function below to generate positive and negative
    %measurements
    
    %YOUR CODE HERE
end

function newWorld = updateSensorLocations(world)
    newWorld = world;
    %FILL IN WITH ALGORITHM FROM PROBLEM 3c or 3d
    
    %YOUR CODE HERE
end

function newWorld = updateLethalLocations(world)
    newWorld = world;
    %FILL IN WITH ALGORITHM FROM PROBLEM 3c or 3d
    
    %YOUR CODE HERE
end

function newWorld = updateLethalActions(world)
    newWorld = world;

    %determines if human warfighters are disabled by combatants
    for i = 1:world.numHumans
        for j = 1:world.numUnknown
            if world.unknown.combatant(j) == 2 && world.unknown.alive(j) == 1
                distance = sqrt((world.unknown.xy(j,1)-world.humans.xy(i,1))^2 + (world.unknown.xy(j,2)-world.humans.xy(i,2))^2);
                if distance < world.lethalRad
                    newWorld.humans.alive(i) = 0;
                end
            end
        end
    end

    %determines if combatants are disabled by lethal assets
    %FILL IN WITH BEHAVIORIST ARCHITECTURE FROM PROBLEM 1

    %YOUR CODE HERE

end

%You should call this function from updateCombatantEstimate()
%j = index of civilian/combatant
%falsePositiveRate and falseNegativeRate are determiend and passed by you
%world = data structure passed from parent function
function measurement = simSensor(j,falsePositiveRate,falseNegativeRate,world)
    %simulate sensor measurement, returns 1 if measurement says combatant,
    %returns 0 if measurement says civilian
    
    x = rand();
    %it is actually a combatant
    if world.unknown.combatant(j) == 2
        %correct measurement
        if x > falseNegativeRate
            measurement = 1;
        %false negative
        else
            measurement = 0;
        end
    %it is actually a civilian
    else
        %correct measurement
        if x > falsePositiveRate
            measurement = 0;
        %false positive
        else
            measurement = 1;
        end
    end
end

%%YOU SHOULDN'T NEED TO MODIFY BELOW HERE
%%But important to read to understand how simulator is working

%update the locations of the uncontrolled human warfighters
function newWorld = updateHumanLocations(world)
    newWorld = world;
    %move towards goal
    for i = 1:world.numHumans
        if world.humans.alive(i) == 1           
            %generate new goal
            if (abs(world.humans.xy(i,1) - world.humans.goal(i,1))<2) && (abs(world.humans.xy(i,2) == world.humans.goal(i,2))<2)
                newWorld.humans.goal(i,:) = randi(world.xySize,1,2);
            end
            newWorld.humans.xy(i,1) = sign(newWorld.humans.goal(i,1) - world.humans.xy(i,1)) + world.humans.xy(i,1);
            newWorld.humans.xy(i,2) = sign(newWorld.humans.goal(i,2) - world.humans.xy(i,2)) + world.humans.xy(i,2);
        end
    end
end

%update the locations of the combatants and civilians
function newWorld = updateUnknownLocations(world)
    newWorld = world;
    for i = 1:world.numUnknown
        if world.unknown.alive(i) == 1
        if world.unknown.combatant(i) == 2
            %if combatant move towards human warfighter
            minDistance = world.xySize*world.xySize;
            closestWarfighter = -1;
            for j = 1:world.numHumans
                if world.humans.alive(i) == 1 
                    distance = sqrt((world.unknown.xy(i,1)-world.humans.xy(j,1))^2 + (world.unknown.xy(i,2)-world.humans.xy(j,2))^2);
                    if distance < minDistance
                        minDistance = distance;
                        closestWarfighter = j;
                    end
                end
            end
            if closestWarfighter > -1
                %move towards warfighter
                newWorld.unknown.xy(i,1) = sign(world.humans.xy(closestWarfighter,1) - world.unknown.xy(i,1)) + world.unknown.xy(i,1);
                newWorld.unknown.xy(i,2) = sign(world.humans.xy(closestWarfighter,2) - world.unknown.xy(i,2)) + world.unknown.xy(i,2);
            end
        else
            %if civilian, move towards goal or generate new goal if reached
            if (abs(world.unknown.xy(i,1) - world.unknown.goal(i,1))<2) && (abs(world.unknown.xy(i,2) == world.unknown.goal(i,2))<2)
                newWorld.unknown.goal(i,:) = randi(world.xySize,1,2);
            end
            newWorld.unknown.xy(i,1) = sign(newWorld.unknown.goal(i,1) - world.unknown.xy(i,1)) + world.unknown.xy(i,1);
            newWorld.unknown.xy(i,2) = sign(newWorld.unknown.goal(i,2) - world.unknown.xy(i,2)) + world.unknown.xy(i,2);    
        end
        end
    end
end

%draw the agents in the GUI
function newImage = drawAgent(x,y,color,oldImage)
    newImage = oldImage;
    newImage(x,y,:) = color;
end

%intialize the world based on the scenario
function world = initializeWorld(scenario)
%size of sides of simulator
world.xySize = 50;
%radius of lethality
world.lethalRad = 10;
%number of agents in each category
world.numSensors = 2;
world.numLethal = 2;
world.numHumans = 4;
world.numUnknown = 4;
%starting locations
world.sensors.xy(:,:) = randi(world.xySize,world.numSensors,2);
world.lethal.xy(:,:) = randi(world.xySize,world.numLethal,2);
world.humans.xy(:,:) = randi(world.xySize,world.numHumans,2);
%is this warfighter alive (1 yes, 0 no)
world.humans.alive = ones(world.numHumans);
world.humans.goal = randi(world.xySize,world.numHumans,2);
world.unknown.xy(:,:) = randi(world.xySize,world.numUnknown,2);
%start with 50% certainty of combatant, could adjust this based on scenario
%if you wanted to
world.unknown.estimate = ones(world.numUnknown,1)*0.5;
%percent combatant based on scenario
%2 = combatant, 1 = civilian
if scenario == 1
    %peacekeeping 10% combatants
    for i = 1:world.numUnknown
        x = rand();
        if x > 0.1
            world.unknown.combatant(i) = 1;
        else
            world.unknown.combatant(i) = 2;
        end
    end
elseif scenario == 2
    %guerilla forces, 30% combatants
    for i = 1:world.numUnknown
      x = rand();
      if x > 0.3
          world.unknown.combatant(i) = 1;
      else
          world.unknown.combatant(i) = 2;
      end
    end
elseif scenario == 3
    %active war zone, 80% combatants
      for i = 1:world.numUnknown
        x = rand();
        if x > 0.8
              world.unknown.combatant(i) = 1;
        else
              world.unknown.combatant(i) = 2;
        end
      end
else
    display('scenario not known');
    return;
end
%is this civilian alive (1 yes, 0 no)
world.unknown.alive = ones(world.numUnknown,1);
world.unknown.goal = randi(world.xySize,world.numUnknown,2);
end

%draw the world in the GUI
function drawWorld(world)
%color of various agents
c_enemy = [1,0,0]; % red, enemy as determined by tau
c_sensor = [0,1,0]; %green, sensor asset
c_lethal = [0.49,0.18,0.56]; %purple, lethal asset
c_human = [0,0,1]; %blue, human warfighter
c_unknown = [0,0,0]; %black, unknown (civilian or enemy)
%initialize image to white
curimage = ones(world.xySize,world.xySize,3);
%draw agents
for i = 1:world.numSensors
    curimage = drawAgent(world.sensors.xy(i,1),world.sensors.xy(i,2),c_sensor,curimage);
end
for i = 1:world.numLethal
    curimage = drawAgent(world.lethal.xy(i,1),world.lethal.xy(i,2),c_lethal,curimage);
end
for i = 1:world.numHumans
    if world.humans.alive(i) == 1
        curimage = drawAgent(world.humans.xy(i,1),world.humans.xy(i,2),c_human,curimage);
    end
end
for i = 1:world.numUnknown
    if world.unknown.alive(i) == 1
        if world.unknown.estimate(i) > world.tau
            curimage = drawAgent(world.unknown.xy(i,1),world.unknown.xy(i,2),c_enemy,curimage);
        else
            curimage = drawAgent(world.unknown.xy(i,1),world.unknown.xy(i,2),c_unknown,curimage);
        end
    end
end
%display current frame
imshow(curimage, 'InitialMagnification', 1000);
end



