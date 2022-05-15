import random
from Generate_standard_nodes import AD_settings

settings = AD_settings.setting
country_dict = {'US':[ 'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
           'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME',
           'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM',
           'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
           'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY'], 'Canada':['AB','BC','MB','NB','NL',
           'NS','NT','NU','ON','PE','QC','SK','YT'],'Australia':['NSW','QLD','SA','TAS',
           'VIC' ,'WA' ,'ACT','NT'],'UK':['ENG','SCT','NIR','WLS'],'France':['ARA','BFC',
           'BRE','CVL','COR','GES','HDF','IDF','NOR','NAQ','OCC','PDL','PAC'],'Germany':['BW',
            'BY','BE','BB','HB','HH','HE','NI','MV','NW','RP','SL','SN','ST','SH','TH']}
PC_dict = {'Laptop':'LT','Printer':'PTR','Server':'S','Virtual_Machine':'VM'}
list_department = ['HR','SALES','MANAGEMENT','R&D','MARKTING','ACCOUNTING','SERVICE','PRODUCTION','ADVERTISING',
               'SECURITY','FIANCE'] 
list_acl = ['GenericAll' , 'GenericWrite', 'WriteOwner', 'WriteDacl', 'AddMember', 'ForceChangePassword', 
            'ReadLAPSPassword','Owns','AllExtendedRights','ReadGMSAPassword']

def random_percent(split_size):
    size = 100
    percent =[]
    for i in range(split_size-1,0,-1):
        s = random.randint(5, size-  5 * i)
        percent.append(str(s))
        size -= s
    percent.append(str(size))
    return percent

last_sid = random.randint(1000000000,9999999999)
sid = 'S-1-5-21-' + str(random.randint(100000000,999999999))+'-'+str(random.randint(100000000,999999999))

class random_settings():
    def __init__(self):
        self.model = random.choice(['Single','Multiple'])
        self.Security_level = random.choice(['High','Medium','Low'])
        self.country = random.choice(list(country_dict.keys()))
        self.num_states = random.randint(1,len(country_dict[self.country]))
        self.States = random.sample(country_dict[self.country],self.num_states)
        self.num_domain_controllers = random.randint(1,self.num_states)
        self.num_PCs = random.randint(500,2000)
        self.PC_types = ['Workstation']+random.sample(list(PC_dict.keys()), random.randint(0,len(list(PC_dict.keys()))))
        self.PC_short = ['WS'] + [PC_dict[key] for key in self.PC_types[1:]]
        self.num_users = random.randint(int(self.num_PCs*0.5),self.num_PCs)
        self.num_groups = random.randint(self.num_users,self.num_users*3)
        self.PC_percent = random_percent(len(self.PC_types))
        self.department = ['IT']+random.sample(list_department, random.randint(3,len(list_department)))
        self.department_percent = random_percent(len(self.department))
        self.acl_list = random.sample(list_acl, random.randint(5,len(list_acl)))
        self.acl_percent  = random_percent(len(self.acl_list))
        self.sid = sid+'-'+str(last_sid)
    def change_sid(self,last_num):
        self.sid = str(sid) +'-'+str(last_num)
    def change_country(self,country):
        self.country = country
        self.num_states = random.randint(1,len(country_dict[self.country]))
        self.States = random.sample(country_dict[self.country],self.num_states)

num_child_domain = random.randint(2,4)
Users_can_login_overseas_computers = random.choice(['Y','N'])

file = open("AD_settings.txt", "w")
print("Generating random AD settings")
rand = random_settings()
if rand.model == 'Single':
    file.write("url =" + settings['url']+ "\n"
            "username = " + settings['username']+ "\n"
            "password = " + settings['password']+ "\n"
            "model = " + rand.model+ "\n"
            "Security_level = " + rand.Security_level+ "\n"+
            "domain = " + settings['domain']+ "\n"+
            "base_sid = " + rand.sid +"\n"+
            "Country = " + rand.country+ "\n"+
                "States = " + ','.join(rand.States)+ "\n"+
                "num_domain_controllers = " + str(rand.num_domain_controllers)+ "\n"+
                "num_PCs = " + str(rand.num_PCs)+ "\n"+
                "PC_types = " + ','.join(rand.PC_types)+ "\n"+
                "PC_short = " + ','.join(rand.PC_short)+ "\n"+
                "PC_percent = " + ','.join(rand.PC_percent)+ "\n"+
                "num_users = " + str(rand.num_users) + "\n"+
                "num_groups = " + str(rand.num_groups) + "\n"+
                "department = " + ','.join(rand.department)+ "\n"+
                "department_percent = " +','.join(rand.department_percent) + "\n"+
                "acl_list = " +','.join(rand.acl_list) + "\n"+
                "acl_percent ="+','.join(rand.acl_percent) + "\n"
    )
    file.close()
else:
    file.write("url =" + settings['url']+ "\n"
                "username = " + settings['username']+ "\n"
                "password = " + settings['password']+ "\n"
                "model = " + rand.model+ "\n"
                "domain = " + settings['domain']+ "\n"+
                "base_sid = " + rand.sid +"\n"+
                "num_child_domain =" + str(num_child_domain)+ "\n"+
                "Users_can_ login_overseas_computers ="+ Users_can_login_overseas_computers+ "\n"
)
    countries = random.sample(list(country_dict.keys()),num_child_domain)
    for i in range(num_child_domain):
        rand = random_settings()
        last_sid = last_sid+1
        rand.change_sid(last_sid)
        rand.change_country(countries[i])
        file.write("\n"+str(i+1)+" child domain:"+ "\n"
           "Security_level = " + rand.Security_level+ "\n"+
           "base_sid = " + rand.sid +"\n"+
           "Country = " + rand.country+ "\n"+
            "States = " + ','.join(rand.States)+ "\n"+
            "num_domain_controllers = " + str(rand.num_domain_controllers)+ "\n"+
            "num_PCs = " + str(rand.num_PCs)+ "\n"+
            "PC_types = " + ','.join(rand.PC_types)+ "\n"+
            "PC_short = " + ','.join(rand.PC_short)+ "\n"+
            "PC_percent = " + ','.join(rand.PC_percent)+ "\n"+
            "num_users = " + str(rand.num_users) + "\n"+
            "num_groups = " + str(rand.num_groups) + "\n"+
            "department = " + ','.join(rand.department)+ "\n"+
            "department_percent = " +','.join(rand.department_percent) + "\n"+
            "acl_list = " +','.join(rand.acl_list) + "\n"+
            "acl_percent ="+','.join(rand.acl_percent) + "\n"
        )
    file.close()
    

