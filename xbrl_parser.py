import os
import json
from typing import Dict, List, Optional, Any
from arelle import Cntlr, ModelManager, FileSource
from arelle.ModelDtsObject import ModelConcept
from arelle.ModelInstanceObject import ModelFact
import pandas as pd


class XBRLParser:
    """
    A comprehensive XBRL parser using the Arelle library.
    Supports parsing instance documents and extracting facts, contexts, and taxonomies.
    """
    
    def __init__(self, log_level: str = "WARNING"):
        """Initialize the XBRL parser with Arelle controller."""
        self.controller = Cntlr.Cntlr(hasGui=False)
        self.model_manager = ModelManager.initialize(self.controller)
        self.model_xbrl = None
        
    def load_filing(self, file_path: str) -> bool:
        """
        Load an XBRL filing from file path or URL.
        
        Args:
            file_path: Path to XBRL file or URL
            
        Returns:
            bool: True if successfully loaded, False otherwise
        """
        try:
            file_source = FileSource.FileSource(file_path)
            self.model_xbrl = self.model_manager.load(file_source)
            return self.model_xbrl is not None
        except Exception as e:
            print(f"Error loading XBRL file: {e}")
            return False
    
    def get_company_info(self) -> Dict[str, Any]:
        """Extract basic company information from the filing."""
        if not self.model_xbrl:
            return {}
            
        company_info = {}
        
        # Common DEI (Document and Entity Information) concepts
        dei_concepts = {
            'EntityRegistrantName': 'company_name',
            'EntityCentralIndexKey': 'cik',
            'TradingSymbol': 'ticker',
            'DocumentPeriodEndDate': 'period_end_date',
            'DocumentType': 'document_type',
            'EntityFilerCategory': 'filer_category'
        }
        
        for fact in self.model_xbrl.facts:
            concept_name = fact.concept.name
            if concept_name in dei_concepts:
                company_info[dei_concepts[concept_name]] = fact.value
                
        return company_info
    
    def extract_facts(self, concept_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract all facts from the XBRL instance.
        
        Args:
            concept_filter: Optional list of concept names to filter by
            
        Returns:
            List of dictionaries containing fact information
        """
        if not self.model_xbrl:
            return []
            
        facts_data = []
        
        for fact in self.model_xbrl.facts:
            concept_name = fact.concept.name
            
            # Apply concept filter if provided
            if concept_filter and concept_name not in concept_filter:
                continue
                
            fact_info = {
                'concept': concept_name,
                'namespace': fact.concept.qname.namespaceURI,
                'value': fact.value,
                'unit': self._get_unit_info(fact),
                'context': self._get_context_info(fact),
                'decimals': getattr(fact, 'decimals', None),
                'precision': getattr(fact, 'precision', None)
            }
            
            facts_data.append(fact_info)
            
        return facts_data
    
    def _get_unit_info(self, fact: ModelFact) -> Optional[str]:
        """Extract unit information from a fact."""
        if hasattr(fact, 'unit') and fact.unit:
            if fact.unit.measures:
                # Handle both single and ratio measures
                numerator = [str(m) for m in fact.unit.measures[0]] if fact.unit.measures[0] else []
                denominator = [str(m) for m in fact.unit.measures[1]] if len(fact.unit.measures) > 1 and fact.unit.measures[1] else []
                
                if denominator:
                    return f"{'/'.join(numerator)}/{'/'.join(denominator)}"
                else:
                    return '/'.join(numerator)
        return None
    
    def _get_context_info(self, fact: ModelFact) -> Dict[str, Any]:
        """Extract context information from a fact."""
        context_info = {}
        
        if hasattr(fact, 'context') and fact.context:
            context = fact.context
            
            # Entity information
            if context.entityIdentifier:
                context_info['entity_scheme'] = context.entityIdentifier[0]
                context_info['entity_identifier'] = context.entityIdentifier[1]
            
            # Period information
            if context.period:
                if context.isInstantPeriod:
                    context_info['period_type'] = 'instant'
                    context_info['instant'] = str(context.instantDate)
                elif context.isStartEndPeriod:
                    context_info['period_type'] = 'duration'
                    context_info['start_date'] = str(context.startDatetime)
                    context_info['end_date'] = str(context.endDatetime)
            
            # Dimensional information (segments)
            if context.qnameDims:
                dimensions = {}
                for dim_qname, member in context.qnameDims.items():
                    if member.isExplicit:
                        dimensions[str(dim_qname)] = str(member.member)
                    elif member.isTyped:
                        dimensions[str(dim_qname)] = str(member.typedMember)
                context_info['dimensions'] = dimensions
                
        return context_info
    
    def get_financial_statements(self) -> Dict[str, pd.DataFrame]:
        """
        Extract common financial statement data and organize into DataFrames.
        
        Returns:
            Dictionary with DataFrames for different financial statements
        """
        if not self.model_xbrl:
            return {}
            
        # Common financial statement concepts
        income_statement_concepts = [
            'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
            'CostOfRevenue', 'CostOfGoodsAndServicesSold', 'GrossProfit',
            'OperatingExpenses', 'OperatingIncomeLoss', 'NetIncomeLoss',
            'EarningsPerShareBasic', 'EarningsPerShareDiluted'
        ]
        
        balance_sheet_concepts = [
            'Assets', 'AssetsCurrent', 'AssetsNoncurrent',
            'Liabilities', 'LiabilitiesCurrent', 'LiabilitiesNoncurrent',
            'StockholdersEquity', 'RetainedEarningsAccumulatedDeficit'
        ]
        
        cash_flow_concepts = [
            'NetCashProvidedByUsedInOperatingActivities',
            'NetCashProvidedByUsedInInvestingActivities',
            'NetCashProvidedByUsedInFinancingActivities',
            'CashAndCashEquivalentsAtCarryingValue'
        ]
        
        statements = {}
        
        # Extract each statement type
        for statement_name, concepts in [
            ('income_statement', income_statement_concepts),
            ('balance_sheet', balance_sheet_concepts),
            ('cash_flow', cash_flow_concepts)
        ]:
            facts = self.extract_facts(concept_filter=concepts)
            if facts:
                statements[statement_name] = pd.DataFrame(facts)
                
        return statements
    
    def get_taxonomy_info(self) -> Dict[str, Any]:
        """Extract taxonomy information from the loaded XBRL."""
        if not self.model_xbrl:
            return {}
            
        taxonomy_info = {
            'schema_refs': [],
            'linkbase_refs': [],
            'namespaces': {}
        }
        
        # Schema references
        for schema_ref in self.model_xbrl.schemaLocationElements.values():
            taxonomy_info['schema_refs'].append({
                'namespace': schema_ref.namespaceURI,
                'location': schema_ref.schemaLocation
            })
        
        # Linkbase references  
        for linkbase_ref in self.model_xbrl.linkbaseDiscover:
            taxonomy_info['linkbase_refs'].append({
                'type': linkbase_ref.arcrole,
                'href': linkbase_ref.href
            })
            
        # Namespace prefixes
        taxonomy_info['namespaces'] = dict(self.model_xbrl.prefixedNamespaces)
        
        return taxonomy_info
    
    def export_to_json(self, output_path: str, include_facts: bool = True, 
                      include_company_info: bool = True, include_taxonomy: bool = False):
        """
        Export parsed XBRL data to JSON file.
        
        Args:
            output_path: Path for output JSON file
            include_facts: Whether to include facts data
            include_company_info: Whether to include company information
            include_taxonomy: Whether to include taxonomy information
        """
        export_data = {}
        
        if include_company_info:
            export_data['company_info'] = self.get_company_info()
            
        if include_facts:
            export_data['facts'] = self.extract_facts()
            
        if include_taxonomy:
            export_data['taxonomy'] = self.get_taxonomy_info()
            
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def close(self):
        """Clean up resources."""
        if self.model_xbrl:
            self.model_xbrl.close()
        if self.controller:
            self.controller.close()


# Example usage
def example_usage():
    """Example of how to use the XBRLParser class."""
    
    # Initialize parser
    parser = XBRLParser()
    
    # Load XBRL filing (replace with actual path or URL)
    file_path = "https://www.sec.gov/Archives/edgar/data/1018724/000101872425000004/amzn-20241231_htm.xml"  # or URL
    
    if parser.load_filing(file_path):
        print("XBRL file loaded successfully!")
        
        # Get company information
        company_info = parser.get_company_info()
        print(f"Company: {company_info.get('company_name', 'Unknown')}")
        print(f"CIK: {company_info.get('cik', 'Unknown')}")
        
        # Extract specific facts
        revenue_facts = parser.extract_facts()
        print(revenue_facts)
        
        # Get financial statements as DataFrames
        statements = parser.get_financial_statements()
        for statement_name, df in statements.items():
            print(f"{statement_name}: {len(df)} facts")
        
        # Export to JSON
        parser.export_to_json("xbrl_data.json")
        
        # Clean up
        parser.close()
    else:
        print("Failed to load XBRL file")


if __name__ == "__main__":
    example_usage()