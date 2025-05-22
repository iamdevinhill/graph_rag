from .database import db
import logging

logger = logging.getLogger(__name__)

def drop_vector_index():
    try:
        with db.get_session() as session:
            session.run("DROP INDEX chunk_embeddings IF EXISTS")
            logger.info("Successfully dropped vector search index")
    except Exception as e:
        logger.error(f"Error dropping vector index: {str(e)}")
        raise

def initialize_database():
    try:
        with db.get_session() as session:
            # Drop existing index if it exists
            drop_vector_index()
            
            # Create vector search index for chunk embeddings
            session.run("""
            CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
            FOR (c:Chunk)
            ON (c.embedding)
            OPTIONS {
                indexConfig: {
                    `vector.dimensions`: 768,
                    `vector.similarity_function`: 'cosine'
                }
            }
            """)
            logger.info("Successfully created vector search index")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_database() 