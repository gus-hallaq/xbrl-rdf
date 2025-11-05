# XBRL Parser

A comprehensive Python library for parsing, analyzing, and visualizing XBRL (eXtensible Business Reporting Language) financial documents. This project provides tools to extract financial data from SEC filings and convert XBRL data to RDF format with interactive visualization capabilities.

## Features

- **XBRL Parsing**: Parse XBRL instance documents from files or URLs (including SEC Edgar filings)
- **Data Extraction**: Extract facts, concepts, contexts, and taxonomies
- **Financial Statements**: Organize data into structured DataFrames (Income Statement, Balance Sheet, Cash Flow)
- **RDF Conversion**: Convert XBRL data to RDF (Resource Description Framework) format
- **Interactive Visualization**: Visualize XBRL/RDF data as interactive network graphs using Plotly and Streamlit
- **Multiple Export Formats**: Export to JSON, Excel, Turtle (RDF), and more
- **Financial Ratios**: Calculate common financial ratios automatically
- **Validation**: Validate XBRL instances against their taxonomies

## Installation

### Prerequisites

- Python >= 3.12
- pip or uv (recommended)

### Using uv (Recommended)

```bash
# Install uv if you haven't already
pip install uv

# Clone the repository
git clone <repository-url>
cd xbrl-parser

# Install dependencies
uv sync
```

### Using pip

```bash
pip install arelle-release[crypto,db,efm,objectmaker,webserver] pandas requests rdflib networkx matplotlib streamlit plotly numpy scipy
```

## Quick Start

### Basic XBRL Parsing

```python
from xbrl_parser import XBRLParser

# Initialize parser
parser = XBRLParser()

# Load XBRL filing from URL or file path
file_path = "https://www.sec.gov/Archives/edgar/data/1018724/000101872425000004/amzn-20241231_htm.xml"
if parser.load_filing(file_path):
    # Get company information
    company_info = parser.get_company_info()
    print(f"Company: {company_info.get('company_name')}")

    # Extract all facts
    facts = parser.extract_facts()

    # Get financial statements as DataFrames
    statements = parser.get_financial_statements()

    # Export to JSON
    parser.export_to_json("output.json")

    # Clean up
    parser.close()
```

### Convert XBRL to RDF

```python
from xbrl_parser import XBRLParser
from xbrl_to_rdf import XBRLToRDF

# Load XBRL
parser = XBRLParser()
parser.load_filing("filing.xml")

# Convert to RDF
xbrl_to_rdf = XBRLToRDF(parser.model_xbrl)
graph = xbrl_to_rdf.xbrl_to_rdf()

# Save RDF graph
xbrl_to_rdf.save_rdf_graph(graph, 'output.ttl', 'turtle')
```

### Visualize RDF Data

```python
from rdflib import Graph
from rdf_visualizer import RDFVisualizer

# Load RDF graph
g = Graph()
g.parse('output.ttl', format='turtle')

# Create visualizer
visualizer = RDFVisualizer(g)

# Create interactive Plotly visualization
visualizer.visualize_plotly('visualization.html')

# Export to JSON
visualizer.export_to_json('graph.json')
```

### Run Streamlit Visualization App

```bash
streamlit run rdf_visualizer.py
```

Then upload your RDF file (.ttl, .xml, .n3, or .json-ld) and explore the interactive visualization.

## Project Structure

```
xbrl-parser/
├── xbrl_parser.py       # Main XBRL parser class
├── xbrl_to_rdf.py       # XBRL to RDF converter
├── rdf_visualizer.py    # RDF visualization tools
├── main.py              # Example SEC filing parser
├── arelle_guide.md      # Comprehensive Arelle library guide
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## Core Components

### XBRLParser

The main parser class that handles:
- Loading XBRL instance documents
- Extracting company information and metadata
- Parsing facts, contexts, and units
- Navigating taxonomy relationships
- Exporting to various formats

Key methods:
- `load_filing(file_path)` - Load XBRL document
- `get_company_info()` - Extract company metadata
- `extract_facts()` - Get all facts
- `get_financial_statements()` - Get organized financial statements
- `calculate_financial_ratios()` - Calculate key ratios
- `export_to_json()` / `export_to_excel()` - Export data

### XBRLToRDF

Converts XBRL data to RDF format:
- Translates concepts, facts, contexts, and relationships
- Preserves dimensional information
- Maintains taxonomy structure
- Supports multiple RDF serialization formats

### RDFVisualizer

Interactive visualization tools:
- Network graph visualization using Plotly
- Streamlit web application
- Tree view and table view
- Export to JSON format

## Use Cases

### 1. Financial Analysis
Extract and analyze financial data from SEC filings:

```python
parser = XBRLParser()
parser.load_filing("sec_filing.xml")

# Get financial statements
statements = parser.get_financial_statements()
income_statement = statements.get('income_statement')

# Calculate ratios
ratios = parser.calculate_financial_ratios()
print(f"Current Ratio: {ratios.get('current_ratio')}")
```

### 2. Data Integration
Convert XBRL to RDF for semantic web integration:

```python
# Parse XBRL and convert to RDF
xbrl_to_rdf = XBRLToRDF(model_xbrl)
graph = xbrl_to_rdf.xbrl_to_rdf()

# Query using SPARQL
query = """
SELECT ?concept ?value WHERE {
    ?fact xbrl:concept ?concept .
    ?fact xbrl:value ?value .
}
"""
results = graph.query(query)
```

### 3. Compliance and Validation
Validate XBRL filings:

```python
validation_results = parser.validate_instance()
if validation_results['status'] == 'error':
    print("Validation errors found:")
    for error in validation_results['errors']:
        print(f"  - {error}")
```

## SEC Edgar Integration

The project includes support for downloading XBRL filings from SEC Edgar:

```python
from main import parse_amazon_xbrl

# Parse Amazon's latest filing
model_xbrl = parse_amazon_xbrl()
```

**Important**: When accessing SEC Edgar, you must:
1. Use a proper User-Agent header with your company name and email
2. Respect rate limiting (10 requests per second max)
3. Follow SEC's fair access guidelines

## Dependencies

- **arelle-release**: Core XBRL parsing library
- **pandas**: Data manipulation and analysis
- **requests**: HTTP requests for downloading filings
- **rdflib**: RDF graph manipulation
- **networkx**: Graph algorithms and structures
- **matplotlib**: Static plotting
- **streamlit**: Interactive web applications
- **plotly**: Interactive visualizations
- **numpy & scipy**: Numerical computing

## Documentation

For detailed information about using the Arelle library, see [arelle_guide.md](arelle_guide.md).

## Examples

### Extract Presentation Hierarchy

```python
parser.get_presentation_hierarchy()
```

### Get Calculation Relationships

```python
parser.get_calculation_relationships()
```

### Get All Relationship Types

```python
arcrole_uris = parser.arcrole_uri()
for uri in arcrole_uris:
    print(f"Relationship type: {uri}")
```

## Visualization Options

The RDF visualizer supports multiple visualization modes:

1. **Network Graph**: Interactive node-link diagram
2. **Tree View**: Hierarchical tree structure
3. **Table View**: Tabular display of triples

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

[Add your license information here]

## Acknowledgments

- Built on top of the [Arelle](https://arelle.org/) XBRL processor
- Uses SEC Edgar for accessing public company filings

## Support

For issues, questions, or contributions, please visit the project repository.

## Resources

- [XBRL International](https://www.xbrl.org/)
- [SEC Edgar](https://www.sec.gov/edgar)
- [Arelle Documentation](https://arelle.org/arelle/)
- [RDF Primer](https://www.w3.org/TR/rdf11-primer/)
