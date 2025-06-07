# Complete Arelle Python Guide

## Installation

```bash
# Install Arelle
pip install arelle-release

# Or for development version
pip install git+https://github.com/Arelle/Arelle.git
```

## Basic Setup and Loading

### Method 1: Using Controller (Most Common)
```python
from arelle import Cntlr
from arelle.ModelManager import ModelManager

# Create controller (main entry point)
ctrl = Cntlr.Cntlr()

# Load XBRL instance document
modelXbrl = ctrl.modelManager.load("path/to/filing.xml")

# Check if loading was successful
if modelXbrl is None:
    print("Failed to load XBRL document")
else:
    print(f"Successfully loaded: {modelXbrl.modelDocument.basename}")
```

### Method 2: Using Beta API (Newer)
```python
from arelle.api import Session

# Create session
session = Session()

# Configure session
session.config.file = "path/to/filing.xml"

# Run Arelle
session.run()

# Get the model
modelXbrl = session.model
```

## Core Concepts

### 1. ModelXbrl - The Main Container
```python
# Basic properties
print(f"Document URI: {modelXbrl.modelDocument.uri}")
print(f"Document type: {modelXbrl.modelDocument.type}")
print(f"Target namespace: {modelXbrl.modelDocument.targetNamespace}")

# Get all loaded documents
for uri, doc in modelXbrl.urlDocs.items():
    print(f"Document: {doc.basename}, Type: {doc.type}")
```

### 2. Facts - The Actual Data
```python
# Get all facts
facts = modelXbrl.facts
print(f"Total facts: {len(facts)}")

# Iterate through facts
for fact in facts:
    print(f"Concept: {fact.concept.qname}")
    print(f"Value: {fact.value}")
    print(f"Context ID: {fact.contextID}")
    print(f"Unit: {fact.unit.id if fact.unit else 'None'}")
    print(f"Decimals: {fact.decimals}")
    print("---")
```

### 3. Concepts - Element Definitions
```python
# Get all concepts
concepts = modelXbrl.qnameConcepts
print(f"Total concepts: {len(concepts)}")

# Iterate through concepts
for qname, concept in concepts.items():
    print(f"Concept: {qname}")
    print(f"Label: {concept.label()}")
    print(f"Type: {concept.type}")
    print(f"Period type: {concept.periodType}")
    print("---")
```

### 4. Contexts - When and What Dimension
```python
# Get all contexts
contexts = modelXbrl.contexts
print(f"Total contexts: {len(contexts)}")

for context_id, context in contexts.items():
    print(f"Context ID: {context_id}")
    print(f"Entity: {context.entityIdentifier}")
    print(f"Period: {context.period}")
    
    # Dimensional information
    if context.qnameDims:
        print("Dimensions:")
        for dim_qname, dim_value in context.qnameDims.items():
            print(f"  {dim_qname}: {dim_value}")
    print("---")
```

## Common Tasks

### 1. Extract Specific Facts
```python
def get_facts_by_concept(modelXbrl, concept_name):
    """Get all facts for a specific concept"""
    matching_facts = []
    
    for fact in modelXbrl.facts:
        if concept_name in str(fact.concept.qname):
            matching_facts.append({
                'concept': str(fact.concept.qname),
                'value': fact.value,
                'context_id': fact.contextID,
                'unit': fact.unit.id if fact.unit else None,
                'period': modelXbrl.contexts[fact.contextID].period.endDatetime if fact.contextID in modelXbrl.contexts else None
            })
    
    return matching_facts

# Example usage
revenue_facts = get_facts_by_concept(modelXbrl, "Revenues")
for fact in revenue_facts:
    print(f"Revenue: {fact['value']} for period {fact['period']}")
```

### 2. Work with Presentation Linkbase
```python
def get_presentation_hierarchy(modelXbrl):
    """Get presentation hierarchy"""
    # Get presentation relationships
    pres_linkbase = modelXbrl.relationshipSet("http://www.xbrl.org/2003/arcrole/parent-child")
    
    # Get root concepts (those without parents)
    roots = pres_linkbase.rootConcepts
    
    def print_hierarchy(concept, level=0):
        indent = "  " * level
        print(f"{indent}{concept.qname}: {concept.label()}")
        
        # Get children
        children = pres_linkbase.fromModelObject(concept)
        for rel in sorted(children, key=lambda x: x.order):
            print_hierarchy(rel.toModelObject, level + 1)
    
    for root in roots:
        print_hierarchy(root)

# Usage
get_presentation_hierarchy(modelXbrl)
```

### 3. Work with Calculation Linkbase
```python
def get_calculation_relationships(modelXbrl):
    """Get calculation relationships"""
    calc_linkbase = modelXbrl.relationshipSet("http://www.xbrl.org/2003/arcrole/summation-item")
    
    for rel in calc_linkbase.modelRelationships:
        parent = rel.fromModelObject
        child = rel.toModelObject
        weight = rel.weight
        
        print(f"{parent.qname} = {child.qname} * {weight}")

# Usage
get_calculation_relationships(modelXbrl)
```

### 4. Extract Financial Statement Data
```python
def extract_financial_data(modelXbrl, statement_concepts):
    """Extract specific financial statement line items"""
    financial_data = {}
    
    for fact in modelXbrl.facts:
        concept_name = str(fact.concept.qname)
        
        # Check if this concept is in our list
        for statement_concept in statement_concepts:
            if statement_concept.lower() in concept_name.lower():
                context = modelXbrl.contexts.get(fact.contextID)
                
                if context and context.period:
                    period_key = str(context.period.endDatetime.date()) if context.period.endDatetime else "Unknown"
                    
                    if period_key not in financial_data:
                        financial_data[period_key] = {}
                    
                    financial_data[period_key][concept_name] = {
                        'value': fact.value,
                        'unit': fact.unit.id if fact.unit else None
                    }
    
    return financial_data

# Example usage
key_concepts = ['Revenues', 'NetIncomeLoss', 'Assets', 'Liabilities', 'StockholdersEquity']
financial_data = extract_financial_data(modelXbrl, key_concepts)

for period, data in financial_data.items():
    print(f"\nPeriod: {period}")
    for concept, info in data.items():
        print(f"  {concept}: {info['value']} {info['unit']}")
```

### 5. Export Data to Different Formats
```python
import pandas as pd
import json

def export_facts_to_dataframe(modelXbrl):
    """Export all facts to pandas DataFrame"""
    facts_data = []
    
    for fact in modelXbrl.facts:
        context = modelXbrl.contexts.get(fact.contextID)
        
        fact_dict = {
            'concept': str(fact.concept.qname),
            'value': fact.value,
            'context_id': fact.contextID,
            'unit': fact.unit.id if fact.unit else None,
            'decimals': fact.decimals,
            'entity': context.entityIdentifier[1] if context else None,
            'period_end': str(context.period.endDatetime.date()) if context and context.period and context.period.endDatetime else None,
            'period_start': str(context.period.startDatetime.date()) if context and context.period and context.period.startDatetime else None
        }
        
        facts_data.append(fact_dict)
    
    return pd.DataFrame(facts_data)

# Export to CSV
df = export_facts_to_dataframe(modelXbrl)
df.to_csv('xbrl_facts.csv', index=False)
print(f"Exported {len(df)} facts to CSV")
```

## Error Handling and Validation

```python
def load_and_validate_xbrl(file_path):
    """Load XBRL with proper error handling"""
    try:
        ctrl = Cntlr.Cntlr()
        
        # Load with validation
        modelXbrl = ctrl.modelManager.load(file_path)
        
        if modelXbrl is None:
            print("Failed to load XBRL document")
            return None
        
        # Check for errors
        if modelXbrl.errors:
            print(f"Validation errors found: {len(modelXbrl.errors)}")
            for error in modelXbrl.errors:
                print(f"  Error: {error}")
        
        # Check for warnings
        if hasattr(modelXbrl, 'warnings') and modelXbrl.warnings:
            print(f"Warnings: {len(modelXbrl.warnings)}")
        
        return modelXbrl
        
    except Exception as e:
        print(f"Error loading XBRL: {str(e)}")
        return None

# Usage
modelXbrl = load_and_validate_xbrl("filing.xml")
if modelXbrl:
    print("XBRL loaded successfully")
```

## Working with Taxonomies

```python
def analyze_taxonomy(modelXbrl):
    """Analyze the taxonomy structure"""
    print("=== TAXONOMY ANALYSIS ===")
    
    # Schema documents
    schemas = [doc for doc in modelXbrl.urlDocs.values() if doc.type == "schema"]
    print(f"Schema documents: {len(schemas)}")
    
    for schema in schemas:
        print(f"  Schema: {schema.basename}")
        print(f"    Namespace: {schema.targetNamespace}")
        print(f"    Elements: {len(schema.xmlRootElement.xpath('//xs:element', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'}))}")
    
    # Linkbase documents
    linkbases = [doc for doc in modelXbrl.urlDocs.values() if doc.type == "linkbase"]
    print(f"\nLinkbase documents: {len(linkbases)}")
    
    for linkbase in linkbases:
        print(f"  Linkbase: {linkbase.basename}")
    
    # Relationship sets
    print(f"\nRelationship sets: {len(modelXbrl.baseSets)}")
    for base_set_key in modelXbrl.baseSets.keys():
        if isinstance(base_set_key, tuple) and len(base_set_key) >= 1:
            arcrole = base_set_key[0]
            rel_set = modelXbrl.relationshipSet(arcrole)
            print(f"  {arcrole}: {len(rel_set.modelRelationships)} relationships")

# Usage
analyze_taxonomy(modelXbrl)
```

## Performance Tips

```python
# For large files, disable unnecessary validation
ctrl = Cntlr.Cntlr()
ctrl.webCache.workOffline = True  # Work offline to avoid network delays
ctrl.validate = False  # Disable validation for faster loading

# Load only what you need
modelXbrl = ctrl.modelManager.load(file_path, isSupplemental=True)

# Clear memory when done
if modelXbrl:
    modelXbrl.close()
    del modelXbrl
```

## Common Issues and Solutions

### Issue 1: Memory Usage
```python
# Process large files in chunks or clear memory frequently
def process_large_xbrl(file_path):
    ctrl = Cntlr.Cntlr()
    modelXbrl = ctrl.modelManager.load(file_path)
    
    if modelXbrl:
        # Extract what you need quickly
        data = extract_key_data(modelXbrl)
        
        # Clean up immediately
        modelXbrl.close()
        del modelXbrl
        
        return data
```

### Issue 2: Network Dependencies
```python
# Work offline to avoid taxonomy downloads
ctrl = Cntlr.Cntlr()
ctrl.webCache.workOffline = True
```

### Issue 3: Encoding Issues
```python
# Handle encoding properly
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

This guide covers the most common Arelle usage patterns. The key is to start with the Controller (`Cntlr.Cntlr()`) and work through the ModelXbrl object to access facts, concepts, and relationships.