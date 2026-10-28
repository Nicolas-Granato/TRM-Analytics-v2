import './audit_table.css';

export interface AuditItem {
  cnpj_issuer?: string;
  nfe_model?: string;
  composite_key?: string;
  access_key?: string;
  xml_value: number;
  sped_value?: number;
  sintegra_value?: number;
  value_difference: number;
  xml_emission_date?: string;
  sped_emission_date?: string;
  sintegra_emission_date?: string;
  divergence_type: string;
}

interface AuditTableProps {
  items: AuditItem[];
  isSped: boolean;
  onExportExcel: () => void;
}

export function AuditTable({ items, isSped, onExportExcel }: AuditTableProps) {
  const formatCurrency = (val: number) =>
    ((val || 0) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const renderModelBadge = (model?: string) => {
    const cleanModel = (model || '').trim();
    if (cleanModel === '65') {
      return <span className="model-badge badge-nfce">NFC-e (65)</span>;
    }
    if (cleanModel === '55') {
      return <span className="model-badge badge-nfe">NF-e (55)</span>;
    }
    return <span className="model-badge">{cleanModel ? `Mod. ${cleanModel}` : 'N/A'}</span>;
  };

  return (
    <div className="trm-table-card">
      <div className="trm-table-header">
        <div>
          <h3>Prévia do Relatório de Inconsistências ({isSped ? 'SPED' : 'Sintegra'})</h3>
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
              <th>Identificador / Chave</th>
              <th>Tipo Doc / Modelo</th>
              <th>Data Emissão (XML)</th>
              <th>Data Emissão ({isSped ? 'SPED' : 'Sintegra'})</th>
              <th>Valor XML</th>
              <th>Valor {isSped ? 'SPED' : 'Sintegra'}</th>
              <th>Diferença</th>
              <th>Tipo de Divergência</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => {
              const valorFiscal = isSped 
                ? (item.sped_value ?? 0) 
                : (item.sintegra_value ?? 0);
              
              const dataEmissaoFiscal = isSped 
                ? item.sped_emission_date 
                : item.sintegra_emission_date;

              const identificador = isSped 
                ? (item.access_key || 'N/A') 
                : (item.composite_key || item.access_key || 'N/A');

              const diff = item.value_difference ?? (item.xml_value - valorFiscal);
              const isAlertOnly = item.divergence_type?.startsWith('ALERTA');

              return (
                <tr key={index}>
                  <td className="font-mono">{identificador}</td>
                  <td>{renderModelBadge(item.nfe_model)}</td>
                  <td>{item.xml_emission_date || '-'}</td>
                  <td>{dataEmissaoFiscal || '-'}</td>
                  <td>{formatCurrency(item.xml_value)}</td>
                  <td>{formatCurrency(valorFiscal)}</td>
                  <td className={diff !== 0 ? 'text-divergent' : ''}>
                    {formatCurrency(diff)}
                  </td>
                  <td>
                    <span 
                      className={`status-badge ${
                        diff === 0 && !isAlertOnly 
                          ? 'badge-ok' 
                          : isAlertOnly 
                            ? 'badge-warning' 
                            : 'badge-alert'
                      }`}
                    >
                      {item.divergence_type ? item.divergence_type.replace(/_/g, ' ') : 'DIVERGÊNCIA'}
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