import './reset_audit.css';

interface ResetAuditProps {
  onReset: () => void;
  disabled?: boolean;
}

export function ResetAudit({ onReset, disabled = false }: ResetAuditProps) {
  return (
    <button 
      className="trm-btn-reset" 
      onClick={onReset} 
      disabled={disabled}
      title="Reiniciar painel de auditoria"
    >
      <span className="trm-reset-icon">🔄</span> Reiniciar Operação
    </button>
  );
}
