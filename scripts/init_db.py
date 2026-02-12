#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database():
    """Create database tables"""
    DATABASE_URL = "postgresql://digital_twin:digital_pass@localhost:5432/digital_twin_db"
    
    engine = create_engine(DATABASE_URL)
    
    # SQL for creating tables
    create_tables_sql = """
    -- Schemas
    CREATE TABLE IF NOT EXISTS schemas (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        definition JSONB NOT NULL,
        user_id UUID,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP
    );

    -- Generation jobs
    CREATE TABLE IF NOT EXISTS generation_jobs (
        id UUID PRIMARY KEY,
        schema_id UUID REFERENCES schemas(id),
        status VARCHAR(50) DEFAULT 'pending',
        job_type VARCHAR(50),
        row_count INTEGER NOT NULL,
        entity_counts JSONB,
        parameters JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        result_url VARCHAR(500),
        error_message TEXT
    );

    -- Correlation rules
    CREATE TABLE IF NOT EXISTS correlation_rules (
        id UUID PRIMARY KEY,
        schema_id UUID REFERENCES schemas(id),
        name VARCHAR(255),
        rule_type VARCHAR(50) NOT NULL,
        source_entity VARCHAR(100),
        target_entity VARCHAR(100),
        condition JSONB NOT NULL,
        effect JSONB NOT NULL,
        priority INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Entity definitions
    CREATE TABLE IF NOT EXISTS entity_definitions (
        id UUID PRIMARY KEY,
        schema_id UUID REFERENCES schemas(id),
        name VARCHAR(100) NOT NULL,
        fields JSONB NOT NULL,
        count INTEGER DEFAULT 1000,
        parent_entity VARCHAR(100),
        parent_field VARCHAR(100),
        relationship_type VARCHAR(50),
        relationship_ratio FLOAT
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_schemas_user ON schemas(user_id);
    CREATE INDEX IF NOT EXISTS idx_correlation_schema ON correlation_rules(schema_id);
    CREATE INDEX IF NOT EXISTS idx_generation_status ON generation_jobs(status);
    CREATE INDEX IF NOT EXISTS idx_generation_created ON generation_jobs(created_at);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.commit()
            logger.info("Tables created successfully")
            
            # Check tables
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [row[0] for row in result]
            logger.info(f"Tables: {', '.join(tables)}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
