from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

CONSTRAINTS = [
"""
CREATE CONSTRAINT project_id IF NOT EXISTS
FOR (p:Project) REQUIRE p.project_id IS UNIQUE;
""",
"""
CREATE CONSTRAINT unit_id IF NOT EXISTS
FOR (u:Unit) REQUIRE u.unit_id IS UNIQUE;
""",
"""
CREATE CONSTRAINT amenity_name IF NOT EXISTS
FOR (a:Amenity) REQUIRE a.name IS UNIQUE;
""",
"""
CREATE CONSTRAINT buyer_type_name IF NOT EXISTS
FOR (b:BuyerType) REQUIRE b.name IS UNIQUE;
""",
"""
CREATE CONSTRAINT unit_type_name IF NOT EXISTS
FOR (ut:UnitType) REQUIRE ut.name IS UNIQUE;
""",
"""
CREATE CONSTRAINT location_name IF NOT EXISTS
FOR (l:Location) REQUIRE l.name IS UNIQUE;
"""
]

def create_constraints():
    with driver.session() as session:
        for c in CONSTRAINTS:
            session.run(c)
            print("✅ Constraint ensured")

if __name__ == "__main__":
    create_constraints()
    driver.close()
    print("🎉 All constraints created successfully")
