# BloodHound Database Creator

This python script will generate a relastics active directory graph.

## Requirements

This script requires Python 3.7+, as well as the neo4j-driver. The script will only work with BloodHound 3.0.0 and above.

The Neo4j Driver can be installed using pip:

```
pip install neo4j-driver
```

or

```
pip install -r requirements.txt
```

## Running

Ensure that all files in this repo are in the same directory.
Change the varible in AD_settings file

```
python main.py
```

## AD_settings

- url - Set the credentials and URL for the database you're connecting to
- model  - Set the AD model(Single/Multiple)
- Security_level  - Set the security level(High/Medium/Low) for the AD
- domain  - the domain name
- Country - the country which the domain located
- States  - the states of the country
- num_PCs  - number of PC nodes
- num_users   - number of User nodes
