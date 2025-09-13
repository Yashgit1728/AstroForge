import React from 'react';

interface VehiclePreset {
  id: string;
  name: string;
  description: string;
  vehicleType: string;
  massKg: number;
  thrustN: number;
  specificImpulseS: number;
  fuelCapacityKg: number;
  payloadMassKg: number;
  powerW: number;
}

interface VehicleCardProps {
  vehicle: VehiclePreset;
  onSelect: (vehicle: VehiclePreset) => void;
  isSelected: boolean;
}

const VehicleCard: React.FC<VehicleCardProps> = ({ vehicle, onSelect, isSelected }) => {
  const getVehicleIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'cubesat': return '📡';
      case 'small_sat': return '🛰️';
      case 'medium_sat': return '🛰️';
      case 'large_sat': return '🛰️';
      case 'probe': return '🚀';
      case 'lander': return '🌙';
      case 'rover': return '🤖';
      case 'crewed': return '👨‍🚀';
      default: return '🚀';
    }
  };

  const formatNumber = (num: number, unit: string) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M ${unit}`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k ${unit}`;
    }
    return `${num.toFixed(1)} ${unit}`;
  };

  return (
    <div
      className={`bg-space-800/50 backdrop-blur-sm rounded-lg p-6 border-2 transition-all cursor-pointer hover:bg-space-700/50 ${
        isSelected ? 'border-blue-400 bg-space-700/50' : 'border-space-600'
      }`}
      onClick={() => onSelect(vehicle)}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getVehicleIcon(vehicle.vehicleType)}</span>
          <div>
            <h3 className="text-lg font-semibold text-white">{vehicle.name}</h3>
            <p className="text-space-300 text-sm capitalize">
              {vehicle.vehicleType.replace('_', ' ')}
            </p>
          </div>
        </div>
        {isSelected && (
          <div className="w-6 h-6 bg-blue-400 rounded-full flex items-center justify-center">
            <span className="text-white text-xs">✓</span>
          </div>
        )}
      </div>
      
      <p className="text-space-200 text-sm mb-4 line-clamp-2">
        {vehicle.description}
      </p>
      
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-space-900 rounded p-2">
          <div className="text-space-400 text-xs">Mass</div>
          <div className="text-white font-medium">{formatNumber(vehicle.massKg, 'kg')}</div>
        </div>
        <div className="bg-space-900 rounded p-2">
          <div className="text-space-400 text-xs">Thrust</div>
          <div className="text-white font-medium">{formatNumber(vehicle.thrustN, 'N')}</div>
        </div>
        <div className="bg-space-900 rounded p-2">
          <div className="text-space-400 text-xs">Isp</div>
          <div className="text-white font-medium">{vehicle.specificImpulseS}s</div>
        </div>
        <div className="bg-space-900 rounded p-2">
          <div className="text-space-400 text-xs">Payload</div>
          <div className="text-white font-medium">{formatNumber(vehicle.payloadMassKg, 'kg')}</div>
        </div>
      </div>
    </div>
  );
};

export default VehicleCard;