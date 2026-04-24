# Windrose Dedicated Server settings

## Content
- [Hardware requirements](#hardware-requirements)
- [Easy Start](#easy-start)
- [Server Settings](#server-settings)
  - [ServerDescription.json](#serverdescriptionjson)
  - [WorldDescription.json](#worlddescriptionjson)


## Hardware requirements
### 2 players
- CPU: Intel Xeon Scalable (Sapphire Rapids), 2 cores, 3.2 GHz
- RAM: 8 GB
- Storage: 35 GB SSD
### 4 players
- CPU: Intel Xeon Scalable (Sapphire Rapids), 2 cores, 3.2 GHz
- RAM: 12 GB
- Storage: 35 GB SSD
### 10 players
- CPU: Intel Xeon Scalable (Sapphire Rapids), 2 cores, 3.2 GHz
- RAM: 16 GB
- Storage: 35 GB SSD

## Easy Start
If you just want a simple way to start the server on your PC, here are some quick instructions:

1. Start the Windrose Dedicated Server on your platform of choice or via StartServerForeground.bat.
2. You will see a console window appear on your screen.
3. Once it finishes loading, you should see an invite code that looks something like this: `f1014dc1`
4. If you cannot find it (sometimes the console messages disappear too quickly), do not worry. Go to the folder where you installed the Windrose Dedicated Server, then open the `R5` folder. Inside the `R5` folder, you will find the `ServerDescription.json` file. Open it with any text editor (simple Notepad will do). Inside this file, look for the invite code. It will look something like this: `f1014dc1`
5. Now you can launch the game itself. Go to **Play → Connect to Server →** paste the invite code there. You should now be able to see the server and connect to it.
6. Send the invite code to your friends, and they should be able to connect to the server as well (**Play → Connect to Server →** paste the invite code).
7. Yarr!

If you want to change your server settings or need more technical details, please look below:

## Server Settings
We split server settings into 2 separate .json files. The first one is ServerDescription.json for common server settings. There can be only one such file regardless of the number of worlds. The file is located in root folder of the application. The second one is WorldDescription.json. There is one file of this type per world.

Server creates default version of ServerDescription.json and makes first World with WorldDescription.json on initial start, so it is recommended to start and stop the server so the files are created and then work with them.

### ServerDescription.json
This is a single file in the root folder of the application.

List of fields:

1. PersistentServerId - unique ID of your server. Do not edit it. **_It will be changed in upcoming builds_**
2. InviteCode - invite code to find your server. 0-9, a-z and A-Z symbols are allowed. Should contain at least 6 symbols. Case sensitive.
3. IsPasswordProtected - specify if password is required. Should be true if password specified and false if password field is empty. Otherwise it may cause unexpected behavior.
4. Password - this is the password.
5. ServerName - name of your server. Helpful if invite codes look similar
6. WorldIslandId - ID of currently selected world. It should be the same as a similar field in one of WorldDescription.json file of the server. This world will be loaded on start of the server.
7. MaxPlayerCount - maximum number of simultaneous players on your server.
8. UserSelectedRegion - specifies the region for the Connection Service. Supported options: SEA, CIS, EU (EU covers both EU & NA). If left empty, the server will automatically detect and select the optimal region based on latency. If desired region is specified (for example, EU), the server will use that region exclusively.
9. P2pProxyAddress - IP Address for listening sockets.
10. UseDirectConnection - if true, the server will create sockets for direct connection with clients. If false, the server will use ICE protocol to establish P2P connection.
11. DirectConnectionServerAddress - address for direct connection. For future purposes. Not used now.
12. DirectConnectionServerPort - port for direct connection. Should be available for TCP and UDP connection if UseDirectConnection is true.
13. DirectConnectionProxyAddress - сan be used to choose specified network on computer where server with direct connection is running. 0.0.0.0 should be used by default.

This file can be changed manually only when the server is shut down. Any field might be automatically changed by the server in case of any issue.

Example:
```json
{
        "Version": 1,
        "DeploymentId": "0.10.0.0.251-master-9f800c33",
        "ServerDescription_Persistent":
        {
                "PersistentServerId": "1B80182E460F727CEA080C8EEBB1EA0A",
                "InviteCode": "d6221bb7",
                "IsPasswordProtected": false,
                "Password": "",
                "ServerName": "",
                "WorldIslandId": "DB57768A8A7746899683D0EEE91F97BF",
                "MaxPlayerCount": 4,
                "UserSelectedRegion": "EU",
                "P2pProxyAddress": "192.168.31.49",
                "UseDirectConnection": false,
        "DirectConnectionServerAddress ": "",
                "DirectConnectionServerPort": 7777,
        "DirectConnectionProxyAddress": "0.0.0.0"
        }
}
```


### WorldDescription.json
You can create as many worlds as you need on your server. All worlds are located in a folder

`<root folder>/R5/Saved/SaveProfiles/Default/RocksDB/<game version>/Worlds/<world document id>/WorldDescription.json`

First one is created automatically on start of a server.

Pay attention that the WorldIslandId must be the same as a similar field in WorldSettings.json located in this folder.

List of fields:

1. IslandId - unique ID of the world. Must be the same as folder name where the file is located.
2. WorldName - Name of the world.
3. CreationTime - time of creation in internal format.
4. WorldPresetType - gameplay difficulty preset. You can use these values: "Easy", "Medium", "Hard". If any custom values present in "WorldSettings", the preset will be forcefully set to "Custom" on next server launch.
5. WorldSettings - world parameters grouped by types: bool, float and tag. Should be empty for all preserts except "Custom"

List of available world parameters for custom preset. Please note it might be easier to set up the custom server preset in the game and then copy them to a dedicated server file manually: **_Parameters list and their values/ranges might be changed in upcoming builds_**
1. CoopQuests: If any player on the server completes a quest marked as a co-op quest, it auto-completes for all players who currently have it active; Default: true;
2. EasyExplore: When this option is set true it disables markers on the map that highlight points of interest making them harder to find; Default: false; The "EasyExplore" is the legacy name, in-game it is called "Immersive exploration" and in fact, it makes exploration harder.
3. MobHealthMultiplier: Defines how much Health enemies have; Default: 1.0; Range: [0.2; 5.0];
4. MobDamageMultiplier: Defines how hard enemies hit; Default: 1.0; Range: [0.2; 5.0];
5. ShipHealthMultiplier: Defines how much Ship Health enemy ships have; Default: 1.0; Range: [0.4; 5.0];
6. ShipDamageMultiplier: Defines how much Damage enemy ships deal; Default: 1.0; Range: [0.2; 2.5];
7. BoardingDifficultyMultiplier: Defines how many enemy sailors must be defeated to win a boarding action; Default: 1.0; Range: [0.2; 5.0];
8. Coop_StatsCorrectionModifier: Adjusts enemy Health and how fast enemies lose Posture based on the number of players on the server; Default: 1.0; Range: [0.0; 2.0];
9. Coop_ShipStatsCorrectionModifier: Adjusts enemy Ship Health based on the number of players on the server; Default: 0.0; Range: [0.0; 2.0];
10. CombatDifficulty: Defines how difficult are boss encounters and how aggressive are enemies in general; Default: {"TagName": "WDS.Parameter.CombatDifficulty.Normal"}; Range: {TagName="WDS.Parameter.CombatDifficulty.Easy"},{TagName="WDS.Parameter.CombatDifficulty.Normal"},{TagName="WDS.Parameter.CombatDifficulty.Hard"} ;

Example "WorldPresetType": "Medium":
```json
{
    "Version": 1,
    "WorldDescription":
    {
        "islandId": "E24A22C9C8D3448951AFD002162576D5",
        "WorldName": "The Archipelago",
        "CreationTime": 6.3910902400911002e+17,
        "WorldPresetType": "Medium",
        "WorldSettings":
        {
            "BoolParameters":
            {
                "{\"TagName\": \"WDS.Parameter.Coop.SharedQuests\"}": true,
                "{\"TagName\": \"WDS.Parameter.EasyExplore\"}": false
            },
            "FloatParameters":
            {
                "{\"TagName\": \"WDS.Parameter.MobHealthMultiplier\"}": 1,
                "{\"TagName\": \"WDS.Parameter.MobDamageMultiplier\"}": 1,
                "{\"TagName\": \"WDS.Parameter.ShipsHealthMultiplier\"}": 1,
                "{\"TagName\": \"WDS.Parameter.ShipsDamageMultiplier\"}": 1,
                "{\"TagName\": \"WDS.Parameter.BoardingDifficultyMultiplier\"}": 1,
                "{\"TagName\": \"WDS.Parameter.Coop.StatsCorrectionModifier\"}": 1,
                "{\"TagName\": \"WDS.Parameter.Coop.ShipStatsCorrectionModifier\"}": 0
            },
            "TagParameters":
            {
                "{\"TagName\": \"WDS.Parameter.CombatDifficulty\"}":
                {
                    "TagName": "WDS.Parameter.CombatDifficulty.Normal"
                }
            }
        }
    }
}
```

Example "WorldPresetType": "Easy":
```json
{
    "Version": 1,
    "WorldDescription":
    {
        "islandId": "26C14DC8A78D4AF69E9C77527C934CF3",
        "WorldName": "The Archipelago",
        "CreationTime": 6.3911887576664998e+17,
        "WorldPresetType": "Easy",
        "WorldSettings":
        {
            "BoolParameters":
            {
                "{\"TagName\": \"WDS.Parameter.Coop.SharedQuests\"}": true,
                "{\"TagName\": \"WDS.Parameter.EasyExplore\"}": false
            },
            "FloatParameters":
            {
                "{\"TagName\": \"WDS.Parameter.MobHealthMultiplier\"}": 0.7,
                "{\"TagName\": \"WDS.Parameter.MobDamageMultiplier\"}": 0.6,
                "{\"TagName\": \"WDS.Parameter.ShipsHealthMultiplier\"}": 0.7,
                "{\"TagName\": \"WDS.Parameter.ShipsDamageMultiplier\"}": 0.6,
                "{\"TagName\": \"WDS.Parameter.BoardingDifficultyMultiplier\"}": 0.7,
                "{\"TagName\": \"WDS.Parameter.Coop.StatsCorrectionModifier\"}": 1,
                "{\"TagName\": \"WDS.Parameter.Coop.ShipStatsCorrectionModifier\"}": 0
            },
            "TagParameters":
            {
                "{\"TagName\": \"WDS.Parameter.CombatDifficulty\"}":
                {
                    "TagName": "WDS.Parameter.CombatDifficulty.Easy"
                }
            }
        }
    }
}
```

Example "WorldPresetType": "Hard":
```json
{
    "Version": 1,
    "WorldDescription":
    {
        "islandId": "26C14DC8A78D4AF69E9C77527C934CF3",
        "WorldName": "The Archipelago",
        "CreationTime": 6.3911887576664998e+17,
        "WorldPresetType": "Hard",
        "WorldSettings":
        {
            "BoolParameters":
            {
                "{\"TagName\": \"WDS.Parameter.Coop.SharedQuests\"}": true,
                "{\"TagName\": \"WDS.Parameter.EasyExplore\"}": false
            },
            "FloatParameters":
            {
                "{\"TagName\": \"WDS.Parameter.MobHealthMultiplier\"}": 1.5,
                "{\"TagName\": \"WDS.Parameter.MobDamageMultiplier\"}": 1.25,
                "{\"TagName\": \"WDS.Parameter.ShipsHealthMultiplier\"}": 1.5,
                "{\"TagName\": \"WDS.Parameter.ShipsDamageMultiplier\"}": 1.25,
                "{\"TagName\": \"WDS.Parameter.BoardingDifficultyMultiplier\"}": 1.5,
                "{\"TagName\": \"WDS.Parameter.Coop.StatsCorrectionModifier\"}": 1,
                "{\"TagName\": \"WDS.Parameter.Coop.ShipStatsCorrectionModifier\"}": 0
            },
            "TagParameters":
            {
                "{\"TagName\": \"WDS.Parameter.CombatDifficulty\"}":
                {
                    "TagName": "WDS.Parameter.CombatDifficulty.Hard"
                }
            }
        }
    }
}
```
