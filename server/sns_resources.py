import json
import random

user_addr_table = {}
player_func_table = {}

class baseFaction():
    def __init__(self):
        self.hull_HP = 70
        self.max_hull_HP = 70
        self.armory_HP = 25
        self.max_armory_HP = 25
        self.boarding_station_HP = 25
        self.max_boarding_station_HP = 25

        self.ship_action_dice_sides = {
            "Repair"    : 6,
            "Ram"       : 6,
            "Loot"      : 6,
            "Invade"    : 6 
        }

    def damage_hull(self,dmg):
        self.hull_HP = max(min(self.hull_HP - dmg,self.max_hull_HP),0)

    def damage_armory(self,dmg):
        self.armory_HP = max(min(self.armory_HP - dmg,self.max_armory_HP),0)

    def damage_boarding_station(self,dmg):
        self.boarding_station_HP = max(min(self.boarding_station_HP - dmg,self.max_boarding_station_HP),0)
    
    def get_fresh(self,available_actions,action_history):
        available_actions = available_actions if available_actions else self.get_available_actions()
        fresh = list(available_actions)
        for action in fresh:
            for round in action_history:
                if action in round:
                    fresh.remove(action)
        return fresh
    def stale_recurse(self,available_actions,action_history,i = -1):
        stale = []
        available_actions = available_actions if available_actions else self.get_available_actions()
        if len(action_history) >= i: return []
        for action in available_actions:
            if action in action_history[i]:
                stale.append(action)
        return stale + self.stale_recurse(stale, action_history, i = i - 1)
        

    def stale_penal(self,n):
        return (n > 0) * (-1 -  n)
    
    def fresh_bonus(self,round):
        return [0,1,1,3,3][round]
    
class sns_game():
    codenum = 0
    valid_code_symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    game_list = []
    code_digits = 4
    @classmethod
    def get_code(cls):
        l = cls.get_code_list()
        s = ""
        while (not s or s in l):
            for i in range(0,cls.code_digits):
                s = cls.valid_code_symbols[cls.codenum // len(cls.valid_code_symbols)**i % len(cls.valid_code_symbols)] + s
            cls.codenum = (cls.codenum + 1) % (len(cls.valid_code_symbols)**cls.code_digits)
        return s
    
    def get_code_list(cls):
        return [game.code for game in cls.game_list]

    def __init__(self,settings=None):
        self.set_settings(settings)
        self.code = sns_game.getCode()
        self.info = {
            "players": {"Unassigned": [], "Team1": [], "Team2": [] },
            "modifications": {"Team1": [], "Team2": []},
            "action_history":[ # Round : [Actions...]
            ]
        }
        self.team1_faction = baseFaction()
        self.team2_faction = baseFaction()
    
    @property
    def players(self):
        pd = self.info["players"]
        return pd["Unassigned"] + pd["Team1"] + pd["Team2"]
    
    @property
    def round(self):
        return len(self.info["action_history"])

    def join(self,player):
        if self.player_connections >= 6 or player["name"] in list(user_addr_table.keys()):
            server_message(player,None,{"MessageType":"Join Response","Success":False})
            return False
        self.player_connections.append(player["name"])
        self.info["players"]["Unassigned"].append(player["name"])
        o = {"MessageType":"Join Response","Success":True}
        o.update(self.info["players"])
        server_message(player,None,o)
        self.room_update()
        return True
    
    def join_team(self,player,team):
        current = self.info["players"]
        if len(current[team]) >= 3 or player in current[team]: return False
        for group in list(current.keys()):
            current[group].remove(player)
        current[team].append(player)
        self.room_update()
        return True
    
    def room_message(self,message):
        for player in self.players:
            message(player,None,message)

    def room_update(self):
        o ={"MessageType":"Room Update"}
        o.update(self.info["players"])
        self.room_message(o)
    
    def game_start(self):
        o ={"MessageType":"Game Start"}
        self.room_message(o)

    def game_end(self):
        o ={"MessageType":"Game End"}
        self.room_message(o)

    def game_update(self,states):
        o = {"MessageType":"Game Update", "Game States":states}
        self.room_message(o)

    
    def set_settings(self,settings):
        pass #TODO: Implement

    
    @staticmethod
    def roll(sides):
        return int(random.random() * sides) + 4


def server_message(player,userfunc,message):
    f = userfunc | player_func_table[player]
    f(message)


def handle_client_tcp_message(data,userfunc):
    pass
    #{   "Connection":   lambda x: add_user_connection(x["Username"],userfunc,x["MessageBoard"]),
    #    "Message":      lambda x: handle_user_message(x["Username"],userfunc,x["MessageBoard"],x["Content"]),
    #    "Disconnect":   lambda x: end_user_connection(x["Username"],userfunc,x["MessageBoard"]) if x["MessageBoard"] else end_user_connection_all(x["Username"],userfunc),
    #    "Groups":       lambda x: userfunc(Message_Board.get_groups_message())
    #}[data["MessageType"]](data)