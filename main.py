from neo4j import GraphDatabase
from Generate_standard_nodes import AD_settings
import networkx as nx
import pickle

if __name__ == '__main__':
    exec(open("Random_setting.py").read())
    exec(open("ADCreator.py").read())
    print("Saving the graph")
    setting_dict = AD_settings.setting
    driver = GraphDatabase.driver(setting_dict['url'], auth=(setting_dict['username'], setting_dict['password']))
    session = driver.session()  
    results = session.run("""MATCH (n)-[r]->(c) RETURN *""")
    G = nx.MultiDiGraph()
    nodes = list(results.graph()._nodes.values())
    for node in nodes:
        G.add_node(node.id, labels=node._labels, properties=node._properties)
    rels = list(results.graph()._relationships.values())
    for rel in rels:
        G.add_edge(rel.start_node.id, rel.end_node.id, key=rel.id, type=rel.type, properties=rel._properties)
    with open("./Data/graph.p", 'wb') as f:
        pickle.dump(G, f)
    print("Saving finished")






