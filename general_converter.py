import csv
from csv import DictReader
import numpy as np
import pandas as pd
from datetime import datetime
import dateparser
from rdflib import Dataset, Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL, XSD
from iribaker import to_iri
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from pprint import pprint

# A namespace for our resources
resource = 'http://stardog.clariah-sdh.eculture.labs.vu.nl/databases/trump/resource/'
RESOURCE = Namespace(resource)

# A namespace for our vocabulary items (schema information, RDFS, OWL classes and properties etc.)
vocab = 'http://stardog.clariah-sdh.eculture.labs.vu.nl/databases/trump/vocab/'
VOCAB = Namespace(vocab)

# The namespaces of external ontologies
geo = 'http://www.w3.org/2003/01/geo/wgs84_pos#'
GEO = Namespace(geo)
dbo = 'http://dbpedia.org/ontology/'
DBO = Namespace(dbo)
dbr = 'http://dbpedia.org/resource/'
DBR = Namespace(dbr)
sdmx_code = 'http://purl.org/linked-data/sdmx/2009/code#'
SDMX = Namespace(sdmx_code)

# Our repository url
repo_url = "http://stardog.clariah-sdh.eculture.labs.vu.nl/databases/trump"

VOCAB_FILE = 'ontologies/the_migration_portal.ttl'
SOURCE_DATA_DIR = '../source_datasets/'
OUTPUT_DIR = 'data/'

def convert_unemployment_csv(path, dataset, graph_uri):
    filename = path
    with open(path,'r') as csvfile:

        csv_contents = csv_parser(filename)
        enum = 0
        #graph_uri = URIRef('http://stardog.clariah-sdh.eculture.labs.vu.nl/databases/trump/resource/unemployment_graph')  # The URI for our graph
        graph = dataset.graph(graph_uri)                                   # new graph object with our URI from the dataset

        for row in csv_contents[1:]:
            # Pre processing of the data + creation of triples
            country = URIRef(to_iri(dbr + row['GEO'].strip()))
            country_name = Literal(row['GEO'].strip(), datatype=XSD['string'])

            unemployment_rate = URIRef(to_iri(resource + 'Unemployment_rate' + str(enum)))
            try:
                gender = row['SEX'].strip()
                gender = URIRef(to_iri(sdmx_code + 'Total'))
            except Exception as e:
                gender =  Literal('N/A', datatype= XSD['string'])

            #Preprocess dates
            temp_date = row['TIME'].strip()
            try:
                date = Literal(temp_date,datatype=XSD['gYear'])
            except Exception as e:
                date = Literal('N/A', datatype= XSD['string'])

            try:
                unemployment_value = Literal(row['Value'].strip(), datatype= XSD['float'])
            except Exception as e:
                unemployment_value = Literal('N/A', datatype= XSD['string'])

            try:
                unit = row['UNIT']
                if 'total' in unit:
                    unit_value = Literal('Total population', datatype = XSD['string'])
                else:
                    unit_value = Literal('Active population', datatype = XSD['string'])
            except Exception as e:
                unit = Literal('N/A', datatype = XSD['string'])

            try:
                age_group = Literal(row['AGE'].strip(), datatype = XSD['string'])
            except Exception as e:
                age_group = Literal('N/A', datatype = XSD['string'])


            print 'Country : '+ country_name + ', in year ' + date + ', had unemployment rate : ' \
            + unemployment_value + ', for age group : '+ age_group + ', unit : ' + unit_value


            dataset.add((country, RDF.type, DBO['Country']))
            dataset.add((country, RDFS.label, country_name))
            dataset.add((country, VOCAB['unemployment_rate'], unemployment_rate))

            graph.add((unemployment_rate, RDF.type, VOCAB['Unemployment_rate']))
            graph.add((unemployment_rate, VOCAB['gender'], gender))
            graph.add((unemployment_rate, VOCAB['indicator_value'], unemployment_value))
            graph.add((unemployment_rate, VOCAB['time_period'],date))
            graph.add((unemployment_rate, VOCAB['country'], country))
            graph.add((unemployment_rate, VOCAB['unit'], unit_value))

            enum += 1

    return dataset, graph

def convert_population_csv(path, dataset, graph_uri):
    filename = path
    with open(path,'r') as csvfile:
        csv_contents = csv_parser(filename)
        enum = 0
        #graph_uri = URIRef('http://stardog.clariah-sdh.eculture.labs.vu.nl/databases/trump/resource/population_graph')  # The URI for our graph
        graph = dataset.graph(graph_uri)                                   # new graph object with our URI from the dataset

        for row in csv_contents[1:]:
            # Pre processing of the data + creation of triples
            country = URIRef(to_iri(dbr + row['GEO'].strip()))
            country_name = Literal(row['GEO'].strip(), datatype=XSD['string'])
            population = URIRef(to_iri(resource + 'Population' + str(enum)))
            try:
                gender = row['SEX'].strip()
                gender = URIRef(to_iri(sdmx_code + 'Total'))
            except Exception as e:
                gender =  Literal('N/A', datatype= XSD['string'])

            #Preprocess dates
            temp_date = row['TIME'].strip()
            try:
                date = Literal(temp_date,datatype=XSD['gYear'])
            except Exception as e:
                date = Literal('N/A', datatype= XSD['string'])

            try:
                temp = row['Value'].strip().replace(',','')
                if temp == ':':
                    pass
                else:
                    population_value = Literal(temp, datatype= XSD['Integer'])
            except Exception as e:
                population_value = Literal('N/A', datatype= XSD['string'])

            try:
                age_group = Literal(row['AGE'].strip(), datatype = XSD['string'])
            except Exception as e:
                age_group = Literal('N/A', datatype = XSD['string'])

            print 'Country : '+ country_name + ', in year ' + date + ', had population : ' \
            + population_value + ', for age group : '+ age_group


            dataset.add((country, RDF.type, DBO['Country']))
            dataset.add((country, RDFS.label, country_name))
            dataset.add((country, VOCAB['population'], population))

            graph.add((population, RDF.type, VOCAB['Population']))
            graph.add((population, VOCAB['country'], country))
            graph.add((population, VOCAB['gender'], gender))
            graph.add((population, VOCAB['population_value'], population_value))
            graph.add((population, VOCAB['time_period'],date))

            enum += 1

    return dataset, graph

def convert_inflow_csv(path, dataset, graph_uri):
    filename = path
    with open(path,'r') as csvfile:
        csv_contents = csv_parser(filename)
        pd.read_csv("source_datasets/inflow_dataset.csv")
        enum = 0
        graph_uri = URIRef('http://stardog.clariah-sdh.eculture.labs.vu.nl/databases/trump/resource/inflow_graph')  # The URI for our graph
        graph = dataset.graph(graph_uri)  # new graph object with our URI from the dataset

        for row in csv_contents[1:]:
            # Pre processing of the data + creation of triples
            from_country_code = URIRef(to_iri(dbr + row['Code'].strip()))

            temp_from_country_name = row['Country of birth/nationality'].strip().replace(",","")

            from_country = URIRef(to_iri(dbr + temp_from_country_name))
            from_country_name = Literal(temp_from_country_name, datatype=XSD['string'])

            to_counry_code = URIRef(to_iri(dbr + row['COU'].strip()))

            temp_to_country_name = row['Country'].strip().replace(",","")
            to_country =  URIRef(to_iri(dbr + temp_to_country_name ))
            to_country_name = Literal(temp_to_country_name, datatype=XSD['string'])

            inflow = URIRef(to_iri(resource + 'Inflow' + str(enum)))

            try:
                gender = row['Gender'].strip()
                gender = URIRef(to_iri(sdmx_code + 'Total'))
            except Exception as e:
                gender =  Literal('N/A', datatype= XSD['string'])

            #Preprocess dates
            try:
                date = Literal(row['Year'].strip(),datatype=XSD['gYear'])
            except Exception as e:
                date = Literal('N/A', datatype= XSD['string'])

            try:
                inflow_value = int(row['Value'].strip())
                #print type(inflow_value)
                if isinstance(inflow_value, int):
                #    print "This number is an int"
                    inflow_value = Literal(row['Value'].strip(), datatype= XSD['integer'])
                else:
                    #print "This number is a int"
                    inflow_value = Literal(inflow_value, datatype= XSD['float'])
            except Exception as e:
                inflow_value = Literal('N/A', datatype= XSD['string'])

            #print 'From Country : '+ from_country_name + ' to country ' + to_country_name + ', in year ' + date + ', inflow value : ' \
            #+ inflow_value
            print 'Converting row' + str(enum)

            dataset.add((from_country, RDF.type, DBO['Country']))
            dataset.add((from_country, RDFS.label, from_country_name))
            dataset.add((from_country, VOCAB['country_code'], from_country_code))

            graph.add((inflow, RDF.type, VOCAB['Inflow_of_population']))

            graph.add((inflow, VOCAB['to_country'], to_country))
            graph.add((inflow, VOCAB['from_country'], from_country))
            graph.add((inflow, VOCAB['movement_time_period'], date))
            graph.add((inflow, VOCAB['movement_value'], inflow_value))
            graph.add((inflow, VOCAB['gender'], gender))

            enum += 1

    return dataset, graph


def upload_to_stardog(data,repo_url):
    transaction_begin_url = repo_url + "/transaction/begin"
    print transaction_begin_url

    # Start the transaction, and get a transaction_id
    response = requests.post(transaction_begin_url, headers={'Accept': 'text/plain'})
    print response
    transaction_id = response.content
    print 'Transaction ID', transaction_id

    # POST the data to the transaction
    post_url = repo_url + "/" + transaction_id + "/add"
    response = requests.post(post_url, data=data, headers={'Accept': 'text/plain', 'Content-type': 'application/trig'})

    # Close the transaction
    transaction_close_url = repo_url + "/transaction/commit/" + transaction_id
    response = requests.post(transaction_close_url)

    return str(response.status_code)

#************* uploader + creation of trig ************#
def serialize_upload(filename, dataset, upload=True):
    print filename
    with open(filename, 'w') as f:
        dataset.serialize(f, format='trig')

#//************* uploader + creation of trig ************//#

#***************** csv parser ****************#
def csv_parser(filename):
    with open(filename,'r') as csvfile:
        csvreader = csv.reader(csvfile,quotechar='"',delimiter=',')
        # If the first row contains header information, we can retrieve it like so:
        header = csvreader.next()
        print header
    with open(filename,'r') as csvfile:
        csv_contents = [{k: v for k, v in row.items()}
            for row in csv.DictReader(csvfile, skipinitialspace=True, quotechar='"', delimiter=',')]
    return csv_contents
#//*************** csv parser ****************//#

graph_uri_base = resource

path = 'source_datasets/'
filename_population = 'population_eu.csv'
filename_unemployment = 'unemployment_eu.csv'
filename_inflow = 'inflow_dataset.csv'

dataset = Dataset()
dataset.bind('trumpres', RESOURCE)
dataset.bind('trumpvoc', VOCAB)
dataset.bind('geo', GEO)
dataset.bind('dbo', DBO)
dataset.bind('dbr', DBR)
dataset.bind('sdmx', SDMX)

dataset.default_context.parse(VOCAB_FILE, format='turtle')

dataset, unemployment_eu_graph = convert_unemployment_csv(filename_unemployment,dataset,URIRef(graph_uri_base + 'unemployment_eu_graph'))

dataset, population_eu_graph = convert_population_csv(filename_population,dataset,URIRef(graph_uri_base + 'population_eu_graph'))

dataset, inflow_graph = convert_inflow_csv(filename_inflow,dataset,URIRef(graph_uri_base + 'inflow_graph'))


#serialize_upload(OUTPUT_DIR + 'merged_dataset_population_unemployment.trig',dataset)
serialize_upload(OUTPUT_DIR + 'merged_dataset.trig',dataset)


#upload_to_stardog(dataset.serialize(format='trig'), "http://stardog.clariah-sdh.eculture.labs.vu.nl/#/databases/trump/")
