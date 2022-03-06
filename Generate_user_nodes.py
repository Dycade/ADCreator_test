from Generate_standard_nodes import cn,cs
import random
import pickle
import time

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

def generate_user_nodes(driver,domain,base_sid,num_nodes):
    with driver.session() as session:
        print("Generating User Nodes")
        group_name = "DOMAIN USERS@{}".format(domain)
        props = []
        users = []
        num_PCs = session.run(
                'MATCH (n:Computer) WHERE n.domain=$domain RETURN count(n) as count', domain=domain).single()[0]
        ridcount = 1000+num_PCs
        with open('first.pkl', 'rb') as f:
            first_names = pickle.load(f)
        with open('last.pkl', 'rb') as f:
            last_names = pickle.load(f)

        for i in range(1, num_nodes+1):
            first = random.choice(first_names)
            last = random.choice(last_names)
            user_name = "{}{}{:05d}@{}".format(
                first[0], last, i, domain).upper()
            user_name = user_name.format(first[0], last, i).upper()
            users.append(user_name)
            dispname = "{} {}".format(first, last)
            enabled = True
            pwdlastset = generate_timestamp()
            lastlogon = generate_timestamp()
            objectsid = cs(ridcount,base_sid)
            ridcount += 1
            props.append({'id': objectsid, 'props': {
                'displayname': dispname,
                'name': user_name,
                'enabled': enabled,
                'pwdlastset': pwdlastset,
                'lastlogon': lastlogon,
                'domain': domain,
            }})
            if (len(props) > 500):
                session.run(
                    'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:User, n += prop.props WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=group_name)
                props = []

        session.run(
            'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:User, n += prop.props WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=group_name)
        
        
        print("Generating Adminstrator accounts")
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


    return users



        