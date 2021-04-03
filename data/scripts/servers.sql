CREATE TABLE IF NOT EXISTS servers (
    server_id bigint PRIMARY KEY,
    server_name VARCHAR(100),
    owner_id bigint,
    prefix VARCHAR(5) DEFAULT '-',
    muterole BIGINT,
    profanities TEXT,
    autoroles TEXT,
    antiinvite BOOLEAN DEFAULT False,
    reassign BOOLEAN DEFAULT True
);

CREATE TABLE IF NOT EXISTS logging (
    server_id BIGINT PRIMARY KEY,
    message_edits BOOLEAN DEFAULT True,
    message_deletions BOOLEAN DEFAULT True,
    role_changes BOOLEAN DEFAULT True,
    channel_updates BOOLEAN DEFAULT True,
    name_updates BOOLEAN DEFAULT True,
    voice_state_updates BOOLEAN DEFAULT True,
    avatar_changes BOOLEAN DEFAULT True,
    bans BOOLEAN DEFAULT True,
    leaves BOOLEAN DEFAULT True,
    joins BOOLEAN DEFAULT True,
    ignored_channels TEXT,
    logchannel BIGINT,
    logging_webhook_id VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS ignored (
    server_id BIGINT,
    user_id BIGINT,
    author_id BIGINT,
    react BOOLEAN,
    timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mutes (
    muted_user bigint,
    server_id bigint,
    role_ids text,
    endtime timestamp
);

CREATE TABLE IF NOT EXISTS lockedchannels (
    channel_id bigint PRIMARY KEY,
    server_id bigint,
    command_executor bigint,
    everyone_perms text
);

CREATE TABLE IF NOT EXISTS warn (
    user_id bigint,
    server_id bigint,
    warnings smallint
);
