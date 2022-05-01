from Generate_standard_nodes import cs,AD_settings
import random
import math


def Percentage_of_Users (level):
    if level == 'High':
        return 0.03
    if level == 'Medium':
        return 0.06
    if level == 'Low':
        return 0.12


def generate_group(driver,domain,users):
    with driver.session() as session:
        setting_dict = AD_settings.setting
        base_sid = setting_dict['base_sid']
        num_groups = int(setting_dict['num_groups'])
        level = setting_dict['Security_level']
        print("Generating Group Nodes")
        departments = [elt.strip() for elt in setting_dict['department'].split(',')]
        department_percent = [float(elt.strip()) for elt in setting_dict['department_percent'].split(',')]
        props = []
        groups = []
        num_PCs = session.run(
                'MATCH (n:Computer) WHERE n.domain=$domain RETURN count(n) as count', domain=domain).single()[0]
        num_users = session.run(
                'MATCH (n:User) WHERE n.domain=$domain RETURN count(n) as count', domain=domain).single()[0]
        ridcount = 1000+num_PCs+num_users
        for i in range(1, num_groups + 1):
            dept = random.choices(departments, department_percent)[0]
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
            'MATCH (n:Computer) WHERE n.domain=$pcdomain MATCH (m:Group {objectid: $id}) MERGE (m)-[:AdminTo]->(n)',pcdomain = domain, id=cs(512,base_sid))



        num_Privileged =  random.sample(users, int(num_users*Percentage_of_Users (level)))
        temp_Privileged = session.run("""MATCH (n:Group {highvalue: true}) WHERE not(n.name CONTAINS "CONTROLLERS") AND (n.name CONTAINS $domain_name)
                                            RETURN n.name""",domain_name = domain)     
        Privileged_group = []              
        for temp in temp_Privileged:
            Privileged_group.append(temp["n.name"]) 
        for user in num_Privileged:
            session.run(
                'MERGE (n:Base {name:$name}) SET n:User,n.department=$dept_name WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', name=user,dept_name = "IT", gname=random.choice(Privileged_group))
     


        print("Applying random group nesting")
        max_nest = int(round(math.log10(num_groups)))
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
  

        print("Calculated {} groups per user with a variance of - {}".format(num_groups_base, variance*2))

        for user in users:
            dept = random.choices(departments, department_percent)[0]
            if user not in num_Privileged:
                session.run('MATCH (n:User {name:$name}) SET n.department = $dept_name', name=user, dept_name = dept)
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
      
        

    return groups