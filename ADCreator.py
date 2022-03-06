import random
from neo4j import GraphDatabase
from py2neo import Graph
import cmd
import sys
from Generate_standard_nodes import generate_standard_nodes
from Generate_computer_nodes import generate_computer_nodes
from Generate_user_nodes import generate_user_nodes
from Generate_group_nodes import generate_group
from Generate_permission import generate_permission
from Generate_OUs_GPOs import generate_OUs_GPOs
from Generate_ACLs import Generate_ACLs

class Messages():
    def title(self):
        print("================================================================")
        print("BloodHound Sample Database Creator")
        print("================================================================")

    def input_default(self, prompt, default):
        return input("%s [%s] " % (prompt, default)) or default

    def input_yesno(self, prompt, default):
        temp = input(prompt + " " + ("Y" if default else "y") + "/" + ("n" if default else "N") + " ")
        if temp == "y" or temp == "Y":
            return True
        elif temp == "n" or temp == "N":
            return False
        return default


class MainMenu(cmd.Cmd):
    def __init__(self):
        self.m = Messages()
        self.url = "bolt://localhost:7687"
        self.username = "neo4j"
        self.password = "neo4j"
        self.driver = None
        self.model = None
        self.Security_level = 'High'
        self.num_nodes = 500
        self.domain = "TESTLAB"
        self.base_sid = "S-1-5-21-883232822-274137685-4173207990"
        self.Country = "US"
        cmd.Cmd.__init__(self)

    def cmdloop(self):
        while True:
            self.m.title()
            self.do_help("")
            try:
                cmd.Cmd.cmdloop(self)
            except KeyboardInterrupt:
                if self.driver is not None:
                    self.driver.close()
                raise KeyboardInterrupt

    def help_dbconfig(self):
        print("Configure database connection parameters")

    def help_connect(self):
        print("Test connection to the database and verify credentials")

    def help_setnodes(self):
        print("Set base number of nodes to generate in each domain (default 500)")

    def help_setdomain(self):
        print("Set domain name (default 'TESTLAB.LOCAL')")

    def help_cleardb(self):
        print("Clear the database and set constraints")

    def help_clear_and_generate(self):
        print("Connect to the database, clear the db, set the schema, and generate random data")

    def help_exit(self):
        print("Exits the database creator")
    
    def help_setmodel(self):
        print("Set the AD model(Single/Multiple)")
    
    def help_setSecurity_level(self):
        print("Set the security level(High/Medium/Low) for the AD")
    

    def do_dbconfig(self, args):
        print("Current Settings:")
        print("DB Url: {}".format(self.url))
        print("DB Username: {}".format(self.username))
        print("DB Password: {}".format(self.password))
        print("")
        self.url = self.m.input_default("Enter DB URL", self.url)
        self.username = self.m.input_default(
            "Enter DB Username", self.username)
        self.password = self.m.input_default(
            "Enter DB Password", self.password)

        print("")
        print("New Settings:")
        print("DB Url: {}".format(self.url))
        print("DB Username: {}".format(self.username))
        print("DB Password: {}".format(self.password))
        print("")
        print("Testing DB Connection")
        self.test_db_conn()

    def do_setnodes(self, args):
        if not self.model:
            print("Not set the AD model, Use setmodel first")
            return
        passed = args
        if passed != "":
            try:
                self.num_nodes = int(passed)
                return
            except ValueError:
                pass
        if self.model == 'Single':
            self.num_nodes = int(self.m.input_default(
            "Number of nodes of each type to generate", self.num_nodes))
        if self.model == 'Multiple':
            for i in range(3):
                self.num_nodes[i] = int(self.m.input_default(
            "Number of nodes of each type to generate in "+ str(i+1) + " child domain:", self.num_nodes[i]))

    def do_setSecurity_level(self, args):
        if not self.model:
            print("Not set the AD model, Use setmodel first")
            return
        passed = args
        if passed != "":
            try:
                self.Security_level = str(passed)
                return
            except ValueError:
                pass
        if self.model == 'Single':
            self.Security_level = str(self.m.input_default(
            "Security_level for the domain(High/Medium/Low): ", self.Security_level))
        if self.model == 'Multiple':
            for i in range(3):
                self.Security_level[i] = str(self.m.input_default(
            "Security_level for the "+ str(i+1) + " child domain(High/Medium/Low):", self.Security_level[i]))

    def do_setdomain(self, args):
        passed = args
        if passed != "":
            try:
                self.domain = passed.upper()
                return
            except ValueError:
                pass

        self.domain = self.m.input_default("Domain", self.domain).upper()
        print("")
        print("New Settings:")
        print("Domain: {}".format(self.domain))

    def do_exit(self, args):
        raise KeyboardInterrupt

    def do_connect(self, args):
        self.test_db_conn()

    def do_cleardb(self, args):
        if not self.connected:
            print("Not connected to database. Use connect first")
            return

        print("Clearing Database")
        d = self.driver
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

    def test_db_conn(self):
        self.connected = False
        if self.driver is not None:
            self.driver.close()
        try:
            graph = Graph(self.url, auth=(self.username, self.password))
            self.connected = True
            self.driver = GraphDatabase.driver(self.url, auth=(self.username, self.password))
            print("Database Connection Successful!")
        except Exception:
            print("Database Connection Failed. Check your settings.")

    def do_clear_and_generate(self, args):
        self.test_db_conn()
        if not self.model:
            print("Not set the AD model, Use setmodel first")
            return
        self.do_cleardb("a")
        if self.model == 'Single':
            self.generate_singleAD()
        if self.model == 'Multiple':
            self.generate_multipleAD()

    def do_setmodel(self, args):
        passed = args
        print("Set the AD model(Single/Multiple)")
        if passed != "":
            try:
                self.model = str(passed)
                return
            except ValueError:
                pass
        self.model = self.m.input_default("Model", self.model)
        print("")
        print("New Settings:")
        print("Model: {}".format(self.model))
        if self.model == 'Multiple':
            self.num_nodes = [500,500,500]
            self.Security_level = ['High','Medium','Low']


        
    def generate_multipleAD(self):
        print ("Generateing the root domain")
        session = self.driver.session()
        self.domain = str(self.domain)+".COM"
        generate_standard_nodes(self.driver,self.domain,self.base_sid,'root')
        root_sid = self.base_sid
        Country = ['US','CANADA','AUSTRALIA']
        base_sid = ["S-1-5-21-883232822-274137685-4173207991","S-1-5-21-883232822-274137685-4173207992","S-1-5-21-883232822-274137685-4173207993"]
        overseas_users ={}
        overseas_PCs = {}
        for i in range(len(Country)):
            print ("Generateing the "+ str(i+1) + " child domain")
            self.domain = str(Country[i])+".LOCAL"
            self.base_sid = base_sid[i]
            self.Country = Country[i]
            generate_standard_nodes(self.driver,self.domain,self.base_sid,'a')
            print("Starting data generation with nodes={}".format(self.num_nodes[i]))
            computers = generate_computer_nodes(self.driver,self.domain,self.base_sid,self.Country,self.num_nodes[i])
            overseas_PCs[Country[i]] = random.sample(computers,int(self.num_nodes[i]*0.02))
            users = generate_user_nodes(self.driver,self.domain,self.base_sid,self.num_nodes[i])
            overseas_users[Country[i]] = random.sample(users,int(self.num_nodes[i]*0.02))
            groups = generate_group(self.driver,self.domain,self.base_sid,self.num_nodes[i],users,self.Security_level[i])
            generate_permission(self.driver,self.domain,self.num_nodes[i],computers,groups,users,self.Security_level[i])
            generate_OUs_GPOs(self.driver,self.domain,computers,self.Country,users)
            Generate_ACLs(self.driver,self.domain,computers)
            session.run(
                'MERGE (n:domain {objectid:$root_id}) WITH n MERGE (m:domain {objectid:$sid}) WITH n,m MERGE (m)-[:TrustedBy]->(n)',root_id = root_sid,sid = base_sid[i])
            session.run(
                'MERGE (n:domain {objectid:$root_id}) WITH n MERGE (m:domain {objectid:$sid}) WITH n,m MERGE (n)-[:TrustedBy]->(m)',root_id = root_sid,sid = base_sid[i])
        # child omain trust by each other
        for i in range(len(base_sid)):
            if i<2:
                session.run(
                    'MERGE (n:domain {objectid:$root_id}) WITH n MERGE (m:domain {objectid:$sid}) WITH n,m MERGE (m)-[:TrustedBy]->(n)',root_id = base_sid[i],sid = base_sid[i+1])
                session.run(
                    'MERGE (n:domain {objectid:$root_id}) WITH n MERGE (m:domain {objectid:$sid}) WITH n,m MERGE (n)-[:TrustedBy]->(m)',root_id = base_sid[i],sid = base_sid[i+1])

        # overseas users
        for i in Country:
            possible_country = list(set(Country) - set([i]))
            possible_choice = random.randrange(0, 3)
            if possible_choice == 0:
                continue
            if possible_choice == 1:
                overseas_country = random.choice(possible_country)
                for user in overseas_users[i]:
                    for pc in overseas_PCs[overseas_country]:
                        if random.choice([True, False]):
                            session.run(
                                'MERGE (n:User {name:$uname}) MERGE (m:Computer {name:$pcname}) WITH n,m MERGE (m)-[:HasSession]->(n)', uname=user,pcname = pc)
            else:
                for user in overseas_users[i]:
                    for overseas_country in possible_country:
                        for pc in overseas_PCs[overseas_country]:
                            if random.choice([True, False]):
                                session.run(
                                    'MERGE (n:User {name:$uname}) MERGE (m:Computer {name:$pcname}) WITH n,m MERGE (m)-[:HasSession]->(n)', uname=user,pcname = pc)
                        



    
    
    def generate_singleAD(self):
        self.domain = str(self.domain)+".LOCAL"
        generate_standard_nodes(self.driver,self.domain,self.base_sid,'a')
        print("Starting data generation with nodes={}".format(self.num_nodes))
        computers = generate_computer_nodes(self.driver,self.domain,self.base_sid,self.Country,self.num_nodes)
        users = generate_user_nodes(self.driver,self.domain,self.base_sid,self.num_nodes)
        groups = generate_group(self.driver,self.domain,self.base_sid,self.num_nodes,users,self.Security_level)
        generate_permission(self.driver,self.domain,self.num_nodes,computers,groups,users,self.Security_level)
        generate_OUs_GPOs(self.driver,self.domain,computers,self.Country,users)
        Generate_ACLs(self.driver,self.domain,computers)
        


if __name__ == '__main__':
    try:
        MainMenu().cmdloop()
    except KeyboardInterrupt:
        print("Exiting")
        sys.exit()
