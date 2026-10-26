// src/App.tsx
import { useState } from 'react';
import axios from 'axios';
import { Header } from './components/Header/Header';
import { FiscalTypeSwitch } from './components/FiscalTypeSwitch/FiscalTypeSwitch';
import { FileContainer, type FiscalArchive } from './components/FileCardContainer/FileCardContainer';
import { RunAudit } from './components/RunAudit/RunAudit';
import { AuditTable, type AuditItem } from './components/AuditTable/AuditTable';
import { Footer } from './components/Footer/Footer';
import './app.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export function App() {
  const [isSped, setIsSped] = useState<boolean>(true);
  const [xmlZipFile, setXmlZipFile] = useState<File | null>(null);
  const [fiscalFile, setFiscalFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [auditResults, setAuditResults] = useState<AuditItem[] | null>(null);

  const fiscalArchiveType: FiscalArchive = isSped ? 'Sped' : 'Sintegra';

  const handleToggleFiscalType = (checked: boolean) => {
    setIsSped(checked);
    setFiscalFile(null);
  };

  const handleRunAudit = async () => {
    if (!xmlZipFile || !fiscalFile) {
      alert('Por favor, selecione o pacote XML (.ZIP) e o arquivo fiscal (.TXT).');
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    
    formData.append('zip_files', xmlZipFile);
    formData.append('fiscal_file', fiscalFile);
    formData.append('is_sped', String(isSped));

    try {
      const response = await axios.post(`${API_BASE_URL}/audit/run`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setAuditResults(response.data.items || response.data.data || []);
    } catch (error: any) {
      console.error('Erro ao executar auditoria:', error);
      const message = error.response?.data?.detail || 'Erro ao processar a auditoria fiscal.';
      alert(`Erro na requisição: ${message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportExcel = async () => {
    if (!auditResults || auditResults.length === 0) return;

    try {
      const payload = {
        enterprise_name: 'TRM_SISTEMAS',
        items: auditResults
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
      console.error('Erro ao exportar planilha:', error);
      alert('Erro ao gerar e exportar o arquivo Excel.');
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
          <FiscalTypeSwitch isSped={isSped} onToggle={handleToggleFiscalType} />
        </div>

        <div className="trm-files-row">
          <FileContainer 
            fiscalArchive="Xml" 
            selectedFile={xmlZipFile} 
            onFileSelect={setXmlZipFile} 
          />
          <FileContainer 
            fiscalArchive={fiscalArchiveType} 
            selectedFile={fiscalFile} 
            onFileSelect={setFiscalFile} 
          />
        </div>

        <div className="trm-actions-bar">
          <RunAudit 
            onClick={handleRunAudit} 
            isLoading={isLoading} 
            disabled={!xmlZipFile || !fiscalFile}
          />
        </div>

        {auditResults && (
          <AuditTable items={auditResults} onExportExcel={handleExportExcel} />
        )}
      </main>

      <Footer />
    </div>
  );
}