from app.database import API

class SDRcontroller():
    def __init__(self, controller):
        self.controller = controller
        self.current_bcch_list = []
        return
        
def strongest_bcch_channel(bcch_list=[]):
    if len(bcch_list) == 0:
        return None
    strongest_bcch = bcch_list.pop(0)
    for channel in bcch_list:
        if strongest_bcch[1] + strongest_bcch[2]/3 < channel[1] + channel[2]/3:
            strongest_bcch = channel

    return strongest_bcch[0]

def sort_bcch_channels(bcch_list = []):
    if len(bcch_list) == 0:
        return None
    
    return sorted(bcch_list, key=priority, reverse=True)

def priority(tupple):
    channel, pwr, number_msg = tupple
    return pwr + number_msg/3
