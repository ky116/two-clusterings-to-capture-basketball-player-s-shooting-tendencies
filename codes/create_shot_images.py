#%%
import os
import scipy.io as sio
import pandas as pd
import numpy as np
import cv2
from PIL import Image, ImageOps
import imageio
#%%
hundred_milliseconds_before_shot = 30
#%%
nba_allevent_attack = pd.read_csv("../meta_data/nba_allevent_attack.csv")
nba_datalength = pd.read_csv("../meta_data/nba_datalength.csv")
id_player_positions = pd.read_csv("../meta_data/id_player_positions.csv")
id_team = pd.read_csv("../meta_data/id_team.csv")
#%%
nba_allevent_attack_id_player = pd.merge(nba_allevent_attack, id_player_positions, on="player_id", how="left")
nba_allevent_attack_id_player
#%%
nba_allevent_attack_id_player_team = pd.merge(nba_allevent_attack_id_player, id_team, on="team_id", how="left")
nba_allevent_attack_id_player_team
#%%
metadata_allgame = pd.merge(nba_allevent_attack_id_player_team, nba_datalength, on=['game_id', 'event_id'], how="right")
#%%
data_allgames = [sio.loadmat(f"../team_representation_data/nba_attack2/data/attackDataset_game{i:03d}.mat") for i in range(1, 631)]
#%%
target_flag_list = []
for i in range(630):
    target_flag = metadata_allgame[metadata_allgame["game_x"] == i+1][["shot_x","datalength"]]
    target_flag_list.append(target_flag)
#%%
ring_coordinate = np.array([1.575, 7.62])
#%%
target_event_list = []
for i in range(630):
    for e in range(len(target_flag_list[i])):
        flag = target_flag_list[i].iloc[e]
        if i == 31:
            e += 1
        if (flag["shot_x"] > 1) and (flag["datalength"] >= hundred_milliseconds_before_shot):
            target_event = data_allgames[i]["data"][0][e]
            last_attacker = target_event[-1][69]
            shooter_id = target_event[-1][47+int(last_attacker)]
            if i == 31 and e == 93:
                e -= 1
            target_metadata = metadata_allgame[metadata_allgame["game_x"] == i+1].iloc[e]
            event_time = list(range(int(target_metadata["start"]), int(target_metadata["end"]), -1))
            if e != 0:
                if event_time[0] in previous_event_time:
                    continue
            x_meter, y_meter = target_event[-1][2*int(last_attacker)-2], target_event[-1][2*int(last_attacker)-1]
            shooter_coordinate = np.array([x_meter, y_meter])
            shot_distance = np.linalg.norm(ring_coordinate - shooter_coordinate)
            if (target_metadata["shot_x"] == 2 and shot_distance < 7.5) or (target_metadata["shot_x"] == 3 and shot_distance > 6.5):
                if shooter_id == target_metadata["player_id"]:
                    target_data = {"eventdata":target_event, "metadata":target_metadata}
                    target_event_list.append(target_data)
                    previous_event_time = event_time
#%%
int(target_event_list[0]["metadata"]["shot_x"])
#%%
last_attacker_list = []
for event in target_event_list:
    last_attacker_list.append(event["eventdata"][-1][69])
#%%
court = Image.open('../images/halfcourt.png')
court_ = court.resize((564,600))
# if court_.mode == 'RGBA':
#     court_ = court_.convert('RGB')
# court_ = ImageOps.invert(court_)
court_
#%%
output_dir = '../images/shot_images'
#%%
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

shot_images = []
for i in range(len(target_event_list)):
    eventdata = target_event_list[i]["eventdata"]
    metadata = target_event_list[i]["metadata"]

    data_justbefore_shot = eventdata[-hundred_milliseconds_before_shot:]
    last_attacker = eventdata[-1][69]
    shooter_trajectory = []
    shooter_ball_hold = []
    for data_t in data_justbefore_shot:
        x_meter, y_meter = data_t[2*int(last_attacker)-2], data_t[2*int(last_attacker)-1]
        x_feet, y_feet = x_meter/0.3048, y_meter/0.3048
        x_inch, y_inch = x_feet*12, y_feet*12
        shooter_coordinate = (x_inch, y_inch)
        shooter_trajectory.append(shooter_coordinate)
        if data_t[69] == last_attacker:
            shooter_ball_holding = data_t[68]
        else:
            shooter_ball_holding = 0
        shooter_ball_hold.append(shooter_ball_holding)

    shot_image = np.array(court_)

    shooter_color_alpha = 15
    shooter_ball_holding_color_alpha = 15
    shooter_trajectory = np.int32(shooter_trajectory)
    for t in range(len(shooter_trajectory)-1):
        start = shooter_trajectory[t]
        end = shooter_trajectory[t+1]
        if shooter_ball_hold[t] == 1:
            shot_image = cv2.line(shot_image, start, end, (shooter_ball_holding_color_alpha, 0, 0), thickness=5)
        else:
            shot_image = cv2.line(shot_image, start, end, (0, 0, shooter_color_alpha), thickness=5)
        shooter_color_alpha += 8
        shooter_ball_holding_color_alpha += 8

    n_game = str(int(metadata["game_x"])).zfill(3)
    event_id = str(metadata["event_id"]).zfill(3)
    if n_game == "002" and event_id == "165":
        print(len(eventdata)-1)
        break
    team = metadata["team_2"]
    position = metadata["position"]
    if position == "C":
        position = "C "
    shooter_name = metadata["player_name"]

    shot_image = cv2.cvtColor(shot_image, cv2.COLOR_BGR2RGB)

    cv2.imwrite(output_dir + '/game' + n_game + '_eventid' + event_id + '_' + str(int(target_event_list[i]["metadata"]["shot_x"])) + "P_" + team + "_" + position + "_" + shooter_name + '.png', shot_image)

    shot_images.append(shot_image)
# %%
# shot_images = []

# for i in range(len(target_event_list)):
#     eventdata = target_event_list[i]["eventdata"]
#     metadata = target_event_list[i]["metadata"]

#     data_justbefore_shot = eventdata[-hundred_milliseconds_before_shot:]
#     last_attacker = eventdata[-1][69]
#     shooter_trajectory = []
#     shooter_ball_hold = []
    
#     # Loop to generate an image for each time step.
#     for data_t in data_justbefore_shot:
#         x_meter, y_meter = data_t[2*int(last_attacker)-2], data_t[2*int(last_attacker)-1]
#         x_feet, y_feet = x_meter / 0.3048, y_meter / 0.3048
#         x_inch, y_inch = x_feet * 12, y_feet * 12
#         shooter_coordinate = (x_inch, y_inch)
#         shooter_trajectory.append(shooter_coordinate)
#         if data_t[69] == last_attacker:
#             shooter_ball_holding = data_t[68]
#         else:
#             shooter_ball_holding = 0
#         shooter_ball_hold.append(shooter_ball_holding)
        
#         # Initialisation of images
#         shot_image = np.array(court_).copy()
        
#         # Initialisation of color alpha values
#         shooter_color_alpha = 255
#         shooter_ball_holding_color_alpha = 255
        
#         # Drawing the trajectory of the shooter
#         shooter_trajectory_int = np.int32(shooter_trajectory)
#         for t in range(len(shooter_trajectory_int) - 1):
#             start = shooter_trajectory_int[t]
#             end = shooter_trajectory_int[t + 1]
#             if shooter_ball_hold[t] == 1:
#                 shot_image = cv2.line(shot_image, start, end, (0, 0, shooter_ball_holding_color_alpha), thickness=5)
#             else:
#                 shot_image = cv2.line(shot_image, start, end, (shooter_color_alpha, 0, 0), thickness=5)
        
#         shot_image = cv2.cvtColor(shot_image, cv2.COLOR_BGR2RGB)
#         shot_images.append(shot_image)
    
#     n_game = str(int(metadata["game_x"])).zfill(3)
#     event_id = str(metadata["event_id"]).zfill(3)
#     team = metadata["team_2"]
#     position = metadata["position"]
#     if position == "C":
#         position = "C "
#     shooter_name = metadata["player_name"]
    
#     # Save individual shot GIFs.
#     gif_path = 'output_dir + /game' + n_game + '_eventid' + event_id + '_' + team + "_" + position + "_" + shooter_name + '.gif'
#     imageio.mimsave(gif_path, shot_images, fps=10)  # 10 frames per second

#     # Clear the shot_images list
#     shot_images.clear()
# %%
