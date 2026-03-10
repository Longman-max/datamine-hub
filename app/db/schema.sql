CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    api_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_nodes (
    hash TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS node_edges (
    parent_hash TEXT NOT NULL,
    child_hash TEXT NOT NULL,
    PRIMARY KEY (parent_hash, child_hash),
    FOREIGN KEY(parent_hash) REFERENCES data_nodes(hash),
    FOREIGN KEY(child_hash) REFERENCES data_nodes(hash)
);

CREATE TABLE IF NOT EXISTS channels (
    name TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(channel_name) REFERENCES channels(name),
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);
