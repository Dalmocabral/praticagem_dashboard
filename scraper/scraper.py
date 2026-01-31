import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
import json
import sys
import pytz

# ... constants ...

# ... functions ...

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
    
    # Save to file
    # If running in GH Actions, we might want to save to 'public/data.json'
    # Check if 'public' dir exists relative to this script, otherwise just save in current dir
    
    # We assume the script is in /scraper/scraper.py and we want /public/data.json (siblings)
    # OR we are running from root.
    
    # Let's try to find the 'public' folder
    base_dir = os.getcwd()
    public_dir = os.path.join(base_dir, "public")
    
    # Try one level up if not found (case: running inside scraper/)
    if not os.path.exists(public_dir):
        public_dir = os.path.join(base_dir, "..", "public")
        
    if not os.path.exists(public_dir):
        # Create if doesn't exist (e.g. locally)
        os.makedirs(public_dir, exist_ok=True)
        
    output_path = os.path.join(public_dir, "data.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Dados salvos com sucesso em: {output_path}")

if __name__ == "__main__":
    main()
