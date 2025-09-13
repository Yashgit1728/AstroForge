"""
Unit tests for orbital mechanics calculations.
"""

import math
import pytest
import numpy as np

from app.physics.orbital_mechanics import (
    OrbitalMechanics,
    OrbitalElements,
    DeltaVCalculator,
    TrajectoryCalculator,
    CELESTIAL_BODIES,
    SUN_MU
)
from app.models.mission import CelestialBody, TransferType


class TestOrbitalElements:
    """Test orbital elements calculations."""
    
    def test_orbital_elements_properties(self):
        """Test orbital element property calculations."""
        # Earth-like orbit
        elements = OrbitalElements(
            semi_major_axis=7000e3,  # 7000 km
            eccentricity=0.1,
            inclination=math.radians(28.5),
            longitude_of_ascending_node=0,
            argument_of_periapsis=0,
            true_anomaly=0
        )
        
        # Test semi-minor axis
        expected_b = 7000e3 * math.sqrt(1 - 0.1**2)
        assert abs(elements.semi_minor_axis - expected_b) < 1e-6
        
        # Test periapsis and apoapsis
        assert abs(elements.periapsis - 6300e3) < 1e-6
        assert abs(elements.apoapsis - 7700e3) < 1e-6
        
        # Test orbital period (Earth's mu)
        mu_earth = CELESTIAL_BODIES[CelestialBody.EARTH]['mu']
        period = elements.orbital_period(mu_earth)
        expected_period = 2 * math.pi * math.sqrt((7000e3)**3 / mu_earth)
        assert abs(period - expected_period) < 1e-6
    
    def test_orbital_velocity(self):
        """Test orbital velocity calculation."""
        elements = OrbitalElements(
            semi_major_axis=7000e3,
            eccentricity=0.0,  # Circular orbit
            inclination=0,
            longitude_of_ascending_node=0,
            argument_of_periapsis=0,
            true_anomaly=0
        )
        
        mu_earth = CELESTIAL_BODIES[CelestialBody.EARTH]['mu']
        velocity = elements.orbital_velocity(mu_earth, 7000e3)
        expected_velocity = math.sqrt(mu_earth / 7000e3)
        assert abs(velocity - expected_velocity) < 1e-6


class TestOrbitalMechanics:
    """Test core orbital mechanics calculations."""
    
    def test_kepler_equation_solver(self):
        """Test Kepler's equation solver."""
        # Test cases with known solutions
        test_cases = [
            (0, 0, 0),  # Circular orbit at periapsis
            (math.pi, 0, math.pi),  # Circular orbit at apoapsis
            (0, 0.5, 0),  # Elliptical orbit at periapsis
            (math.pi, 0.5, math.pi),  # Elliptical orbit at apoapsis
        ]
        
        for mean_anomaly, eccentricity, expected_E in test_cases:
            E = OrbitalMechanics.kepler_equation_solver(mean_anomaly, eccentricity)
            assert abs(E - expected_E) < 1e-8
    
    def test_true_anomaly_conversion(self):
        """Test conversion from eccentric to true anomaly."""
        # Test circular orbit (e=0)
        nu = OrbitalMechanics.true_anomaly_from_eccentric(math.pi/2, 0)
        assert abs(nu - math.pi/2) < 1e-8
        
        # Test elliptical orbit at periapsis
        nu = OrbitalMechanics.true_anomaly_from_eccentric(0, 0.5)
        assert abs(nu - 0) < 1e-8
    
    def test_state_vector_conversion(self):
        """Test conversion between orbital elements and state vectors."""
        mu_earth = CELESTIAL_BODIES[CelestialBody.EARTH]['mu']
        
        # Create test orbital elements
        elements = OrbitalElements(
            semi_major_axis=7000e3,
            eccentricity=0.1,
            inclination=math.radians(28.5),
            longitude_of_ascending_node=math.radians(45),
            argument_of_periapsis=math.radians(30),
            true_anomaly=math.radians(60)
        )
        
        # Convert to state vectors
        position, velocity = OrbitalMechanics.state_vector_from_orbital_elements(elements, mu_earth)
        
        # Convert back to orbital elements
        elements_back = OrbitalMechanics.orbital_elements_from_state_vector(position, velocity, mu_earth)
        
        # Check that we get back the same elements (within tolerance)
        assert abs(elements_back.semi_major_axis - elements.semi_major_axis) < 1e3
        assert abs(elements_back.eccentricity - elements.eccentricity) < 1e-6
        assert abs(elements_back.inclination - elements.inclination) < 1e-6


class TestDeltaVCalculator:
    """Test delta-V calculations."""
    
    def test_hohmann_transfer(self):
        """Test Hohmann transfer calculations."""
        mu_earth = CELESTIAL_BODIES[CelestialBody.EARTH]['mu']
        
        # LEO to GEO transfer
        r1 = 6.571e6  # LEO (200 km altitude)
        r2 = 4.2164e7  # GEO
        
        delta_v1, delta_v2, total_delta_v = DeltaVCalculator.hohmann_transfer(r1, r2, mu_earth)
        
        # Check that delta-V values are positive and reasonable
        assert delta_v1 > 0
        assert delta_v2 > 0
        assert total_delta_v == delta_v1 + delta_v2
        
        # LEO to GEO should require approximately 3.9 km/s total
        assert 3500 < total_delta_v < 4500  # m/s
    
    def test_bi_elliptic_transfer(self):
        """Test bi-elliptic transfer calculations."""
        mu_earth = CELESTIAL_BODIES[CelestialBody.EARTH]['mu']
        
        # Test case where bi-elliptic might be beneficial
        r1 = 6.571e6  # LEO
        r2 = 8.0e7    # Very high orbit
        r3 = 1.5e8    # Intermediate apoapsis
        
        delta_v1, delta_v2, delta_v3, total_delta_v = DeltaVCalculator.bi_elliptic_transfer(r1, r2, r3, mu_earth)
        
        # Check that all delta-V values are positive
        assert delta_v1 > 0
        assert delta_v2 > 0
        assert delta_v3 > 0
        assert total_delta_v == delta_v1 + delta_v2 + delta_v3
    
    def test_plane_change_delta_v(self):
        """Test plane change delta-V calculation."""
        velocity = 7500  # m/s (typical LEO velocity)
        angle = math.radians(30)  # 30 degree plane change
        
        delta_v = DeltaVCalculator.plane_change_delta_v(velocity, angle)
        
        # 30 degree plane change should require significant delta-V
        expected_dv = 2 * velocity * math.sin(angle / 2)
        assert abs(delta_v - expected_dv) < 1e-6
        assert delta_v > 1900  # Should be around 1950 m/s
    
    def test_escape_velocity(self):
        """Test escape velocity calculation."""
        earth_data = CELESTIAL_BODIES[CelestialBody.EARTH]
        
        # Earth escape velocity from surface
        v_escape = DeltaVCalculator.escape_velocity(earth_data['radius'], earth_data['mu'])
        
        # Earth escape velocity should be approximately 11.2 km/s
        assert 11000 < v_escape < 11300
    
    def test_interplanetary_delta_v(self):
        """Test interplanetary delta-V calculations."""
        # Earth to Mars transfer
        delta_v_data = DeltaVCalculator.interplanetary_delta_v(CelestialBody.EARTH, CelestialBody.MARS)
        
        # Check that all components are present and positive
        required_keys = ['escape_delta_v', 'heliocentric_delta_v1', 'heliocentric_delta_v2', 'capture_delta_v', 'total_delta_v']
        for key in required_keys:
            assert key in delta_v_data
            assert delta_v_data[key] > 0
        
        # Total should be sum of components
        expected_total = (delta_v_data['escape_delta_v'] + 
                         delta_v_data['heliocentric_delta_v1'] + 
                         delta_v_data['heliocentric_delta_v2'] + 
                         delta_v_data['capture_delta_v'])
        assert abs(delta_v_data['total_delta_v'] - expected_total) < 1e-6
        
        # Earth to Mars should require reasonable delta-V (roughly 12-15 km/s)
        assert 10000 < delta_v_data['total_delta_v'] < 20000


class TestTrajectoryCalculator:
    """Test trajectory planning calculations."""
    
    def test_transfer_time_calculation(self):
        """Test transfer time calculations for different types."""
        mu_earth = CELESTIAL_BODIES[CelestialBody.EARTH]['mu']
        r1 = 6.571e6  # LEO
        r2 = 4.2164e7  # GEO
        
        # Hohmann transfer time
        hohmann_time = TrajectoryCalculator.calculate_transfer_time(r1, r2, mu_earth, TransferType.HOHMANN)
        
        # Should be about 5.25 hours for LEO to GEO
        expected_time = math.pi * math.sqrt(((r1 + r2) / 2)**3 / mu_earth)
        assert abs(hohmann_time - expected_time) < 1e-6
        assert 18000 < hohmann_time < 20000  # seconds (5-6 hours)
        
        # Bi-elliptic should take longer
        bi_elliptic_time = TrajectoryCalculator.calculate_transfer_time(r1, r2, mu_earth, TransferType.BI_ELLIPTIC)
        assert bi_elliptic_time > hohmann_time
        
        # Direct should be faster
        direct_time = TrajectoryCalculator.calculate_transfer_time(r1, r2, mu_earth, TransferType.DIRECT)
        assert direct_time < hohmann_time
    
    def test_transfer_type_optimization(self):
        """Test optimal transfer type selection."""
        mu_earth = CELESTIAL_BODIES[CelestialBody.EARTH]['mu']
        
        # Small ratio - should prefer Hohmann
        r1 = 6.571e6
        r2 = 1.0e7
        transfer_type, delta_v = TrajectoryCalculator.optimize_transfer_type(r1, r2, mu_earth)
        assert transfer_type == TransferType.HOHMANN
        
        # Large ratio - might prefer bi-elliptic (though our simplified calculation may not show this)
        r1 = 6.571e6
        r2 = 1.0e8
        transfer_type, delta_v = TrajectoryCalculator.optimize_transfer_type(r1, r2, mu_earth)
        # Result depends on implementation details, just check it returns valid values
        assert transfer_type in [TransferType.HOHMANN, TransferType.BI_ELLIPTIC]
        assert delta_v > 0
    
    def test_launch_window_calculation(self):
        """Test launch window calculations."""
        start_date = 0  # Epoch
        
        # Earth to Mars
        launch_time, window_duration = TrajectoryCalculator.calculate_launch_window(
            CelestialBody.EARTH, CelestialBody.MARS, start_date
        )
        
        # Should return reasonable values
        assert launch_time > start_date
        assert window_duration > 0
        assert window_duration < 365 * 24 * 3600  # Less than a year
    
    def test_unsupported_celestial_body(self):
        """Test error handling for unsupported celestial bodies."""
        with pytest.raises(ValueError):
            DeltaVCalculator.interplanetary_delta_v(CelestialBody.EARTH, CelestialBody.ASTEROID_BELT)


class TestPhysicalConstants:
    """Test that physical constants are reasonable."""
    
    def test_celestial_body_data(self):
        """Test that celestial body data is reasonable."""
        # Earth data
        earth = CELESTIAL_BODIES[CelestialBody.EARTH]
        assert 5.9e24 < earth['mass'] < 6.0e24  # kg
        assert 6.3e6 < earth['radius'] < 6.4e6  # m
        assert 3.9e14 < earth['mu'] < 4.0e14    # m³/s²
        
        # Moon data
        moon = CELESTIAL_BODIES[CelestialBody.MOON]
        assert moon['mass'] < earth['mass']
        assert moon['radius'] < earth['radius']
        assert moon['mu'] < earth['mu']
        
        # Mars data
        mars = CELESTIAL_BODIES[CelestialBody.MARS]
        assert mars['mass'] < earth['mass']
        assert mars['radius'] < earth['radius']
        assert mars['mu'] < earth['mu']
    
    def test_gravitational_constant(self):
        """Test gravitational constant value."""
        from app.physics.orbital_mechanics import G
        assert 6.67e-11 < G < 6.68e-11
    
    def test_astronomical_unit(self):
        """Test astronomical unit value."""
        from app.physics.orbital_mechanics import AU
        assert 1.49e11 < AU < 1.50e11


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_circular_orbit_edge_cases(self):
        """Test calculations with circular orbits (e=0)."""
        elements = OrbitalElements(
            semi_major_axis=7000e3,
            eccentricity=0.0,  # Circular
            inclination=0,
            longitude_of_ascending_node=0,
            argument_of_periapsis=0,
            true_anomaly=0
        )
        
        # Periapsis and apoapsis should be equal to semi-major axis
        assert abs(elements.periapsis - elements.semi_major_axis) < 1e-6
        assert abs(elements.apoapsis - elements.semi_major_axis) < 1e-6
        assert abs(elements.semi_minor_axis - elements.semi_major_axis) < 1e-6
    
    def test_parabolic_orbit_edge_case(self):
        """Test calculations near parabolic orbit (e=1)."""
        elements = OrbitalElements(
            semi_major_axis=1e10,  # Very large for near-parabolic
            eccentricity=0.99,     # Near parabolic
            inclination=0,
            longitude_of_ascending_node=0,
            argument_of_periapsis=0,
            true_anomaly=0
        )
        
        # Should still calculate reasonable values
        assert elements.periapsis > 0
        assert elements.apoapsis > elements.periapsis
    
    def test_zero_delta_v_cases(self):
        """Test cases where delta-V should be zero or minimal."""
        mu_earth = CELESTIAL_BODIES[CelestialBody.EARTH]['mu']
        
        # Same orbit transfer
        r1 = r2 = 7000e3
        delta_v1, delta_v2, total_delta_v = DeltaVCalculator.hohmann_transfer(r1, r2, mu_earth)
        
        # Should be very small (numerical precision limits)
        assert total_delta_v < 1e-6
        
        # Zero plane change
        velocity = 7500
        angle = 0
        delta_v = DeltaVCalculator.plane_change_delta_v(velocity, angle)
        assert abs(delta_v) < 1e-10