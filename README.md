# BloodHound Database Creator

This python script will generate a relastics active directory graph.

## Requirements

This script requires Python 3.7+, python Faker package as well as the neo4j-driver. The script will only work with BloodHound 3.0.0 and above.

The Neo4j Driver can be installed using pip:

```
pip install neo4j-driver
```
The Faker package can be installed using pip:

```
pip install Faker
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
- Country - the country which the domain located such as it_IT, en_US, ja_JP more options refer to https://faker.readthedocs.io/en/master/
- num_PCs  - number of PC nodes
- num_users   - number of User nodes
- num_child_domain - for Multiple domain model, the number of child doiains
- Users_can_ login_overseas_computers - Some user will has connect to the pc in other domain if this is set to Y
