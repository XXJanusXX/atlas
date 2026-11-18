import duckdb


class Ledger:
    def __init__(self, database_path: str) -> None:
        self.connection = duckdb.connect(database_path)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id VARCHAR PRIMARY KEY,
                event_type VARCHAR NOT NULL,
                occurred_at TIMESTAMP NOT NULL,
                payload JSON NOT NULL,
                previous_hash VARCHAR,
                event_hash VARCHAR NOT NULL
            )
        """)

    def close(self) -> None:
        self.connection.close()
