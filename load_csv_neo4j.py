import pandas as pd
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def load_projects(tx, row):
    # Creates Project and Location nodes and links them
    tx.run("""
    MERGE (p:Project {project_id: $project_id})
    SET p.name = $name,
        p.launch_year = toInteger($launch_year),
        p.price_per_sqft = toInteger($price_per_sqft),
        p.status = toLower($status)
    
    MERGE (l:Location {name: $location})
    MERGE (p)-[:LOCATED_IN]->(l)
    """, **row)

def load_units(tx, row):
    # Links Units to Projects and classifies them by UnitType
    tx.run("""
    MATCH (p:Project {project_id: $project_id})
    MERGE (u:Unit {unit_id: $unit_id})
    SET u.size_sqft = toInteger($size_sqft),
        u.price = toInteger($price)
    
    MERGE (ut:UnitType {name: $unit_type})
    MERGE (p)-[:HAS_UNIT]->(u)
    MERGE (u)-[:HAS_UNIT_TYPE]->(ut)
    """, **row)

def load_buyers(tx, row):
    # Loads the reference data for buyer categories
    tx.run("""
    MERGE (b:BuyerType {name: $buyer_type})
    SET b.description = $description
    """, **row)

def load_sales(tx, row):
    # Connects a Unit to a BuyerType based on a sale event
    tx.run("""
    MATCH (u:Unit {unit_id: $unit_id})
    MATCH (b:BuyerType {name: $buyer_type})
    MERGE (u)-[r:TARGETED_FOR]->(b)
    SET r.sale_id = $sale_id,
        r.sold_date = date($sold_date)
    """, **row)

def load_amenities(tx, row):
    # Links Amenities to Projects
    tx.run("""
    MATCH (p:Project {project_id: $project_id})
    MERGE (a:Amenity {name: $amenity})
    MERGE (p)-[:HAS_AMENITY]->(a)
    """, **row)

def run_import():
    """Main execution loop reading CSVs and calling Cypher functions."""
    with driver.session() as session:
        # Note: Order matters! Create Projects/Buyers before linking them in Sales/Units
        
        print("📥 Processing Projects...")
        for _, row in pd.read_csv("data/projects_100.csv").iterrows():
            session.execute_write(load_projects, row.to_dict())

        print("📥 Processing Buyer Types...")
        for _, row in pd.read_csv("data/buyers_100.csv").iterrows():
            session.execute_write(load_buyers, row.to_dict())

        print("📥 Processing Units...")
        for _, row in pd.read_csv("data/units_100.csv").iterrows():
            session.execute_write(load_units, row.to_dict())

        print("📥 Processing Sales...")
        for _, row in pd.read_csv("data/sales_100.csv").iterrows():
            session.execute_write(load_sales, row.to_dict())

        print("📥 Processing Amenities...")
        for _, row in pd.read_csv("data/amenities_100.csv").iterrows():
            session.execute_write(load_amenities, row.to_dict())

if __name__ == "__main__":
    run_import()
    driver.close()
    print("🚀 Knowledge Graph update complete.")