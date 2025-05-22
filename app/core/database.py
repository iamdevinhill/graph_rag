from neo4j import GraphDatabase
from .config import get_settings
import time
import logging
import json

settings = get_settings()
logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self):
        self.driver = None
        self.connect_with_retry()

    def connect_with_retry(self, max_retries=5, retry_delay=5):
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to Neo4j at {settings.NEO4J_URI}")
                self.driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                # Test the connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                logger.info("Successfully connected to Neo4j")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to Neo4j (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to Neo4j after {max_retries} attempts: {str(e)}")
                    raise

    def close(self):
        if self.driver:
            self.driver.close()

    def get_session(self):
        try:
            if not self.driver:
                self.connect_with_retry()
            return self.driver.session()
        except Exception as e:
            logger.error(f"Error getting Neo4j session: {str(e)}")
            raise

    def create_constraints(self):
        try:
            with self.get_session() as session:
                # Create constraints for Document nodes
                session.run("CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
                # Create constraints for Chunk nodes
                session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE")
                logger.info("Successfully created Neo4j constraints")
        except Exception as e:
            logger.error(f"Error creating constraints: {str(e)}")
            raise

    def create_document(self, doc_id: str, content: str, metadata: dict = None):
        try:
            with self.get_session() as session:
                def create_doc_tx(tx):
                    # Convert metadata to string if it exists
                    metadata_str = json.dumps(metadata) if metadata else None
                    query = """
                    CREATE (d:Document {
                        id: $doc_id,
                        content: $content,
                        metadata: $metadata
                    })
                    RETURN d
                    """
                    result = tx.run(query, doc_id=doc_id, content=content, metadata=metadata_str)
                    record = result.single()
                    logger.info(f"create_document result: {record}")
                db_name = session.run("CALL db.info() YIELD name RETURN name").single()[0]
                logger.info(f"Using Neo4j database: {db_name}")
                session.execute_write(create_doc_tx)
                logger.info(f"Successfully created document with ID: {doc_id}")
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}", exc_info=True)
            raise

    def create_chunk(self, chunk_id: str, content: str, embedding: list, doc_id: str):
        try:
            with self.get_session() as session:
                def create_chunk_tx(tx):
                    query = """
                    MATCH (d:Document {id: $doc_id})
                    CREATE (c:Chunk {
                        id: $chunk_id,
                        content: $content,
                        embedding: $embedding
                    })
                    CREATE (d)-[:CONTAINS]->(c)
                    RETURN c
                    """
                    result = tx.run(query, chunk_id=chunk_id, content=content, embedding=embedding, doc_id=doc_id)
                    record = result.single()
                    logger.info(f"create_chunk result: {record}")
                db_name = session.run("CALL db.info() YIELD name RETURN name").single()[0]
                logger.info(f"Using Neo4j database: {db_name}")
                session.execute_write(create_chunk_tx)
                logger.info(f"Successfully created chunk with ID: {chunk_id}")
        except Exception as e:
            logger.error(f"Error creating chunk: {str(e)}", exc_info=True)
            raise

    def search_similar_chunks(self, embedding: list, limit: int = 5):
        try:
            with self.get_session() as session:
                query = """
                CALL db.index.vector.queryNodes('chunk_embeddings', $limit, $embedding)
                YIELD node, score
                RETURN node.content as content, score
                ORDER BY score DESC
                """
                result = session.run(query, embedding=embedding, limit=limit)
                chunks = [record for record in result]
                logger.info(f"Found {len(chunks)} similar chunks")
                return chunks
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise

db = Neo4jConnection() 