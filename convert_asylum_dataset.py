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
resource = 'http://localhost:5820/test/resource/'
RESOURCE = Namespace(resource)

# A namespace for our vocabulary items (schema information, RDFS, OWL classes and properties etc.)
vocab = 'http://localhost:5820/test/vocab/'
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
repo_url = "http://localhost:5820/test"

VOCAB_FILE = 'ontologies/version_V1.2.ttl'
SOURCE_DATA_DIR = '../source_datasets/'
OUTPUT_DIR = 'data/'


def convert_asylum_csv(path, dataset):
    with open(path,'r') as csvfile:
        country = URIRef(to_iri(dbr + 'Kingdom of the Netherlands'))
        csv_contents = csv_parser(filename)
        enum = 0
        graph_uri = URIRef('http://localhost:5820/test/resource/asylumGraph')  # The URI for our graph
        graph = dataset.graph(graph_uri)                                   # new graph object with our URI from the dataset

        for row in csv_contents[1:]:
            # Pre processing of the data + creation of triples
            asylum_seeker = URIRef(to_iri(resource + str(enum)))
            try:
                gender = row['Geslacht'].strip()
                if gender == 'Vrouwen':
                    gender = URIRef(to_iri(sdmx_code + 'sex-F'))
                else:
                    gender = URIRef(to_iri(sdmx_code + 'sex-M'))
            except Exception as e:
                gender =  Literal('N/A', datatype= XSD['string'])

            try:
                nationality_value = Literal(row['Nationaliteit'].strip(), lang = 'nl')
                nationality = URIRef(to_iri(resource + nationality_value ))
            except Exception as e:
                nationality = Literal('N/A', datatype= XSD['string'])

            #Preprocess dates
            temp_date = row['Perioden']
            date = temp_date.split()
            year = date[0].strip()
            month = date[1] if date[1] != '' else None

            test = dateparser.parse(row['Perioden'], languages=['nl','en'])
            if test.month/5 >= 2:
                temp_date = str(test.year) +'-'+ str(test.month)
            else:
                temp_date = str(test.year) +'-'+'0'+str(test.month)

            try:
                date = Literal(temp_date,datatype=XSD['gYearMonth'])
            except Exception as e:
                date = Literal('N/A', datatype= XSD['string'])

            try:
                value = Literal(row['aantal'].strip(), datatype= XSD['integer'])
            except Exception as e:
                value = Literal('N/A', datatype= XSD['string'])

            graph.add((country, RDF.type, VOCAB['Country']))
            graph.add((country, VOCAB['asylum_seekers'], asylum_seeker))

            dataset.add((asylum_seeker, VOCAB['gender'], gender))
            dataset.add((asylum_seeker, VOCAB['nationality'], nationality))
            dataset.add((asylum_seeker, VOCAB['application_country'],country))
            dataset.add((asylum_seeker, VOCAB['application_period'], date))
            dataset.add((asylum_seeker, VOCAB['value'], value))

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
        # for line in csvreader:
        #         for str in range(0,len(line)):
        #             line[str] = strip_tags(line[str])
        #             line[str] = unicode(line[str], errors='replace')
        #         #print line
    with open(filename,'r') as csvfile:
        csv_contents = [{k: v for k, v in row.items()}
            for row in csv.DictReader(csvfile, skipinitialspace=True, quotechar='"', delimiter=',')]
    return csv_contents
#//*************** csv parser ****************//#


path = 'source_datasets/'
filename = 'asylum_seekers.csv'

dataset = Dataset()
dataset.bind('trumpres', RESOURCE)
dataset.bind('trumpvoc', VOCAB)
dataset.bind('geo', GEO)
dataset.bind('dbo', DBO)
dataset.bind('dbr', DBR)
dataset.bind('sdmx', SDMX)

dataset.default_context.parse(VOCAB_FILE, format='turtle')

dataset, t_graph = convert_asylum_csv(filename,dataset)
serialize_upload(OUTPUT_DIR + 'asylum_seekers.trig',dataset)
