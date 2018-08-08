USE waggle;

CREATE TABLE IF NOT EXISTS waggle.sensor_data_by_date (
    date                  DATE,
    timestamp             TIMESTAMP,
    node_id               TEXT,
    subsystem             TEXT,
    sensor                TEXT,
    parameter             TEXT,
    value                 TEXT,
    PRIMARY KEY  (date, timestamp, node_id, subsystem, sensor, parameter)
);

CREATE TABLE IF NOT EXISTS waggle.sensor_data_by_type (
    node_id               TEXT,
    subsystem             TEXT,
    sensor                TEXT,
    parameter             TEXT,
    timestamp             TIMESTAMP,
    value                 TEXT,
    PRIMARY KEY  ((node_id, subsystem, sensor, parameter), timestamp)
);
