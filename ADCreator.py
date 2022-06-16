import uuid
import random
from neo4j import GraphDatabase
from faker import Faker
import time
import math

def cn(name,domain):
    return f"{name}@{domain}"

def cs(relative_id,base_sid):
    return f"{base_sid}-{str(relative_id)}"

def cws(security_id,domain):
    return f"{domain}-{str(security_id)}"

def generate_timestamp():
    current_time = int(time.time())
    choice = random.randint(-1, 1)
    if choice == 1:
        variation = random.randint(0, 31536000)
        return current_time - variation
    elif choice == 0:
        return 'Never'
    else:
        return current_time

def generate_permission(driver,users,computers):
    with driver.session() as session:
        count = int(math.floor(len(computers) * .1))
        props = []
        for i in range(0, count):
            comp = random.choice(computers)
            user = random.choice(users)
            props.append({'a': user, 'b': comp})

        session.run(
            'UNWIND $props AS prop MERGE (n:User {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:CanRDP]->(m)', props=props)

        props = []
        for i in range(0, count):
            comp = random.choice(computers)
            user = random.choice(users)
            props.append({'a': user, 'b': comp})

        session.run(
            'UNWIND $props AS prop MERGE (n:User {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:ExecuteDCOM]->(m)', props=props)

        props = []
        for i in range(0, count):
            comp = random.choice(computers)
            user = random.choice(users)
            props.append({'a': user, 'b': comp})

        session.run(
            'UNWIND $props AS prop MERGE (n:User {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:AllowedToDelegate]->(m)', props=props)
        
        props = []
        for i in range(0, count):
            comp = random.choice(computers)
            user = random.choice(users)
            props.append({'a': user, 'b': comp})

        session.run(
            'UNWIND $props AS prop MERGE (n:User {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:ReadLAPSPassword]->(m)', props=props)


def generate_ACL(driver,ACE,source,target):
    with driver.session() as session:
        ace_string = '[r:' + ace + '{isacl:true}]'
        session.run(
        'MERGE (n:Group {name:$group}) MERGE (m {name:$principal}) MERGE (n)-' + ace_string + '->(m)', group=source, principal=target)

def do_cleardb():
    num = 1
    while num > 0:
        result = session.run(
            "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(n)")
        for r in result:
            num = int(r['count(n)'])

    print("Resetting Schema")
    for constraint in session.run("CALL db.constraints"):
        session.run("DROP {}".format(constraint['description']))
    
    icount = session.run(
        "CALL db.indexes() YIELD name RETURN count(*)")
    for r in icount:
        ic = int(r['count(*)'])
            
    while ic >0:
        print("Deleting indices from database")
    
        showall = session.run(
            "SHOW INDEXES")
        for record in showall:
            name = (record['name'])
            session.run("DROP INDEX {}".format(name))
        ic = 0

    print("DB Cleared and Schema Reset")


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
url = setting_dict['url']
username = setting_dict['username']
password = setting_dict['password']
domain = str(setting_dict['domain'])+".LOCAL"
base_sid = 'S-1-5-21-987213679-315867604-3049297612'
states =  [elt.strip() for elt in setting_dict['States'].split(',')]
country = setting_dict['Country']
level = setting_dict['Security_level'] 
driver = GraphDatabase.driver(url, auth=(username,password))
num_users = int(setting_dict['num_users'])
num_pcs = int(setting_dict['num_PCs'])

with driver.session() as session:
    do_cleardb()
    session.run("MERGE (n:Base {name: $gname}) SET n:Domain, n.objectid=$sid",
            gname=domain, sid=base_sid)
    print("Populating Standard Nodes")
    base_statement = "MERGE (n:Base {name: $gname}) SET n:Group, n.objectid=$sid"
    session.run(f"{base_statement},n.highvalue=true",
                sid=cs(512,base_sid), gname=cn("DOMAIN ADMINS",domain))
    session.run(f"{base_statement},n.highvalue=true",
                gname=cn("DOMAIN CONTROLLERS",domain), sid=cs(516,base_sid))
    session.run(base_statement, gname=cn(
        "ENTERPRISE DOMAIN CONTROLLERS",domain), sid=cws("S-1-5-9",domain))
    session.run(f"{base_statement},n.highvalue=true",
                gname=cn("ADMINISTRATORS",domain), sid=cs(544,base_sid))
    session.run(f"{base_statement},n.highvalue=true",
                gname=cn("ENTERPRISE ADMINS",domain), sid=cs(519,base_sid))
    session.run(f"{base_statement},n.highvalue=true",
                gname=cn("PRINT OPERATORS",domain), sid=cs(550,base_sid))
    session.run(f"{base_statement},n.highvalue=true",
                gname=cn("ACCOUNT OPERATORS",domain), sid=cs(548,base_sid))
    session.run(f"{base_statement},n.highvalue=true",
                gname=cn("SERVER OPERATORS",domain), sid=cs(549,base_sid))
    session.run(base_statement, sid=cs(515,base_sid), gname=cn("DOMAIN COMPUTERS",domain))
    session.run(base_statement, gname=cn("DOMAIN USERS",domain), sid=cs(513,base_sid))



    session.run(
        "MERGE (n:Base {name:$domain}) SET n:Domain, n.highvalue=true", domain=domain)
    ddp = str(uuid.uuid4())
    ddcp = str(uuid.uuid4())
    dcou = str(uuid.uuid4())
    base_statement = "MERGE (n:Base {name:$gpo, objectid:$guid}) SET n:GPO"
    session.run(base_statement, gpo=cn("DEFAULT DOMAIN POLICY",domain), guid=ddp)
    session.run(base_statement, gpo=cn(
        "DEFAULT DOMAIN CONTROLLERS POLICY",domain), guid=ddcp)
    session.run("MERGE (n:Base {name:$ou, objectid:$guid, blocksInheritance: false}) SET n:OU", ou=cn(
        "DOMAIN CONTROLLERS",domain), guid=dcou)

    print("Adding Standard Edges")

    # Default GPOs
    gpo_name = cn("DEFAULT DOMAIN POLICY",domain)
    session.run(
        'MERGE (n:GPO {name:$gpo}) MERGE (m:Domain {name:$domain}) MERGE (n)-[:GpLink {isacl:false, enforced:toBoolean(false)}]->(m)', gpo=gpo_name, domain=domain)
    session.run(
        'MERGE (n:Domain {name:$domain}) MERGE (m:OU {objectid:$guid}) MERGE (n)-[:Contains {isacl:false}]->(m)', domain=domain, guid=dcou)
    gpo_name = cn("DEFAULT DOMAIN CONTROLLERS POLICY",domain)
    OU_name =  cn("DOMAIN CONTROLLERS",domain)
    session.run(
        'MERGE (n:GPO {name:$gpo}) MERGE (m:OU {name:$OU}) MERGE (n)-[:GpLink {isacl:false, enforced:toBoolean(false)}]->(m)', gpo=gpo_name, OU=OU_name)

    ADGroup_name = cn("ADMINISTRATORS",domain)
    # Administrators -> DCSync Rights
    session.run(
        'MERGE (n:Domain {name:$domain}) MERGE (m:Group {name:$gname}) MERGE (m)-[:Owns {isacl:true}]->(n)', domain=domain, gname=ADGroup_name)
    session.run(
        'MERGE (n:Domain {name:$domain}) MERGE (m:Group {name:$gname}) MERGE (m)-[:GetChanges]->(n)', domain=domain, gname=ADGroup_name)
    session.run(
        'MERGE (n:Domain {name:$domain}) MERGE (m:Group {name:$gname}) MERGE (m)-[:GetChangesAll]->(n)', domain=domain, gname=ADGroup_name)
    # Administrators -> High Value Targets
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ENTERPRISE ADMINS",domain), gname=ADGroup_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("DOMAIN ADMINS",domain), gname=ADGroup_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("DOMAIN CONTROLLERS",domain), gname=ADGroup_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("SERVER OPERATORS",domain), gname=ADGroup_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ACCOUNT OPERATORS",domain), gname=ADGroup_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("BACKUP OPERATORS",domain), gname=ADGroup_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("PRINT OPERATORS",domain), gname=ADGroup_name)



    # Ent Admins -> High Value Targets
    group_name = cn("ENTERPRISE ADMINS",domain)
    session.run(
        'MERGE (n:Domain {name:$domain}) MERGE (m:Group {name:$gname}) MERGE (m)-[:GenericAll {isacl:true}]->(n)', domain=domain, gname=group_name)
    session.run(
        'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$ADgname}) WITH n,m MERGE (n)-[:MemberOf]->(m)',ADgname = ADGroup_name,  gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ADMINISTRATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("BACKUP OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("PRINT OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("SERVER OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("DOMAIN ADMINS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ACCOUNT OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("DOMAIN CONTROLLERS",domain), gname=group_name)


    # Domain Admins -> High Value Targets
    group_name = cn("DOMAIN ADMINS",domain)
    session.run(
        'MERGE (n:Domain {name:$domain}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:AllExtendedRights {isacl:true}]->(n)', domain=domain, gname=group_name)
    session.run(
        'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$ADgname}) WITH n,m MERGE (n)-[:MemberOf]->(m)',ADgname = ADGroup_name,  gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:Owns {isacl:true}]->(n)', nname=cn("ADMINISTRATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("PRINT OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("BACKUP OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:Owns {isacl:true}]->(n)', nname=cn("ACCOUNT OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("SERVER OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("DOMAIN CONTROLLERS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:Owns {isacl:true}]->(n)', nname=cn("ENTERPRISE ADMINS",domain), gname=group_name)

        # ENTERPRISE ADMINS -> High Value Targets
    group_name = cn("ENTERPRISE ADMINS",domain)
    session.run(
        'MERGE (n:Domain {name:$domain}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericAll {isacl:true}]->(n)', domain=domain, gname=group_name)
    session.run(
        'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$ADgname}) WITH n,m MERGE (n)-[:MemberOf]->(m)',ADgname = ADGroup_name,  gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ADMINISTRATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("PRINT OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("BACKUP OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ACCOUNT OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("SERVER OPERATORS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("DOMAIN ADMINS",domain), gname=group_name)
    session.run(
        'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ENTERPRISE ADMINS",domain), gname=group_name)





    # DC Groups -> Domain Node
    group_name = cn("ENTERPRISE DOMAIN CONTROLLERS",domain)
    session.run(
        'MERGE (n:Domain {name:$domain}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GetChanges]->(n)', domain=domain, gname=group_name)
    group_name = cn("DOMAIN CONTROLLERS",domain)
    session.run(
        'MERGE (n:Domain {name:$domain}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GetChangesAll]->(n)', domain=domain, gname=group_name)



    print("Creating Tierd OUs")
    # Creating root OUs
    base_statement = "MERGE (n:Base {name: $uname}) SET n:OU, n.objectid=$guid"
    OU_names = ['Admin','Groups','Quarantine','Workstations','Tire 1 servers','User Accounts']
    for name in OU_names:
        session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(name,domain))
        session.run( 'MERGE (n:OU {name:$uname}) WITH n MERGE (m:Domain {name:$domain}) WITH n,m MERGE (m)-[:Contains]->(n)', uname=cn(name,domain), domain=domain)

    # Tierd OUs
    Tierd_OU = {'Tier 0':['T0_Accounts','T0_Devices','T0_Groups','T0_Service Accounts'],
                'Tier 1':['T1_Accounts','T1_Devices','T1_Groups','T1_Service Accounts'],
                'Tier 2':['T2_Accounts','T2_Devices','T2_Groups','T2_Service Accounts']}
    for key in Tierd_OU.keys():
        session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(key,domain))
        session.run(
            'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn('Admin',domain), gname=cn(key,domain))
        for sub in Tierd_OU[key]:
            session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(sub,domain))
            session.run(
                'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn(key,domain), gname=cn(sub,domain))

    # Groups OU
    sub_group =['Distribution Groups','Security Groups']
    for name in sub_group:
        session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(name,domain))
        session.run(
            'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn('Groups',domain), gname=cn(name,domain))


    # Workstations OU
    for name in states:
        session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(name,domain))
        session.run(
            'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn('Workstations',domain), gname=cn(name,domain))

    # User Accounts OU
    session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn('Enabled Users',domain))
    session.run(
            'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn('User Accounts',domain), gname=cn('Enabled Users',domain))
    session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn('Disabled Users',domain))
    session.run(
            'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn('User Accounts',domain), gname=cn('Disabled Users',domain))


    # T1 services
    sub_service = ['Application','Print','Database','Exchange','Remote Desktop']
    for name in sub_service:
        session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(name,domain))
        session.run(
            'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn('Tire 1 servers',domain), gname=cn(name,domain))

    print("Creating GPOs")
    #Creating GPOs for the root OUs
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('Restrict Server Logon',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('Restrict Server Logon',domain), uname=cn('Tire 1 servers',domain)) 
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('Restrict Workstation Logon',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('Restrict Workstation Logon',domain), uname=cn('Workstations',domain)) 
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('New_PC Configuration',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('New_PC Configuration',domain), uname=cn('Quarantine',domain)) 
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('Admins Configuration',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('Admins Configuration',domain), uname=cn('Admin',domain)) 
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('Normal_Users Configuration',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('Normal_Users Configuration',domain), uname=cn('User Accounts',domain)) 
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('Group Configuration',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('Normal_Users Configuration',domain), uname=cn('Groups',domain)) 
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('PAW Configuration',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('PAW Configuration',domain), uname=cn('T0_Devices',domain)) 
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('PAW Outbound restrictions',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('PAW Outbound restrictions',domain), uname=cn('T0_Devices',domain)) 
    session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn('RestrictedAdmin Required -Computer',domain), guid=str(uuid.uuid4()))
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('RestrictedAdmin Required -Computer',domain), uname=cn('T1_Devices',domain)) 
    session.run(
            "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn('RestrictedAdmin Required -Computer',domain), uname=cn('T2_Devices',domain)) 

    query = session.run("MATCH (n:OU) WHERE not((:GPO)-[:GpLink]->(n))RETURN n.name") .data()
    unlink_OU = [list(i.values())[0] for i in query]
    GPO_names = ["Network_Restriction_", "Data_Access_Restriction_", "System_Restriction_","Software_Restriction_"]
    for i in range(random.randint(10,30)):
        gpo_name = cn(random.choice(GPO_names)+str(i),domain)
        guid = str(uuid.uuid4())
        session.run(
                "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=gpo_name, guid=guid)
        session.run(
                "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=gpo_name, gname=random.choice(unlink_OU))
   
 
    ridcount = 1000
    print("Generating User Nodes")
    props = []
    users = []
    disable_users = []
    enable = [True]*98 + [False]*2
    fake = Faker([country])
    for i in range(0, num_users):
        user_name = "{}@{}".format(
            fake.unique.name(), domain).upper()
        enabled = random.choice(enable)
        if enabled == True:
            users.append(user_name)
        else:
            disable_users.append(user_name)
        pwdlastset = generate_timestamp()
        lastlogon = generate_timestamp()
        objectsid = cs(ridcount,base_sid)
        ridcount += 1
        props.append({'id': objectsid, 'props': {
            'name': user_name,
            'enabled': enabled,
            'pwdlastset': pwdlastset,
            'lastlogon': lastlogon,
            'domain': domain,
        }})
        if (len(props) > 500):
            session.run(
                'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:User, n += prop.props WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=cn("DOMAIN USERS",domain))
            props = []
    session.run(
        'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:User, n += prop.props WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=cn("DOMAIN USERS",domain))

    
    admin = random.sample(users,int(num_users*0.1))
    normal_users = [i for i in users if i not in admin]

    # Adminstrator account
    base_statement = "MERGE (n:Base {name: $uname}) SET n:User,n.objectid=$sid"
    session.run(f"{base_statement}",sid=cs(500,base_sid), uname=cn("ADMINSTRATOR",domain))
    session.run(  
            'MERGE (n:User {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=cn("ADMINSTRATOR",domain), gname=cn("DOMAIN ADMINS",domain))
    session.run(
            'MERGE (n:User {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=cn("ADMINSTRATOR",domain), gname=cn("ADMINISTRATORS",domain))
    session.run(
            'MERGE (n:User {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=cn("ADMINSTRATOR",domain), gname=cn("ENTERPRISE ADMINS",domain))
    session.run(
            'MERGE (n:User {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=cn("ADMINSTRATOR",domain), gname=cn("DOMAIN USERS",domain))


    #Assign Tiered admins Users
    Tiered_OU = [cn('T0_Accounts',domain)]*25 + [cn('T1_Accounts',domain)]*35 + [cn('T2_Accounts',domain)]*40
    T0_gropup = [cn("PRINT OPERATORS",domain),cn("ACCOUNT OPERATORS",domain),cn("SERVER OPERATORS",domain),cn("DOMAIN ADMINS",domain)]
    T1_gropup = [cn("T1 Admins",domain),cn("T1 PAW maintenances",domain),cn("T1 service Accounts",domain),cn("T1 Management",domain)]
    T2_gropup = [cn("T2 Admins",domain),cn("T2 PAW maintenances",domain),cn("T2 service Accounts",domain),cn("T2 Management",domain)]
    for group_name in T1_gropup + T2_gropup:
        props =[]
        sid = cs(ridcount,base_sid)
        ridcount += 1
        props.append({'name': group_name, 'id': sid})
        session.run(
            'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Group, n.name=prop.name', props=props)
    
    T0_users =[]
    T1_users =[]
    T2_users =[]
    for user in admin:
        OU_name = random.choice(Tiered_OU)
        if OU_name == cn('T0_Accounts',domain):
            T0_users.append(user)
            if random.choice([1]*85+[0]*15):
                session.run(
                'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=OU_name)
                session.run(
                'MERGE (n:User {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=user, gname= random.choice(T0_gropup))
            else:
                session.run(
                'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=cn("T0_Service Accounts",domain))
        if OU_name == cn('T1_Accounts',domain):
            T1_users.append(user)
            temp_name = random.choice(T1_gropup)
            session.run(
            'MERGE (n:User {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=user, gname= temp_name)
            if temp_name == cn("T1 service Accounts",domain):
                session.run(
                'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=cn('T1_Service Accounts',domain))
            else:
                session.run(
                'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=OU_name)
        if OU_name == cn('T2_Accounts',domain):
            T2_users.append(user)
            temp_name = random.choice(T2_gropup)
            session.run(
            'MERGE (n:User {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=user, gname= temp_name)
            if temp_name == cn("T2 service Accounts",domain):
                session.run(
                'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=cn('T2_Service Accounts',domain))
            else:
                session.run(
                'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=OU_name)

    
    #Place disable users and normal users
    for user in normal_users:
        session.run(
            'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=cn('Enabled Users',domain))
    for user in disable_users:
        session.run(
            'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=cn('Disabled Users',domain))
    
 
    #Place groups
    for group in T0_gropup:
        session.run(
            'MERGE (n:Group {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=group, gname=cn('T0_Groups',domain))
    for group in T1_gropup:
        session.run(
            'MERGE (n:Group {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=group, gname=cn('T1_Groups',domain))
    for group in T2_gropup:
        session.run(
            'MERGE (n:Group {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=group, gname=cn('T2_Groups',domain))


    
    print("Creating Domain Controllers")
    num_controllers = 2
    used_states = []
    for i in range(num_controllers):
        use_state = random.choice(list(set(states) - set(used_states)))
        comp_name = cn(f"DC"+str(i+1)+"-"+str(use_state),domain)
        group_name = cn("DOMAIN CONTROLLERS",domain)
        sid = cs(ridcount,domain)
        session.run(
            'MERGE (n:Base {objectid:$sid}) SET n:Computer,n.name=$name,n.domain=$domain WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', sid=sid,domain = domain, name=comp_name, gname=group_name)
        session.run(
            'MATCH (n:Computer {objectid:$sid}) WITH n MATCH (m:OU {name:$uname}) WITH n,m MERGE (m)-[:Contains]->(n)', sid=sid, uname= cn("DOMAIN CONTROLLERS",domain) )
        session.run(
            'MATCH (n:Computer {objectid:$sid}) WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', sid=sid, gname=cn("ENTERPRISE DOMAIN CONTROLLERS",domain))
        session.run(
            'MERGE (n:Computer {objectid:$sid}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:AdminTo]->(n)', sid=sid, gname=cn("DOMAIN ADMINS",domain))
        session.run(
            'MERGE (n:Computer {objectid:$sid}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:AdminTo]->(n)', sid=sid, gname=cn("ENTERPRISE ADMINS",domain))
        session.run(
            'MERGE (n:Computer {objectid:$sid}) WITH n MERGE (m:User {name:$gname}) WITH n,m MERGE (m)-[:AdminTo]->(n)', sid=sid, gname=cn("ADMINISTRATOR",domain))

        used_states.append(use_state)
        if used_states == states:
            used_states = []
        ridcount += 1

    print("Generating Computer Nodes")
    PC_list = ['PAW']*10+['Server']*10 + ['Workstation']*80
    PAW = []
    Server = []
    Workingstation =[]
    props =[]
    for i in range(0, num_pcs):
        Delegatable_weight = ["False"] * 85 + ["True"] * 15
        PC_type = random.choices(PC_list)[0]
        if PC_type == 'PAW':
            comp_name = str('PAW')+"-{:05d}@{}".format(len(PAW), domain)
            PAW.append(comp_name)
        elif PC_type == 'Server':
            comp_name = str('S')+"-{:05d}@{}".format(len(Server), domain)
            Server.append(comp_name)
        else:
            comp_name = str('WS')+"-{:05d}@{}".format(len(Workingstation), domain)
            Workingstation.append(comp_name)
        enabled = True
        Delegatable = random.choice(Delegatable_weight)
        props.append({'id': cs(ridcount,base_sid), 'props': {
            'name': comp_name,
            'type': PC_type,
            'Allows Unconstrained Delegation': Delegatable,
            'domain': domain,
            'enabled': enabled,
        }})
        ridcount += 1
        if (len(props) > 500):
            session.run(
                'UNWIND $props as prop MERGE (n:Base {objectid: prop.id}) SET n:Computer, n += prop.props WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=cn("DOMAIN COMPUTERS",domain))
            props = []
    session.run(
        'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Computer, n += prop.props WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=cn("DOMAIN COMPUTERS",domain))

    #Place PAW
    Tier_name =['T0_','T1_','T2_']
    T0_PAW =[]
    T1_PAW=[]
    T2_PAW =[]
    for pc in PAW:
        i = random.choice(Tier_name)
        session.run(
            'MERGE (n:Computer {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=pc, gname=cn(i+'Devices',domain))
        if i == 'T0_':
            T0_PAW.append(pc)
        elif i == 'T1_':
            T1_PAW.append(pc)
        else:
            T2_PAW.append(pc)
    #Place T1server
    query = session.run('MATCH(n:OU {name:$uname})-[:Contains]->(o:OU) RETURN o.name',uname = cn('Tire 1 servers',domain)).data()
    Server_sub = [list(i.values())[0] for i in query]
    for pc in Server:
        session.run(
            'MERGE (n:Computer {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=pc, gname=random.choice(Server_sub))
    #Place workstations
    query = session.run('MATCH(n:OU {name:$uname})-[:Contains]->(o:OU) RETURN o.name',uname = cn('Workstations',domain)).data()
    WS_sub = [list(i.values())[0] for i in query]
    for pc in Workingstation:
        session.run(
            'MERGE (n:Computer {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=pc, gname=random.choice(WS_sub))

    
    print("Generating Groups")
    
    # depart = ["IT"] * 10 + ["HR"] * 10 + ["MARKETING"] * 20 + ["ACCOUNTING"] * 20 + ["PRODUCTION"] * 25 + ['R&D']*15
    depart = ['IT','HR','MARKETING','ACCOUNTING','PRODUCTION','R&D']
    props =[]
    # Distribution Groups
    for i in depart:
        group_name = cn(i+'_'+'dist', domain)
        sid = cs(ridcount,base_sid)
        ridcount += 1
        props.append({'name': group_name, 'id': sid})
        session.run('UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Group, n.name=prop.name', props=props)      
        for j in states:
            sub_dist = cn(i+'_'+j, domain)
            sid = cs(ridcount,base_sid)
            ridcount += 1
            props.append({'name': sub_dist, 'id': sid})
            session.run(
                'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Group, n.name=prop.name', props=props)
            session.run(
                'MERGE (n:Group {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=group_name, gname=cn('Distribution Groups',domain))
            session.run(
                'MERGE (n:Group {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:MemberOf]->(n)', gname=sub_dist, name=group_name)


    
    # Security Groups
    ACL = ['Read','Modify','Write','Full']
    folder_name = ['Folder_' + str(i) for i in range(1,6) ]
    for i in depart:
        group_name = cn(i+'_'+'sec', domain)
        sid = cs(ridcount,base_sid)
        ridcount += 1
        props.append({'name': group_name, 'id': sid})
        session.run(
            'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Group, n.name=prop.name', props=props)
        for l in ACL:
            for n in range(random.randint(0, 5)):
                sub_sec = cn(i+'_'+folder_name[n]+'_'+l, domain)
                sid = cs(ridcount,base_sid)
                ridcount += 1
                props.append({'name': sub_sec, 'id': sid})
                session.run(
                    'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Group, n.name=prop.name', props=props)
                session.run(
                    'MERGE (n:Group {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=group_name, gname=cn('Security Groups',domain))
                session.run(
                    'MERGE (n:Group {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:MemberOf]->(n)', gname=sub_sec, name=group_name)


    print("Adding users to Groups")
    for user in normal_users:
        dept = random.choice(depart)
        session.run('MATCH (n:User {name:$name}) SET n.department = $dept_name', name=user, dept_name = dept)
        query = session.run('MATCH(n:Group)-[:MemberOf]->(o:Group{name:$uname}) RETURN n.name',uname = cn(dept+'_'+'dist', domain)).data()
        dist_group = [list(i.values())[0] for i in query]
        possible_dist = random.choices(dist_group)
        query = session.run('MATCH(n:Group)-[:Contains]->(o:Group{name:$uname}) RETURN n.name',uname = cn(dept+'_'+'sec', domain)).data()
        sec_group = [list(i.values())[0] for i in query]
        possible_groups = possible_dist + random.sample(sec_group,random.randint(0, len(sec_group)))
        for group in possible_groups:
            props =[]
            props.append({'a': user, 'b': group})
            session.run(
                'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Group {name:prop.b}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props)
    
    print("Generating permissions")
    #ACCOUNT OPERATORS can modfify accounts of most groups 
    all_groups = session.run("""MATCH (n:Group) WHERE not(n.name CONTAINS "ADMINISTRATORS") AND (n.name CONTAINS $domain_name) AND not((n)-[:MemberOf]->(:Group{name:$gname}))
                                        RETURN n.name""",domain_name = domain,gname=cn("ADMINISTRATORS",domain))  
    for temp in all_groups:
        session.run(
        'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$mname}) WITH n,m MERGE (n)-[:GenericAll {isacl:true}]->(m)', gname=cn("ACCOUNT OPERATORS",domain), mname=temp["n.name"])
    
    # Print Operators and Server Operators can log into domain controllers

    query = session.run("""MATCH (n:User) -[:MemberOf]->(:Group{name:$gname})
                                        RETURN n.name""",gname = cn("SERVER OPERATORS",domain)).data() 
    s_Operators = [list(i.values())[0] for i in query]
    query = session.run("""MATCH (n:User) -[:MemberOf]->(:Group{name:$gname})
                                        RETURN n.name""",gname = cn("PRINT OPERATORS",domain))  
    p_Operators = [list(i.values())[0] for i in query]
    query = session.run("MATCH (n:Computer)-[:MemberOf]->(:Group{name:$gname}) RETURN n.name",gname = cn("DOMAIN CONTROLLERS",domain)).data()
    DCs =  [list(i.values())[0] for i in query]
    for OP in s_Operators+p_Operators:
        for DC in DCs:
            if random.choice([True, False]):
                session.run('MERGE (n:User {name:$uname}) WITH n MERGE (m:Computer {name:$cname}) WITH n,m MERGE (m)-[:HasSession]->(n)', uname=OP,cname = DC)
    
    query = session.run("""MATCH (n:User) -[:MemberOf]->(:Group{name:$gname})
                                        RETURN n.name""",gname = cn("SERVER OPERATORS",domain)).data() 

    print("Adding sessions")
    #tiered logon
    max_sessions_per_user = int(math.ceil(math.log10(num_users)))
    props = []
    for user in normal_users:
        num_sessions = random.randrange(0, max_sessions_per_user)
        if num_sessions == 0:
            continue

        for c in random.sample(Workingstation, num_sessions):
            props.append({'a': user, 'b': c})

        if (len(props) > 500):
            session.run(
                'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)
            props = []

    session.run(
        'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)

    for user in T1_users:
        num_sessions = random.randrange(0, max_sessions_per_user)
        if num_sessions == 0:
            continue

        for c in random.sample(Server, num_sessions):
            props.append({'a': user, 'b': c})

        if (len(props) > 500):
            session.run(
                'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)
            props = []

    session.run(
        'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)

    #PAW logon
    T_users = [T0_users,T1_users,T2_users]
    T_PAW = [T0_PAW,T1_PAW,T2_PAW]
    for i in range(3):
        props = []
        for user in T_users[i]:
            num_sessions = random.randrange(0, max_sessions_per_user)
            if num_sessions == 0:
                continue

            for c in random.sample(T_PAW[i], num_sessions):
                props.append({'a': user, 'b': c})

            if (len(props) > 500):
                session.run(
                    'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)
                props = []

        session.run(
            'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)
    
    if level == 'Medium':
        #create cross tier log on
        for user in random.sample(normal_users,20):
            num_sessions = random.randrange(0, max_sessions_per_user)
            if num_sessions == 0:
                continue
            for c in random.sample(Server+T_PAW, num_sessions):
                props.append({'a': user, 'b': c})

                if (len(props) > 500):
                    session.run(
                    'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)
                    props = []

            session.run(
            'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)

        for user in random.sample(T1_users,20):
            num_sessions = random.randrange(0, max_sessions_per_user)
            if num_sessions == 0:
                continue
            for c in random.sample(T0_PAW, num_sessions):
                props.append({'a': user, 'b': c})

                if (len(props) > 500):
                    session.run(
                    'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)
                    props = []

            session.run(
            'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)

        for user in random.sample(T0_users,20):
            num_sessions = random.randrange(0, max_sessions_per_user)
            if num_sessions == 0:
                continue
            for c in random.sample(Workingstation, num_sessions):
                props.append({'a': user, 'b': c})

                if (len(props) > 500):
                    session.run(
                    'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)
                    props = []

            session.run(
            'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)

    print("Gneerateing ACEs")
    #T0 users can has permissions to any level
    generate_permission(driver,T0_users,PAW+Server+Workingstation)
    #T1 users can has permissions to level1 and 2
    generate_permission(driver,T1_users,T1_PAW+T2_PAW+Server+Workingstation)
    #T2 users can has permissions to level2 
    generate_permission(driver,T2_users,T2_PAW+Workingstation)

    acl_list = ["AllExtendedRights"]*3+["GenericAll"]*40+["GenericWrite"]*20+["Owns"]*10+["WriteDACL"]*10+["WriteOwner"]*10+["AddMember"]*7
    T0_principals = T0_users + T0_gropup + T1_users +T1_gropup + T2_users +T2_gropup
    T1_principals = T1_users +T1_gropup + T2_users +T2_gropup +dist_group +sec_group
    T2_principals = T2_users +T2_gropup + dist_group +sec_group

    for i in T1_gropup:
        for j in range(random.randint(1, int(len(T1_principals)*0.5))):
            ace = random.choice(acl_list)
            if ace == "AddMember":
                p = random.choice(T1_gropup + T2_users +T2_gropup +dist_group +sec_group)
            else:
                p = random.choice(T1_principals)
            generate_ACL(driver,ace,i,p)
    
    for i in T2_gropup:
        for j in range(random.randint(1, int(len(T1_principals)*0.5))):
            ace = random.choice(acl_list)
            if ace == "AddMember":
                p = random.choice(T2_users +T2_gropup + dist_group +sec_group)
            else:
                p = random.choice(T2_principals)
            generate_ACL(driver,ace,i,p)
    
    for i in T0_users:
        for j in range(random.randint(1, int(len(T0_principals)*0.5))):
            p = random.choice(T0_principals)
            ace_string = '[r:' + ace + '{isacl:true}]'
            session.run(
            'MERGE (n:User {name:$group}) MERGE (m {name:$principal}) MERGE (n)-' + ace_string + '->(m)', group=i, principal=p)

    

    print("Adding Admin rights")
    session.run(
            'MATCH (n:Computer) MATCH (m:Group {name:$gname}) MERGE (m)-[:AdminTo]->(n)', gname=cn("DOMAIN ADMINS",domain))
    for pc in T1_PAW:
        session.run(
            'MERGE (n:Group {name:$gname}) MERGE (m:Computer {name:$pname}) MERGE (n)-[:AdminTo]->(m)', gname=cn("T1 Admins",domain),pname = pc)
    for pc in T2_PAW:
        session.run(
            'MERGE (n:Group {name:$gname}) MERGE (m:Computer {name:$pname}) MERGE (n)-[:AdminTo]->(m)', gname=cn("T2 Admins",domain),pname = pc)
            

    print("Adding Domain Admin ACEs")
    group_name = cn("DOMAIN ADMINS",domain)
    props = []
    query = session.run('MATCH (n:Group) WHERE (n.name CONTAINS $domain_name)RETURN n.name',domain_name = domain).data()
    groups = [list(i.values())[0] for i in query]
    query = session.run('MATCH (n:Computer) WHERE (n.name CONTAINS $domain_name)RETURN n.name',domain_name = domain).data()
    computers = [list(i.values())[0] for i in query]
    query = session.run('MATCH (n:User) WHERE (n.name CONTAINS $domain_name)RETURN n.name',domain_name = domain).data()
    users = [list(i.values())[0] for i in query]
    query = session.run('MATCH (n:GPO) WHERE (n.name CONTAINS $domain_name)RETURN n.name',domain_name = domain).data()
    all_GPOs = [list(i.values())[0] for i in query]
    for x in computers:
        props.append({'name': x})
        if len(props) > 500:
            session.run(
                'UNWIND $props as prop MATCH (n:Computer {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:GenericAll {isacl:true}]->(n)', props=props, gname=group_name)
            props = []

    session.run(
        'UNWIND $props as prop MATCH (n:Computer {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:GenericAll {isacl:true}]->(n)', props=props, gname=group_name)
    
    for x in all_GPOs:
        props.append({'name': x})
        if len(props) > 500:
            session.run(
                'UNWIND $props as prop MATCH (n:GPO {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:Owns {isacl:true}]->(n)', props=props, gname=group_name)
            props = []

    session.run(
        'UNWIND $props as prop MATCH (n:GPO {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:Owns {isacl:true}]->(n)', props=props, gname=group_name)


    props = []
    for x in users:
        props.append({'name': x})

        if len(props) > 500:
            session.run(
                'UNWIND $props as prop MATCH (n:User {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:GenericAll {isacl:true}]->(n)', props=props, gname=group_name)
            props = []

    session.run(
        'UNWIND $props as prop MATCH (n:User {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:GenericAll {isacl:true}]->(n)', props=props, gname=group_name)

    for x in groups:
        props.append({'name': x})

        if len(props) > 500:
            session.run(
                'UNWIND $props as prop MATCH (n:Group {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:GenericAll {isacl:true}]->(n)', props=props, gname=group_name)
            props = []

    session.run(
        'UNWIND $props as prop MATCH (n:Group {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:GenericAll {isacl:true}]->(n)', props=props, gname=group_name)

    print("Marking some users as Kerberoastable")
    i = random.randint(10, 20)
    i = min(i, len(normal_users))
    for user in random.sample(normal_users, i):
        session.run(
            'MATCH (n:User {name:$user}) SET n.hasspn=true', user=user)

    session.run('MATCH (n:User) SET n.owned=false')
    session.run('MATCH (n:Computer) SET n.owned=false')
    session.run('MATCH (n) WHERE n.domain IS NULL SET n.domain=$domain', domain=domain)

    session.close()
    print("Database Generation Finished!")




    
    
    
