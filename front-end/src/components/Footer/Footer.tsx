import './footer.css';

export function Footer() {
  return (
    <footer className="trm-footer">
      <div className="trm-footer-content">
        <p>© {new Date().getFullYear()} TRM Sistemas — Automação Comercial</p>
        <div className="trm-footer-dev">
          <span>Desenvolvido por <strong>Nícolas Granato</strong></span>
          <a href="https://github.com/Nicolas-Granato" target="_blank" rel="noreferrer">GitHub</a>
          <span className="dot">•</span>
          <a href="https://linkedin.com/in/nicolasgranato-jf" target="_blank" rel="noreferrer">LinkedIn</a>
        </div>
      </div>
    </footer>
  );
}