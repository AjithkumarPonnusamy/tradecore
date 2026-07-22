# Dedicated Historical Market Database Service

This service provides an isolated PostgreSQL + TimescaleDB instance tailored specifically for storing, querying, and managing billions of historical market data points (candles, corporate actions, and sessions) across multiple asset classes and data providers.

It is completely separate from the main application database.

## Directory Structure

```text
docker/
└── historical-market-db/
    ├── backups/            # Local backup dump folder (bind-mounted to container)
    │   └── .gitkeep
    ├── .env.example        # Environment variables template
    ├── docker-compose.yml  # Docker Compose service definition
    ├── init.sql            # Database schema, hypertable, and index setup
    └── README.md           # Operational documentation (this file)
```

## Quick Start

### 1. Configure Environment Variables
Copy the `.env.example` template to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set a secure password for the database:
```env
POSTGRES_PASSWORD=your_secure_password_here
```

### 2. Start the Service
Launch the container in detached mode:
```bash
docker compose up -d
```
The service will automatically:
1. Initialize the TimescaleDB extension.
2. Create the `market_data` schema.
3. Apply table structures (`symbols`, `candles`, `corporate_actions`, `trading_sessions`, `holidays`, and `metadata`).
4. Convert `candles` into a partitioned hypertable.
5. Create composite query indexes.

### 3. Verify Database Status
Check if the service is running and healthy:
```bash
docker compose ps
```
Or view the initialization logs:
```bash
docker compose logs -f historical-market-db
```

---

## Database Connection Details

*   **Host**: `localhost` (or `historical-market-db` within the `historical-market-net` Docker network)
*   **Port**: `5436` (configured in `.env`)
*   **Database Name**: `historical_market`
*   **Database User**: `market_admin`
*   **Password**: *The password specified in `.env`*

### Connecting via Command Line
```bash
docker exec -it historical-market-db psql -U market_admin -d historical_market
```

---

## TimescaleDB Operations & Tuning

### Hypertable Partitioning
The `candles` table is configured as a TimescaleDB hypertable partitioned by the `timestamp` column. The default chunk size is set to **7 days** (`INTERVAL '7 days'`).
*   For minute-level bars (`1m` to `15m`), a 7-day chunk size prevents memory bloat because active chunks fit into RAM.
*   If you ingest only daily/weekly data, you can increase the chunk interval to 1 month or 1 year inside `init.sql`.

### Query Optimization
The database is pre-indexed with:
*   A composite primary key: `(symbol_id, timeframe, timestamp)`
*   An analysis-optimized index: `(symbol_id, timeframe, timestamp DESC)`

This ensures rapid data retrieval when requesting chronological candle history for specific tickers.

### Production Performance Tuning
To optimize PostgreSQL and TimescaleDB for billions of rows, you should tune database configuration parameters (such as `shared_buffers`, `effective_cache_size`, and `work_mem`) based on your system's hardware resources.

Use the `timescaledb-tune` tool packaged within the container:
```bash
docker exec -it historical-market-db timescaledb-tune --yes --quiet
```
*Note: This command analyzes system specs and updates `/var/lib/postgresql/data/postgresql.conf` directly. Restart the container afterwards:*
```bash
docker compose restart
```

### Enabling TimescaleDB Compression
To save up to 90%+ of disk space and speed up historical scans over older data, you can enable native compression on the hypertable. Ingested candles should be compressed once they are no longer subject to updates.

To enable compression for candles older than 14 days, execute the following SQL commands:
```sql
-- Enable compression on the candles table
ALTER TABLE market_data.candles SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol_id, timeframe',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Add a policy to compress chunks older than 14 days automatically
SELECT add_compression_policy('market_data.candles', INTERVAL '14 days');
```

---

## Backups and Restoring Data

All database exports placed in the container's `/backups` directory will be persisted on the host machine inside the local `./backups/` folder.

### 1. Backing Up the Database
Generate a compressed SQL dump of the schema and data:
```bash
docker exec -t historical-market-db pg_dump -U market_admin -F c -b -v -f /backups/historical_market_backup.dump historical_market
```

### 2. Restoring the Database
To restore a backup into a clean database:
```bash
docker exec -t historical-market-db pg_restore -U market_admin -d historical_market -v /backups/historical_market_backup.dump
```
