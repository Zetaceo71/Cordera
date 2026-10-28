import discord
from discord.ext import commands
import aiohttp
import aiosqlite
import os

class InteraccionView(discord.ui.View):
    def __init__(self, autor: discord.Member, objetivo: discord.Member):
        super().__init__(timeout=60)
        self.autor = autor
        self.objetivo = objetivo
        self.valor = None
        self.message = None

    @discord.ui.button(label="Corresponder", emoji="💞", style=discord.ButtonStyle.green)
    async def corresponder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.objetivo.id:
            await interaction.response.send_message("❌ ¡Solo la persona mencionada puede corresponder!", ephemeral=True)
            return
        self.valor = True
        for child in self.children:
            child.disabled = True
        try:
            await interaction.response.edit_message(view=self)
        except Exception:
            pass
        self.stop()

    @discord.ui.button(label="Rechazar", emoji="❌", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.objetivo.id:
            await interaction.response.send_message("❌ ¡Solo la persona mencionada puede rechazar!", ephemeral=True)
            return
        self.valor = False
        for child in self.children:
            child.disabled = True
        try:
            await interaction.response.edit_message(view=self)
        except Exception:
            pass
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class Interacts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color_kindred = discord.Color.from_rgb(167, 130, 232)
        self.db_path = "database/cordera.db"

    async def ejecutar_db(self, query, params=(), fetch=None):
        os.makedirs("database", exist_ok=True)
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_received (
                        user_id INTEGER,
                        action TEXT,
                        count INTEGER,
                        PRIMARY KEY (user_id, action)
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_pairs (
                        user1_id INTEGER,
                        user2_id INTEGER,
                        action TEXT,
                        count INTEGER,
                        PRIMARY KEY (user1_id, user2_id, action)
                    )
                """)
                cursor = await db.execute(query, params)
                if fetch == "one":
                    resultado = await cursor.fetchone()
                    await db.commit()
                    return resultado
                await db.commit()
        except Exception as e:
            print(f"[DB ERROR]: {e}")
        return None

    async def obtener_gif_api(self, categoria: str) -> str:
        url_api = f"https://api.otakugifs.xyz/gif?reaction={categoria}"
        headers = {'User-Agent': 'CorderaBot/1.0 (Python/aiohttp)', 'Accept': 'application/json'}
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url_api) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("url")
        except Exception as e:
            print(f"[API EXCEPTION] Error al obtener GIF: {e}")
        return None

    def obtener_objetivo(self, ctx, miembro: discord.Member = None) -> discord.Member:
        if isinstance(ctx.channel, discord.DMChannel):
            return None
        if miembro:
            return miembro
        if ctx.message.reference and ctx.message.reference.resolved:
            mensaje_referenciado = ctx.message.reference.resolved
            if isinstance(mensaje_referenciado, discord.Message):
                return mensaje_referenciado.author
        return None

    async def incrementar_individual(self, objetivo_id: int, action: str) -> int:
        row = await self.ejecutar_db(
            "SELECT count FROM user_received WHERE user_id = ? AND action = ?", 
            (objetivo_id, action), fetch="one"
        )
        if row:
            nuevo_conteo = row[0] + 1
            await self.ejecutar_db(
                "UPDATE user_received SET count = ? WHERE user_id = ? AND action = ?", 
                (nuevo_conteo, objetivo_id, action)
            )
            return nuevo_conteo
        else:
            await self.ejecutar_db(
                "INSERT INTO user_received (user_id, action, count) VALUES (?, ?, 1)", 
                (objetivo_id, action)
            )
            return 1

    async def incrementar_pareja(self, autor_id: int, objetivo_id: int, action: str) -> int:
        u1, u2 = sorted([autor_id, objetivo_id])
        row = await self.ejecutar_db(
            "SELECT count FROM user_pairs WHERE user1_id = ? AND user2_id = ? AND action = ?", 
            (u1, u2, action), fetch="one"
        )
        if row:
            nuevo_conteo = row[0] + 1
            await self.ejecutar_db(
                "UPDATE user_pairs SET count = ? WHERE user1_id = ? AND user2_id = ? AND action = ?", 
                (nuevo_conteo, u1, u2, action)
            )
            return nuevo_conteo
        else:
            await self.ejecutar_db(
                "INSERT INTO user_pairs (user1_id, user2_id, action, count) VALUES (?, ?, ?, 1)", 
                (u1, u2, action)
            )
            return 1

    async def enviar_interaccion_activa(self, ctx, categoria: str, verbo_principal: str, nombre_accion: str, miembro: discord.Member = None, con_botones: bool = False, verbo_vuelta: str = None):
        objetivo_usuario = self.obtener_objetivo(ctx, miembro)

        if not objetivo_usuario or objetivo_usuario.id == ctx.author.id:
            await ctx.send("🐑💜 ¡Debes mencionar a otra persona para interactuar!")
            return

        gif_url = await self.obtener_gif_api(categoria)
        if not gif_url:
            await ctx.send("❌ No se pudo obtener el GIF correspondiente.")
            return

        linea_1 = f"{ctx.author.mention} {verbo_principal} a {objetivo_usuario.mention}"

        if not con_botones:
            total_recibido = await self.incrementar_individual(objetivo_usuario.id, categoria)
            linea_2 = f"*{objetivo_usuario.display_name} ha recibido {nombre_accion} {total_recibido} veces.*"
            
            embed = discord.Embed(description=f"{linea_1}\n{linea_2}", color=self.color_kindred)
            embed.set_image(url=gif_url)
            await ctx.send(embed=embed)
        else:
            # Incrementamos de inmediato al enviar el comando para que nunca muestre 0
            total_pareja = await self.incrementar_pareja(ctx.author.id, objetivo_usuario.id, categoria)
            linea_2 = f"*{ctx.author.name} y {objetivo_usuario.name} se han {nombre_accion} {total_pareja} veces.*"
            
            embed = discord.Embed(description=f"{linea_1}\n{linea_2}", color=self.color_kindred)
            embed.set_image(url=gif_url)

            view = InteraccionView(ctx.author, objetivo_usuario)
            mensaje = await ctx.send(embed=embed, view=view)
            view.message = mensaje

            await view.wait()

            # Si corresponde: incrementa nuevamente la cuenta y envía la respuesta de vuelta sin botones
            if view.valor is True:
                total_pareja_nuevo = await self.incrementar_pareja(ctx.author.id, objetivo_usuario.id, categoria)
                
                linea_2_actualizada = f"*{ctx.author.name} y {objetivo_usuario.name} se han {nombre_accion} {total_pareja_nuevo} veces.*"
                embed.description = f"{linea_1}\n{linea_2_actualizada}"
                try:
                    await mensaje.edit(embed=embed, view=view)
                except Exception:
                    pass

                gif_vuelta_url = await self.obtener_gif_api(categoria)
                linea_vuelta_1 = f"{objetivo_usuario.mention} {verbo_vuelta} a {ctx.author.mention}"
                linea_vuelta_2 = f"*{objetivo_usuario.name} y {ctx.author.name} se han {nombre_accion} {total_pareja_nuevo} veces.*"
                
                embed_vuelta = discord.Embed(description=f"{linea_vuelta_1}\n{linea_vuelta_2}", color=self.color_kindred)
                if gif_vuelta_url:
                    embed_vuelta.set_image(url=gif_vuelta_url)
                
                await ctx.send(embed=embed_vuelta)

            # Si rechaza: muestra el mensaje de rechazo junto con el GIF de bofetada (slap)
            elif view.valor is False:
                gif_slap_url = await self.obtener_gif_api("slap")
                linea_rechazo = f"{objetivo_usuario.mention} rechaza la interacción de {ctx.author.mention} y le da una merecida bofetada."
                
                embed_rechazo = discord.Embed(description=linea_rechazo, color=self.color_kindred)
                if gif_slap_url:
                    embed_rechazo.set_image(url=gif_slap_url)
                
                await ctx.send(embed=embed_rechazo)

    async def enviar_interaccion_pasiva(self, ctx, categoria: str, descripcion_texto: str):
        gif_url = await self.obtener_gif_api(categoria)
        if not gif_url:
            await ctx.send("❌ No se pudo obtener el GIF correspondiente.")
            return

        embed = discord.Embed(
            description=descripcion_texto.format(autor=ctx.author.mention),
            color=self.color_kindred
        )
        embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    # --- AYUDA Y UTILIDAD ---

    @commands.command(name="interact", aliases=["acciones", "interacciones", "gifs"])
    async def interact(self, ctx):
        embed = discord.Embed(
            title="✨ Catálogo de Interacciones - Cordera",
            description="Menciona a alguien o **responde a su mensaje** para interactuar.",
            color=self.color_kindred
        )
        lista_comandos = [f"• **`{cmd.name}`**" for cmd in self.get_commands() if cmd.name not in ["interact", "avatar"]]
        embed.add_field(name="🎭 Acciones Disponibles", value=" ".join(lista_comandos), inline=False)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["icon", "icono", "pfp"])
    async def avatar(self, ctx, miembro: discord.Member = None):
        objetivo = self.obtener_objetivo(ctx, miembro) or ctx.author
        embed = discord.Embed(title=f"🖼️ Avatar de {objetivo.display_name}", color=self.color_kindred)
        embed.set_image(url=objetivo.display_avatar.url)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
        await ctx.send(embed=embed)

    # --- ACCIONES CON BOTONES (AFECTO MUTUO CON CONTRARRESPUESTA) ---

    @commands.command(name="kiss", aliases=["beso"])
    async def kiss(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "kiss", "planta un tierno beso", "besado", miembro, con_botones=True, verbo_vuelta="devuelve el tierno beso")

    @commands.command(name="hug", aliases=["abrazo"])
    async def hug(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "hug", "le da un cálido abrazo", "abrazado", miembro, con_botones=True, verbo_vuelta="devuelve el cálido abrazo")

    @commands.command(name="cuddle", aliases=["acurrucar"])
    async def cuddle(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "cuddle", "se acurruca pacíficamente con", "acurrucado", miembro, con_botones=True, verbo_vuelta="corresponde acurrucándose con")

    # --- ACCIONES ACTIVAS CON CONTADOR INDIVIDUAL Y NOMBRE DE ACCIÓN ---

    @commands.command(name="pat", aliases=["palmadita", "cabeza"])
    async def pat(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "pat", "le da una palmadita en la cabeza", "palmaditas", miembro, con_botones=False)

    @commands.command(name="poke", aliases=["tocar"])
    async def poke(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "poke", "le da un toque a", "toques", miembro, con_botones=False)

    @commands.command(name="tickle", aliases=["cosquillas"])
    async def tickle(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "tickle", "le hace cosquillas a", "cosquillas", miembro, con_botones=False)

    @commands.command(name="slap", aliases=["bofetada", "cachetada"])
    async def slap(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "slap", "le da una bofetada a", "bofetadas", miembro, con_botones=False)

    @commands.command(name="bite", aliases=["morder"])
    async def bite(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "bite", "le da un mordisco juguetón a", "mordiscos", miembro, con_botones=False)

    @commands.command(name="lick", aliases=["lamer"])
    async def lick(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "lick", "le da un lametón a", "lametones", miembro, con_botones=False)

    @commands.command(name="holdhand", aliases=["manos", "agarrar"])
    async def holdhand(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "holdhand", "toma de la mano a", "tomas de mano", miembro, con_botones=False)

    @commands.command(name="feed", aliases=["alimentar"])
    async def feed(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "feed", "alimenta con cariño a", "porciones de comida", miembro, con_botones=False)

    @commands.command(name="wave", aliases=["saludar"])
    async def wave(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "wave", "saluda alegremente a", "saludos", miembro, con_botones=False)

    @commands.command(name="highfive", aliases=["chocaos", "cinco"])
    async def highfive(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "highfive", "choca los cinco con", "choques de cinco", miembro, con_botones=False)

    @commands.command(name="kill", aliases=["matar", "asesinar"])
    async def kill(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "kill", "elimina dramáticamente a", "eliminaciones", miembro, con_botones=False)

    @commands.command(name="smug", aliases=["presumir"])
    async def smug(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "smug", "sonríe con arrogancia frente a", "miradas presumidas", miembro, con_botones=False)

    @commands.command(name="wink", aliases=["guiño"])
    async def wink(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "wink", "le hace un guiño a", "guiños", miembro, con_botones=False)

    @commands.command(name="punch", aliases=["golpe"])
    async def punch(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "punch", "le propina un golpe a", "golpes", miembro, con_botones=False)

    @commands.command(name="kick", aliases=["patada"])
    async def kick(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "kick", "le da una patada a", "patadas", miembro, con_botones=False)

    @commands.command(name="scold", aliases=["regañar"])
    async def scold(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "scold", "reprende firmemente a", "regaños", miembro, con_botones=False)

    @commands.command(name="stare", aliases=["mirar"])
    async def stare(self, ctx, miembro: discord.Member = None):
        await self.enviar_interaccion_activa(ctx, "stare", "observa fijamente a", "miradas fijas", miembro, con_botones=False)

    # --- ACCIONES PASIVAS ---

    @commands.command(name="dance", aliases=["bailar"])
    async def dance(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "dance", "💃 {autor} se ha puesto a bailar alegremente.")

    @commands.command(name="blush", aliases=["sonrojarse"])
    async def blush(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "blush", "🌸 {autor} se ha sonrojado por completo.")

    @commands.command(name="cry", aliases=["llorar"])
    async def cry(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "cry", "🌧️ {autor} se ha puesto a llorar en silencio.")

    @commands.command(name="pout", aliases=["puchero"])
    async def pout(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "pout", "😒 {autor} hace un evidente puchero.")

    @commands.command(name="bored", aliases=["aburrido"])
    async def bored(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "bored", "🥱 {autor} suspira de puro aburrimiento.")

    @commands.command(name="clap", aliases=["aplaudir"])
    async def clap(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "clap", "👏 {autor} comienza a aplaudir con entusiasmo.")

    @commands.command(name="facepalm", aliases=["carpeta"])
    async def facepalm(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "facepalm", "🤦 {autor} se da una palmada en la cara.")

    @commands.command(name="laugh", aliases=["reir", "risas"])
    async def laugh(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "laugh", "😆 {autor} se ríe a carcajadas.")

    @commands.command(name="sleep", aliases=["dormir"])
    async def sleep(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "sleep", "💤 {autor} se ha quedado profundamente dormido/a.")

    @commands.command(name="smile", aliases=["sonreir"])
    async def smile(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "smile", "😊 {autor} muestra una cálida sonrisa.")

    @commands.command(name="think", aliases=["pensar"])
    async def think(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "think", "🤔 {autor} reflexiona profundamente.")

    @commands.command(name="yawn", aliases=["bostezar"])
    async def yawn(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "yawn", "🥱 {autor} deja escapar un gran bostezo.")

    @commands.command(name="shrug", aliases=["dudas"])
    async def shrug(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "shrug", "🤷 {autor} se encoge de hombros.")

    @commands.command(name="confuse", aliases=["confundido"])
    async def confuse(self, ctx):
        await self.enviar_interaccion_pasiva(ctx, "confuse", "💫 {autor} se encuentra totalmente confundido/a.")

async def setup(bot):
    await bot.add_cog(Interacts(bot))