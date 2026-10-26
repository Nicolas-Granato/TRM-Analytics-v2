import './run_audit.css';

interface RunAuditProps {
  onClick: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function RunAudit({ onClick, isLoading = false, disabled = false }: RunAuditProps) {
  return (
    <button 
      id="run_audit" 
      className={`trm-btn-run ${isLoading ? 'loading' : ''}`}
      onClick={onClick}
      disabled={disabled || isLoading}
    >
      {isLoading ? '⏳ Processando Auditoria...' : '► Executar Auditoria Fiscal'}
    </button>
  );
}