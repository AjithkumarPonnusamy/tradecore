import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os

def create_database():
    db_name = "tradecore"
    pwd = "ak"
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    
    try:
        cfg = {"user": "postgres", "password": pwd, "host": host, "port": port}
        conn = psycopg2.connect(dbname="postgres", **cfg)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if tradecore db exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}';")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Database '{db_name}' does not exist. Creating...")
            cursor.execute(f"CREATE DATABASE {db_name};")
            print(f"Database '{db_name}' created successfully!")
        else:
            print(f"Database '{db_name}' already exists.")
            
        cursor.close()
        conn.close()

        # Connect to tradecore database to execute schema initialization DDL
        conn_app = psycopg2.connect(dbname=db_name, **cfg)
        conn_app.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor_app = conn_app.cursor()

        sql_script_path = os.path.join(os.path.dirname(__file__), "..", "docker", "init_tradecore_db.sql")
        if os.path.exists(sql_script_path):
            print(f"Executing schema initialization script from {sql_script_path}...")
            with open(sql_script_path, "r", encoding="utf-8") as f:
                sql_content = f.read()
            cursor_app.execute(sql_content)
            print("Successfully initialized 9 domain schemas and partitioned market candles!")
        
        cursor_app.close()
        conn_app.close()
        
        # Write connection string to backend/.env
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        db_url = f"postgresql://postgres:{pwd}@{host}:{port}/{db_name}"
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                if line.startswith("DATABASE_URL="):
                    new_lines.append(f"DATABASE_URL={db_url}\n")
                else:
                    new_lines.append(line)
            with open(env_path, "w") as f:
                f.writelines(new_lines)
            print("Successfully updated backend/.env with database credentials.")
            
    except Exception as e:
        print(f"Error checking/creating database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    create_database()
