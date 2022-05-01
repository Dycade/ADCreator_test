from Generate_standard_nodes import cn,AD_settings
import random
import uuid

def generate_OUs_GPOs(driver,domain,computers,users):
    with driver.session() as session:
        setting_dict = AD_settings.setting
        Country = setting_dict['Country']
        print("Creating Narrow OUs")
        # Creating root OUs
        states = [elt.strip() for elt in setting_dict['States'].split(',')]
        Company_dept = [elt.strip() for elt in setting_dict['department'].split(',')]
        base_statement = "MERGE (n:Base {name: $uname}) SET n:OU, n.objectid=$guid"
        session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(str(Country)+'_USERS',domain))
        session.run( 'MERGE (n:OU {name:$uname}) WITH n MERGE (m:Domain {name:$domain}) WITH n,m MERGE (m)-[:Contains]->(n)', uname=cn(str(Country)+'_USERS',domain), domain=domain)
        session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(str(Country)+'_COMPUTERS',domain))
        session.run( 'MERGE (n:OU {name:$uname}) WITH n MERGE (m:Domain {name:$domain}) WITH n,m MERGE (m)-[:Contains]->(n)', uname=cn(str(Country)+'_COMPUTERS',domain), domain=domain)
        for dep in Company_dept:
            session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(str(dep)+'_USERS',domain))
            session.run(
                'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn(str(Country)+'_USERS',domain), gname=cn(str(dep)+'_USERS',domain))
            session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(str(dep)+'_COMPUTERS',domain))
            session.run(
                'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn(str(Country)+'_COMPUTERS',domain), gname=cn(str(dep)+'_COMPUTERS',domain))
            for state in states:
                session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(str(dep)+'_COMPUTERS_'+str(state),domain))
                session.run(f"{base_statement}",guid = str(uuid.uuid4()),uname=cn(str(dep)+'_USERS_'+str(state),domain))
                session.run(
                    'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn(str(dep)+'_USERS',domain), gname=cn(str(dep)+'_USERS_'+str(state),domain))
                session.run(
                    'MERGE (n:OU {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[:Contains]->(m)', name=cn(str(dep)+'_COMPUTERS',domain), gname=cn(str(dep)+'_COMPUTERS_'+str(state),domain))
        
        das = []
        temp_das =session.run('MATCH (n:User)-[:MemberOf]->(:Group{name:$gname}) RETURN n.name', gname=cn("DOMAIN ADMINS",domain))
        for temp in temp_das:
            das.append(temp["n.name"])
        temp_das =session.run('MATCH (n:User)-[:MemberOf]->(:Group{name:$gname}) RETURN n.name', gname=cn("ADMINISTRATORS",domain))
        for temp in temp_das:
            das.append(temp["n.name"])
        temp_das =session.run('MATCH (n:User)-[:MemberOf]->(:Group{name:$gname}) RETURN n.name', gname=cn("ENTERPRISE ADMINS",domain))
        for temp in temp_das:
            das.append(temp["n.name"])


        Regular_users = [x for x in users if x not in das]
        for user in Regular_users:
            state = random.choice(states)
            user_dep = session.run(
                'Match (n:User {name:$name}) RETURN n.department',name=user).single()[0]
            session.run(
                'MERGE (n:User {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=user, gname=cn(str(user_dep)+'_USERS_'+str(state),domain))
            

        
        for pc in computers:
            state = random.choice(states)
            pc_dep = session.run(
                'Match (n:Computer{name:$name}) RETURN n.department',name=pc).single()[0]
            session.run(
                'MERGE (n:Computer {name:$name}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (m)-[:Contains]->(n)', name=pc, gname=cn(str(pc_dep)+'_COMPUTERS_'+str(state),domain))
        


        print("Creating GPOs")
        #Creating GPOs for the root OUs
        session.run(
                "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn(str(Country)+"_users_settings",domain), guid=str(uuid.uuid4()))
        session.run(
                "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn(str(Country)+"_users_settings",domain), uname=cn(str(Country)+"_USERS",domain))  
        session.run(
                "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=cn(str(Country)+"_Computers_settings",domain), guid=str(uuid.uuid4()))      
        session.run(
                "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$uname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=cn(str(Country)+"_Computers_settings",domain), uname=cn(str(Country)+"_COMPUTERS",domain))

        
        GPO_names = ["Software", "Windows", "Control_panel", "Desktop", "Network", "Shared_folders", "Taskbar", "System"]
        for dep in Company_dept:
            gpo_name = cn(str(dep)+'_Computer_Settings',domain)
            guid = str(uuid.uuid4())
            session.run(
                "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=gpo_name, guid=guid)
            session.run(
                "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=gpo_name, gname=cn(str(dep)+'_COMPUTERS',domain))
            gpo_name = cn(str(dep)+'_User_Settings',domain)
            guid = str(uuid.uuid4())
            session.run(
                "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=gpo_name, guid=guid)
            session.run(
                "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=gpo_name, gname=cn(str(dep)+'_USERS',domain))
            for state in states:
                num_links = random.randint(0, 3)
                for num in range(num_links):
                    user_gpo_name = cn('User_'+random.choice(GPO_names) +'_Settings_0' + str(num+1),domain)
                    user_guid = str(uuid.uuid4())
                    computer_gpo_name = cn('Computer_'+random.choice(GPO_names) +'_Settings_0' + str(num+1),domain)
                    computer_guid = str(uuid.uuid4())
                    session.run(
                        "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=user_gpo_name, guid=user_guid)
                    session.run(
                        "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=user_gpo_name, gname=cn(str(dep)+'_USERS_'+str(state),domain))
                    session.run(
                        "MERGE (n:Base {name:$gponame}) SET n:GPO, n.objectid=$guid", gponame=computer_gpo_name, guid=computer_guid)
                    session.run(
                        "MERGE (n:GPO {name:$gponame}) WITH n MERGE (m:OU {name:$gname}) WITH n,m MERGE (n)-[r:GpLink]->(m)", gponame=computer_gpo_name, gname=cn(str(dep)+'_COMPUTERS_'+str(state),domain))
        

