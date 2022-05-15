import random
from Generate_standard_nodes import AD_settings

def Generate_ACLs(driver,domain,computers):
    with driver.session() as session:
        setting_dict = AD_settings.setting
        acl_list = [elt.strip() for elt in setting_dict['acl_list'].split(',')]
        acl_percent = [float(elt.strip()) for elt in setting_dict['acl_percent'].split(',')]
        it_users = []
        temp_user = session.run('MATCH (n:User {domain: $domain,department:$dept_name}) RETURN n.name', domain=domain,dept_name = "IT")
        for temp in temp_user:
            it_users.append(temp["n.name"])

        it_groups = []
        temp_groups = session.run("""MATCH (n:Group) WHERE (n.name CONTAINS "IT") AND (n.name CONTAINS $domain_name) 
                                    RETURN n.name""",domain_name = domain)  
        for temp in temp_groups:
            it_groups.append(temp["n.name"])
        
        gpos = []
        temp_gpos = session.run("""MATCH (n:GPO) WHERE not(n.name CONTAINS "DEFAULT") AND (n.name CONTAINS $domain_name) 
                                    RETURN n.name""",domain_name = domain)  
        for temp in temp_gpos:
            gpos.append(temp["n.name"])


        num_acl_principals = int(round(len(it_groups) * .1))
        print("Adding outbound ACLs to {} objects".format(num_acl_principals))

        acl_groups = random.sample(it_groups, num_acl_principals)
        all_principals = it_users + it_groups
        for i in acl_groups:
            ace = random.choices(acl_list, acl_percent)[0]
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

        session.close()
        session.run('MATCH (n:User) SET n.owned=false')
        session.run('MATCH (n:Computer) SET n.owned=false')
        session.run('MATCH (n) WHERE n.Domain IS NULL SET n.Domain=$domain', domain=domain)
        
        print("Database Generation Finished!")