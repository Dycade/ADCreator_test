import random

def Generate_ACLs(driver,domain,computers):
    with driver.session() as session:
        acl_list = ["GenericAll"] * 10 + ["GenericWrite"] * 15 + ["WriteOwner"] * 15 + ["WriteDacl"] * \
            15 + ["AddMember"] * 30 + ["ForceChangePassword"] * \
            15 + ["ReadLAPSPassword"] * 10
        
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

        session.close()
        session.run('MATCH (n:User) SET n.owned=false')
        session.run('MATCH (n:Computer) SET n.owned=false')
        session.run('MATCH (n) WHERE n.domain IS NULL SET n.domain=$domain', domain=domain)
        
        print("Database Generation Finished!")
