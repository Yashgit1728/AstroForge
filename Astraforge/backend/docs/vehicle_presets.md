# Vehicle Preset System

The Vehicle Preset System provides a comprehensive solution for managing spacecraft configurations in AstraForge. It allows users to create, store, and reuse realistic spacecraft configurations for mission planning.

## Features

### Core Functionality
- **CRUD Operations**: Create, read, update, and delete vehicle presets
- **Realistic Presets**: Pre-seeded database with 10 realistic spacecraft configurations
- **Validation**: Comprehensive validation of spacecraft parameters
- **Filtering**: Filter presets by vehicle type, public status, and creator
- **API Integration**: RESTful API endpoints for all operations

### Vehicle Types Supported
- **CubeSat**: Small satellites (1U, 3U, 6U configurations)
- **SmallSat**: Standard small satellites for commercial missions
- **Medium Satellite**: Mid-size satellites for telecommunications and Earth observation
- **Large Satellite**: Heavy satellites for geostationary operations
- **Probe**: Interplanetary exploration vehicles
- **Lander**: Surface landing vehicles (Moon, Mars)
- **Rover**: Surface exploration vehicles
- **Crewed**: Human-rated spacecraft

## Database Schema

### VehiclePreset Table
```sql
CREATE TABLE vehicle_presets (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    vehicle_type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    mass_kg FLOAT NOT NULL,
    thrust_n FLOAT NOT NULL,
    specific_impulse_s FLOAT NOT NULL
);
```

## API Endpoints

### Base URL: `/api/v1/vehicle-presets`

#### Create Preset
- **POST** `/`
- **Body**: VehiclePresetCreate schema
- **Response**: VehiclePresetResponse

#### List Presets
- **GET** `/`
- **Query Parameters**:
  - `vehicle_type`: Filter by vehicle type
  - `is_public`: Filter by public status
  - `created_by`: Filter by creator
  - `limit`: Maximum results (default: 50)
  - `offset`: Skip results (default: 0)
- **Response**: VehiclePresetListResponse

#### Get Preset by ID
- **GET** `/{preset_id}`
- **Response**: VehiclePresetResponse

#### Get Preset by Name
- **GET** `/by-name/{preset_name}`
- **Response**: VehiclePresetResponse

#### Update Preset
- **PUT** `/{preset_id}`
- **Body**: VehiclePresetUpdate schema
- **Response**: VehiclePresetResponse

#### Delete Preset
- **DELETE** `/{preset_id}`
- **Response**: Success message

#### Seed Database
- **POST** `/seed`
- **Response**: Success message

#### Get Spacecraft Config
- **GET** `/{preset_id}/spacecraft-config`
- **Response**: SpacecraftConfig

## Validation Rules

### Physical Constraints
- Fuel capacity cannot exceed 95% of total mass
- Payload mass cannot exceed 80% of total mass
- All masses must be positive
- Thrust and specific impulse must be non-negative

### Vehicle-Specific Rules
- **CubeSat**: Mass should not exceed 50 kg
- **Rover**: Should not have propulsive thrust
- **Spacecraft with thrust**: Must have specific impulse > 0

## Pre-seeded Presets

The system comes with 10 realistic vehicle presets:

1. **CubeSat 3U** (4 kg) - Standard 3U CubeSat
2. **CubeSat 6U** (8 kg) - Enhanced 6U CubeSat
3. **SmallSat Standard** (150 kg) - Commercial small satellite
4. **Medium Satellite** (1,500 kg) - Telecommunications satellite
5. **Large Geostationary Satellite** (6,000 kg) - Heavy GEO satellite
6. **Mars Reconnaissance Probe** (2,180 kg) - Interplanetary probe
7. **Lunar Lander** (3,500 kg) - Moon landing vehicle
8. **Mars Rover** (899 kg) - Surface exploration rover
9. **Crew Dragon Capsule** (12,055 kg) - Human-rated spacecraft
10. **Deep Space Probe** (5,712 kg) - Outer solar system explorer

## Usage Examples

### Python Service Usage
```python
from app.services.vehicle_presets import VehiclePresetService
from app.models.mission import SpacecraftConfig, VehicleType

# Create service
service = VehiclePresetService(db_session)

# Create a new preset
config = SpacecraftConfig(
    vehicle_type=VehicleType.MEDIUM_SAT,
    name="My Satellite",
    mass_kg=1000.0,
    fuel_capacity_kg=400.0,
    thrust_n=500.0,
    specific_impulse_s=300.0,
    payload_mass_kg=200.0
)

preset = await service.create_preset(
    name="Custom Satellite",
    description="My custom satellite configuration",
    spacecraft_config=config
)

# List presets
presets = await service.list_presets(
    vehicle_type=VehicleType.MEDIUM_SAT,
    is_public=True
)
```

### API Usage
```bash
# Create a preset
curl -X POST "http://localhost:8000/api/v1/vehicle-presets/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Satellite",
    "description": "Custom satellite configuration",
    "spacecraft_config": {
      "vehicle_type": "medium_sat",
      "name": "Test Satellite",
      "mass_kg": 1000.0,
      "fuel_capacity_kg": 400.0,
      "thrust_n": 500.0,
      "specific_impulse_s": 300.0,
      "payload_mass_kg": 200.0,
      "power_w": 2000.0
    }
  }'

# List all presets
curl "http://localhost:8000/api/v1/vehicle-presets/"

# Filter by vehicle type
curl "http://localhost:8000/api/v1/vehicle-presets/?vehicle_type=cubesat"

# Seed database with realistic presets
curl -X POST "http://localhost:8000/api/v1/vehicle-presets/seed"
```

## Testing

The system includes comprehensive tests:

### Service Tests (`test_vehicle_presets.py`)
- CRUD operations
- Validation logic
- Database seeding
- Configuration conversion

### API Tests (`test_vehicle_presets_api.py`)
- All API endpoints
- Error handling
- Filtering and pagination
- Authentication integration

### Run Tests
```bash
# Run all vehicle preset tests
python -m pytest tests/test_vehicle_presets.py tests/test_vehicle_presets_api.py -v

# Validate preset data
python scripts/validate_presets.py
```

## Database Seeding

### Automatic Seeding
```bash
# Seed database with realistic presets
python scripts/seed_database.py
```

### API Seeding
```bash
curl -X POST "http://localhost:8000/api/v1/vehicle-presets/seed"
```

## Performance Characteristics

The system is optimized for performance with:
- Database indexes on commonly queried fields
- Efficient filtering and pagination
- Cached performance metrics in the database
- Async/await throughout for non-blocking operations

## Integration with Mission Planning

Vehicle presets integrate seamlessly with the mission planning system:
- Presets can be loaded into mission spacecraft configurations
- Validation ensures mission feasibility
- Performance metrics help with mission optimization
- Realistic data improves simulation accuracy