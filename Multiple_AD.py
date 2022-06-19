from ADCreator import generate_AD,do_cleardb
from ADCreatorLow import generate_low
import random
import uuid
from faker import Faker
from neo4j import GraphDatabase

def cn(name,domain):
    return f"{name}@{domain}"

def cs(relative_id,base_sid):
    return f"{base_sid}-{str(relative_id)}"

def cws(security_id,domain):
    return f"{domain}-{str(security_id)}"

def generate_standard_nodes(driver,domain,base_sid):
    with driver.session() as session:
        session.run("MERGE (n:Base {name: $gname}) SET n:Domain, n.objectid=$sid",
                    gname=domain, sid=base_sid)
        print("Populating Standard Nodes")
        base_statement = "MERGE (n:Base {name: $gname}) SET n:Group, n.objectid=$sid"
        session.run(f"{base_statement},n.highvalue=true",
                    sid=cs(512,base_sid), gname=cn("DOMAIN ADMINS",domain))
        session.run(base_statement, sid=cs(515,base_sid), gname=cn("DOMAIN COMPUTERS",domain))
        session.run(base_statement, gname=cn("DOMAIN USERS",domain), sid=cs(513,base_sid))
        session.run(f"{base_statement},n.highvalue=true",
                    gname=cn("DOMAIN CONTROLLERS",domain), sid=cs(516,base_sid))
        session.run(base_statement, gname=cn(
            "ENTERPRISE DOMAIN CONTROLLERS",domain), sid=cws("S-1-5-9",domain))
        session.run(f"{base_statement},n.highvalue=true",
                    gname=cn("ADMINISTRATORS",domain), sid=cs(544,base_sid))
        session.run(f"{base_statement},n.highvalue=true",
                    gname=cn("ENTERPRISE ADMINS",domain), sid=cs(519,base_sid))
        session.run(f"{base_statement},n.highvalue=true",
                    gname=cn("PRINT OPERATORS",domain), sid=cs(550,base_sid))
        session.run(f"{base_statement},n.highvalue=true",
                    gname=cn("ACCOUNT OPERATORS",domain), sid=cs(548,base_sid))
        session.run(f"{base_statement},n.highvalue=true",
                    gname=cn("SERVER OPERATORS",domain), sid=cs(549,base_sid))
        
        
        
        session.run(
            "MERGE (n:Base {name:$domain}) SET n:Domain, n.highvalue=true", domain=domain)
        ddp = str(uuid.uuid4())
        ddcp = str(uuid.uuid4())
        dcou = str(uuid.uuid4())
        base_statement = "MERGE (n:Base {name:$gpo, objectid:$guid}) SET n:GPO"
        session.run(base_statement, gpo=cn("DEFAULT DOMAIN POLICY",domain), guid=ddp)
        session.run(base_statement, gpo=cn(
            "DEFAULT DOMAIN CONTROLLERS POLICY",domain), guid=ddcp)
        session.run("MERGE (n:Base {name:$ou, objectid:$guid, blocksInheritance: false}) SET n:OU", ou=cn(
            "DOMAIN CONTROLLERS",domain), guid=dcou)

        print("Adding Standard Edges")

        # Default GPOs
        gpo_name = cn("DEFAULT DOMAIN POLICY",domain)
        session.run(
            'MERGE (n:GPO {name:$gpo}) MERGE (m:Domain {name:$domain}) MERGE (n)-[:GpLink {isacl:false, enforced:toBoolean(false)}]->(m)', gpo=gpo_name, domain=domain)
        session.run(
            'MERGE (n:Domain {name:$domain}) MERGE (m:OU {objectid:$guid}) MERGE (n)-[:Contains {isacl:false}]->(m)', domain=domain, guid=dcou)
        gpo_name = cn("DEFAULT DOMAIN CONTROLLERS POLICY",domain)
        OU_name =  cn("DOMAIN CONTROLLERS",domain)
        session.run(
           'MERGE (n:GPO {name:$gpo}) MERGE (m:OU {name:$OU}) MERGE (n)-[:GpLink {isacl:false, enforced:toBoolean(false)}]->(m)', gpo=gpo_name, OU=OU_name)

        ADGroup_name = cn("ADMINISTRATORS",domain)
        # Administrators -> DCSync Rights
        session.run(
            'MERGE (n:Domain {name:$domain}) MERGE (m:Group {name:$gname}) MERGE (m)-[:Owns {isacl:true}]->(n)', domain=domain, gname=ADGroup_name)
        session.run(
            'MERGE (n:Domain {name:$domain}) MERGE (m:Group {name:$gname}) MERGE (m)-[:GetChanges]->(n)', domain=domain, gname=ADGroup_name)
        session.run(
            'MERGE (n:Domain {name:$domain}) MERGE (m:Group {name:$gname}) MERGE (m)-[:GetChangesAll]->(n)', domain=domain, gname=ADGroup_name)
        # Administrators -> High Value Targets
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ENTERPRISE ADMINS",domain), gname=ADGroup_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("DOMAIN ADMINS",domain), gname=ADGroup_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("DOMAIN CONTROLLERS",domain), gname=ADGroup_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("SERVER OPERATORS",domain), gname=ADGroup_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ACCOUNT OPERATORS",domain), gname=ADGroup_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("BACKUP OPERATORS",domain), gname=ADGroup_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("PRINT OPERATORS",domain), gname=ADGroup_name)


        
        # Ent Admins -> High Value Targets
        group_name = cn("ENTERPRISE ADMINS",domain)
        session.run(
            'MERGE (n:Domain {name:$domain}) MERGE (m:Group {name:$gname}) MERGE (m)-[:GenericAll {isacl:true}]->(n)', domain=domain, gname=group_name)
        session.run(
            'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$ADgname}) WITH n,m MERGE (n)-[:MemberOf]->(m)',ADgname = ADGroup_name,  gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ADMINISTRATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("BACKUP OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("PRINT OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("SERVER OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("DOMAIN ADMINS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ACCOUNT OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("DOMAIN CONTROLLERS",domain), gname=group_name)


        # Domain Admins -> High Value Targets
        group_name = cn("DOMAIN ADMINS",domain)
        session.run(
            'MERGE (n:Domain {name:$domain}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:AllExtendedRights {isacl:true}]->(n)', domain=domain, gname=group_name)
        session.run(
            'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$ADgname}) WITH n,m MERGE (n)-[:MemberOf]->(m)',ADgname = ADGroup_name,  gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:Owns {isacl:true}]->(n)', nname=cn("ADMINISTRATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("PRINT OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("BACKUP OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:Owns {isacl:true}]->(n)', nname=cn("ACCOUNT OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("SERVER OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("DOMAIN CONTROLLERS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:Owns {isacl:true}]->(n)', nname=cn("ENTERPRISE ADMINS",domain), gname=group_name)
        
         # ENTERPRISE ADMINS -> High Value Targets
        group_name = cn("ENTERPRISE ADMINS",domain)
        session.run(
            'MERGE (n:Domain {name:$domain}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericAll {isacl:true}]->(n)', domain=domain, gname=group_name)
        session.run(
            'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$ADgname}) WITH n,m MERGE (n)-[:MemberOf]->(m)',ADgname = ADGroup_name,  gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ADMINISTRATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("PRINT OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("BACKUP OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ACCOUNT OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("SERVER OPERATORS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GenericWrite {isacl:true}]->(n)', nname=cn("DOMAIN ADMINS",domain), gname=group_name)
        session.run(
            'MERGE (n:Group {name:$nname}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:WriteDacl {isacl:true}]->(n)', nname=cn("ENTERPRISE ADMINS",domain), gname=group_name)





        # DC Groups -> Domain Node
        group_name = cn("ENTERPRISE DOMAIN CONTROLLERS",domain)
        session.run(
            'MERGE (n:Domain {name:$domain}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GetChanges]->(n)', domain=domain, gname=group_name)
        group_name = cn("DOMAIN CONTROLLERS",domain)
        session.run(
            'MERGE (n:Domain {name:$domain}) WITH n MERGE (m:Group {name:$gname}) WITH n,m MERGE (m)-[:GetChangesAll]->(n)', domain=domain, gname=group_name)
        

        

        #Generate an administrator for the root domain
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
        
        #Generate a domain controller for the root domain
        group_name = cn("DOMAIN CONTROLLERS",domain)
        comp_name = cn(f"DC-root-",domain)
        sid = cs(1000,domain)
        session.run(
            'MERGE (n:Base {objectid:$sid}) SET n:Computer,n.name=$name,n.Domain=$domain WITH n MATCH (m:Group {name:$gname}) WITH n,m MERGE (n)-[:MemberOf]->(m)', sid=sid,domain = domain, name=comp_name, gname=group_name)
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
        session.run('MATCH (n:User) SET n.owned=false')
        session.run('MATCH (n:Computer) SET n.owned=false')
        session.run('MATCH (n) WHERE n.Domain IS NULL SET n.Domain=$domain', domain=domain)
        #ACCOUNT OPERATORS can modfify accounts of most groups 
        all_groups = session.run("""MATCH (n:Group) WHERE not(n.name CONTAINS "ADMINISTRATORS") AND (n.name CONTAINS $domain_name) AND not((n)-[:MemberOf]->(:Group{name:$gname}))
                                        RETURN n.name""",domain_name = domain,gname=cn("ADMINISTRATORS",domain))  
        for temp in all_groups:
            session.run(
            'MERGE (n:Group {name:$gname}) WITH n MERGE (m:Group {name:$mname}) WITH n,m MERGE (n)-[:GenericAll {isacl:true}]->(m)', gname=cn("ACCOUNT OPERATORS",domain), mname=temp["n.name"])

class Load_settings:
    def __init__(self):
        file = open("AD_settings.txt", 'r')
        self.whole_settings = file.read().split('\n\n')
        base_dict = {}
        for line in self.whole_settings[0].split('\n'):
            if '=' in line:
                k, v = line.strip().split('=')
                base_dict[k.strip()] = v.strip()
        self.setting = base_dict

country_list = ['ar_AA','ar_AE','ar_BH','ar_EG','ar_JO','ar_PS','ar_SA','az_AZ','bg_BG','bn_BD','bs_BA','cs_CZ','da_DK','de_AT','de_CH','de_DE','dk_DK','el_CY','el_GR'
'en','en_AU','en_CA','en_GB','en_IE''en_IN','en_NZ','en_PH','en_TH','en_US','es_CA','es_CL'
'es_CO','es_ES','es_MX','et_EE','fa_IR','fi_FI','fil_PH','fr_CA','fr_CH','fr_FR',
'ga_IE','he_IL','hi_IN','hr_HR','hu_HU','hy_AM','id_ID','it_CH','it_IT',
'ja_JP','ka_GE','ko_KR','lb_LU','lt_LT','lv_LV','mt_MT','ne_NP','nl_BE','nl_NL','no_NO','or_IN',
'pl_PL','pt_BR','pt_PT','ro_RO','ru_RU','sk_SK','sl_SI','sq_AL''sv_SE','ta_IN','th_TH','tl_PH','tr_TR','tw_GH','uk_UA','vi_VN','zh_CN','zh_TW']


if __name__ == '__main__':
    do_cleardb()
    AD_settings = Load_settings()
    setting_dict = AD_settings.setting
    url = setting_dict['url']
    username = setting_dict['username']
    password = setting_dict['password']
    base_sid = 'S-1-5-21-987213679-315867604-3049297612'
    driver = GraphDatabase.driver(url, auth=(username,password))
    session = driver.session()
    print ("Generateing the root domain")
    domain = str(setting_dict['domain'])+".COM"
    generate_standard_nodes(driver,domain,base_sid)
    num_users = int(setting_dict['num_users'])
    num_pcs = int(setting_dict['num_PCs'])
    overseas_users = []
    overseas_PCs = []
    Countries = random.sample(country_list, int(setting_dict['num_child_domain']))
    for i in range(int(setting_dict['num_child_domain'])):
        print ("Generateing the "+ str(i+1) + " child domain")
        Security_level = random.choice(['High','Medium','Low'])
        country = Countries[i]
        domain = country+".LOCAL"
        states = [Faker(country).country_code() for _ in range(random.randint(3, 6))]
        last_sid = random.randint(1000000000,9999999999)
        root_sid = 'S-1-5-21-' + str(random.randint(100000000,999999999))+'-'+str(random.randint(100000000,999999999))
        if Security_level == 'Low':
            temp_pc,temp_user = generate_low(driver,domain,root_sid,states,country,Security_level,num_users,num_pcs)
            session.run(
                'MERGE (n:Domain {objectid:$root_id}) WITH n MERGE (m:Domain {objectid:$sid}) WITH n,m MERGE (m)-[:TrustedBy{isacl:false}]->(n)',root_id = root_sid,sid = base_sid)
            session.run(
                'MERGE (n:Domain {objectid:$root_id}) WITH n MERGE (m:Domain {objectid:$sid}) WITH n,m MERGE (n)-[:TrustedBy{isacl:false}]->(m)',root_id = root_sid,sid = base_sid)
        else:
            temp_pc,temp_user =generate_AD(driver,domain,root_sid,states,country,Security_level,num_users,num_pcs)
            session.run(
                'MERGE (n:Domain {objectid:$root_id}) WITH n MERGE (m:Domain {objectid:$sid}) WITH n,m MERGE (m)-[:TrustedBy{isacl:false}]->(n)',root_id = root_sid,sid = base_sid)
            session.run(
                'MERGE (n:Domain {objectid:$root_id}) WITH n MERGE (m:Domain {objectid:$sid}) WITH n,m MERGE (n)-[:TrustedBy{isacl:false}]->(m)',root_id = root_sid,sid = base_sid)
        
        overseas_users.append(random.sample(temp_user,int(len(temp_user)*0.01)))
        overseas_PCs.append(random.sample(temp_user,int(len(temp_user)*0.01)))

    if setting_dict['Users_can_ login_overseas_computers'] == 'Y':
        for user in overseas_users:
            possible_log = random.randrange(1, 3)
            PCs = random.sample(overseas_PCs,possible_log)
            for pc in PCs:
                session.run('MERGE (n:User {name:$uname}) MERGE (m:Computer {name:$pcname}) WITH n,m MERGE (m)-[:HasSession]->(n)', uname=user,pcname = pc)
         

   
       
         


