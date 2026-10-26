import React, { useRef } from 'react';
import './file_card_container.css'

export type FiscalArchive = 'Xml' | 'Sped' | 'Sintegra';

interface FileContainerProps {
  fiscalArchive: FiscalArchive;
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
}

export function FileContainer({ fiscalArchive, selectedFile, onFileSelect }: FileContainerProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const isXml = fiscalArchive === 'Xml';

  const title = isXml 
    ? 'Pacote de XMLs (.ZIP)' 
    : `Arquivo Fiscal (${fiscalArchive.toUpperCase()})`;

  const acceptFormats = isXml ? '.zip' : '.txt';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="trm-file-card">
      <div className="trm-card-header">
        <span className="trm-card-title">
          <span className="trm-icon">{isXml ? '📦' : '📄'}</span> {title}
        </span>
      </div>

      <div 
        className={`trm-dropzone ${selectedFile ? 'has-file' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          ref={inputRef}
          accept={acceptFormats}
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        {selectedFile ? (
          <div className="trm-file-info">
            <span className="trm-file-icon">{isXml ? '📦' : '📄'}</span>
            <div className="trm-file-details">
              <span className="trm-file-name">{selectedFile.name}</span>
              <span className="trm-file-size">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </span>
            </div>
            <button 
              className="trm-btn-remove" 
              onClick={(e) => {
                e.stopPropagation();
                onFileSelect(null);
              }}
              title="Remover arquivo"
            >
              ×
            </button>
          </div>
        ) : (
          <div className="trm-upload-prompt">
            <span className="trm-upload-icon">+</span>
            <p className="trm-upload-text">
              Arraste ou clique para selecionar {isXml ? 'o pacote .ZIP' : `o arquivo .TXT (${fiscalArchive.toUpperCase()})`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}