import logoImg from '../../assets/LogoTRM.png';
import './header.css';

export function Header() {
  return (
    <header className="trm-header">
      <div className="trm-header-brand">
        <img src={logoImg} alt="Logotipo TRM Sistemas" className="trm-logo" />
        <div className="trm-brand-text">
          <h1>TRM Análises</h1>
          <h2>AUDITORIA FISCAL E ANÁLISES DE DOCUMENTOS</h2>
        </div>
      </div>
      <a 
        className="trm-header-link" 
        href="https://trmsistemas.com.br/" 
        target="_blank" 
        rel="noreferrer"
      >
        Sobre a TRM Sistemas ↗
      </a>
    </header>
  );
}