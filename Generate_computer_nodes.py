from Generate_standard_nodes import cn,cs,Country_states
import random

def name_computer(domain,type,department,i):
    if type == "Workstation":
        return "WS-"+str(department)+"-{:05d}.{}".format(i, domain)
    if type == "Laptop":
        return "LT-"+str(department)+"-{:05d}.{}".format(i, domain)
    if type == "Printer":
        return "PTR-"+str(department)+"-{:05d}.{}".format(i, domain)
    if type == "Server":
        return "S-"+str(department)+"-{:05d}.{}".format(i, domain)
    if type == "Virtual_Machine":
        return "VM-"+str(department)+"-{:05d}.{}".format(i, domain)
    


def generate_computer_nodes(driver,domain,base_sid,Country,num_nodes):
    with driver.session() as session:
        print("Generating Computer Nodes")
        group_name = cn("DOMAIN COMPUTERS",domain)
        props = []
        ridcount = 1000
        computers =[]
        PC_types = ["Workstation"] * 60 + ["Laptop"] * 15 + ["Printer"] * 10 + ["Server"] * 5 + ["Virtual_Machine"] * 10
        Delegatable_weight = ["False"] * 85 + ["True"] * 15
        PC_departments = ["IT","HR","SALES","MANAGEMENT","R&D","MARKTING","ACCOUNTING"] 
        for i in range(1, num_nodes+1):
            PC_type = random.choice(PC_types)
            PC_department = random.choice(PC_departments)
            comp_name = name_computer(domain,PC_type,PC_department,i)
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

        states = Country_states(Country)
        
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
        
    return computers
