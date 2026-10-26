import './audit_table.css';

export interface AuditItem {
  chave_acesso: string;
  data_emissao: string;
  valor_xml: number;
  valor_fiscal: number;
  status: string;
}

interface AuditTableProps {
  items: AuditItem[];
  onExportExcel: () => void;
}

export function AuditTable({ items, onExportExcel }: AuditTableProps) {
  const formatCurrency = (val: number) =>
    val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <div className="trm-table-card">
      <div className="trm-table-header">
        <div>
          <h3>Prévia do Relatório de Inconsistências</h3>
          <p>{items.length} registros processados</p>
        </div>
        <button className="trm-btn-excel" onClick={onExportExcel}>
          📊 Exportar para Excel
        </button>
      </div>

      <div className="trm-table-wrapper">
        <table className="trm-data-table">
          <thead>
            <tr>
              <th>Chave de Acesso</th>
              <th>Data Emissão</th>
              <th>Valor XML</th>
              <th>Valor Fiscal</th>
              <th>Diferença</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => {
              const diff = item.valor_fiscal - item.valor_xml;
              return (
                <tr key={index}>
                  <td className="font-mono">{item.chave_acesso}</td>
                  <td>{item.data_emissao}</td>
                  <td>{formatCurrency(item.valor_xml)}</td>
                  <td>{formatCurrency(item.valor_fiscal)}</td>
                  <td className={diff !== 0 ? 'text-divergent' : ''}>
                    {formatCurrency(diff)}
                  </td>
                  <td>
                    <span className={`status-badge ${diff === 0 ? 'badge-ok' : 'badge-alert'}`}>
                      {diff === 0 ? 'OK' : 'Divergente'}
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