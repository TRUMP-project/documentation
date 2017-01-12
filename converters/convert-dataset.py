# coding=utf-8
import csv
from csv import DictReader
import numpy as np
import pandas as pd
from datetime import datetime
import locale
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

geo = 'http://www.w3.org/2003/01/geo/wgs84_pos#'
GEO = Namespace(geo)
dbo = 'http://dbpedia.org/ontology/'
DBO = Namespace(dbo)
dbr = 'http://dbpedia.org/resource/'
DBR = Namespace(dbr)
prov= 'http://www.w3.org/ns/prov#'

repo_url = "http://localhost:5820/test"

VOCAB_FILE = 'ontologies/version_V1.0.ttl'
SOURCE_DATA_DIR = '../source_datasets/'
OUTPUT_DIR = 'data/'

def convert_csv(path, dataset, graph_uri):
    with open(path,'r') as csvfile:
        csv_contents = csv_parser(filename)

        graph_uri = URIRef('http://localhost:5820/test/resource/movement_graph')  # The URI for our graph
        graph = dataset.graph(graph_uri)                                   # new graph object with our URI from the dataset

        for row in csv_contents[2:]:
            # Pre processing of the data + creation of triples
            country = URIRef(to_iri(dbr + row['Country'].strip()))
            country_name = Literal(row['Country'].strip(), datatype=XSD['string'])

            net_migration = URIRef(to_iri(resource + row['Net migration'].strip()))
            try:
                net_migration_value = Literal((int(row['Net migration']) * 1000), datatype=XSD['int'])
            except Exception as e:
                net_migration_value = Literal('N/A',datatype=XSD['string'])

            international_migrant_stock = URIRef(to_iri(resource + row['International migrant stock'].strip()))
            try:
                international_migrant_stock_value = Literal((int(row['International migrant stock']) * 1000), datatype=XSD['int'])
            except Exception as e:
                international_migrant_stock_value = Literal('N/A',datatype=XSD['string'])

            tetriary_educated_emigration = URIRef(to_iri(resource + \
            row['Emigration rate of tertiary educated to OECD countries'].strip()))
            try:
                tetriary_educated_emigration_value_prct = float(row['Emigration rate of tertiary educated to OECD countries'])
                tetriary_educated_emigration_value_prct = Literal(tetriary_educated_emigration_value_prct, datatype=XSD['float'])
            except Exception as e:
                tetriary_educated_emigration_value_prct = Literal('N/A',datatype=XSD['string'])

            refugees_by_country_of_origin = URIRef(to_iri(resource + \
            row['Refugees By country of origin'].strip()))
            try:
                refugees_by_country_of_origin_value = int(float(row['Refugees By country of origin']) * 1000) # make them thousands
                refugees_by_country_of_origin_value = Literal(refugees_by_country_of_origin_value, datatype=XSD['int'])
            except Exception as e:
                refugees_by_country_of_origin_value = Literal('N/A', datatype=XSD['string'])

            refugees_by_country_of_asylum = URIRef(to_iri(resource + \
            row['Refugees By country of asylum'].strip()))
            try:
                refugees_by_country_of_asylum_value = int(float(row['Refugees By country of asylum']) * 1000) # make them thousands and int
                refugees_by_country_of_asylum_value = Literal(refugees_by_country_of_asylum_value, datatype=XSD['int'])
            except Exception as e:
                refugees_by_country_of_asylum_value = Literal('N/A', datatype=XSD['string'])

            personal_remittances_received = URIRef(to_iri(resource + row['Personal remittances received'].strip()))
            try:
                personal_remittances_received_value = long(row['Personal remittances received']) * 1000000 # make them millions and int
                personal_remittances_received_value = Literal(personal_remittances_received_value, datatype=XSD['long'])
            except Exception as e:
                personal_remittances_received_value = Literal('N/A', datatype=XSD['string'])

            personal_remittances_paid = URIRef(to_iri(resource + row['Personal remittances paid'].strip()))
            try:
                personal_remittances_paid_value = long(row['Personal remittances paid']) * 1000000 # make them millions
                personal_remittances_paid_value = Literal(personal_remittances_paid_value, datatype=XSD['long']) # turn it back to int
            except Exception as e:
                personal_remittances_paid_value = Literal('N/A', datatype=XSD['string'])

            # Add data to graph_uri_base
            graph.add((country, RDF.type, VOCAB['Country']))
            graph.add((country, RDFS.label, country_name))
            graph.add((country, VOCAB['net_migration'], net_migration_value))
            graph.add((country, VOCAB['international_migrant_stock'], international_migrant_stock_value))
            graph.add((country, VOCAB['emmigration_rate_to_OECD'], tetriary_educated_emigration_value_prct))
            graph.add((country, VOCAB['refugees_by_country_of_origin'],refugees_by_country_of_origin_value))
            graph.add((country, VOCAB['refugees_by_country_of_asylum'],refugees_by_country_of_asylum_value))
            graph.add((country, VOCAB['personal_remittances_received'],personal_remittances_received_value))
            graph.add((country, VOCAB['personal_remittances_paid'], personal_remittances_paid_value))

            dataset.add((country, RDF.type, VOCAB['Country']))
            dataset.add((country, RDFS.label, country_name))

            dataset.add((net_migration, RDF.type , VOCAB['Net_migration']))
            dataset.add((net_migration, VOCAB['value'], net_migration_value))
            dataset.add((net_migration, VOCAB['year'], Literal('2012', datatype=XSD['gYear'])))

            dataset.add((international_migrant_stock, RDF.type, VOCAB['International_migrant_stock']))
            dataset.add((international_migrant_stock,VOCAB['value'],international_migrant_stock_value))
            dataset.add((international_migrant_stock, VOCAB['year'], Literal('2010', datatype=XSD['gYear'])))

            dataset.add((tetriary_educated_emigration,RDF.type,VOCAB['Emmigration_rate_to_OECD']))
            dataset.add((tetriary_educated_emigration, VOCAB['value'], tetriary_educated_emigration_value_prct))
            dataset.add((tetriary_educated_emigration, VOCAB['year'], Literal('2000', datatype=XSD['gYear'])))

            dataset.add((refugees_by_country_of_origin,RDF.type,VOCAB['Refugees_by_country_of_origin']))
            dataset.add((refugees_by_country_of_origin, VOCAB['value'], refugees_by_country_of_origin_value))
            dataset.add((refugees_by_country_of_origin, VOCAB['year'], Literal('2014', datatype=XSD['gYear'])))

            dataset.add((refugees_by_country_of_asylum,RDF.type,VOCAB['Refugees_by_country_of_asylum']))
            dataset.add((refugees_by_country_of_asylum, VOCAB['value'],
            refugees_by_country_of_asylum_value))
            dataset.add((refugees_by_country_of_asylum, VOCAB['year'], Literal('2014', datatype=XSD['gYear'])))

            dataset.add((personal_remittances_received,RDF.type,VOCAB['Personal_remittances_received']))
            dataset.add((personal_remittances_received, VOCAB['value'],
            personal_remittances_received_value))
            dataset.add((personal_remittances_received, VOCAB['year'], Literal('2014', datatype=XSD['gYear'])))

            dataset.add((personal_remittances_received,RDF.type,VOCAB['Personal_remittances_paid']))
            dataset.add((personal_remittances_paid,VOCAB['value'],personal_remittances_paid_value))
            dataset.add((personal_remittances_received, VOCAB['year'], Literal('2014', datatype=XSD['gYear'])))

    info = u'FrÃ©dÃ©ric Docquier, B. Lindsay Lowell, and Abdeslam Marfouk'+'s' +', "A Gendered Assessment of Highly Skilled Emigration" (2009)'.decode('utf-8')

    graph.add((VOCAB['net_migration'], URIRef(to_iri(prov + 'wasDerivedFrom')),
    Literal('United Nations Population Division, World Population Prospects', datatype=XSD['string'])))

    graph.add((VOCAB['international_migrant_stock'], URIRef(to_iri(prov + 'wasDerivedFrom')),
    Literal('United Nations Population Division, Trends in Total Migrant Stock: 2012 Revision.', datatype=XSD['string'])))

    graph.add((VOCAB['tetriary_educated_emigration'], URIRef(to_iri(prov + 'wasDerivedFrom')),
    Literal(info, datatype=XSD['string'])))

    graph.add((VOCAB['refugees_by_country_of_origin'], URIRef(to_iri(prov + 'wasDerivedFrom')),
    Literal('United Nations High Commissioner for Refugees (UNHCR), Statistical Yearbook and data files, \
    complemented by statistics on Palestinian refugees under the mandate of the UNRWA as published on its website.\
    Data from UNHCR are available online at: www.unhcr.org/statistics/populationdatabase.', datatype=XSD['string'])))

    graph.add((VOCAB['refugees_by_country_of_asylum'], URIRef(to_iri(prov + 'wasDerivedFrom')),
    Literal('United Nations High Commissioner for Refugees (UNHCR), Statistical Yearbook and data files, \
    complemented by statistics on Palestinian refugees under the mandate of the UNRWA as published on its website. \
    Data from UNHCR are available online at: www.unhcr.org/statistics/populationdatabase.', datatype=XSD['string'])))

    graph.add((VOCAB['personal_remittances_received'], URIRef(to_iri(prov + 'wasDerivedFrom')),
    Literal('World Bank staff estimates based on IMF balance of payments data.', datatype=XSD['string'])))

    graph.add((VOCAB['personal_remittances_paid'], URIRef(to_iri(prov + 'wasDerivedFrom')),
    Literal('World Bank staff estimates based on IMF balance of payments data.', datatype=XSD['string'])))

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

graph_uri_base = resource + 'movement_of_people/'


path = 'source_datasets/'
filename = 'Movement_of_people_across_borders_dataset.csv'

dataset = Dataset()
dataset.bind('trumpres', RESOURCE)
dataset.bind('trumpvoc', VOCAB)
dataset.bind('geo', GEO)
dataset.bind('dbo', DBO)
dataset.bind('dbr', DBR)

dataset.default_context.parse(VOCAB_FILE, format='turtle')

dataset, movement_graph = convert_csv(path + filename,dataset,URIRef(graph_uri_base + 'movement_graph'))
serialize_upload(OUTPUT_DIR + 'movement_of_people.trig',dataset)



### Generate VoID metadata
from rdflib.void import generateVoID
from rdflib.namespace import VOID
dcterms_uri = 'http://purl.org/dc/terms/'
DCTERMS = Namespace(dcterms_uri)

# Movement of people
void_dataset_movement = URIRef(graph_uri_base + 'void')
void_g_movement, _ = generateVoID(movement_graph, dataset=void_dataset_movement)
serialize_upload(OUTPUT_DIR + 'void_movement.trig', void_g_movement)

# Generate linked dataset
void_linked_ds = URIRef(graph_uri_base + 'void')
void_linked_g = Graph()
void_linked_g.add((void_linked_ds, RDF.type, VOID.Linkset))
void_linked_g.add((void_linked_ds, VOID.target, void_dataset_movement))
void_linked_g.add((void_linked_ds, VOID.sparqlEndpoint, URIRef('http://stardog.clariah-sdh.eculture.labs.vu.nl/test#!/query')))
void_linked_g.add((void_linked_ds, DCTERMS['license'], URIRef('http://creativecommons.org/publicdomain/zero/1.0/')))
void_linked_g.add((void_linked_ds, DCTERMS['subject'], DBR['Movement_of_people']))
void_linked_g.add((void_linked_ds, DCTERMS['title'], Literal('The unified migration portal, movement of people')))
void_linked_g.add((void_linked_ds, DCTERMS['source'], URIRef('http://worldbank.org/')))
void_linked_g.add((void_linked_ds, DCTERMS['description'],
    Literal('A linked dataset on migration, movement of people across countries and asylum seekers specifically in the Netherlands', lang='en')))
void_linked_g.add((void_linked_ds, VOID.exampleResource, VOCAB['Country']))
serialize_upload(OUTPUT_DIR + 'void_linked.trig', void_linked_g)
