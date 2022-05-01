import random
import math
from Generate_standard_nodes import cn,AD_settings
def level_num_sessions(level):
    if level == 'High':
        return 1
    if level == 'Medium':
        return 2
    if level == 'Low':
        return 3


def generate_permission(driver,domain,computers,groups,users):
    with driver.session() as session:
        setting_dict = AD_settings.setting
        level = setting_dict['Security_level']
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
        it_users = []
        temp_user = session.run('MATCH (n:User {domain: $domain,department:$dept_name}) RETURN n.name', domain=domain,dept_name = "IT")
        for temp in temp_user:
            it_users.append(temp["n.name"])

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

        print("Adding sessions")
        max_sessions_per_user = 3

        props = []
        das = []
        users.append(cn("ADMINSTRATOR",domain))
        temp_das =session.run('MATCH (n:User)-[:MemberOf]->(m:Group {highvalue: true}) WHERE m.name CONTAINS $domain_name RETURN n.name',domain_name = domain)
        for temp in temp_das:
            das.append(temp["n.name"])
        for user in users:
            num_sessions = random.randrange(0, max_sessions_per_user)
            if (user in das):
                num_sessions = max(num_sessions*level_num_sessions(level), 1)

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

        
        print("Marking some users as Kerberoastable")
        i = random.randint(10, 20)
        i = min(i, len(it_users))
        for user in random.sample(it_users, i):
            session.run(
                'MATCH (n:User {name:$user}) SET n.hasspn=true', user=user)
        
        #ACCOUNT OPERATORS can modfify accounts of most groups 
        all_groups = session.run("""MATCH (n:Group) WHERE not(n.name CONTAINS "ADMINISTRATORS") AND (n.name CONTAINS $domain_name) AND not((n)-[:MemberOf]->(:Group{name:$gname}))
                                            RETURN n.name""",domain_name = domain,gname=cn("ADMINISTRATORS",domain))  
        for temp in all_groups:
            session.run(
            'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$mname}) WITH n,m MERGE (n)-[:GenericAll {isacl:true}]->(m)', gname=cn("ACCOUNT OPERATORS",domain), mname=temp["n.name"])
        
        # Print Operators and Server Operators can log into domain controllers
        Operators = []
        temp_ops = session.run("""MATCH (n:User) -[:MemberOf]->(:Group{name:$gname})
                                            RETURN n.name""",gname = cn("SERVER OPERATORS",domain))  
        for temp in temp_ops:
            Operators.append(temp["n.name"])
        temp_ops = session.run("""MATCH (n:User) -[:MemberOf]->(:Group{name:$gname})
                                            RETURN n.name""",gname = cn("PRINT OPERATORS",domain))  
        for temp in temp_ops:
            Operators.append(temp["n.name"])
        DCs = []
        temp_DCs = session.run("MATCH (n:Computer)-[:MemberOf]->(:Group{name:$gname}) RETURN n.name",gname = cn("DOMAIN CONTROLLERS",domain))  
        for temp in temp_DCs:
            DCs.append(temp["n.name"])
        for OP in Operators:
            for DC in DCs:
                if random.choice([True, False]):
                    session.run('MERGE (n:User {name:$uname}) WITH n MERGE (m:Computer {name:$cname}) WITH n,m MERGE (m)-[:HasSession]->(n)', uname=OP,cname = DC)
        
