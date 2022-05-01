from Generate_standard_nodes import cn,cs,AD_settings
import random

def name_computer(domain,type,department,dict,i):
    return str(dict[type])+"-"+str(department)+"-{:05d}.{}".format(i, domain)

def generate_computer_nodes(driver,domain):
    with driver.session() as session:
        setting_dict = AD_settings.setting
        base_sid = setting_dict['base_sid']
        num_nodes = int(setting_dict['num_PCs'])
        print("Generating Computer Nodes")
        group_name = cn("DOMAIN COMPUTERS",domain)
        props = []
        ridcount = 1000
        computers =[]
        PC_list = [elt.strip() for elt in setting_dict['PC_types'].split(',')]
        PC_short = [elt.strip() for elt in setting_dict['PC_short'].split(',')]
        PC_percent = [float(elt.strip()) for elt in setting_dict['PC_percent'].split(',')]
        PC_dict = dict(zip(PC_list, PC_short))
        Delegatable_weight = ["False"] * 85 + ["True"] * 15
        PC_departments = [elt.strip() for elt in setting_dict['department'].split(',')]
        department_percent = [float(elt.strip()) for elt in setting_dict['department_percent'].split(',')]
        for i in range(1, num_nodes+1):
            PC_type = random.choices(PC_list, PC_percent)[0]
            PC_department = random.choices(PC_departments, department_percent)[0]
            comp_name = name_computer(domain,PC_type,PC_department,PC_dict,i)
            computers.append(comp_name)
            enabled = True
            Delegatable = random.choice(Delegatable_weight)
            props.append({'id': cs(ridcount,base_sid), 'props': {
                'name': comp_name,
                'type': PC_type,
                'Allows Unconstrained Delegation': Delegatable,
                'domain': domain,
                'department': PC_department,
                'enabled': enabled,
            }})
            ridcount += 1
            if (len(props) > 500):
                session.run(
                    'UNWIND $props as prop MERGE (n:Base {objectid: prop.id}) SET n:Computer, n += prop.props WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=group_name)
                props = []
        session.run(
            'UNWIND $props as prop MERGE (n:Base {objectid:prop.id}) SET n:Computer, n += prop.props WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', props=props, gname=group_name)

        states = [elt.strip() for elt in setting_dict['States'].split(',')]
        
        print("Creating Domain Controllers")
        num_controllers = int(setting_dict['num_domain_controllers'])
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
        
    return computers
