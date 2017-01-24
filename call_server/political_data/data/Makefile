all: legislators-current.yaml us_districts.csv us_states.csv

clean:
	rm -rf -- *.csv *.yaml

us_congress_current.yaml :
	curl -k "https://raw.githubusercontent.com/unitedstates/congress-legislators/master/legislators-current.yaml" -o "us_congress_current.yaml"

us_districts.csv:
	curl -k "http://assets.sunlightfoundation.com/data/districts.csv" -o "us_districts.csv"

us_states.csv:
	curl -k "https://raw.githubusercontent.com/spacedogXYZ/us_governors_contact/master/data.csv" -o "us_states.csv"

ca_house_of_commons.csv:
	curl -k "http://represent.opennorth.ca.s3.amazonaws.com/csv/representatives/house-of-commons.csv" -o "ca_house_of_commons.csv"