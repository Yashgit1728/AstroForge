import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, Text } from '@react-three/drei';
import * as THREE from 'three';

interface CelestialBodyProps {
  position: [number, number, number];
  size: number;
  color: string;
  name: string;
  rotationSpeed?: number;
}

const CelestialBody: React.FC<CelestialBodyProps> = ({ 
  position, 
  size, 
  color, 
  name, 
  rotationSpeed = 0.01 
}) => {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += rotationSpeed;
    }
  });

  return (
    <group position={position}>
      <Sphere ref={meshRef} args={[size, 32, 32]}>
        <meshStandardMaterial color={color} />
      </Sphere>
      <Text
        position={[0, size + 0.5, 0]}
        fontSize={0.3}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {name}
      </Text>
    </group>
  );
};

interface TrajectoryLineProps {
  start: [number, number, number];
  end: [number, number, number];
  color?: string;
}

const TrajectoryLine: React.FC<TrajectoryLineProps> = ({ 
  start, 
  end, 
  color = '#00ff88' 
}) => {
  const points = [
    new THREE.Vector3(...start),
    new THREE.Vector3(...end)
  ];
  
  const geometry = new THREE.BufferGeometry().setFromPoints(points);

  return (
    <line>
      <bufferGeometry attach="geometry" {...geometry} />
      <lineBasicMaterial attach="material" color={color} />
    </line>
  );
};

interface SolarSystemVisualizationProps {
  departureBody: string;
  targetBody: string;
  showTrajectory?: boolean;
}

const SolarSystemVisualization: React.FC<SolarSystemVisualizationProps> = ({
  departureBody,
  targetBody,
  showTrajectory = true
}) => {
  const celestialBodies = {
    earth: { position: [0, 0, 0] as [number, number, number], size: 1, color: '#4A90E2', name: 'Earth' },
    moon: { position: [3, 0, 0] as [number, number, number], size: 0.3, color: '#C0C0C0', name: 'Moon' },
    mars: { position: [8, 0, 0] as [number, number, number], size: 0.7, color: '#CD5C5C', name: 'Mars' },
    venus: { position: [-4, 0, 0] as [number, number, number], size: 0.9, color: '#FFC649', name: 'Venus' },
    jupiter: { position: [15, 0, 0] as [number, number, number], size: 2.5, color: '#D2691E', name: 'Jupiter' },
    saturn: { position: [20, 0, 0] as [number, number, number], size: 2.2, color: '#FAD5A5', name: 'Saturn' }
  };

  const departure = celestialBodies[departureBody as keyof typeof celestialBodies];
  const target = celestialBodies[targetBody as keyof typeof celestialBodies];

  return (
    <div className="w-full h-96 bg-black rounded-lg overflow-hidden">
      <Canvas camera={{ position: [0, 10, 25], fov: 60 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[0, 0, 0]} intensity={1} color="#FFF8DC" />
        
        {/* Sun */}
        <Sphere args={[0.5, 32, 32]} position={[0, 0, 0]}>
          <meshBasicMaterial color="#FFD700" />
        </Sphere>
        <Text
          position={[0, -1, 0]}
          fontSize={0.3}
          color="white"
          anchorX="center"
          anchorY="middle"
        >
          Sun
        </Text>

        {/* Celestial Bodies */}
        {Object.entries(celestialBodies).map(([key, body]) => (
          <CelestialBody
            key={key}
            position={body.position}
            size={body.size}
            color={body.color}
            name={body.name}
            rotationSpeed={key === 'earth' ? 0.02 : 0.01}
          />
        ))}

        {/* Trajectory Line */}
        {showTrajectory && departure && target && (
          <TrajectoryLine
            start={departure.position}
            end={target.position}
            color="#00ff88"
          />
        )}

        <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
      </Canvas>
    </div>
  );
};

export default SolarSystemVisualization;