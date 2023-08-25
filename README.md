
# objectchecker
Check for existing address objects and address groups and add them to Panorama if they don't already exist.

# Create a .env file
```
It should be created within the directory this repo was cloned into.
The .env file should contain:

	```
	'PAN_API_KEY=<YOUR PAN API KEY>'
	'DEVICE_GROUP=<THE DG THAT THE POLCIES NEED TO BE RANAMED ON>'
	'FW_HOST=<HOSTNAME OR IP ADDRESS OF PANORAMA>'
	```

```
# Build the dockerfile by running: 
```
docker build -t <The name youd like to apply to the docker container> .
	Example:
	docker build -t policyrenamer .

Once it's done building run:
	docker run --rm -it -v $(pwd):/scripts policyrenamer

You should now be inside of the docker container.

From within the docker container run:
	python3 grabandparse.py 
```
# check_address_object.py.py vs check_object_address_group.py.py
```
The names should be self explanatory:

Pay attention to the example csv's. check_address_object.py.py should be formatted in the way address_objects.csv is. 

check_object_address_group.py.py should be formatted in the same way address_groups.csv is. 

```
