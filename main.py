from arelle import ModelManager, ModelXbrl, Cntlr
import requests
import os
from urllib.parse import urljoin
import time

def parse_amazon_xbrl():
    # SEC filing URL
    base_url = "https://www.sec.gov/Archives/edgar/data/1018724/000101872425000004/"
    # index_url = "amzn-20241231.htm"
    
    # Create a session with SEC headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Pillar Base Inc. services@pillarbase.com',  # Replace with your information
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    })
    
    # SEC requires a delay between requests
    time.sleep(0.1)
    
    try:
        # Get the index page
        # response = session.get(urljoin(base_url, index_url))
        # response.raise_for_status()
        
        # Parse the index page to find the XBRL instance document
        # For now, we'll use a direct URL to the instance document
        xbrl_url = urljoin(base_url, "amzn-20241231_htm.xml")  # This is the instance document
        
        # SEC requires a delay between requests
        time.sleep(0.1)
        
        # Download the XBRL file
        xbrl_response = session.get(xbrl_url)
        xbrl_response.raise_for_status()
        
        # Save the XBRL file temporarily
        temp_file = "temp_amazon.xbrl"
        with open(temp_file, "wb") as f:
            f.write(xbrl_response.content)
        
        try:
            # Initialize Arelle controller
            controller = Cntlr.Cntlr()
            
            # Initialize model manager with the controller
            model_manager = ModelManager.initialize(controller)
            
            # Load the XBRL file
            model_xbrl = ModelXbrl.load(model_manager, temp_file)
            
            # Print some basic information
            print("Filing Information:")
            print(f"Entity: {model_xbrl.modelDocument.entityName}")
            print(f"Period: {model_xbrl.modelDocument.period}")
            
            # Print some key facts
            print("\nKey Financial Facts:")
            for fact in model_xbrl.facts:
                if fact.concept.label() and fact.value:
                    print(f"{fact.concept.label()}: {fact.value}")
            
            return model_xbrl

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if model_manager:
                model_manager.close()
            if controller:
                controller.close()
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("Access denied. Please ensure you're following SEC's guidelines:")
            print("1. Use a proper User-Agent header with your company name and contact email")
            print("2. Respect the rate limiting (10 requests per second)")
            print("3. Visit https://www.sec.gov/developer for more information")
        raise

def main():
    print("Parsing Amazon's XBRL filing...")
    try:
        model_xbrl = parse_amazon_xbrl()
        print("\nParsing completed successfully!")
    except Exception as e:
        print(f"Error parsing XBRL file: {str(e)}")

if __name__ == "__main__":
    main()
