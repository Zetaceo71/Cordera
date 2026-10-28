import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = ["lamb ", "Lamb "]

# Verificación de seguridad para el token
if not TOKEN:
    print("-------------------------------------------------------------------------")
    print("❌ ERROR CRÍTICO: No se encontró el DISCORD_TOKEN en el archivo .env")
    print("-------------------------------------------------------------------------")
    input("\nPresiona Enter para cerrar la consola...")
    exit()

# Configurar Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Instanciar el bot con el prefijo y case_insensitive en True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, case_insensitive=True)

async def cargar_cogs():
    """Función para cargar los cogs de manera segura y ordenada."""
    if not os.path.exists("./cogs"):
        print("⚠️ Advertencia: No se encontró la carpeta 'cogs'. Creándola ahora...")
        os.makedirs("cogs", exist_ok=True)
        return

    print("-----------------------------------")
    print("🔍 Buscando módulos en la carpeta 'cogs'...")
    
    archivos = os.listdir("./cogs")
    cogs_encontrados = [f for f in archivos if f.endswith(".py")]

    if not cogs_encontrados:
        print("⚠️ No se encontraron archivos .py dentro de la carpeta 'cogs'.")
        return

    for filename in cogs_encontrados:
        cog_name = filename[:-3]
        try:
            # Nota: Asegúrate de que el nombre del archivo sea exacto (ej. interacts.py)
            await bot.load_extension(f"cogs.{cog_name}")
            print(f"📦 Módulo cargado con éxito: {cog_name}")
        except Exception as e:
            print(f"❌ Error crítico al cargar el módulo 'cogs.{cog_name}':")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

@bot.event
async def on_ready():
    print(f"-----------------------------------")
    print(f"✅ Bot conectado como: {bot.user.name} (ID: {bot.user.id})")
    print(f"🚀 Prefijo configurado: {PREFIX}")
    print(f"-----------------------------------")

async def main():
    async with bot:
        await cargar_cogs()
        await bot.start(TOKEN)

# Ejecutar el bot usando asyncio
if __name__ == "__main__":
    asyncio.run(main())