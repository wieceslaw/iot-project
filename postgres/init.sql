create table if not exists "order" (
    id UUID PRIMARY KEY,
    client_id UUID,
    volume INT,
    created_at TIMESTAMP,
    finished_at TIMESTAMP
);
