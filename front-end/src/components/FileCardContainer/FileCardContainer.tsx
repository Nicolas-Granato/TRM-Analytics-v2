import React, { useRef } from 'react';
import './file_card_container.css';

export type FiscalArchive = 'Xml' | 'Sped' | 'Sintegra';

interface FileContainerProps {
  fiscalArchive: FiscalArchive;
  selectedFiles: File[];
  onFilesSelect: (files: File[]) => void;
  maxFiles: number;
}

export function FileContainer({
  fiscalArchive,
  selectedFiles,
  onFilesSelect,
  maxFiles,
}: FileContainerProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const isXml = fiscalArchive === 'Xml';

  const title = isXml
    ? `Pacotes de XMLs (.ZIP) [Máx. ${maxFiles}]`
    : `Arquivo Fiscal (${fiscalArchive.toUpperCase()}) [Máx. ${maxFiles}]`;

  const acceptFormats = isXml ? '.zip' : '.txt';

  const processAndSetFiles = (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    
    const combinedFiles = [...selectedFiles];
    fileArray.forEach((file) => {
      if (!combinedFiles.some((f) => f.name === file.name)) {
        combinedFiles.push(file);
      }
    });

    if (combinedFiles.length > maxFiles) {
      alert(`Limite excedido: Envie no máximo ${maxFiles} arquivo(s) para este campo.`);
      onFilesSelect(combinedFiles.slice(0, maxFiles));
    } else {
      onFilesSelect(combinedFiles);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processAndSetFiles(e.target.files);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processAndSetFiles(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (indexToRemove: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = selectedFiles.filter((_, idx) => idx !== indexToRemove);
    onFilesSelect(updated);
  };

  return (
    <div className="trm-file-card">
      <div className="trm-card-header">
        <span className="trm-card-title">
          <span className="trm-icon">{isXml ? '📦' : '📄'}</span> {title}
        </span>
      </div>

      <div
        className={`trm-dropzone ${selectedFiles.length > 0 ? 'has-file' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={inputRef}
          accept={acceptFormats}
          multiple={maxFiles > 1}
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        {selectedFiles.length > 0 ? (
          <div className="trm-file-list" style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {selectedFiles.map((file, index) => (
              <div key={`${file.name}-${index}`} className="trm-file-info">
                <span className="trm-file-icon">{isXml ? '📦' : '📄'}</span>
                <div className="trm-file-details">
                  <span className="trm-file-name">{file.name}</span>
                  <span className="trm-file-size">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <button
                  className="trm-btn-remove"
                  onClick={(e) => handleRemoveFile(index, e)}
                  title="Remover arquivo"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="trm-upload-prompt">
            <span className="trm-upload-icon">+</span>
            <p className="trm-upload-text">
              Arraste ou clique para selecionar {isXml ? 'os pacotes .ZIP' : `o(s) arquivo(s) .TXT (${fiscalArchive.toUpperCase()})`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}