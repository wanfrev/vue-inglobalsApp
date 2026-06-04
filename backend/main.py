import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

app = FastAPI(title="Backend Simulador DAD")

# Configurar CORS para que tu frontend en Vue se pueda conectar sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambia esto por la URL de tu PWA
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar el cliente de DeepSeek usando la librería de OpenAI
# ya que la API de DeepSeek usa la misma estructura.
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1" # La URL mágica de DeepSeek
)

class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
def home():
    return {"status": "Backend del Simulador DAD Activo y Corriendo"}

@app.post("/api/simulate")
async def simulate_audit(request: PromptRequest):
    try:
        # Prueba básica de conexión con el modelo DeepSeek-V3 (chat)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en auditoría digital bajo la ecuación DAD."},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.2, # Temperatura baja para que sea preciso y no invente leyes
            max_tokens=1000
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))