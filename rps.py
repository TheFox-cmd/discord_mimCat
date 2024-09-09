import discord
import asyncio

rpsGameCache = {}

class RPSView(discord.ui.View):
    def __init__(self, game_id, initiator):
        super().__init__()
        self.challenger: discord.Member = rpsGameCache[game_id]["challenger"]["member"]
        self.opponent: discord.Member = rpsGameCache[game_id]["opponent"]["member"]
        self.initiator = initiator
        self.game_id = game_id

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.store_rps_state("Rock")
        await self.process_result(interaction, "Rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.store_rps_state("Paper")
        await self.process_result(interaction, "Paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.store_rps_state("Scissors")
        await self.process_result(interaction, "Scissors")

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game_id in rpsGameCache: del rpsGameCache[self.game_id]
        
        await interaction.response.edit_message(
            content=f"{self.challenger.mention}夹着尾巴跑了.",
            view=None
        )

    def store_rps_state(self, player_choice):
        """Store the player's choice in the cache."""
        if self.initiator: rpsGameCache[self.game_id]["challenger"]["select"] = player_choice
        else: rpsGameCache[self.game_id]["opponent"]["select"] = player_choice

    async def process_result(self, interaction, player_choice):
        if self.opponent.display_name == "mim猫":
            # "mim猫" always wins
            winning_choice = self.always_win(player_choice)
            await interaction.response.edit_message(
                content=f"{self.opponent.mention}选择了{winning_choice}。你输了! \n哈哈哈，你斗不过mim猫的！",
                view=None
            )

            if self.game_id in rpsGameCache: del rpsGameCache[self.game_id]

        else:
            if rpsGameCache[self.game_id]["challenger"]["select"] and rpsGameCache[self.game_id]["opponent"]["select"]:
                challenger_choice = rpsGameCache[self.game_id]["challenger"]["select"]
                opponent_choice = rpsGameCache[self.game_id]["opponent"]["select"]

                await self.determine_winner(interaction, challenger_choice, opponent_choice)
                
                if self.game_id in rpsGameCache: del rpsGameCache[self.game_id]
            else: 
                # TODO: 
                # ! doesn't output the correct message
                # when opponent answers, it changed to challenger while complete the opponent duel but not the initial challenger duel
                await interaction.response.edit_message(
                    content=f"你已经做出了选择。Waiting for {self.opponent.mention} to choose.",
                    view=None
                )

    def always_win(self, player_choice):
        """Return the choice that beats the player's choice."""
        if player_choice == "Rock": return "Paper"
        elif player_choice == "Paper": return "Scissors"
        else: return "Rock"

    async def determine_winner(self, interaction, challenger_choice, opponent_choice):
        """Determine the winner of the game."""
        challenger_win = [("Rock", "Scissors"), ("Paper", "Rock"), ("Scissors", "Paper")]
        if challenger_choice == opponent_choice: 
            await interaction.response.edit_message(
                content=f"{self.challenger.mention}和{self.opponent.mention}都选择了{opponent_choice}！是旗鼓相当的对手呢！！",
                view=None
            )
        else:
            if (challenger_choice, opponent_choice) in challenger_win:
                await interaction.response.edit_message(
                    content=f"{self.challenger.mention}选择了{challenger_choice}，{self.opponent.mention}选择了{opponent_choice}。\n恭喜{self.challenger.mention}轻松获胜！\n{self.opponent.mention}, 菜就得多练啊！",
                    view=None
                )
            else:
                await interaction.response.edit_message(
                    content=f"{self.challenger.mention}选择了{challenger_choice}，{self.opponent.mention}选择了{opponent_choice}。\n恭喜{self.opponent.mention}轻松获胜！\n{self.challenger.mention}, 菜就得多练啊！",                    
                    view=None
                )

async def close_rps_game(ctx, target_user: discord.member, game_id: tuple):
    await asyncio.sleep(180)
    if game_id in rpsGameCache: del rpsGameCache[game_id]
    await ctx.send(f'{target_user.mention} 不想和你玩，{ctx.author.mention}。')

async def start_rps_game(ctx, target_user : discord.Member):
    """Play rock paper scissors with a user"""
    # Check if target user is valid
    if target_user == ctx.author: 
        await ctx.send(f"已经没有朋友和你一起玩了吗? {ctx.author.mention}") 
        return
    
    game_id = tuple(sorted([ctx.author.id, target_user.id]))

    if game_id in rpsGameCache:
        if rpsGameCache[game_id]["challenger"]["member"] == ctx.author:
            await ctx.send(f"你已经和{target_user.mention}在一场对局中了，就这么没有耐心吗？")
            return 
        
        if rpsGameCache[game_id]["opponent"]["member"] == ctx.author:
            await ctx.send(f"{target_user.mention}在等你做出选择!!", view=RPSView(game_id, initiator=False))
            return

    rpsGameCache[game_id] = {"challenger": {"member": ctx.author, "select": None}, "opponent": {"member": target_user, "select": None}}

    # Check if the target is "mim猫"
    if target_user.display_name == "mim猫":
        await ctx.send(f"{ctx.author.mention}, 做出你的选择吧!!", view=RPSView(game_id, initiator=True))
        return    
    
    # Start the game for other users
    await ctx.send(f"{ctx.author.mention}, 做出你的选择吧!!", view=RPSView(game_id, initiator=True))
    asyncio.create_task(close_rps_game(ctx, target_user, game_id))
    