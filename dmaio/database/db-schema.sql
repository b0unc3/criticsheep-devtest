-- Elevators table: Tracks each elevator, its current state, and resting behavior
CREATE TABLE elevators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL
);

-- Elevator Movements: Logs elevator trips (for ML training data)
CREATE TABLE movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    elevator_id INTEGER NOT NULL,
    start_floor INTEGER NOT NULL,
    end_floor INTEGER NOT NULL,
    arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    departure_time TIMESTAMP,
    FOREIGN KEY (elevator_id) REFERENCES elevators(id)
);

-- -- Indexes for data queries
-- CREATE INDEX idx_elevator_status ON elevators(status);
-- CREATE INDEX idx_calls_requested_floor ON elevator_calls(requested_floor);
CREATE INDEX idx_movements_start_floor ON movements(start_floor);
CREATE INDEX idx_movements_end_floor ON movements(end_floor);
