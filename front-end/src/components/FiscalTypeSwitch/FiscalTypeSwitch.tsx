import './fiscal_type_switch.css';

interface FiscalTypeSwitchProps {
  isSped: boolean;
  onToggle: (checked: boolean) => void;
}

export function FiscalTypeSwitch({ isSped, onToggle }: FiscalTypeSwitchProps) {
  return (
    <div className="trm-switch-container">
      <span className={`trm-switch-label ${!isSped ? 'active' : ''}`}>SINTEGRA</span>
      <label className="trm-switch">
        <input 
          type="checkbox" 
          checked={isSped} 
          onChange={(e) => onToggle(e.target.checked)} 
        />
        <span className="trm-slider"></span>
      </label>
      <span className={`trm-switch-label ${isSped ? 'active' : ''}`}>SPED</span>
    </div>
  );
}