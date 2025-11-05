import json
from typing import Dict, List, Optional, Any
from arelle import Cntlr, ModelManager, FileSource, ModelXbrl
from arelle.ModelDocument import Type
from arelle.ModelDtsObject import ModelConcept
from arelle.ModelInstanceObject import ModelFact
import pandas as pd

from rdflib import Graph, Literal, Namespace, URIRef, RDF, RDFS, XSD

from xbrl_to_rdf import XBRLToRDF


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
            self.model_xbrl = self.model_manager.load(file_source, isSupplementalFile=False)
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
            'EntityFilerCategory': 'filer_category',
            'AmendmentFlag': 'amendment_flag',
            'DocumentFiscalYearFocus': 'document_fiscal_year_focus',
            'DocumentFiscalPeriodFocus': 'document_fiscal_period_focus',
            'EmployeeServiceShareBasedCompensationNonvestedAwardsCompensationCostExpensedInNextTwelveMonthsExpectedToExceedPercentage': 'employee_service_share_based_compensation_nonvested_awards_compensation_cost_expensed_in_next_twelve_months_expected_to_exceed_percentage',
            'DocumentAnnualReport': 'document_annual_report',
            'CurrentFiscalYearEndDate': 'current_fiscal_year_end_date',
            'DocumentTransitionReport': 'document_transition_report',
            'EntityFileNumber': 'entity_file_number',
            'EntityIncorporationStateCountryCode': 'entity_incorporation_state_country_code',
            'EntityTaxIdentificationNumber': 'entity_tax_identification_number',
            'EntityAddressAddressLine1': 'entity_address_address_line_1',
            'EntityAddressCityOrTown': 'entity_address_city_or_town',
            'EntityAddressStateOrProvince': 'entity_address_state_or_province',
            'EntityAddressPostalZipCode': 'entity_address_postal_zip_code',
            'CityAreaCode': 'city_area_code',
            'LocalPhoneNumber': 'local_phone_number',
            'Security12bTitle': 'security_12b_title',
            'SecurityExchangeName': 'security_exchange_name',
            'EntityWellKnownSeasonedIssuer': 'entity_well_known_seasoned_issuer',
            'EntityVoluntaryFilers': 'entity_voluntary_filers',
            'EntityCurrentReportingStatus': 'entity_current_reporting_status',
            'EntityInteractiveDataCurrent': 'entity_interactive_data_current',
            'EntitySmallBusiness': 'entity_small_business',
            'EntityEmergingGrowthCompany': 'entity_emerging_growth_company',
            'IcfrAuditorAttestationFlag': 'icfr_auditor_attestation_flag',
            'DocumentFinStmtErrorCorrectionFlag': 'document_fin_stmt_error_correction_flag',
            'EntityShellCompany': 'entity_shell_company',
            'EntityPublicFloat': 'entity_public_float',
            'EntityCommonStockSharesOutstanding': 'entity_common_stock_shares_outstanding',
            'DocumentsIncorporatedByReferenceTextBlock': 'documents_incorporated_by_reference_text_block'
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
                'concept_qname': fact.concept.qname,
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
        for doc in self.model_xbrl.urlDocs.values():
            if doc.type == Type.SCHEMA:
                taxonomy_info['schema_refs'].append({
                        'namespace': doc.targetNamespace,
                        'location': doc.uri
                    })
            elif doc.type == Type.LINKBASE:
                # Get the arcrole from the linkbase document's roleRefs
                taxonomy_info['linkbase_refs'].append({
                        'base': doc.basename,
                        'type': value.referenceTypes,
                        'href': doc.uri
                    })

        # Namespace prefixes
        if hasattr(self.model_xbrl, 'prefixedNamespaces'):
            taxonomy_info['namespaces'] = dict(self.model_xbrl.prefixedNamespaces)
        
        return taxonomy_info
    
    def get_presentation_hierarchy(self):
        """Get presentation hierarchy"""
        # Get presentation relationships
        pres_linkbase = self.model_xbrl.relationshipSet("http://www.xbrl.org/2003/arcrole/parent-child")
        
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

    def get_calculation_relationships(self):
        """Get calculation relationships"""
        calc_linkbase = self.model_xbrl.relationshipSet("http://www.xbrl.org/2003/arcrole/summation-item")
        
        for rel in calc_linkbase.modelRelationships:
            parent = rel.fromModelObject
            child = rel.toModelObject
            weight = rel.weight
            
            print(f"{parent.qname} = {child.qname} * {weight}")

    def arcrole_uri(self) -> list:
        """Get the URI for an arcrole"""
        arcrole_uri = set()
        for k,v in self.model_xbrl.baseSets.items():
            if k[0] == "XBRL-dimensions":
                continue
            arcrole_uri.add(k[0])
        return list(arcrole_uri)
    
    def get_all_relationships(self) -> list:
        """Get all relationships"""
        
        for arcrole_uri in self.arcrole_uri():
            linkbase = self.model_xbrl.relationshipSet(arcrole_uri)
            
            print(f"Arcrole: {arcrole_uri}")

            for rel in linkbase.modelRelationships:
                parent = rel.fromModelObject
                child = rel.toModelObject
                print(f"{parent.qname} -> {child.qname}")
            print("--------------------------------")
        
        return 

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

    def validate_instance(self) -> Dict[str, Any]:
        """
        Validate the XBRL instance against its taxonomy.
        
        Returns:
            Dictionary containing validation results and any errors/warnings
        """
        if not self.model_xbrl:
            return {'status': 'error', 'message': 'No XBRL instance loaded'}
            
        validation_results = {
            'status': 'success',
            'errors': [],
            'warnings': []
        }
        
        # Check for required facts
        required_concepts = self._get_required_concepts()
        for concept in required_concepts:
            if not any(fact.concept == concept for fact in self.model_xbrl.facts):
                validation_results['warnings'].append(f"Missing required fact: {concept.qname}")
        
        # Check calculation consistency
        calc_errors = self._validate_calculations()
        validation_results['errors'].extend(calc_errors)
        
        if validation_results['errors']:
            validation_results['status'] = 'error'
            
        return validation_results
    
    def _get_required_concepts(self) -> List[ModelConcept]:
        """Get list of required concepts from taxonomy."""
        required_concepts = []
        for concept in self.model_xbrl.qnameConcepts.values():
            if concept.isRequired:
                required_concepts.append(concept)
        return required_concepts
    
    def _validate_calculations(self) -> List[str]:
        """Validate calculation relationships."""
        errors = []
        calc_linkbase = self.model_xbrl.relationshipSet("http://www.xbrl.org/2003/arcrole/summation-item")
        
        for rel in calc_linkbase.modelRelationships:
            parent = rel.fromModelObject
            child = rel.toModelObject
            weight = rel.weight
            
            # Get parent and child values
            parent_facts = [f for f in self.model_xbrl.facts if f.concept == parent]
            child_facts = [f for f in self.model_xbrl.facts if f.concept == child]
            
            if parent_facts and child_facts:
                for parent_fact in parent_facts:
                    # Find matching child facts by context
                    matching_children = [f for f in child_facts if f.context == parent_fact.context]
                    if matching_children:
                        calculated_sum = sum(float(f.value) * weight for f in matching_children)
                        actual_value = float(parent_fact.value)
                        if abs(calculated_sum - actual_value) > 0.01:  # Allow small rounding differences
                            errors.append(f"Calculation error: {parent.qname} = {calculated_sum}, actual = {actual_value}")
        
        return errors
    
    def calculate_financial_ratios(self) -> Dict[str, float]:
        """
        Calculate common financial ratios from the XBRL data.
        
        Returns:
            Dictionary of calculated ratios
        """
        if not self.model_xbrl:
            return {}
            
        ratios = {}
        facts = {fact.concept.qname: float(fact.value) for fact in self.model_xbrl.facts 
                if fact.value and fact.value.strip() and fact.value.replace('.', '').isdigit()}
        
        # Current Ratio
        if 'AssetsCurrent' in facts and 'LiabilitiesCurrent' in facts:
            ratios['current_ratio'] = facts['AssetsCurrent'] / facts['LiabilitiesCurrent']
        
        # Debt to Equity Ratio
        if 'Liabilities' in facts and 'StockholdersEquity' in facts:
            ratios['debt_to_equity'] = facts['Liabilities'] / facts['StockholdersEquity']
        
        # Return on Assets (ROA)
        if 'NetIncomeLoss' in facts and 'Assets' in facts:
            ratios['roa'] = facts['NetIncomeLoss'] / facts['Assets']
        
        # Return on Equity (ROE)
        if 'NetIncomeLoss' in facts and 'StockholdersEquity' in facts:
            ratios['roe'] = facts['NetIncomeLoss'] / facts['StockholdersEquity']
        
        return ratios
    
    def get_concept_metadata(self, concept_name: str) -> Dict[str, Any]:
        """
        Get detailed metadata for a specific concept.
        
        Args:
            concept_name: Name of the concept to get metadata for
            
        Returns:
            Dictionary containing concept metadata
        """
        if not self.model_xbrl:
            return {}
            
        concept = self.model_xbrl.qnameConcepts.get(concept_name)
        if not concept:
            return {}
            
        metadata = {
            'name': concept.qname,
            'type': concept.type.qname,
            'period_type': concept.periodType,
            'balance': concept.balance,
            'labels': {},
            'references': []
        }
        
        # Get labels in different languages
        for label in concept.labels():
            metadata['labels'][label.role] = label.text
            
        # Get references
        for ref in concept.references():
            metadata['references'].append({
                'role': ref.role,
                'text': ref.text
            })
            
        return metadata
    
    def export_to_excel(self, output_path: str):
        """
        Export XBRL data to Excel with formatted sheets.
        
        Args:
            output_path: Path for output Excel file
        """
        if not self.model_xbrl:
            return
            
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Export company info
            company_info = self.get_company_info()
            pd.DataFrame([company_info]).to_excel(writer, sheet_name='Company Info', index=False)
            
            # Export financial statements
            statements = self.get_financial_statements()
            for statement_name, df in statements.items():
                df.to_excel(writer, sheet_name=statement_name, index=False)
            
            # Export all facts
            facts_df = pd.DataFrame(self.extract_facts())
            facts_df.to_excel(writer, sheet_name='All Facts', index=False)
            
            # Export ratios
            ratios_df = pd.DataFrame([self.calculate_financial_ratios()])
            ratios_df.to_excel(writer, sheet_name='Financial Ratios', index=False)
    
    def get_filing_metadata(self) -> Dict[str, Any]:
        """Get metadata about the filing."""
        if not self.model_xbrl:
            return {}
            
        metadata = {
            'filing_date': self.model_xbrl.modelDocument.reportingDate,
            'document_type': self.model_xbrl.modelDocument.type,
            'namespaces': dict(self.model_xbrl.namespaceDocs),
            'schema_refs': [doc.uri for doc in self.model_xbrl.urlDocs.values() if doc.type == Type.SCHEMA],
            'linkbase_refs': [doc.uri for doc in self.model_xbrl.urlDocs.values() if doc.type == Type.LINKBASE]
        }
        
        return metadata

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
        # company_info = parser.get_company_info()

        # print(f"Company: {company_info.get('company_name', 'Unknown')}")
        # print(f"CIK: {company_info.get('cik', 'Unknown')}")
        
        # Extract specific facts
        # revenue_facts = parser.extract_facts()
        
    #     # Get financial statements as DataFrames
    #     statements = parser.get_financial_statements()
    #     for statement_name, df in statements.items():
    #         print(f"{statement_name}: {len(df)} facts")
        
        # Export to JSON
        # parser.export_to_json("xbrl_data.json", include_facts=True, include_company_info=True, include_taxonomy=True)
        # parser.get_presentation_hierarchy()
        # parser.get_calculation_relationships()
        # print(parser.arcrole_uri())
        # parser.get_all_relationships()
        xbrl_to_rdf = XBRLToRDF(parser.model_xbrl)
        graph = xbrl_to_rdf.xbrl_to_rdf()
        xbrl_to_rdf.save_rdf_graph(graph,'xbrl_data.ttl','turtle')
    #     # Clean up
    #     parser.close()
    # else:
    #     print("Failed to load XBRL file")


if __name__ == "__main__":
    example_usage()