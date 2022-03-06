# BloodHound Database Creator

This python script will generate a randomized data set for testing BloodHound features and analysis.

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

```
python ADCreator.py
```

## Commands

- dbconfig - Set the credentials and URL for the database you're connecting too
- connect - Connects to the database using supplied credentials
- setnodes - Set the number of nodes in each domain to generate (defaults to 500, this is a safe number!)
- setdomain - Set the domain name
- cleardb - Clears the database and sets the schema properly
- clear_and_generate - Connects to the database, clears the DB, sets the schema, and generates random data
- setmodel- Set the AD model(Single/Multiple)
- setSecurity_level - Set the security level(High/Medium/Low) for the AD
- exit - Exits the script
