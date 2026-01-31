import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import os
import json
import sys
import pytz

# URL base
URL = "https://www.praticagem-rj.com.br/"

# Berços de interesse
BERCOS_INCLUIR_TODOS = {
    'TECONTPROLONG', 'TECONT1', 'TECONT2', 'TECONT3', 'TECONT4', 'TECONT5', 
    'MANGUINHOS', 'PG-1'
}

def get_status_barra():
    try:
        response = requests.get(URL)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "lxml")

        all_tds = soup.find_all("td")
        baia_td = None
        for td in all_tds:
            if td.get_text(strip=True).upper() == "BAÍA DE GUANABARA":
                baia_td = td
                break
        
        if baia_td:
            status_td = baia_td.find_next_sibling("td")
            if status_td:
                texto = status_td.get_text(separator=" ", strip=True)
                if "BARRA RESTRITA" in texto.upper():
                    return {"restrita": True, "mensagem": texto}
                elif "BARRA FECHADA" in texto.upper():
                    return {"restrita": True, "fechada": True, "mensagem": texto}
                else:
                    return {"restrita": False, "mensagem": texto}
    except Exception as e:
        print(f"Erro ao verificar status da barra: {e}", file=sys.stderr)
        
    return {"restrita": False, "mensagem": "Não foi possível obter o status da barra."}

def get_all_navios_manobras():
    print("Iniciando scraping das manobras...")
    try:
        response = requests.get(URL)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "lxml")
    except Exception as e:
        print(f"Erro ao acessar site: {e}", file=sys.stderr)
        return []

    navios_manobras = []
    main_table = soup.find("table", class_="tbManobrasArea")
    if not main_table:
        print("Tabela principal de manobras não encontrada.", file=sys.stderr)
        return []

    rows = main_table.find_all("tr", id=re.compile(r"rptAreas_ctl\d+_rptManobrasArea_ctl\d+_trManobraArea"))

    for row in rows:
        cols = row.find_all("td", class_="tdManobraArea")
        if len(cols) >= 12:
            try:
                data_hora = cols[0].get_text(strip=True)
                navio_nome_div = cols[1].find("div", class_="tooltipDiv")
                navio_nome = navio_nome_div.contents[0].strip() if navio_nome_div else "N/A"
                calado = cols[2].get_text(strip=True)
                manobra = cols[7].get_text(strip=True)
                becos = cols[8].get_text(strip=True) if cols[8].get_text(strip=True) else cols[11].get_text(strip=True)

                if not any(berco in becos for berco in BERCOS_INCLUIR_TODOS):
                    continue

                current_terminal = None
                if "TECONTPROLONG" in becos or "TECONT1" in becos:
                    current_terminal = "rio"
                elif "TECONT4" in becos or "TECONT2" in becos or "TECONT3" in becos or "TECONT5" in becos:
                    current_terminal = "multi"
                elif "MANGUINHOS" in becos:
                    current_terminal = "manguinhos"
                elif "PG-1" in becos:
                    current_terminal = "pg1"

                imo, tipo_navio = None, None
                tooltip_escondida = cols[1].find("div", class_="tooltipDivEscondida")
                if tooltip_escondida:
                    imo_span = tooltip_escondida.find("span", id="ST_NR_IMO")
                    if imo_span: imo = imo_span.get_text(strip=True)
                    tipo_navio_span = tooltip_escondida.find("span", id="DS_TIPO_NAVIO")
                    if tipo_navio_span: tipo_navio = tipo_navio_span.get_text(strip=True).split("(")[0].strip()
                
                # Parsing date
                data, hora = data_hora.split()
                if ":" not in hora: hora += ":00"
                elif hora.count(":") == 1 and len(hora.split(":")[1]) == 1: hora = hora.replace(":", ":0")
                
                dia, mes = map(int, data.split("/"))
                hora_part, minuto_part = map(int, hora.split(":"))
                hoje = datetime.now()
                # Assuming current year, handling year rollover could be added if needed
                navio_date = datetime(hoje.year, mes, dia, hora_part, minuto_part)

                status = "futuro"
                if navio_date.date() == hoje.date(): status = "hoje"
                elif navio_date < hoje: status = "passado"
                
                alerta = None
                agora = datetime.now()
                if manobra == "E":
                    if navio_date - timedelta(hours=1) <= agora < navio_date: alerta = "entrada_antecipada"
                    elif agora >= navio_date: alerta = "entrada_futura"
                elif manobra in ["S", "M"]:
                    if navio_date - timedelta(hours=1) <= agora < navio_date: alerta = "saida_futura"
                    elif agora >= navio_date: alerta = "saida_atrasada"
                
                icone = "https://i.ibb.co/cX1DXDhW/icon-container.png"
                if tipo_navio:
                    if "CONTAINER SHIP" in tipo_navio.upper(): icone = "https://i.ibb.co/cX1DXDhW/icon-container.png"
                    elif "CHEMICAL TANKER" in tipo_navio.upper() or "PRODUCT TANKER" in tipo_navio.upper() or "TANKER" in tipo_navio.upper(): icone = "https://i.ibb.co/T315cM3/TANKER.png"
                    elif "CARGO SHIP" in tipo_navio.upper() or "OFFSHORE SHIP" in tipo_navio.upper() or "OFFSHORE SUPPORT VESSEL" in tipo_navio.upper() or "DIVING SUPPORT VESSEL" in tipo_navio.upper(): icone = "https://i.ibb.co/ymWQg66b/offshoer.png"
                    elif "SUPPLY SHIP" in tipo_navio.upper(): icone = "https://i.ibb.co/ccHFRkVD/suplay-ship.png"
                
                navios_manobras.append({
                    "data": data, "hora": hora, "navio": navio_nome, "calado": calado,
                    "manobra": manobra, "beco": becos, "status": status, "imo": imo,
                    "tipo_navio": tipo_navio, "icone": icone, "alerta": alerta,
                    "terminal": current_terminal,
                    "timestamp": navio_date.isoformat() # Use ISO format for JSON compatibility
                })
            except Exception as e:
                print(f"Erro ao processar linha: {e}", file=sys.stderr)
                continue

    return navios_manobras

def detectar_conflitos(navios_rio_manobras, navios_multi_manobras):
    conflitos = []
    
    # Helper to add date obj
    def add_date_obj(n):
        n['navio_date_obj'] = datetime.fromisoformat(n['timestamp'])
        return n

    rio = [add_date_obj(n.copy()) for n in navios_rio_manobras]
    multi = [add_date_obj(n.copy()) for n in navios_multi_manobras]
    
    navios_rio_agrupados = {}
    for manobra_rio in rio:
        navio_nome = manobra_rio["navio"]
        if navio_nome not in navios_rio_agrupados: navios_rio_agrupados[navio_nome] = []
        navios_rio_agrupados[navio_nome].append(manobra_rio)
    
    for navio_nome_rio, manobras_rio in navios_rio_agrupados.items():
        manobras_rio.sort(key=lambda x: x["navio_date_obj"])
        periodo_inicio_rio, periodo_fim_rio = None, None
        
        for m in manobras_rio:
            if m["manobra"] == "E" or periodo_inicio_rio is None:
                periodo_inicio_rio = m["navio_date_obj"]; break
        for m in reversed(manobras_rio):
            if m["manobra"] == "S" or periodo_fim_rio is None:
                periodo_fim_rio = m["navio_date_obj"]; break
                
        if periodo_inicio_rio and not periodo_fim_rio: periodo_fim_rio = periodo_inicio_rio + timedelta(hours=1)
        elif not periodo_inicio_rio and periodo_fim_rio: periodo_inicio_rio = periodo_fim_rio - timedelta(hours=1)
        elif not periodo_inicio_rio and not periodo_fim_rio and manobras_rio:
            periodo_inicio_rio = manobras_rio[0]["navio_date_obj"]
            periodo_fim_rio = manobras_rio[-1]["navio_date_obj"]
            if periodo_inicio_rio == periodo_fim_rio: periodo_fim_rio = periodo_inicio_rio + timedelta(hours=1)
        
        if not periodo_inicio_rio or not periodo_fim_rio: continue

        for manobra_multi in multi:
            if manobra_multi["manobra"] in ["E", "S"]:
                janela_multi_inicio = manobra_multi["navio_date_obj"] - timedelta(hours=1)
                janela_multi_fim = manobra_multi["navio_date_obj"] + timedelta(hours=1)
                
                if max(periodo_inicio_rio, janela_multi_inicio) < min(periodo_fim_rio, janela_multi_fim):
                    manobra_afetada_rio, min_diff = None, timedelta(days=999)
                    for m_rio in manobras_rio:
                        if m_rio["manobra"] in ["E", "S"]:
                            diff = abs(m_rio["navio_date_obj"] - manobra_multi["navio_date_obj"])
                            if (m_rio["manobra"] == manobra_multi["manobra"] and diff <= min_diff):
                                min_diff, manobra_afetada_rio = diff, m_rio["manobra"]
                                if diff == timedelta(0): break
                            elif (m_rio["manobra"] != manobra_multi["manobra"] and diff < min_diff):
                                min_diff, manobra_afetada_rio = diff, m_rio["manobra"]
                                
                    conflitos.append({
                        "navio_rio": navio_nome_rio, "manobra_rio_afetada": manobra_afetada_rio,
                        "manobra_rio_inicio": periodo_inicio_rio.strftime("%d/%m %H:%M"),
                        "manobra_rio_fim": periodo_fim_rio.strftime("%d/%m %H:%M"),
                        "navio_multi": manobra_multi["navio"], "manobra_multi_tipo": manobra_multi["manobra"],
                        "manobra_multi_data_hora": manobra_multi["navio_date_obj"].strftime("%d/%m %H:%M"),
                    })
    return conflitos

def main():
    print("Obtendo manobras...")
    all_navios = get_all_navios_manobras()
    
    print("Obtendo status da barra...")
    barra = get_status_barra()
    
    print("Verificando conflitos...")
    rio = [n for n in all_navios if n["terminal"] == "rio"]
    multi = [n for n in all_navios if n["terminal"] == "multi"]
    conflitos = detectar_conflitos(rio, multi)
    
    # Fix Timezone to Sao Paulo
    tz_sp = pytz.timezone("America/Sao_Paulo")
    agora_sp = datetime.now(tz_sp)

    output_data = {
        "ultima_atualizacao": agora_sp.strftime("%d/%m/%Y %H:%M"),
        "barra_info": barra,
        "navios": all_navios,
        "conflitos": conflitos
    }
    
    # Save to public/data.json
    try:
        os.makedirs("public", exist_ok=True)
        with open("public/data.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print("Dados salvos em public/data.json com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar JSON: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
