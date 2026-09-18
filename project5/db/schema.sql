CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    building_id TEXT,
    primary_property_type TEXT,
    gross_floor_area FLOAT,
    year_built INT,
    site_energy_use FLOAT
);

CREATE TABLE ml_inputs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feature1 FLOAT NOT NULL,
    feature2 FLOAT NOT NULL
);

CREATE TABLE ml_predictions (
    id SERIAL PRIMARY KEY,
    input_id INT REFERENCES ml_inputs(id),
    prediction INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
