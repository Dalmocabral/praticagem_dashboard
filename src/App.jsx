
import { Github, Linkedin, Map } from 'lucide-react';
import { useEffect, useState } from 'react';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Adiciona timestamp para evitar cache do navegador
        const response = await fetch(`./data.json?t=${new Date().getTime()}`);
        if (!response.ok) {
          throw new Error('Aguardando sincronização de dados...');
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // 1 min refresh
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading">Carregando dados da Praticagem...</div>;
  if (error) return <div className="error">{error} <br/> <small>Verifique se o Scraper rodou.</small></div>;
  if (!data) return null;

  const { navios, barra_info, ultima_atualizacao } = data;

  // Filtra apenas para o terminal 'rio'
  const filteredNavios = navios.filter(n => n.terminal === 'rio');

  // Ordena navios pelo timestamp
  filteredNavios.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  return (
    <div className="dashboard">
      <header className="header">
        <div className="logo">
            <h1>🚢 Praticagem Rio</h1>
            <span className="badge">LIVE</span>
        </div>
        <div className="meta">
          <p>Última atualização: {ultima_atualizacao}</p>
          <div className={`status-barra ${barra_info.restrita ? 'restrita' : 'aberta'}`}>
            <span className="icon">{barra_info.restrita ? '🚫' : '✅'}</span>
            <span>{barra_info.mensagem}</span>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="table-container">
          <table className="navios-table">
            <thead>
              <tr>
                <th>Data / Hora</th>
                <th>Navio</th>
                <th>Manobra</th>
                <th>Berço</th>
                <th>Calado</th>
                <th className="text-center">Live Traffic</th>
              </tr>
            </thead>
            <tbody>
              {filteredNavios.map((navio, index) => (
                <tr key={index} className={`row-status-${navio.status} row-alerta-${navio.alerta || 'none'}`}>
                  <td className="col-data" data-label="Data / Hora">
                    <div className="data-cell">
                      <span>{navio.data}</span>
                      <span className="hora">{navio.hora}</span>
                    </div>
                  </td>
                  <td className="col-navio" data-label="Navio">
                    <div className="navio-info">
                        <img src={navio.icone} alt="" className="navio-icon-sm" onError={(e) => e.target.style.display='none'} />
                        <div className="navio-text">
                            <span className="navio-name">{navio.navio}</span>
                            <span className="navio-type">{navio.tipo_navio}</span>
                            {navio.imo && <span className="navio-imo">IMO: {navio.imo}</span>}
                        </div>
                    </div>
                  </td>
                  <td data-label="Manobra">
                    <span className={`badge-manobra badge-${navio.manobra}`}>
                        {navio.manobra === 'E' ? 'Entrada' : navio.manobra === 'S' ? 'Saída' : 'Mudança'}
                    </span>
                  </td>
                  <td data-label="Berço">
                    <span className="value-text">{navio.beco}</span>
                  </td>
                  <td data-label="Calado">
                    <span className="value-text">{navio.calado}m</span>
                  </td>
                  <td data-label="Live Traffic" className="col-traffic">
                    {navio.imo ? (
                      <a 
                        href={`https://www.marinetraffic.com/en/ais/details/ships/imo:${navio.imo}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="traffic-link"
                        title="Ver no MarineTraffic"
                      >
                        <Map size={20} className="map-icon" />
                        <span className="map-text">Ver Mapa</span>
                      </a>
                    ) : (
                      <span className="no-imo">-</span>
                    )}
                  </td>
                </tr>
              ))}
              {filteredNavios.length === 0 && (
                <tr>
                    <td colSpan="6" className="no-data">Nenhuma manobra encontrada para o Terminal Rio.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>

      <footer className="footer">
        <p>Desenvolvido por <strong>Dalmo dos Santos Cabral</strong></p>
        <div className="social-links">
          <a href="https://github.com/Dalmocabral" target="_blank" rel="noopener noreferrer" className="social-btn">
            <Github size={20} />
            <span>GitHub</span>
          </a>
          <a href="https://www.linkedin.com/in/dalmo-cabral-062374131/" target="_blank" rel="noopener noreferrer" className="social-btn">
            <Linkedin size={20} />
            <span>LinkedIn</span>
          </a>
        </div>
      </footer>
    </div>
  );
}

export default App;
