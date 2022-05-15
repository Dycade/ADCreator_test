from lib2to3.pgen2 import driver
import random
from neo4j import GraphDatabase
from py2neo import Graph
import sys
from Generate_standard_nodes import generate_standard_nodes,AD_settings
from Generate_computer_nodes import generate_computer_nodes
from Generate_user_nodes import generate_user_nodes
from Generate_group_nodes import generate_group
from Generate_permission import generate_permission
from Generate_OUs_GPOs import generate_OUs_GPOs
from Generate_ACLs import Generate_ACLs




def do_cleardb():
    print("Clearing Database")
    d = test_db_conn()
    session = d.session()
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
    
    print("Schema has been cleared")
            
    session.close()

    print("DB Cleared and Schema Reset")

def test_db_conn():
    try:
        graph = Graph(setting_dict['url'], auth=(setting_dict['username'], setting_dict['password']))
        driver = GraphDatabase.driver(setting_dict['url'], auth=(setting_dict['username'], setting_dict['password']))
        print("Database Connection Successful!")
    except Exception:
        print("Database Connection Failed. Check your settings.")
        sys.exit()
    return driver

def do_clear_and_generate():
    do_cleardb()
    if setting_dict['model'] == 'Single':
        generate_singleAD()
    if setting_dict['model'] == 'Multiple':
        generate_multipleAD()



def generate_multipleAD():
    driver = test_db_conn()
    print ("Generateing the root domain")
    domain = str(setting_dict['domain'])+".COM"
    generate_standard_nodes(driver,domain,'root',setting_dict,0)
    overseas_users ={}
    overseas_PCs = {}
    Countries = []
    for i in range(int(setting_dict['num_child_domain'])):
        print ("Generateing the "+ str(i+1) + " child domain")
        AD_settings.change(i+1)
        next_setting = AD_settings.setting
        domain = str(next_setting['Country'])+".LOCAL"
        generate_standard_nodes(driver,domain,'a',next_setting,i+1)
        computers = generate_computer_nodes(driver,domain)
        users = generate_user_nodes(driver,domain)
        groups = generate_group(driver,domain,users)
        generate_permission(driver,domain,computers,groups,users)
        generate_OUs_GPOs(driver,domain,computers,users)
        Generate_ACLs(driver,domain,computers)
        if setting_dict['Users_can_ login_overseas_computers'] == 'Y':
            Countries.append(next_setting['Country'])
            overseas_PCs[Countries[i]] = random.sample(computers,int(int(setting_dict['num_PCs'])*0.02))
            overseas_users[Countries[i]] = random.sample(users,int(int(setting_dict['num_users'])*0.02))


    # overseas users
    session = driver.session()
    if setting_dict['Users_can_ login_overseas_computers'] == 'Y':
        for i in Countries:
            possible_country = list(set(Countries) - set([i]))
            possible_choice = random.randrange(1, int(setting_dict['num_child_domain']))
            if possible_choice == 1:
                overseas_country = random.choice(possible_country)
                for user in overseas_users[i]:
                    for pc in overseas_PCs[overseas_country]:
                        if random.choice([True, False]):
                            session.run(
                                'MERGE (n:User {name:$uname}) MERGE (m:Computer {name:$pcname}) WITH n,m MERGE (m)-[:HasSession]->(n)', uname=user,pcname = pc)
            else:
                selected_country = random.sample(possible_country, possible_choice)
                for user in overseas_users[i]:
                    for overseas_country in selected_country:
                        for pc in overseas_PCs[overseas_country]:
                            if random.choice([True, False]):
                                session.run(
                                    'MERGE (n:User {name:$uname}) MERGE (m:Computer {name:$pcname}) WITH n,m MERGE (m)-[:HasSession]->(n)', uname=user,pcname = pc)
         





def generate_singleAD():
    driver = test_db_conn()
    domain = str(setting_dict['domain'])+".LOCAL"
    generate_standard_nodes(driver,domain,'a',setting_dict,0)
    print("Starting data generation")
    computers = generate_computer_nodes(driver,domain)
    users = generate_user_nodes(driver,domain)
    groups = generate_group(driver,domain,users)
    generate_permission(driver,domain,computers,groups,users)
    generate_OUs_GPOs(driver,domain,computers,users)
    Generate_ACLs(driver,domain,computers)
    


if __name__ == '__main__':
    setting_dict = AD_settings.setting
    do_clear_and_generate()
