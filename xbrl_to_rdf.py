from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS
from datetime import datetime
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XBRLToRDF:
    def __init__(self, xbrl_model):
        """
        Initialize XBRL to RDF converter.
        
        Args:
            xbrl_model: The loaded XBRL model object
        """
        if not xbrl_model:
            raise ValueError("XBRL model cannot be None")
        self.xbrl_model = xbrl_model
        self.errors = []

    def xbrl_to_rdf(self):
        """
        Translates an XBRL model to RDF format including concepts, facts, contexts, and relationships.
        
        Returns:
            rdflib.Graph: RDF graph containing the translated XBRL data
        """
        try:
            # Create RDF graph
            g = Graph()
            
            # Define namespaces
            XBRL = Namespace("http://www.xbrl.org/2003/instance#")
            XBRLI = Namespace("http://www.xbrl.org/2003/instance#")
            XBRLDT = Namespace("http://xbrl.org/2005/xbrldt#")
            XLINK = Namespace("http://www.w3.org/1999/xlink#")
            COMPANY = Namespace("http://example.com/company/")
            CONCEPT = Namespace("http://example.com/concepts/")
            FACT = Namespace("http://example.com/facts/")
            CONTEXT = Namespace("http://example.com/contexts/")
            REL = Namespace("http://example.com/relationships/")
            TAXONOMY = Namespace("http://example.com/taxonomy/")
            
            # Bind namespaces to graph
            g.bind("xbrl", XBRL)
            g.bind("xbrli", XBRLI)
            g.bind("xbrldt", XBRLDT)
            g.bind("xlink", XLINK)
            g.bind("company", COMPANY)
            g.bind("concept", CONCEPT)
            g.bind("fact", FACT)
            g.bind("context", CONTEXT)
            g.bind("rel", REL)
            g.bind("dcterms", DCTERMS)
            g.bind("taxonomy", TAXONOMY)
            
            # Create main document URI
            doc_uri = COMPANY["document"]
            g.add((doc_uri, RDF.type, XBRL.Instance))
            g.add((doc_uri, DCTERMS.created, Literal(datetime.now(), datatype=XSD.dateTime)))
            
            def translate_concepts():
                """Translate XBRL concepts to RDF"""
                try:
                    for concept in self.xbrl_model.qnameConcepts.values():
                        concept_uri = CONCEPT[concept.qname.localName]
                        
                        # Basic concept properties
                        g.add((concept_uri, RDF.type, XBRL.Concept))
                        g.add((concept_uri, RDFS.label, Literal(concept.qname.localName)))
                        
                        if hasattr(concept, 'label') and concept.label:
                            g.add((concept_uri, XBRL.standardLabel, Literal(concept.label)))
                        
                        # Type information
                        if hasattr(concept, 'type') and concept.type:
                            if concept.type.qname:
                                g.add((concept_uri, XBRL.type, Literal(concept.type.qname.localName)))
                        
                        # Period type
                        if hasattr(concept, 'periodType'):
                            g.add((concept_uri, XBRL.periodType, Literal(concept.periodType)))
                        
                        # Balance type for monetary items
                        if hasattr(concept, 'balance') and concept.balance:
                            g.add((concept_uri, XBRL.balance, Literal(concept.balance)))
                        
                        # Abstract indicator
                        if hasattr(concept, 'isAbstract'):
                            g.add((concept_uri, XBRL.abstract, Literal(concept.isAbstract, datatype=XSD.boolean)))
                        
                        # Substitution group
                        if hasattr(concept, 'substitutionGroup') and concept.substitutionGroup:
                            g.add((concept_uri, XBRL.substitutionGroup, Literal(concept.substitutionGroup.localName)))
                        
                except Exception as e:
                    print(f"Error translating concepts: {e}")
            
            def translate_contexts():
                """Translate XBRL contexts to RDF"""
                try:
                    for context_id, context in self.xbrl_model.contexts.items():
                        context_uri = CONTEXT[context_id]
                        
                        # Basic context properties
                        g.add((context_uri, RDF.type, XBRL.Context))
                        g.add((context_uri, XBRL.id, Literal(context_id)))
                        
                        # Entity information
                        if hasattr(context, 'entityIdentifier'):
                            entity_node = BNode()
                            g.add((context_uri, XBRL.entity, entity_node))
                            g.add((entity_node, RDF.type, XBRL.Entity))
                            
                            if context.entityIdentifier:
                                g.add((entity_node, XBRL.identifier, Literal(context.entityIdentifier[1])))
                                g.add((entity_node, XBRL.scheme, Literal(context.entityIdentifier[0])))
                        
                        # Period information
                        if hasattr(context, 'period'):
                            period_node = BNode()
                            g.add((context_uri, XBRL.period, period_node))
                            g.add((period_node, RDF.type, XBRL.Period))
                            
                            if context.isInstantPeriod:
                                g.add((period_node, XBRL.instant, Literal(context.instantDatetime, datatype=XSD.dateTime)))
                            elif context.isStartEndPeriod:
                                g.add((period_node, XBRL.startDate, Literal(context.startDatetime, datatype=XSD.dateTime)))
                                g.add((period_node, XBRL.endDate, Literal(context.endDatetime, datatype=XSD.dateTime)))
                        
                        # Dimensional information (segments)
                        if hasattr(context, 'qnameDims') and context.qnameDims:
                            for dim_qname, dim_value in context.qnameDims.items():
                                dim_node = BNode()
                                g.add((context_uri, XBRL.segment, dim_node))
                                g.add((dim_node, RDF.type, XBRL.Segment))
                                g.add((dim_node, XBRL.dimension, CONCEPT[dim_qname.localName]))
                                
                                if hasattr(dim_value, 'member') and dim_value.member:
                                    g.add((dim_node, XBRL.member, CONCEPT[dim_value.member.qname.localName]))
                                elif hasattr(dim_value, 'typedMember'):
                                    g.add((dim_node, XBRL.typedValue, Literal(str(dim_value.typedMember))))
                                    
                except Exception as e:
                    print(f"Error translating contexts: {e}")
            
            def translate_facts():
                """Translate XBRL facts to RDF"""
                try:
                    for fact in self.xbrl_model.facts:
                        fact_uri = FACT[str(uuid.uuid4())]
                        
                        # Basic fact properties
                        g.add((fact_uri, RDF.type, XBRL.Fact))
                        g.add((doc_uri, XBRL.hasFact, fact_uri))
                        
                        # Link to concept
                        if hasattr(fact, 'concept') and fact.concept:
                            g.add((fact_uri, XBRL.concept, CONCEPT[fact.concept.qname.localName]))
                        
                        # Link to context
                        if hasattr(fact, 'context') and fact.context:
                            g.add((fact_uri, XBRL.context, CONTEXT[fact.context.id]))
                        
                        # Fact value
                        if hasattr(fact, 'value') and fact.value is not None:
                            if fact.isNumeric:
                                # Numeric fact
                                g.add((fact_uri, XBRL.value, Literal(fact.value, datatype=XSD.decimal)))
                                
                                # Unit information
                                if hasattr(fact, 'unit') and fact.unit:
                                    unit_node = BNode()
                                    g.add((fact_uri, XBRL.unit, unit_node))
                                    g.add((unit_node, RDF.type, XBRL.Unit))
                                    
                                    # Handle unit measures
                                    if hasattr(fact.unit, 'measures') and fact.unit.measures:
                                        for measure_list in fact.unit.measures:
                                            for measure in measure_list:
                                                if hasattr(measure, 'localName'):
                                                    g.add((unit_node, XBRL.measure, Literal(measure.localName)))
                                
                                # Precision/Decimals
                                if hasattr(fact, 'precision') and fact.precision is not None:
                                    g.add((fact_uri, XBRL.precision, Literal(fact.precision)))
                                elif hasattr(fact, 'decimals') and fact.decimals is not None:
                                    g.add((fact_uri, XBRL.decimals, Literal(fact.decimals)))
                                    
                            else:
                                # Text fact
                                g.add((fact_uri, XBRL.value, Literal(str(fact.value))))
                        
                        # Footnotes
                        if hasattr(fact, 'footnotes') and fact.footnotes:
                            for footnote in fact.footnotes:
                                footnote_node = BNode()
                                g.add((fact_uri, XBRL.footnote, footnote_node))
                                g.add((footnote_node, RDF.type, XBRL.Footnote))
                                if hasattr(footnote, 'text'):
                                    g.add((footnote_node, XBRL.text, Literal(footnote.text)))
                                    
                except Exception as e:
                    print(f"Error translating facts: {e}")
            
            def translate_relationships():
                """Translate XBRL relationships to RDF"""
                try:
                    # Get all relationship sets
                    if hasattr(self.xbrl_model, 'relationshipSets'):
                        for arcrole, linkrole_dict in self.xbrl_model.relationshipSets.items():
                            for linkrole, rel_set in linkrole_dict.items():
                                for rel in rel_set.modelRelationships:
                                    rel_uri = REL[str(uuid.uuid4())]
                                    
                                    # Basic relationship properties
                                    g.add((rel_uri, RDF.type, XBRL.Relationship))
                                    g.add((doc_uri, XBRL.hasRelationship, rel_uri))
                                    
                                    # Arcrole and linkrole
                                    g.add((rel_uri, XBRL.arcrole, Literal(arcrole)))
                                    g.add((rel_uri, XBRL.linkrole, Literal(linkrole)))
                                    
                                    # Source and target concepts
                                    if hasattr(rel, 'fromModelObject') and rel.fromModelObject:
                                        g.add((rel_uri, XBRL.source, CONCEPT[rel.fromModelObject.qname.localName]))
                                    
                                    if hasattr(rel, 'toModelObject') and rel.toModelObject:
                                        g.add((rel_uri, XBRL.target, CONCEPT[rel.toModelObject.qname.localName]))
                                    
                                    # Order and weight
                                    if hasattr(rel, 'order') and rel.order is not None:
                                        g.add((rel_uri, XBRL.order, Literal(rel.order, datatype=XSD.decimal)))
                                    
                                    if hasattr(rel, 'weight') and rel.weight is not None:
                                        g.add((rel_uri, XBRL.weight, Literal(rel.weight, datatype=XSD.decimal)))
                                    
                                    # Preferred label
                                    if hasattr(rel, 'preferredLabel') and rel.preferredLabel:
                                        g.add((rel_uri, XBRL.preferredLabel, Literal(rel.preferredLabel)))
                                        
                except Exception as e:
                    print(f"Error translating relationships: {e}")
            
            def translate_taxonomy():
                """Translate XBRL taxonomy information to RDF"""
                try:
                    if hasattr(self.xbrl_model, 'taxonomy'):
                        taxonomy_uri = TAXONOMY["main"]
                        g.add((taxonomy_uri, RDF.type, XBRL.Taxonomy))
                        
                        # Add taxonomy metadata
                        if hasattr(self.xbrl_model.taxonomy, 'entryPoint'):
                            g.add((taxonomy_uri, XBRL.entryPoint, Literal(self.xbrl_model.taxonomy.entryPoint)))
                        
                        # Add schema information
                        if hasattr(self.xbrl_model.taxonomy, 'schemas'):
                            for schema in self.xbrl_model.taxonomy.schemas:
                                schema_uri = TAXONOMY[schema.qname.localName]
                                g.add((taxonomy_uri, XBRL.hasSchema, schema_uri))
                                g.add((schema_uri, RDF.type, XBRL.Schema))
                                g.add((schema_uri, XBRL.namespace, Literal(schema.namespaceURI)))
                        
                        # Add linkbase information
                        if hasattr(self.xbrl_model.taxonomy, 'linkbases'):
                            for linkbase in self.xbrl_model.taxonomy.linkbases:
                                linkbase_uri = TAXONOMY[linkbase.qname.localName]
                                g.add((taxonomy_uri, XBRL.hasLinkbase, linkbase_uri))
                                g.add((linkbase_uri, RDF.type, XBRL.Linkbase))
                                g.add((linkbase_uri, XBRL.role, Literal(linkbase.role)))
                                
                except Exception as e:
                    error_msg = f"Error translating taxonomy: {e}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
            
            # Execute all translations
            logger.info("Translating concepts...")
            translate_concepts()
            
            logger.info("Translating contexts...")
            translate_contexts()
            
            logger.info("Translating facts...")
            translate_facts()
            
            logger.info("Translating relationships...")
            translate_relationships()
            
            logger.info("Translating taxonomy information...")
            translate_taxonomy()
            
            logger.info(f"RDF translation complete. Graph contains {len(g)} triples.")
            
            if self.errors:
                logger.warning(f"Completed with {len(self.errors)} errors")
                for error in self.errors:
                    logger.warning(error)
            
            return g
            
        except Exception as e:
            logger.error(f"Fatal error during RDF translation: {e}")
            raise

    def save_rdf_graph(self, graph, filename, format='turtle'):
        """
        Save the RDF graph to a file in the specified format.
        
        Args:
            graph: rdflib.Graph object
            filename: Output filename
            format: RDF serialization format ('turtle', 'xml', 'n3', 'json-ld')
        """
        try:
            if not graph:
                raise ValueError("RDF graph cannot be None")
                
            if not filename:
                raise ValueError("Output filename cannot be None")
                
            if format not in ['turtle', 'xml', 'n3', 'json-ld']:
                raise ValueError(f"Unsupported format: {format}")
                
            graph.serialize(destination=filename, format=format)
            logger.info(f"RDF graph saved to {filename} in {format} format")
            
        except Exception as e:
            error_msg = f"Error saving RDF graph: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            raise

