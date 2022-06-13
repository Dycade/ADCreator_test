import uuid
import random
from neo4j import GraphDatabase
from faker import Faker
import time
import math
import itertools

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

def split_seq(iterable, size):
        it = iter(iterable)
        item = list(itertools.islice(it, size))
        while item:
            yield item
            item = list(itertools.islice(it, size))


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
states = setting_dict['States']
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


    print("Generating Computer Nodes")
    group_name = "DOMAIN COMPUTERS@{}".format(domain)
    props = []
    computers =[]
    ridcount = 1000
    for i in range(0,num_pcs):
        comp_name = "COMP{:05d}.{}".format(i, domain)
        computers.append(comp_name)
        enabled = True
        props.append({'id': cs(ridcount,base_sid), 'props': {
            'name': comp_name,
            'enabled': enabled,
        }})
        ridcount += 1

        if (len(props) > 500):
            session.run(
                'UNWIND $props as prop MERGE (n:Base {objectid: prop.id}) SET n:Computer, n += prop.props WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=group_name)
            props = []
    session.run(
        'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Computer, n += prop.props WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=group_name)

    print("Creating Domain Controllers")
    for state in random.sample(states,2):
        comp_name = cn(f"{state}LABDC",domain)
        group_name = cn("DOMAIN CONTROLLERS",domain)
        sid = cs(ridcount,base_sid)
        session.run(
            'MERGE (n:Base {objectid:$sid}) SET n:Computer,n.name=$name WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', sid=sid, name=comp_name, gname=group_name)
        session.run(
            'MATCH (n:Computer {objectid:$sid}) WITH n MATCH (m:OU {objectid:$dcou}) WITH n,m MERGE (m)-[:Contains]->(n)', sid=sid, dcou=dcou)
        session.run(
            'MATCH (n:Computer {objectid:$sid}) WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', sid=sid, gname=cn("ENTERPRISE DOMAIN CONTROLLERS",domain))
        session.run(
            'MERGE (n:Computer {objectid:$sid}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:AdminTo]->(n)', sid=sid, gname=cn("DOMAIN ADMINS",domain))


    print("Generating User Nodes")
    current_time = int(time.time())
    fake = Faker([country])
    group_name = "DOMAIN USERS@{}".format(domain)
    props = []
    users =[]
    for i in range(0, num_users):
        user_name = "{}@{}".format(
            fake.unique.name(), domain).upper()
        users.append(user_name)
        enabled = True
        pwdlastset = generate_timestamp()
        lastlogon = generate_timestamp()
        ridcount += 1
        objectsid = cs(ridcount,base_sid)

        props.append({'id': objectsid, 'props': {
            'name': user_name,
            'enabled': enabled,
            'pwdlastset': pwdlastset,
            'lastlogon': lastlogon
        }})
        if (len(props) > 500):
            session.run(
                'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:User, n += prop.props WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=group_name)
            props = []

    session.run(
        'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:User, n += prop.props WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=group_name)

    print("Generating Group Nodes")
    weighted_parts = ["IT"] * 7 + ["HR"] * 13 + \
        ["MARKETING"] * 30 + ["OPERATIONS"] * 20 + ["BIDNESS"] * 30
    props = []
    groups =[]
    for i in range(1,  num_users+ 1):
        dept = random.choice(weighted_parts)
        group_name = "{}{:05d}@{}".format(dept, i, domain)
        groups.append(group_name)
        sid = cs(ridcount,base_sid)
        ridcount += 1
        props.append({'name': group_name, 'id': sid})
        if len(props) > 500:
            session.run(
                'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Group, n.name=prop.name', props=props)
            props = []

    session.run(
        'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Group, n.name=prop.name', props=props)

    print("Adding Domain Admins to Local Admins of Computers")
    session.run(
        'MATCH (n:Computer) MATCH (m:Group {objectid: $id}) MERGE (m)-[:AdminTo]->(n)', id=cs(512,base_sid))

    dapctint = random.randint(3, 5)
    dapct = float(dapctint) / 100
    danum = int(math.ceil(num_users * dapct))
    danum = min([danum, 30])
    print("Creating {} Domain Admins ({}% of users capped at 30)".format(
        danum, dapctint))
    das = random.sample(users, danum)
    for da in das:
        session.run(
            'MERGE (n:User {name:$name}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=da, gname=cn("DOMAIN ADMINS",domain))

    print("Applying random group nesting")
    max_nest = int(round(math.log10(1000)))
    props = []
    for group in groups:
        if (random.randrange(0, 100) < 10):
            num_nest = random.randrange(1, max_nest)
            dept = group[0:-19]
            dpt_groups = [x for x in groups if dept in x]
            if num_nest > len(dpt_groups):
                num_nest = random.randrange(1, len(dpt_groups))
            to_nest = random.sample(dpt_groups, num_nest)
            for g in to_nest:
                if not g == group:
                    props.append({'a': group, 'b': g})

        if (len(props) > 500):
            session.run(
                'UNWIND $props AS prop MERGE (n:Group {name:prop.a}) WITH n,prop MERGE (m:Group {name:prop.b}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props)
            props = []

    session.run(
        'UNWIND $props AS prop MERGE (n:Group {name:prop.a}) WITH n,prop MERGE (m:Group {name:prop.b}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props)

    print("Adding users to groups")
    props = []
    a = math.log10(num_users)
    a = math.pow(a, 2)
    a = math.floor(a)
    a = int(a)
    num_groups_base = a
    variance = int(math.ceil(math.log10(num_users)))
    it_users = []

    print("Calculated {} groups per user with a variance of - {}".format(num_groups_base, variance*2))

    for user in users:
        dept = random.choice(weighted_parts)
        if dept == "IT":
            it_users.append(user)
        possible_groups = [x for x in groups if dept in x]

        sample = num_groups_base + random.randrange(-(variance*2), 0)
        if (sample > len(possible_groups)):
            sample = int(math.floor(float(len(possible_groups)) / 4))

        if (sample == 0):
            continue

        to_add = random.sample(possible_groups, sample)

        for group in to_add:
            props.append({'a': user, 'b': group})

        if len(props) > 500:
            session.run(
                'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Group {name:prop.b}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props)
            props = []

    session.run(
        'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Group {name:prop.b}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props)

    it_users = it_users + das
    it_users = list(set(it_users))

    print("Adding local admin rights")
    it_groups = [x for x in groups if "IT" in x]
    random.shuffle(it_groups)
    super_groups = random.sample(it_groups, 4)
    super_group_num = int(math.floor(len(computers) * .85))

    it_groups = [x for x in it_groups if not x in super_groups]

    total_it_groups = len(it_groups)

    dista = int(math.ceil(total_it_groups * .6))
    distb = int(math.ceil(total_it_groups * .3))
    distc = int(math.ceil(total_it_groups * .07))
    distd = int(math.ceil(total_it_groups * .03))

    distribution_list = [1] * dista + [2] * \
        distb + [10] * distc + [50] * distd

    props = []
    for x in range(0, total_it_groups):
        g = it_groups[x]
        dist = distribution_list[x]

        to_add = random.sample(computers, dist)
        for a in to_add:
            props.append({'a': g, 'b': a})

        if len(props) > 500:
            session.run(
                'UNWIND $props AS prop MERGE (n:Group {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (n)-[:AdminTo]->(m)', props=props)
            props = []

    for x in super_groups:
        for a in random.sample(computers, super_group_num):
            props.append({'a': x, 'b': a})

        if len(props) > 500:
            session.run(
                'UNWIND $props AS prop MERGE (n:Group {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (n)-[:AdminTo]->(m)', props=props)
            props = []

    session.run(
        'UNWIND $props AS prop MERGE (n:Group {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (n)-[:AdminTo]->(m)', props=props)

    print("Adding RDP/ExecuteDCOM/AllowedToDelegateTo")
    count = int(math.floor(len(computers) * .1))
    props = []
    for i in range(0, count):
        comp = random.choice(computers)
        user = random.choice(it_users)
        props.append({'a': user, 'b': comp})

    session.run(
        'UNWIND $props AS prop MERGE (n:User {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:CanRDP]->(m)', props=props)

    props = []
    for i in range(0, count):
        comp = random.choice(computers)
        user = random.choice(it_users)
        props.append({'a': user, 'b': comp})

    session.run(
        'UNWIND $props AS prop MERGE (n:User {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:ExecuteDCOM]->(m)', props=props)

    props = []
    for i in range(0, count):
        comp = random.choice(computers)
        user = random.choice(it_groups)
        props.append({'a': user, 'b': comp})

    session.run(
        'UNWIND $props AS prop MERGE (n:Group {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:CanRDP]->(m)', props=props)

    props = []
    for i in range(0, count):
        comp = random.choice(computers)
        user = random.choice(it_groups)
        props.append({'a': user, 'b': comp})

    session.run(
        'UNWIND $props AS prop MERGE (n:Group {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:ExecuteDCOM]->(m)', props=props)

    props = []
    for i in range(0, count):
        comp = random.choice(computers)
        user = random.choice(it_users)
        props.append({'a': user, 'b': comp})

    session.run(
        'UNWIND $props AS prop MERGE (n:User {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:AllowedToDelegate]->(m)', props=props)

    props = []
    for i in range(0, count):
        comp = random.choice(computers)
        user = random.choice(computers)
        if (comp == user):
            continue
        props.append({'a': user, 'b': comp})

    session.run(
        'UNWIND $props AS prop MERGE (n:Computer {name: prop.a}) MERGE (m:Computer {name: prop.b}) MERGE (n)-[r:AllowedToDelegate]->(m)', props=props)

    print("Adding sessions")
    max_sessions_per_user = int(math.ceil(math.log10(num_pcs)))

    props = []
    for user in users:
        num_sessions = random.randrange(0, max_sessions_per_user)
        if (user in das):
            num_sessions = max(num_sessions, 1)

        if num_sessions == 0:
            continue

        for c in random.sample(computers, num_sessions):
            props.append({'a': user, 'b': c})

        if (len(props) > 500):
            session.run(
                'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)
            props = []

    session.run(
        'UNWIND $props AS prop MERGE (n:User {name:prop.a}) WITH n,prop MERGE (m:Computer {name:prop.b}) WITH n,m MERGE (m)-[:HasSession]->(n)', props=props)

    print("Adding Domain Admin ACEs")
    group_name = "DOMAIN ADMINS@{}".format(domain)
    props = []
    for x in computers:
        props.append({'name': x})

        if len(props) > 500:
            session.run(
                'UNWIND $props as prop MATCH (n:Computer {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:GenericAll {isacl:true}]->(n)', props=props, gname=group_name)
            props = []

    session.run(
        'UNWIND $props as prop MATCH (n:Computer {name:prop.name}) WITH n MATCH (m:Group {name:$gname}) WITH m,n MERGE (m)-[r:GenericAll {isacl:true}]->(n)', props=props, gname=group_name)

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

    print("Creating OUs")
    temp_comps = computers
    random.shuffle(temp_comps)
    split_num = int(math.ceil(num_pcs/ 10))
    split_comps = list(split_seq(temp_comps, split_num))
    props = []
    ou_guid_map ={}
    for i in range(0, 10):
        state = states[i]
        ou_comps = split_comps[i]
        ouname = "{}_COMPUTERS@{}".format(state, domain)
        guid = str(uuid.uuid4())
        ou_guid_map[ouname] = guid
        for c in ou_comps:
            props.append({'compname': c, 'ouguid': guid, 'ouname': ouname})
            if len(props) > 500:
                session.run(
                    'UNWIND $props as prop MERGE (n:Computer {name:prop.compname}) WITH n,prop MERGE (m:Base {objectid:prop.ouguid, name:prop.ouname, blocksInheritance: false}) SET m:OU WITH n,m,prop MERGE (m)-[:Contains]->(n)', props=props)
                props = []

    session.run(
        'UNWIND $props as prop MERGE (n:Computer {name:prop.compname}) WITH n,prop MERGE (m:Base {objectid:prop.ouguid, name:prop.ouname, blocksInheritance: false}) SET m:OU WITH n,m,prop MERGE (m)-[:Contains]->(n)', props=props)

    temp_users = users
    random.shuffle(temp_users)
    split_num = int(math.ceil(num_users/ 10))
    split_users = list(split_seq(temp_users, split_num))
    props = []

    for i in range(0, 10):
        state = states[i]
        ou_users = split_users[i]
        ouname = "{}_USERS@{}".format(state, domain)
        guid = str(uuid.uuid4())
        ou_guid_map[ouname] = guid
        for c in ou_users:
            props.append({'username': c, 'ouguid': guid, 'ouname': ouname})
            if len(props) > 500:
                session.run(
                    'UNWIND $props as prop MERGE (n:User {name:prop.username}) WITH n,prop MERGE (m:Base {objectid:prop.ouguid, name:prop.ouname, blocksInheritance: false}) SET m:OU WITH n,m,prop MERGE (m)-[:Contains]->(n)', props=props)
                props = []

    session.run(
        'UNWIND $props as prop MERGE (n:User {name:prop.username}) WITH n,prop MERGE (m:Base {objectid:prop.ouguid, name:prop.ouname, blocksInheritance: false}) SET m:OU WITH n,m,prop MERGE (m)-[:Contains]->(n)', props=props)

    props = []
    for x in list(ou_guid_map.keys()):
        guid = ou_guid_map[x]
        props.append({'b': guid})

    session.run(
        'UNWIND $props as prop MERGE (n:OU {objectid:prop.b}) WITH n MERGE (m:Domain {name:$domain}) WITH n,m MERGE (m)-[:Contains]->(n)', props=props, domain=domain)

    print("Creating GPOs")
    gpos =[]

    for i in range(1, 20):
        gpo_name = "GPO_{}@{}".format(i, domain)
        guid = str(uuid.uuid4())
        session.run(
            "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=gpo_name, guid=guid)
        gpos.append(gpo_name)

    ou_names = list(ou_guid_map.keys())
    for g in gpos:
        num_links = random.randint(1, 3)
        linked_ous = random.sample(ou_names, num_links)
        for l in linked_ous:
            guid = ou_guid_map[l]
            session.run(
                "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {objectid:$guid}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=g, guid=guid)

    num_links = random.randint(1, 3)
    linked_ous = random.sample(ou_names, num_links)
    for l in linked_ous:
        guid = ou_guid_map[l]
        session.run(
            "MERGE (n:Domain {name:$gponame}) WITH n MERGE (m:OU {objectid:$guid}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=domain, guid=guid)

    gpos.append("DEFAULT DOMAIN POLICY@{}".format(domain))
    gpos.append("DEFAULT DOMAIN CONTROLLER POLICY@{}".format(domain))

    acl_list = ["GenericAll"] * 10 + ["GenericWrite"] * 15 + ["WriteOwner"] * 15 + ["WriteDacl"] * \
        15 + ["AddMember"] * 30 + ["ForceChangePassword"] * \
        15 + ["ReadLAPSPassword"] * 10

    num_acl_principals = int(round(len(it_groups) * .1))
    print("Adding outbound ACLs to {} objects".format(num_acl_principals))

    acl_groups = random.sample(it_groups, num_acl_principals)
    all_principals = it_users + it_groups
    props = []
    for i in acl_groups:
        ace = random.choice(acl_list)
        ace_string = '[r:' + ace + '{isacl:true}]'
        if ace == "GenericAll" or ace == 'GenericWrite' or ace == 'WriteOwner' or ace == 'WriteDacl':
            p = random.choice(all_principals)
            p2 = random.choice(gpos)
            session.run(
                'MERGE (n:Group {name:$group}) MERGE (m {name:$principal}) MERGE (n)-' + ace_string + '->(m)', group=i, principal=p)
            session.run('MERGE (n:Group {name:$group}) MERGE (m:GPO {name:$principal}) MERGE (n)-' +
                        ace_string + '->(m)', group=i, principal=p2)
        elif ace == 'AddMember':
            p = random.choice(it_groups)
            session.run(
                'MERGE (n:Group {name:$group}) MERGE (m:Group {name:$principal}) MERGE (n)-' + ace_string + '->(m)', group=i, principal=p)
        elif ace == 'ReadLAPSPassword':
            p = random.choice(all_principals)
            targ = random.choice(computers)
            session.run(
                'MERGE (n {name:$principal}) MERGE (m:Computer {name:$target}) MERGE (n)-[r:ReadLAPSPassword]->(m)', target=targ, principal=p)
        else:
            p = random.choice(it_users)
            session.run(
                'MERGE (n:Group {name:$group}) MERGE (m:User {name:$principal}) MERGE (n)-' + ace_string + '->(m)', group=i, principal=p)

    print("Marking some users as Kerberoastable")
    i = random.randint(10, 20)
    i = min(i, len(it_users))
    for user in random.sample(it_users, i):
        session.run(
            'MATCH (n:User {name:$user}) SET n.hasspn=true', user=user)

    print("Adding unconstrained delegation to a few computers")
    i = random.randint(10, 20)
    i = min(i, len(computers))
    session.run(
        'MATCH (n:Computer {name:$user}) SET n.unconstrainteddelegation=true', user=user)

    session.run('MATCH (n:User) SET n.owned=false')
    session.run('MATCH (n:Computer) SET n.owned=false')
    session.run('MATCH (n) SET n.domain=$domain', domain=domain)

    session.close()

    print("Database Generation Finished!")
