"""
Orbital mechanics calculations for space mission simulation.

This module implements Kepler's laws, orbital parameter calculations,
and trajectory planning algorithms including Hohmann transfers and bi-elliptic transfers.
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import numpy as np
from pydantic import BaseModel, Field

from ..models.mission import CelestialBody, TransferType


# Physical constants
G = 6.67430e-11  # Gravitational constant (m³/kg⋅s²)
AU = 1.496e11    # Astronomical unit (m)

# Celestial body data (mass in kg, radius in m, standard gravitational parameter in m³/s²)
CELESTIAL_BODIES = {
    CelestialBody.EARTH: {
        'mass': 5.972e24,
        'radius': 6.371e6,
        'mu': 3.986004418e14,
        'soi': 9.24e8,  # Sphere of influence (m)
        'orbital_radius': AU,  # Distance from Sun
        'orbital_period': 365.25 * 24 * 3600  # seconds
    },
    CelestialBody.MOON: {
        'mass': 7.342e22,
        'radius': 1.737e6,
        'mu': 4.9048695e12,
        'soi': 6.61e7,
        'orbital_radius': 3.844e8,  # Distance from Earth
        'orbital_period': 27.3 * 24 * 3600
    },
    CelestialBody.MARS: {
        'mass': 6.39e23,
        'radius': 3.390e6,
        'mu': 4.282837e13,
        'soi': 5.77e8,
        'orbital_radius': 1.524 * AU,
        'orbital_period': 687 * 24 * 3600
    },
    CelestialBody.VENUS: {
        'mass': 4.867e24,
        'radius': 6.052e6,
        'mu': 3.24859e14,
        'soi': 6.16e8,
        'orbital_radius': 0.723 * AU,
        'orbital_period': 225 * 24 * 3600
    },
    CelestialBody.JUPITER: {
        'mass': 1.898e27,
        'radius': 6.9911e7,
        'mu': 1.26686534e17,
        'soi': 4.82e10,
        'orbital_radius': 5.204 * AU,
        'orbital_period': 4333 * 24 * 3600
    },
    CelestialBody.SATURN: {
        'mass': 5.683e26,
        'radius': 5.8232e7,
        'mu': 3.7931187e16,
        'soi': 5.48e10,
        'orbital_radius': 9.573 * AU,
        'orbital_period': 10759 * 24 * 3600
    }
}

# Sun data for interplanetary calculations
SUN_MU = 1.32712440018e20  # m³/s²


@dataclass
class OrbitalElements:
    """Classical orbital elements."""
    semi_major_axis: float      # a (m)
    eccentricity: float         # e (dimensionless)
    inclination: float          # i (radians)
    longitude_of_ascending_node: float  # Ω (radians)
    argument_of_periapsis: float       # ω (radians)
    true_anomaly: float         # ν (radians)
    
    @property
    def semi_minor_axis(self) -> float:
        """Calculate semi-minor axis."""
        return self.semi_major_axis * math.sqrt(1 - self.eccentricity**2)
    
    @property
    def periapsis(self) -> float:
        """Calculate periapsis distance."""
        return self.semi_major_axis * (1 - self.eccentricity)
    
    @property
    def apoapsis(self) -> float:
        """Calculate apoapsis distance."""
        return self.semi_major_axis * (1 + self.eccentricity)
    
    def orbital_period(self, mu: float) -> float:
        """Calculate orbital period using Kepler's third law."""
        return 2 * math.pi * math.sqrt(self.semi_major_axis**3 / mu)
    
    def orbital_velocity(self, mu: float, radius: float) -> float:
        """Calculate orbital velocity at given radius using vis-viva equation."""
        return math.sqrt(mu * (2/radius - 1/self.semi_major_axis))


class OrbitalMechanics:
    """Core orbital mechanics calculations."""
    
    @staticmethod
    def kepler_equation_solver(mean_anomaly: float, eccentricity: float, 
                              tolerance: float = 1e-8, max_iterations: int = 100) -> float:
        """
        Solve Kepler's equation M = E - e*sin(E) for eccentric anomaly E.
        Uses Newton-Raphson method.
        """
        # Initial guess
        E = mean_anomaly if eccentricity < 0.8 else math.pi
        
        for _ in range(max_iterations):
            f = E - eccentricity * math.sin(E) - mean_anomaly
            df = 1 - eccentricity * math.cos(E)
            
            if abs(df) < 1e-12:  # Avoid division by zero
                break
                
            E_new = E - f / df
            
            if abs(E_new - E) < tolerance:
                return E_new
                
            E = E_new
        
        return E
    
    @staticmethod
    def true_anomaly_from_eccentric(eccentric_anomaly: float, eccentricity: float) -> float:
        """Convert eccentric anomaly to true anomaly."""
        cos_nu = (math.cos(eccentric_anomaly) - eccentricity) / (1 - eccentricity * math.cos(eccentric_anomaly))
        sin_nu = math.sqrt(1 - eccentricity**2) * math.sin(eccentric_anomaly) / (1 - eccentricity * math.cos(eccentric_anomaly))
        return math.atan2(sin_nu, cos_nu)
    
    @staticmethod
    def orbital_elements_from_state_vector(position: np.ndarray, velocity: np.ndarray, mu: float) -> OrbitalElements:
        """
        Calculate orbital elements from position and velocity vectors.
        
        Args:
            position: Position vector [x, y, z] in meters
            velocity: Velocity vector [vx, vy, vz] in m/s
            mu: Standard gravitational parameter in m³/s²
        """
        r = np.linalg.norm(position)
        v = np.linalg.norm(velocity)
        
        # Specific orbital energy
        energy = v**2 / 2 - mu / r
        
        # Semi-major axis
        a = -mu / (2 * energy)
        
        # Angular momentum vector
        h_vec = np.cross(position, velocity)
        h = np.linalg.norm(h_vec)
        
        # Eccentricity vector
        e_vec = np.cross(velocity, h_vec) / mu - position / r
        e = np.linalg.norm(e_vec)
        
        # Inclination
        i = math.acos(h_vec[2] / h)
        
        # Node vector
        n_vec = np.cross([0, 0, 1], h_vec)
        n = np.linalg.norm(n_vec)
        
        # Longitude of ascending node
        if n > 1e-10:
            omega_lan = math.acos(n_vec[0] / n)
            if n_vec[1] < 0:
                omega_lan = 2 * math.pi - omega_lan
        else:
            omega_lan = 0
        
        # Argument of periapsis
        if n > 1e-10 and e > 1e-10:
            omega = math.acos(np.dot(n_vec, e_vec) / (n * e))
            if e_vec[2] < 0:
                omega = 2 * math.pi - omega
        else:
            omega = 0
        
        # True anomaly
        if e > 1e-10:
            nu = math.acos(np.dot(e_vec, position) / (e * r))
            if np.dot(position, velocity) < 0:
                nu = 2 * math.pi - nu
        else:
            nu = 0
        
        return OrbitalElements(
            semi_major_axis=a,
            eccentricity=e,
            inclination=i,
            longitude_of_ascending_node=omega_lan,
            argument_of_periapsis=omega,
            true_anomaly=nu
        )
    
    @staticmethod
    def state_vector_from_orbital_elements(elements: OrbitalElements, mu: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate position and velocity vectors from orbital elements.
        
        Returns:
            Tuple of (position, velocity) vectors in meters and m/s
        """
        # Calculate position in orbital plane
        r = elements.semi_major_axis * (1 - elements.eccentricity**2) / (1 + elements.eccentricity * math.cos(elements.true_anomaly))
        
        x_orb = r * math.cos(elements.true_anomaly)
        y_orb = r * math.sin(elements.true_anomaly)
        
        # Calculate velocity in orbital plane
        p = elements.semi_major_axis * (1 - elements.eccentricity**2)
        vx_orb = -math.sqrt(mu / p) * math.sin(elements.true_anomaly)
        vy_orb = math.sqrt(mu / p) * (elements.eccentricity + math.cos(elements.true_anomaly))
        
        # Rotation matrices
        cos_omega = math.cos(elements.argument_of_periapsis)
        sin_omega = math.sin(elements.argument_of_periapsis)
        cos_i = math.cos(elements.inclination)
        sin_i = math.sin(elements.inclination)
        cos_Omega = math.cos(elements.longitude_of_ascending_node)
        sin_Omega = math.sin(elements.longitude_of_ascending_node)
        
        # Transform to inertial frame
        position = np.array([
            x_orb * (cos_omega * cos_Omega - sin_omega * cos_i * sin_Omega) - y_orb * (sin_omega * cos_Omega + cos_omega * cos_i * sin_Omega),
            x_orb * (cos_omega * sin_Omega + sin_omega * cos_i * cos_Omega) + y_orb * (cos_omega * cos_i * cos_Omega - sin_omega * sin_Omega),
            x_orb * (sin_omega * sin_i) + y_orb * (cos_omega * sin_i)
        ])
        
        velocity = np.array([
            vx_orb * (cos_omega * cos_Omega - sin_omega * cos_i * sin_Omega) - vy_orb * (sin_omega * cos_Omega + cos_omega * cos_i * sin_Omega),
            vx_orb * (cos_omega * sin_Omega + sin_omega * cos_i * cos_Omega) + vy_orb * (cos_omega * cos_i * cos_Omega - sin_omega * sin_Omega),
            vx_orb * (sin_omega * sin_i) + vy_orb * (cos_omega * sin_i)
        ])
        
        return position, velocity


class DeltaVCalculator:
    """Delta-V calculations for various maneuvers."""
    
    @staticmethod
    def hohmann_transfer(r1: float, r2: float, mu: float) -> Tuple[float, float, float]:
        """
        Calculate delta-V requirements for Hohmann transfer.
        
        Args:
            r1: Initial circular orbit radius (m)
            r2: Final circular orbit radius (m)
            mu: Standard gravitational parameter (m³/s²)
        
        Returns:
            Tuple of (delta_v1, delta_v2, total_delta_v) in m/s
        """
        # Initial and final circular velocities
        v1 = math.sqrt(mu / r1)
        v2 = math.sqrt(mu / r2)
        
        # Transfer orbit semi-major axis
        a_transfer = (r1 + r2) / 2
        
        # Transfer orbit velocities at periapsis and apoapsis
        v_transfer_1 = math.sqrt(mu * (2/r1 - 1/a_transfer))
        v_transfer_2 = math.sqrt(mu * (2/r2 - 1/a_transfer))
        
        # Delta-V requirements
        delta_v1 = abs(v_transfer_1 - v1)
        delta_v2 = abs(v2 - v_transfer_2)
        total_delta_v = delta_v1 + delta_v2
        
        return delta_v1, delta_v2, total_delta_v
    
    @staticmethod
    def bi_elliptic_transfer(r1: float, r2: float, r3: float, mu: float) -> Tuple[float, float, float, float]:
        """
        Calculate delta-V requirements for bi-elliptic transfer.
        
        Args:
            r1: Initial circular orbit radius (m)
            r2: Final circular orbit radius (m)
            r3: Intermediate apoapsis radius (m)
            mu: Standard gravitational parameter (m³/s²)
        
        Returns:
            Tuple of (delta_v1, delta_v2, delta_v3, total_delta_v) in m/s
        """
        # Initial and final circular velocities
        v1 = math.sqrt(mu / r1)
        v2 = math.sqrt(mu / r2)
        
        # First transfer orbit (r1 to r3)
        a1 = (r1 + r3) / 2
        v1_transfer = math.sqrt(mu * (2/r1 - 1/a1))
        v3_transfer1 = math.sqrt(mu * (2/r3 - 1/a1))
        
        # Second transfer orbit (r3 to r2)
        a2 = (r3 + r2) / 2
        v3_transfer2 = math.sqrt(mu * (2/r3 - 1/a2))
        v2_transfer = math.sqrt(mu * (2/r2 - 1/a2))
        
        # Delta-V requirements
        delta_v1 = abs(v1_transfer - v1)
        delta_v2 = abs(v3_transfer2 - v3_transfer1)
        delta_v3 = abs(v2 - v2_transfer)
        total_delta_v = delta_v1 + delta_v2 + delta_v3
        
        return delta_v1, delta_v2, delta_v3, total_delta_v
    
    @staticmethod
    def plane_change_delta_v(velocity: float, angle_rad: float) -> float:
        """
        Calculate delta-V for plane change maneuver.
        
        Args:
            velocity: Orbital velocity at maneuver point (m/s)
            angle_rad: Plane change angle in radians
        
        Returns:
            Delta-V requirement in m/s
        """
        return 2 * velocity * math.sin(angle_rad / 2)
    
    @staticmethod
    def escape_velocity(radius: float, mu: float) -> float:
        """
        Calculate escape velocity from given radius.
        
        Args:
            radius: Distance from center of body (m)
            mu: Standard gravitational parameter (m³/s²)
        
        Returns:
            Escape velocity in m/s
        """
        return math.sqrt(2 * mu / radius)
    
    @staticmethod
    def interplanetary_delta_v(departure_body: CelestialBody, target_body: CelestialBody) -> Dict[str, float]:
        """
        Calculate approximate delta-V requirements for interplanetary transfer.
        
        Args:
            departure_body: Starting celestial body
            target_body: Destination celestial body
        
        Returns:
            Dictionary with delta-V components
        """
        if departure_body not in CELESTIAL_BODIES or target_body not in CELESTIAL_BODIES:
            raise ValueError("Unsupported celestial body")
        
        dep_data = CELESTIAL_BODIES[departure_body]
        tgt_data = CELESTIAL_BODIES[target_body]
        
        # Simplified calculation using circular orbits
        r1 = dep_data['orbital_radius']
        r2 = tgt_data['orbital_radius']
        
        # Hohmann transfer in heliocentric frame
        delta_v1, delta_v2, total_helio = DeltaVCalculator.hohmann_transfer(r1, r2, SUN_MU)
        
        # Escape from departure body (from low orbit)
        low_orbit_alt = 200e3  # 200 km altitude
        escape_radius = dep_data['radius'] + low_orbit_alt
        v_escape = DeltaVCalculator.escape_velocity(escape_radius, dep_data['mu'])
        v_circular = math.sqrt(dep_data['mu'] / escape_radius)
        escape_delta_v = v_escape - v_circular
        
        # Capture at target body (to low orbit)
        capture_radius = tgt_data['radius'] + low_orbit_alt
        v_capture_escape = DeltaVCalculator.escape_velocity(capture_radius, tgt_data['mu'])
        v_capture_circular = math.sqrt(tgt_data['mu'] / capture_radius)
        capture_delta_v = v_capture_escape - v_capture_circular
        
        return {
            'escape_delta_v': escape_delta_v,
            'heliocentric_delta_v1': delta_v1,
            'heliocentric_delta_v2': delta_v2,
            'capture_delta_v': capture_delta_v,
            'total_delta_v': escape_delta_v + delta_v1 + delta_v2 + capture_delta_v
        }


class TrajectoryCalculator:
    """High-level trajectory planning calculations."""
    
    @staticmethod
    def calculate_transfer_time(r1: float, r2: float, mu: float, transfer_type: TransferType) -> float:
        """
        Calculate transfer time for different trajectory types.
        
        Args:
            r1: Initial orbit radius (m)
            r2: Final orbit radius (m)
            mu: Standard gravitational parameter (m³/s²)
            transfer_type: Type of transfer
        
        Returns:
            Transfer time in seconds
        """
        if transfer_type == TransferType.HOHMANN:
            a_transfer = (r1 + r2) / 2
            return math.pi * math.sqrt(a_transfer**3 / mu)
        
        elif transfer_type == TransferType.BI_ELLIPTIC:
            # Assume intermediate radius is 3 times the larger of r1, r2
            r3 = 3 * max(r1, r2)
            a1 = (r1 + r3) / 2
            a2 = (r3 + r2) / 2
            t1 = math.pi * math.sqrt(a1**3 / mu)
            t2 = math.pi * math.sqrt(a2**3 / mu)
            return t1 + t2
        
        elif transfer_type == TransferType.DIRECT:
            # Simplified direct transfer (faster than Hohmann)
            a_transfer = (r1 + r2) / 2
            return 0.7 * math.pi * math.sqrt(a_transfer**3 / mu)
        
        else:
            # Default to Hohmann
            a_transfer = (r1 + r2) / 2
            return math.pi * math.sqrt(a_transfer**3 / mu)
    
    @staticmethod
    def optimize_transfer_type(r1: float, r2: float, mu: float) -> Tuple[TransferType, float]:
        """
        Determine optimal transfer type based on delta-V efficiency.
        
        Args:
            r1: Initial orbit radius (m)
            r2: Final orbit radius (m)
            mu: Standard gravitational parameter (m³/s²)
        
        Returns:
            Tuple of (optimal_transfer_type, delta_v_requirement)
        """
        # Calculate Hohmann transfer
        _, _, hohmann_dv = DeltaVCalculator.hohmann_transfer(r1, r2, mu)
        
        # Calculate bi-elliptic transfer (if beneficial)
        ratio = r2 / r1 if r2 > r1 else r1 / r2
        
        if ratio > 11.94:  # Bi-elliptic becomes more efficient
            r3 = 3 * max(r1, r2)  # Intermediate radius
            _, _, _, bi_elliptic_dv = DeltaVCalculator.bi_elliptic_transfer(r1, r2, r3, mu)
            
            if bi_elliptic_dv < hohmann_dv:
                return TransferType.BI_ELLIPTIC, bi_elliptic_dv
        
        return TransferType.HOHMANN, hohmann_dv
    
    @staticmethod
    def calculate_launch_window(departure_body: CelestialBody, target_body: CelestialBody, 
                               start_date: float) -> Tuple[float, float]:
        """
        Calculate optimal launch window for interplanetary missions.
        
        Args:
            departure_body: Starting celestial body
            target_body: Destination celestial body
            start_date: Start date in seconds since epoch
        
        Returns:
            Tuple of (optimal_launch_time, window_duration) in seconds
        """
        if departure_body not in CELESTIAL_BODIES or target_body not in CELESTIAL_BODIES:
            raise ValueError("Unsupported celestial body")
        
        dep_data = CELESTIAL_BODIES[departure_body]
        tgt_data = CELESTIAL_BODIES[target_body]
        
        # Synodic period calculation
        if dep_data['orbital_period'] != tgt_data['orbital_period']:
            synodic_period = abs(1 / (1/dep_data['orbital_period'] - 1/tgt_data['orbital_period']))
        else:
            synodic_period = float('inf')
        
        # Launch window is typically a few weeks
        window_duration = min(30 * 24 * 3600, synodic_period * 0.1)  # 30 days or 10% of synodic period
        
        # Optimal launch time (simplified - would need more complex orbital mechanics)
        optimal_launch = start_date + (synodic_period * 0.25)  # Quarter synodic period offset
        
        return optimal_launch, window_duration