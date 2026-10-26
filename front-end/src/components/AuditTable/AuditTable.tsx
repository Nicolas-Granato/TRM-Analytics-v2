import './audit_table.css';

export interface AuditItem {
  access_key: string;
  nfe_model?: string;
  xml_value: number;
  sped_value?: number;
  sintegra_value?: number;
  value_difference: number;
  xml_emission_date?: string;
  sped_emission_date?: string;
  divergence_type: string;
}

interface AuditTableProps {
  items: AuditItem[];
  onExportExcel: () => void;
}

export function AuditTable({ items, onExportExcel }: AuditTableProps) {
  const formatCurrency = (val: number) =>
    ((val || 0) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <div className="trm-table-card">
      <div className="trm-table-header">
        <div>
          <h3>Prévia do Relatório de Inconsistências</h3>
          <p>{items.length} registros com divergência encontrados</p>
        </div>
        <button className="trm-btn-excel" onClick={onExportExcel}>
          📊 Exportar para Excel
        </button>
      </div>

      <div className="trm-table-wrapper">
        <table className="trm-data-table">
          <thead>
            <tr>
              <th>Chave de Acesso / Doc</th>
              <th>Data Emissão (XML)</th>
              <th>Valor XML</th>
              <th>Valor Fiscal</th>
              <th>Diferença</th>
              <th>Tipo de Divergência</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => {
              const valorFiscal = item.sped_value ?? item.sintegra_value ?? 0;
              const diff = item.value_difference ?? (item.xml_value - valorFiscal);

              return (
                <tr key={index}>
                  <td className="font-mono">{item.access_key || 'N/A'}</td>
                  <td>{item.xml_emission_date || item.sped_emission_date || '-'}</td>
                  <td>{formatCurrency(item.xml_value)}</td>
                  <td>{formatCurrency(valorFiscal)}</td>
                  <td className={diff !== 0 ? 'text-divergent' : ''}>
                    {formatCurrency(diff)}
                  </td>
                  <td>
                    <span className={`status-badge ${diff === 0 ? 'badge-ok' : 'badge-alert'}`}>
                      {item.divergence_type ? item.divergence_type.replace(/_/g, ' ') : (diff === 0 ? 'OK' : 'DIVERGÊNCIA')}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}