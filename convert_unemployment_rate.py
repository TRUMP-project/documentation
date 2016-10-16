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
    with open(path,'r') as csvfile:

        csv_contents = csv_parser(filename)
        enum = 0
        graph_uri = URIRef('http://stardog.clariah-sdh.eculture.labs.vu.nl/databases/trump/resource/unemployment_eu_graph')  # The URI for our graph
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


            graph.add((country, RDF.type, VOCAB['Country']))
            graph.add((country, VOCAB['unemployment_rate'], unemployment_rate))


            dataset.add((unemployment_rate, VOCAB['gender'], gender))
            dataset.add((unemployment_rate, VOCAB['indicator_value'], unemployment_value))
            dataset.add((unemployment_rate, VOCAB['time_period'],date))
            dataset.add((unemployment_rate, VOCAB['country'], country))
            dataset.add((unemployment_rate, VOCAB['unit'], unit_value))

            enum += 1

    return dataset, graph



def serialize_upload(filename, dataset, upload=True):
    print filename
    with open(filename, 'w') as f:
        dataset.serialize(f, format='trig')

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

graph_uri_base = resource + 'unemployment_rate/'

path = 'source_datasets/'
filename = 'unemployment_eu.csv'

dataset = Dataset()
dataset.bind('trumpres', RESOURCE)
dataset.bind('trumpvoc', VOCAB)
dataset.bind('geo', GEO)
dataset.bind('dbo', DBO)
dataset.bind('dbr', DBR)
dataset.bind('sdmx', SDMX)

dataset.default_context.parse(VOCAB_FILE, format='turtle')

dataset, unemployment_eu_graph = convert_unemployment_csv(filename,dataset,URIRef(graph_uri_base + 'unemployment_eu_graph'))
serialize_upload(OUTPUT_DIR + 'unemployment_eu.trig',dataset)

'''
### Generate VoID metadata
from rdflib.void import generateVoID
from rdflib.namespace import VOID
dcterms_uri = 'http://purl.org/dc/terms/'
DCTERMS = Namespace(dcterms_uri)

# Asylum seekers
void_dataset_asylum = URIRef(graph_uri_base + 'void')
void_g_asylum, _ = generateVoID(asylum_graph, dataset=void_dataset_asylum)
serialize_upload(OUTPUT_DIR + 'void_asylum.trig', void_g_asylum)

# Generate linked dataset
void_linked_ds = URIRef(graph_uri_base + 'void')
void_linked_g = Graph()
void_linked_g.add((void_linked_ds, RDF.type, VOID.Linkset))
void_linked_g.add((void_linked_ds, VOID.target, void_dataset_asylum))
void_linked_g.add((void_linked_ds, VOID.sparqlEndpoint, URIRef('http://stardog.clariah-sdh.eculture.labs.vu.nl/test#!/query')))
void_linked_g.add((void_linked_ds, DCTERMS['license'], URIRef('http://creativecommons.org/publicdomain/zero/1.0/')))
void_linked_g.add((void_linked_ds, DCTERMS['subject'], DBR['Asylum_seekers']))
void_linked_g.add((void_linked_ds, DCTERMS['title'], Literal('The unified migration portal, asylum seekers in the city of Amsterdam')))
void_linked_g.add((void_linked_ds, DCTERMS['source'], URIRef('https://www.cbs.nl/')))
void_linked_g.add((void_linked_ds, DCTERMS['description'],
    Literal('A linked dataset on migration, movement of people across countries and asylum seekers specifically in the Netherlands', lang='en')))
void_linked_g.add((void_linked_ds, VOID.exampleResource, VOCAB['asylum_seekers']))
serialize_upload(OUTPUT_DIR + 'void_linked_asylum.trig', void_linked_g)
'''
