import './summary_cards.css';

interface SummaryCardsProps {
  xmlCount: number;
  xmlValue: number;
  fiscalType: string;
  fiscalCount: number;
  fiscalValue: number;
  isAuditDone: boolean;
}

export function SummaryCards({
  xmlCount,
  xmlValue,
  fiscalType,
  fiscalCount,
  fiscalValue,
  isAuditDone
}: SummaryCardsProps) {
  const formatCurrency = (val: number) => 
    val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <div className="summary-wrapper">
      <div className="summary-card">
        <span className="summary-title">DOCUMENTOS XML (NF-E / NFC-E)</span>
        <div className="summary-metrics">
          <div>
            <label>QUANTIDADE</label>
            <p>{xmlCount}</p>
          </div>
          <div>
            <label>VALOR TOTAL</label>
            <p>{formatCurrency(xmlValue)}</p>
          </div>
        </div>
      </div>

      {isAuditDone && (
        <div className="audit-check-icon">
          ✔
        </div>
      )}

      <div className="summary-card">
        <span className="summary-title">ARQUIVO FISCAL ({fiscalType.toUpperCase()})</span>
        <div className="summary-metrics">
          <div>
            <label>QUANTIDADE</label>
            <p>{fiscalCount}</p>
          </div>
          <div>
            <label>VALOR TOTAL</label>
            <p>{formatCurrency(fiscalValue)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}