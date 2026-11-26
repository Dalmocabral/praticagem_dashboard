import os
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from scraper.scraper import scrape_data

# Armazenamento em memória dos dados raspados
cached_data = None
SCRAPE_INTERVAL_SECONDS = 300  # Intervalo de 5 minutos

def load_initial_data():
    """Carrega dados existentes do disco para disponibilização instantânea no boot."""
    global cached_data
    candidates = [
        "public/data.json",
        "dist/data.json",
        "scraper/public/data.json"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    print(f"[BOOT] Dados iniciais carregados de {path}")
                    return
            except Exception as e:
                print(f"[BOOT] Aviso ao ler {path}: {e}")

async def scraper_background_loop():
    """Loop assíncrono em segundo plano para manter os dados atualizados."""
    global cached_data
    while True:
        try:
            print("[SCRAPER] Executando coleta de dados da Praticagem...")
            loop = asyncio.get_running_loop()
            # Executa a raspagem síncrona em uma thread separada para não travar o servidor
            data = await loop.run_in_executor(None, scrape_data)
            if data and data.get("navios"):
                cached_data = data
                print(f"[SCRAPER] Coleta concluída com sucesso. Última atualização: {data.get('ultima_atualizacao')}")
                
                # Salva em dist/data.json também se a pasta existir
                if os.path.exists("dist"):
                    try:
                        with open("dist/data.json", "w", encoding="utf-8") as f:
                            json.dump(cached_data, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"[SCRAPER] Aviso ao salvar em dist/data.json: {e}")
        except Exception as e:
            print(f"[SCRAPER] Erro no ciclo de scraping: {e}")
        
        await asyncio.sleep(SCRAPE_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carrega cache inicial imediatamente
    load_initial_data()
    # Inicia a tarefa em segundo plano
    task = asyncio.create_task(scraper_background_loop())
    yield
    task.cancel()

app = FastAPI(title="Praticagem Dashboard", lifespan=lifespan)

# Endpoint de verificação e ping (UptimeRobot pinga aqui para manter o Render acordado)
@app.get("/healthz")
@app.get("/ping")
async def healthz():
    last_update = cached_data.get("ultima_atualizacao") if cached_data else "Aguardando primeira sincronização"
    total_navios = len(cached_data.get("navios", [])) if cached_data else 0
    return {
        "status": "ok",
        "service": "praticagem-dashboard",
        "ultima_atualizacao": last_update,
        "total_navios": total_navios
    }

# Endpoint data.json consumido pelo frontend React
@app.get("/data.json")
async def get_data():
    global cached_data
    if cached_data is None:
        load_initial_data()
    
    if cached_data is not None:
        return JSONResponse(
            content=cached_data,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return JSONResponse(
        status_code=503,
        content={"error": "Dados em processo de coleta. Tente novamente em alguns segundos."}
    )

# Endpoint manual para forçar raspagem se necessário
@app.post("/api/scrape")
async def trigger_scrape():
    global cached_data
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, scrape_data)
    if data:
        cached_data = data
    return {"status": "success", "ultima_atualizacao": data.get("ultima_atualizacao") if data else None}

# Servir arquivos do frontend React (pasta dist/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")

if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Se for um arquivo estático específico da raiz (como pwa-icon.svg, sw.js, etc.)
        target_file = os.path.join(DIST_DIR, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        
        # Qualquer outra rota entrega o index.html (SPA Fallback)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
else:
    @app.get("/")
    async def index():
        return {
            "message": "Servidor online. O frontend ainda não foi compilado. Execute 'npm run build'."
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Iniciando servidor na porta {port}...")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
