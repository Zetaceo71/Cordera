import discord
from discord.ext import commands
import datetime

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ⚠️ REEMPLAZA ESTOS IDs CON LOS DE TU SERVIDOR DE DISCORD
        self.LOG_CHANNEL_MEMBERS = 1564804912653541488  # Canal para entradas/salidas y cambios de perfil
        self.LOG_CHANNEL_MESSAGES = 1564804892084936795 # Canal para mensajes borrados/editados
        self.LOG_CHANNEL_ADMIN = 1564804550454419456   # Canal para comandos de moderación y admin

    # --- 1. EVENTOS DE MIEMBROS (Entradas y Salidas) ---
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(self.LOG_CHANNEL_MEMBERS)
        if not channel:
            return

        embed = discord.Embed(
            title="📥 Nuevo Miembro",
            description=f"{member.mention} (`{member}`) ha entrado al servidor.",
            color=0x71368a, # Morado habitual Kindred
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = self.bot.get_channel(self.LOG_CHANNEL_MEMBERS)
        if not channel:
            return

        embed = discord.Embed(
            title="📤 Miembro Saliente",
            description=f"**{member}** ha dejado el servidor.",
            color=0x71368a, # Morado habitual Kindred
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(embed=embed)

    # --- 2. EVENTOS DE MENSAJES (Borrados y Editados) ---
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        channel = self.bot.get_channel(self.LOG_CHANNEL_MESSAGES)
        if not channel:
            return

        contenido = message.content if message.content else "*[Sin contenido de texto / Archivo adjunto]*"
        
        embed = discord.Embed(
            title="🗑️ Mensaje Eliminado",
            description=f"**Canal:** {message.channel.mention}\n**Autor:** {message.author.mention}",
            color=0x71368a, # Morado habitual Kindred
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Contenido", value=contenido[:1024], inline=False)
        
        if message.attachments:
            archivos = "\n".join([att.url for att in message.attachments])
            embed.add_field(name="Archivos adjuntos", value=archivos, inline=False)

        embed.set_footer(text=f"ID de Usuario: {message.author.id} | ID de Mensaje: {message.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return

        channel = self.bot.get_channel(self.LOG_CHANNEL_MESSAGES)
        if not channel:
            return

        embed = discord.Embed(
            title="✏️ Mensaje Editado",
            description=f"**Canal:** {after.channel.mention}\n**Autor:** {after.author.mention} [Ir al mensaje]({after.jump_url})",
            color=0x71368a, # Morado habitual Kindred
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Antes", value=before.content[:1024] or "*[Vacío]*", inline=False)
        embed.add_field(name="Después", value=after.content[:1024] or "*[Vacío]*", inline=False)
        embed.set_footer(text=f"ID de Usuario: {after.id}")
        
        await channel.send(embed=embed)

    # --- 3. REGISTRO DE COMANDOS EJECUTADOS ---
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        channel = self.bot.get_channel(self.LOG_CHANNEL_ADMIN)
        if not channel or not ctx.guild:
            return

        embed = discord.Embed(
            title="⚙️ Comando Ejecutado",
            description=f"**Comando:** `{ctx.command.name}`\n**Usuario:** {ctx.author.mention}\n**Canal:** {ctx.channel.mention}",
            color=0x71368a, # Morado habitual Kindred
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text=f"ID de Usuario: {ctx.author.id}")
        await channel.send(embed=embed)

    # --- 4. EVENTOS DE ACTUALIZACIÓN DE PERFIL (Miembros) ---
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        channel = self.bot.get_channel(self.LOG_CHANNEL_MEMBERS)
        if not channel:
            return

        # Cambio de apodo
        if before.nick != after.nick:
            embed = discord.Embed(
                title="🔄 Cambio de Apodo",
                description=f"**Usuario:** {after.mention} (`{after}`)",
                color=0x71368a, # Morado habitual Kindred
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Antes", value=before.nick or "*[Ninguno]*", inline=True)
            embed.add_field(name="Después", value=after.nick or "*[Ninguno]*", inline=True)
            embed.set_footer(text=f"ID de Usuario: {after.id}")
            await channel.send(embed=embed)

        # Cambio de nombre de usuario
        if before.name != after.name:
            embed = discord.Embed(
                title="🔄 Cambio de Nombre de Usuario",
                description=f"**Usuario:** {after.mention}",
                color=0x71368a, # Morado habitual Kindred
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Antes", value=before.name, inline=True)
            embed.add_field(name="Después", value=after.name, inline=True)
            embed.set_footer(text=f"ID de Usuario: {after.id}")
            await channel.send(embed=embed)

        # Cambio de avatar
        if before.display_avatar != after.display_avatar:
            embed = discord.Embed(
                title="🖼️ Cambio de Avatar",
                description=f"**Usuario:** {after.mention} (`{after}`)",
                color=0x71368a, # Morado habitual Kindred
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text=f"ID de Usuario: {after.id}")
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logger(bot))