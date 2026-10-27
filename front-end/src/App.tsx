import { useState } from 'react';
import axios from 'axios';
import { Header } from './components/Header/Header';
import { FiscalTypeSwitch } from './components/FiscalTypeSwitch/FiscalTypeSwitch';
import { FileContainer, type FiscalArchive } from './components/FileCardContainer/FileCardContainer';
import { RunAudit } from './components/RunAudit/RunAudit';
import { ResetAudit } from './components/ResetAudit/ResetAudit'; // Componente de reset
import { SummaryCards } from './components/SummaryCards/SummaryCards';
import { AuditTable, type AuditItem } from './components/AuditTable/AuditTable';
import { Footer } from './components/Footer/Footer';
import './app.css';

const API_BASE_URL = 'http://192.168.15.11:8000/api/v1';

interface AuditMetrics {
  xml_metrics: {
    total_count?: number;
    total_value: number;
  };
  fiscal_archive_metrics: {
    total_count?: number;
    total_value: number;
  };
}

export function App() {
  const [isSped, setIsSped] = useState<boolean>(true);
  const [xmlZipFiles, setXmlZipFiles] = useState<File[]>([]);
  const [fiscalFiles, setFiscalFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [auditResults, setAuditResults] = useState<AuditItem[] | null>(null);
  const [metrics, setMetrics] = useState<AuditMetrics | null>(null);

  const fiscalArchiveType: FiscalArchive = isSped ? 'Sped' : 'Sintegra';
  const maxFiscalFiles = isSped ? 2 : 1;
  const maxXmlFiles = 2;

  const handleResetAudit = () => {
    setXmlZipFiles([]);
    setFiscalFiles([]);
    setAuditResults(null);
    setMetrics(null);
  };

  const handleToggleFiscalType = (checked: boolean) => {
    setIsSped(checked);
    handleResetAudit();
  };

  const handleRunAudit = async () => {
    if (xmlZipFiles.length === 0 || fiscalFiles.length === 0) {
      alert('Por favor, selecione ao menos um pacote XML (.ZIP) e um arquivo fiscal (.TXT).');
      return;
    }

    setIsLoading(true);
    setAuditResults(null);
    setMetrics(null);

    const formData = new FormData();
    
    formData.append('zip_files', xmlZipFiles[0]);
    if (xmlZipFiles.length > 1) {
      formData.append('zip_files_2', xmlZipFiles[1]);
    }

    formData.append('fiscal_file', fiscalFiles[0]);
    if (isSped && fiscalFiles.length > 1) {
      formData.append('fiscal_file_2', fiscalFiles[1]);
    }

    formData.append('is_sped', isSped ? 'true' : 'false');

    try {
      const response = await axios.post(`${API_BASE_URL}/audit/run`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000,
      });

      const responseData = response.data || {};
      const items = responseData.dataframe || responseData.items || responseData.data || [];
      
      setAuditResults(Array.isArray(items) ? items : []);
      
      if (responseData.metricas) {
        setMetrics(responseData.metricas);
      }
    } catch (error: any) {
      console.error('Erro na requisição de auditoria:', error);

      if (error.code === 'ECONNABORTED') {
        alert('Tempo limite excedido: O processamento demorou mais do que o esperado.');
      } else {
        const detailMessage = error.response?.data?.detail 
          || error.message 
          || 'Erro ao conectar ao servidor.';
        alert(`Erro na requisição: ${detailMessage}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportExcel = async () => {
    if (!auditResults || auditResults.length === 0) return;

    try {
      const payload = {
        enterprise_name: 'TRM_SISTEMAS',
        items: auditResults,
      };

      const response = await axios.post(`${API_BASE_URL}/export/excel`, payload, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Relatorio_Auditoria_TRM.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error: any) {
      console.error('Erro ao exportar:', error);
      alert('Erro ao exportar a planilha.');
    }
  };

  return (
    <div className="trm-app">
      <Header />

      <main className="trm-body-container">
        <div className="trm-toolbar">
          <div className="trm-section-title">
            <h2>Painel de Auditoria Fiscal</h2>
            <p>Selecione a modalidade e faça o envio dos arquivos</p>
          </div>
          <FiscalTypeSwitch isSped={isSped} onToggle={handleToggleToggleFiscalType => handleToggleFiscalType(!isSped)} />
        </div>

        <div className="trm-files-row">
          <FileContainer 
            fiscalArchive="Xml" 
            selectedFiles={xmlZipFiles} 
            onFilesSelect={setXmlZipFiles}
            maxFiles={maxXmlFiles}
          />
          <FileContainer 
            fiscalArchive={fiscalArchiveType} 
            selectedFiles={fiscalFiles} 
            onFilesSelect={setFiscalFiles}
            maxFiles={maxFiscalFiles}
          />
        </div>

        <div className="trm-actions-bar" style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <RunAudit 
            onClick={handleRunAudit} 
            isLoading={isLoading} 
            disabled={xmlZipFiles.length === 0 || fiscalFiles.length === 0}
          />

          {auditResults && (
            <ResetAudit onReset={handleResetAudit} disabled={isLoading} />
          )}
        </div>

        {metrics && (
          <SummaryCards 
            xmlCount={metrics.xml_metrics.total_count ?? 0}
            xmlValue={(metrics.xml_metrics.total_value ?? 0) / 100}
            fiscalType={fiscalArchiveType}
            fiscalCount={metrics.fiscal_archive_metrics.total_count ?? 0}
            fiscalValue={(metrics.fiscal_archive_metrics.total_value ?? 0) / 100}
            isAuditDone={true}
          />
        )}

        {Array.isArray(auditResults) && (
          <AuditTable items={auditResults} onExportExcel={handleExportExcel} />
        )}
      </main>

      <Footer />
    </div>
  );
}