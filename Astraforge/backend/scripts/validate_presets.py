#!/usr/bin/env python3
"""
Validation script for vehicle presets data.
"""
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.vehicle_presets import REALISTIC_VEHICLE_PRESETS, validate_spacecraft_config
from app.models.mission import VehicleType


def validate_all_presets():
    """Validate all realistic vehicle presets."""
    print("🔍 Validating vehicle presets...")
    
    total_presets = len(REALISTIC_VEHICLE_PRESETS)
    valid_presets = 0
    
    for i, preset_data in enumerate(REALISTIC_VEHICLE_PRESETS, 1):
        name = preset_data["name"]
        config = preset_data["config"]
        
        print(f"\n{i}/{total_presets}. Validating '{name}'...")
        
        # Validate the spacecraft configuration
        config_dict = config.model_dump()
        errors = validate_spacecraft_config(config_dict)
        
        if errors:
            print(f"  ❌ Validation errors:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  ✅ Valid configuration")
            valid_presets += 1
            
        # Print key specs
        print(f"    Type: {config.vehicle_type.value}")
        print(f"    Mass: {config.mass_kg} kg")
        print(f"    Thrust: {config.thrust_n} N")
        print(f"    Specific Impulse: {config.specific_impulse_s} s")
        print(f"    Payload: {config.payload_mass_kg} kg")
        
        # Calculate some derived metrics
        if config.fuel_capacity_kg > 0:
            mass_ratio = config.mass_kg / (config.mass_kg - config.fuel_capacity_kg)
            print(f"    Mass Ratio: {mass_ratio:.2f}")
        
        if config.thrust_n > 0:
            twr = config.thrust_n / (config.mass_kg * 9.81)
            print(f"    Thrust-to-Weight: {twr:.3f}")
    
    print(f"\n📊 Summary:")
    print(f"  Total presets: {total_presets}")
    print(f"  Valid presets: {valid_presets}")
    print(f"  Invalid presets: {total_presets - valid_presets}")
    
    if valid_presets == total_presets:
        print("🎉 All presets are valid!")
        return True
    else:
        print("⚠️  Some presets have validation errors.")
        return False


def analyze_preset_distribution():
    """Analyze the distribution of vehicle types in presets."""
    print("\n📈 Analyzing preset distribution...")
    
    type_counts = {}
    for preset_data in REALISTIC_VEHICLE_PRESETS:
        vehicle_type = preset_data["config"].vehicle_type
        type_counts[vehicle_type] = type_counts.get(vehicle_type, 0) + 1
    
    print("\nVehicle type distribution:")
    for vehicle_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {vehicle_type.value}: {count} presets")
    
    # Mass distribution
    masses = [preset["config"].mass_kg for preset in REALISTIC_VEHICLE_PRESETS]
    print(f"\nMass range:")
    print(f"  Minimum: {min(masses):.1f} kg")
    print(f"  Maximum: {max(masses):.1f} kg")
    print(f"  Average: {sum(masses)/len(masses):.1f} kg")


if __name__ == "__main__":
    print("🚀 Vehicle Presets Validation")
    print("=" * 40)
    
    # Validate all presets
    all_valid = validate_all_presets()
    
    # Analyze distribution
    analyze_preset_distribution()
    
    print("\n" + "=" * 40)
    if all_valid:
        print("✅ All validations passed!")
        sys.exit(0)
    else:
        print("❌ Some validations failed!")
        sys.exit(1)