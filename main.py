class Load_settings:
    def __init__(self):
        file = open("AD_settings.txt", 'r')
        self.whole_settings = file.read().split('\n\n')
        base_dict = {}
        for line in self.whole_settings[0].split('\n'):
            if '=' in line:
                k, v = line.strip().split('=')
                base_dict[k.strip()] = v.strip()
        self.setting = base_dict
    def change(self, i):
        temp ={}
        for line in self.whole_settings[i].split('\n'):
            if '=' in line:
                k, v = line.strip().split('=')
                temp[k.strip()] = v.strip()
        self.setting = temp


AD_settings = Load_settings()
setting_dict = AD_settings.setting

if __name__ == '__main__':
    if setting_dict[Security_level] == 'Low':
         exec(open("ADCreator.py").read())
    else:
         exec(open("ADCreatorLow.py").read())






