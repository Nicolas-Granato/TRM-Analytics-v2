import './footer.css';

export function Footer() {
  return (
    <footer className="trm-footer">
      <div className="trm-footer-content">
        <p>© {new Date().getFullYear()} TRM Sistemas — Automação Comercial e Análises Fiscais</p>
        <div className="trm-footer-dev">
          <span>Desenvolvido por <strong>Seu Nome</strong></span>
          <a href="https://github.com/seu-usuario" target="_blank" rel="noreferrer">GitHub</a>
          <span className="dot">•</span>
          <a href="https://linkedin.com/in/seu-usuario" target="_blank" rel="noreferrer">LinkedIn</a>
        </div>
      </div>
    </footer>
  );
}