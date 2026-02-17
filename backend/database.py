import aiosqlite

DB_PATH = "data/sdlc_pipeline.db"


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                brief TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created',
                current_stage TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                agent TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '{}',
                parent_ids TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (id, run_id),
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );

            CREATE TABLE IF NOT EXISTS decision_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '{}',
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );

            CREATE TABLE IF NOT EXISTS hitl_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                feedback TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                resolved_at TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );
        """)
        await db.commit()
