import asyncio
import discord
import random
import logging
from discord import app_commands
from datetime import datetime, timedelta, timezone
from utils.database import (
    get_job_data, create_job_data, update_job_data, assign_job, 
    quit_job, add_work_experience, get_user_balance, update_user_balance
)

logger = logging.getLogger(__name__)

# Job definitions with logarithmic experience scaling
JOBS = {
    "Janitor": {"level": 0, "pay_min": 1500, "pay_max": 2500, "exp_per_work": 12, "exp_required": 0, "work_cooldown": 30, "work_frequency": {"times": 8, "hours": 24}, "grace_period": 24, "exp_loss": 5, "emoji": "🧹", "description": "Clean and maintain facilities"},
    "Cashier": {"level": 0, "pay_min": 2000, "pay_max": 3000, "exp_per_work": 8, "exp_required": 0, "work_cooldown": 30, "work_frequency": {"times": 8, "hours": 24}, "grace_period": 24, "exp_loss": 5, "emoji": "💰", "description": "Handle customer transactions"},
    "Delivery Driver": {"level": 1, "pay_min": 3500, "pay_max": 4500, "exp_per_work": 15, "exp_required": 100, "work_cooldown": 45, "work_frequency": {"times": 7, "hours": 24}, "grace_period": 30, "exp_loss": 15, "emoji": "🚗", "description": "Deliver packages and goods"},
    "Chef": {"level": 2, "pay_min": 4500, "pay_max": 6500, "exp_per_work": 20, "exp_required": 200, "work_cooldown": 60, "work_frequency": {"times": 6, "hours": 26}, "grace_period": 36, "exp_loss": 25, "emoji": "👨‍🍳", "description": "Prepare delicious meals"},
    "Mechanic": {"level": 3, "pay_min": 6500, "pay_max": 8500, "exp_per_work": 25, "exp_required": 300, "work_cooldown": 75, "work_frequency": {"times": 5, "hours": 28}, "grace_period": 42, "exp_loss": 50, "emoji": "🔧", "description": "Fix and maintain vehicles"},
    "Nurse": {"level": 4, "pay_min": 10000, "pay_max": 12000, "exp_per_work": 30, "exp_required": 400, "work_cooldown": 90, "work_frequency": {"times": 5, "hours": 30}, "grace_period": 48, "exp_loss": 100, "emoji": "👩‍⚕️", "description": "Provide medical care"},
    "Engineer": {"level": 5, "pay_min": 14000, "pay_max": 16000, "exp_per_work": 35, "exp_required": 500, "work_cooldown": 105, "work_frequency": {"times": 4, "hours": 32}, "grace_period": 54, "exp_loss": 150, "emoji": "⚙️", "description": "Design and build systems"},
    "Lawyer": {"level": 6, "pay_min": 18000, "pay_max": 20000, "exp_per_work": 40, "exp_required": 600, "work_cooldown": 120, "work_frequency": {"times": 4, "hours": 36}, "grace_period": 60, "exp_loss": 250, "emoji": "⚖️", "description": "Provide legal counsel"},
    "Surgeon": {"level": 7, "pay_min": 23000, "pay_max": 25000, "exp_per_work": 45, "exp_required": 700, "work_cooldown": 135, "work_frequency": {"times": 3, "hours": 40}, "grace_period": 66, "exp_loss": 300, "emoji": "🏥", "description": "Perform complex surgeries"},
    "Pilot": {"level": 8, "pay_min": 28000, "pay_max": 30000, "exp_per_work": 50, "exp_required": 900, "work_cooldown": 150, "work_frequency": {"times": 3, "hours": 48}, "grace_period": 72, "exp_loss": 350, "emoji": "✈️", "description": "Fly commercial aircraft"},
    "CEO": {"level": 9, "pay_min": 38000, "pay_max": 40000, "exp_per_work": 55, "exp_required": 1000, "work_cooldown": 180, "work_frequency": {"times": 2, "hours": 48}, "grace_period": 96, "exp_loss": 400, "emoji": "💼", "description": "Lead a major corporation"}
}

# Interview questions for each job (4 questions per job with randomized correct answers)
INTERVIEW_QUESTIONS = {
    "Janitor": [
        {"question": "What is the most important quality for a janitor?", "options": ["Speed", "Attention to detail", "Strength"], "correct": 1},
        {"question": "What should you do if you spill cleaning chemicals?", "options": ["Clean it immediately and safely", "Leave it for someone else", "Ignore it if it's small"], "correct": 0},
        {"question": "Which tool is essential for a janitor?", "options": ["Laptop", "Calculator", "Mop and bucket"], "correct": 2},
        {"question": "What's the best time to clean high-traffic areas?", "options": ["During rush hour", "During off-peak hours", "Never"], "correct": 1}
    ],
    "Cashier": [
        {"question": "How should you handle a rude customer?", "options": ["Argue back", "Stay calm and professional", "Ignore them"], "correct": 1},
        {"question": "What should you do if the register doesn't match?", "options": ["Ignore the difference", "Report it to management", "Take the extra money"], "correct": 1},
        {"question": "How do you provide good customer service?", "options": ["Be friendly and efficient", "Work as fast as possible", "Only focus on transactions"], "correct": 0},
        {"question": "What's most important when handling cash?", "options": ["Speed", "Accuracy", "Small talk"], "correct": 1}
    ],
    "Delivery Driver": [
        {"question": "What's most important when delivering packages?", "options": ["Speed", "Safety and accuracy", "Taking shortcuts"], "correct": 1},
        {"question": "What should you do if a customer isn't home?", "options": ["Leave it anywhere", "Follow company protocol", "Take it back home"], "correct": 1},
        {"question": "How should you handle bad weather?", "options": ["Drive extra carefully", "Drive faster to finish quickly", "Cancel all deliveries"], "correct": 0},
        {"question": "What's essential before starting your route?", "options": ["Checking social media", "Vehicle inspection and route planning", "Having breakfast"], "correct": 1}
    ],
    "Chef": [
        {"question": "What's the first rule of a professional kitchen?", "options": ["Taste everything", "Kitchen cleanliness and hygiene", "Cook fast"], "correct": 1},
        {"question": "How should you handle food allergies?", "options": ["Ignore them", "Take them very seriously", "It's not my problem"], "correct": 1},
        {"question": "What temperature should you cook chicken to?", "options": ["145°F", "165°F", "185°F"], "correct": 1},
        {"question": "What's the most important knife skill?", "options": ["Chopping fast", "Chopping safely and precisely", "Using the biggest knife"], "correct": 1}
    ],
    "Mechanic": [
        {"question": "What should you check first when diagnosing a car problem?", "options": ["Engine oil", "The obvious symptoms", "Tire pressure"], "correct": 1},
        {"question": "How should you test after a repair?", "options": ["Don't test, just hand it back", "Thoroughly test all functions", "Only test if asked"], "correct": 1},
        {"question": "What's the most important safety equipment?", "options": ["Safety glasses and gloves", "Radio", "Coffee mug"], "correct": 0},
        {"question": "How often should you update your knowledge?", "options": ["Never", "Regularly with new tech", "Only when forced"], "correct": 1}
    ],
    "Nurse": [
        {"question": "What's the most critical skill for a nurse?", "options": ["Medical knowledge", "Patient care and empathy", "Speed"], "correct": 1},
        {"question": "What should you do if you make a medication error?", "options": ["Hide it", "Report it immediately", "Blame someone else"], "correct": 1},
        {"question": "How should you prioritize patient care?", "options": ["First come first served", "By severity and urgency", "By who's nicest"], "correct": 1},
        {"question": "What's essential before administering medication?", "options": ["Verify patient identity and dosage", "Just give it quickly", "Ask another patient"], "correct": 0}
    ],
    "Engineer": [
        {"question": "What's essential in engineering design?", "options": ["Aesthetics", "Functionality and safety", "Cost cutting"], "correct": 1},
        {"question": "How should you handle project deadlines?", "options": ["Rush and skip testing", "Plan properly and test thoroughly", "Ignore them"], "correct": 1},
        {"question": "What's most important in teamwork?", "options": ["Clear communication", "Working alone", "Taking all credit"], "correct": 0},
        {"question": "How do you ensure quality?", "options": ["Hope for the best", "Rigorous testing and documentation", "Ship it and fix later"], "correct": 1}
    ],
    "Lawyer": [
        {"question": "What's the foundation of good legal practice?", "options": ["Winning at all costs", "Ethics and thorough research", "Manipulation"], "correct": 1},
        {"question": "How should you handle client confidentiality?", "options": ["Share with friends", "Protect it absolutely", "Only if they pay more"], "correct": 1},
        {"question": "What's most important when presenting a case?", "options": ["Loud voice", "Solid evidence and logic", "Fancy suit"], "correct": 1},
        {"question": "How do you prepare for trial?", "options": ["Wing it", "Thorough research and preparation", "Just show up"], "correct": 1}
    ],
    "Surgeon": [
        {"question": "What's most critical during surgery?", "options": ["Speed", "Precision and patient safety", "Showing off skills"], "correct": 1},
        {"question": "What should you do before every surgery?", "options": ["Verify patient, procedure, and site", "Just start cutting", "Check your phone"], "correct": 0},
        {"question": "How do you handle complications?", "options": ["Panic", "Stay calm and follow protocol", "Blame the nurse"], "correct": 1},
        {"question": "What's the most important part of post-op?", "options": ["Going home", "Patient monitoring and care", "Updating social media"], "correct": 1}
    ],
    "Pilot": [
        {"question": "What's a pilot's top priority?", "options": ["On-time arrival", "Passenger safety", "Fuel efficiency"], "correct": 1},
        {"question": "What should you do during an emergency?", "options": ["Panic", "Follow emergency procedures calmly", "Abandon ship"], "correct": 1},
        {"question": "How should you handle bad weather?", "options": ["Fly through it", "Assess and make safe decisions", "Turn back always"], "correct": 1},
        {"question": "What's essential before every flight?", "options": ["Pre-flight checks and briefing", "Just take off", "Check email"], "correct": 0}
    ],
    "CEO": [
        {"question": "What makes a great CEO?", "options": ["Profit maximization", "Strategic vision and leadership", "Personal wealth"], "correct": 1},
        {"question": "How should you treat employees?", "options": ["With respect and support", "As disposable resources", "Ignore them"], "correct": 0},
        {"question": "What's most important for company growth?", "options": ["Innovation and adaptation", "Cutting costs only", "Working employees harder"], "correct": 0},
        {"question": "How do you handle business crises?", "options": ["Blame others", "Take responsibility and lead solutions", "Hide"], "correct": 1}
    ]
}

work_cooldowns = {}

def get_job_by_name(job_name):
    """Get job details by name."""
    return JOBS.get(job_name)

def get_available_jobs(user_exp):
    """Get list of jobs available for user's experience level."""
    available = []
    for job_name, job_data in JOBS.items():
        if user_exp >= job_data["exp_required"]:
            available.append((job_name, job_data))
    return available

def get_locked_jobs(user_exp):
    """Get list of jobs locked for user's experience level."""
    locked = []
    for job_name, job_data in JOBS.items():
        if user_exp < job_data["exp_required"]:
            locked.append((job_name, job_data))
    return locked

# Work Question View
class WorkQuestionView(discord.ui.View):
    def __init__(self, user, supabase, job_data, message, code, job_info):
        super().__init__(timeout=20)
        self.user = user
        self.supabase = supabase
        self.job_data = job_data
        self.message = message
        self.code = code
        self.job_info = job_info
        self.answered = False
        
        # Generate 3 random codes + correct code
        wrong_codes = []
        while len(wrong_codes) < 3:
            wrong_code = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
            if wrong_code != code and wrong_code not in wrong_codes:
                wrong_codes.append(wrong_code)
        
        # Shuffle options
        options = [code] + wrong_codes
        random.shuffle(options)
        
        # Add buttons
        for option in options:
            button = discord.ui.Button(label=option, style=discord.ButtonStyle.primary, custom_id=f"code_{option}")
            button.callback = self.create_callback(option == code, option)
            self.add_item(button)
    
    def create_callback(self, is_correct, option):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your work task!", ephemeral=True)
                return
            
            if self.answered:
                await interaction.response.send_message("You've already answered!", ephemeral=True)
                return
            
            self.answered = True
            
            if is_correct:
                # Correct - give payment and exp
                earnings = random.randint(self.job_info["pay_min"], self.job_info["pay_max"])
                exp_gained = self.job_info["exp_per_work"]
                
                # Update database
                add_work_experience(self.supabase, str(self.user.id), exp_gained, earnings)
                update_user_balance(self.supabase, str(self.user.id), earnings, "add")
                
                # Update cooldown
                work_cooldowns[self.user.id] = datetime.now(timezone.utc) + timedelta(seconds=self.job_info["work_cooldown"])
                
                embed = discord.Embed(
                    title="✅ Work Complete!",
                    description=f"Great job! You earned **{earnings} HXC** and **{exp_gained} EXP**!",
                    color=discord.Color.green()
                )
                
                new_balance = get_user_balance(self.supabase, str(self.user.id))
                updated_job_data = get_job_data(self.supabase, str(self.user.id))
                
                embed.add_field(name="💰 Earnings", value=f"Balance: {new_balance['balance']} HXC\nTotal Earned: {updated_job_data['total_earned']} HXC", inline=True)
                embed.add_field(name="⭐ Progress", value=f"Experience: {updated_job_data['experience']} EXP\nWork Count: {updated_job_data['work_count']}", inline=True)
                embed.set_footer(text=f"Next work in {self.job_info['work_cooldown']} seconds")
                
                try:
                    await interaction.response.edit_message(embed=embed, view=None)
                except discord.NotFound:
                    if self.message:
                        await self.message.edit(embed=embed, view=None)
            else:
                # Wrong - no payment or exp
                embed = discord.Embed(title="❌ Work Failed", description="You selected the wrong code! No payment this time.", color=discord.Color.red())
                try:
                    await interaction.response.edit_message(embed=embed, view=None)
                except discord.NotFound:
                    if self.message:
                        await self.message.edit(embed=embed, view=None)
        
        return callback

    async def on_timeout(self):
        if self.answered:
            return
        self.answered = True
        timeout_embed = discord.Embed(
            title="⌛ Work Timed Out",
            description="You didn't select the correct code in time. No payment this round.",
            color=discord.Color.orange()
        )
        if self.message:
            try:
                await self.message.edit(embed=timeout_embed, view=None)
            except (discord.NotFound, discord.HTTPException):
                pass

def setup(bot, supabase):
    @bot.tree.command(name="work", description="Work at your job to earn HXC and experience")
    async def work(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        # Get or create job data
        job_data = get_job_data(supabase, user_id)
        if not job_data:
            job_data = create_job_data(supabase, user_id)
        
        # Check if user has a job
        if not job_data["current_job"]:
            await interaction.response.send_message("❌ You don't have a job! Use `/job` to search for jobs and apply.", ephemeral=True)
            return
        
        # Check cooldown
        if interaction.user.id in work_cooldowns:
            cooldown_end = work_cooldowns[interaction.user.id]
            now = datetime.now(timezone.utc)
            if now < cooldown_end:
                remaining = int((cooldown_end - now).total_seconds())
                await interaction.response.send_message(f"⏳ You need to wait **{remaining}s** before working again!", ephemeral=True)
                return
        
        # Get job info
        job_info = get_job_by_name(job_data["current_job"])
        if not job_info:
            await interaction.response.send_message("❌ Invalid job data!", ephemeral=True)
            return
        
        # Generate memory question
        code = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

        memorize_embed = discord.Embed(
            title=f"{job_info['emoji']} Working as {job_data['current_job']}",
            description=f"**Remember this code:** `{code}`\n\n🕒 Options will appear in **5 seconds**.",
            color=discord.Color.blue()
        )
        memorize_embed.add_field(name="💰 Potential Earnings", value=f"{job_info['pay_min']}-{job_info['pay_max']} HXC", inline=True)
        memorize_embed.add_field(name="⭐ Experience Gain", value=f"+{job_info['exp_per_work']} EXP", inline=True)

        await interaction.response.send_message(embed=memorize_embed)

        await asyncio.sleep(5)

        message = await interaction.original_response()

        challenge_embed = discord.Embed(
            title=f"{job_info['emoji']} Working as {job_data['current_job']}",
            description="Select the correct code below within **20 seconds**!",
            color=discord.Color.blue()
        )
        challenge_embed.add_field(name="💰 Potential Earnings", value=f"{job_info['pay_min']}-{job_info['pay_max']} HXC", inline=True)
        challenge_embed.add_field(name="⭐ Experience Gain", value=f"+{job_info['exp_per_work']} EXP", inline=True)

        view = WorkQuestionView(interaction.user, supabase, job_data, message, code, job_info)
        await message.edit(embed=challenge_embed, view=view)
    
    @bot.tree.command(name="job", description="View and manage your job and career")
    async def job(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        # Get or create job data
        job_data = get_job_data(supabase, user_id)
        if not job_data:
            job_data = create_job_data(supabase, user_id)
        
        # Create main job page
        embed = discord.Embed(
            title="💼 Your Career",
            description="Manage your employment and view job statistics",
            color=discord.Color.gold()
        )
        
        # Current job section
        if job_data["current_job"]:
            job_info = get_job_by_name(job_data["current_job"])
            if job_info:
                job_text = f"{job_info['emoji']} **{job_data['current_job']}** (Level {job_info['level']})\n"
                job_text += f"💵 Pay: {job_info['pay_min']}-{job_info['pay_max']} HXC per work\n"
                job_text += f"⭐ Exp: +{job_info['exp_per_work']} per work\n"
                job_text += f"⏱️ Cooldown: {job_info['work_cooldown']}s\n"
                job_text += f"📅 Requirement: {job_info['work_frequency']['times']} works per {job_info['work_frequency']['hours']} hrs"
                embed.add_field(name="👔 Current Job", value=job_text, inline=False)
        else:
            embed.add_field(name="👔 Current Job", value="🔍 Not employed - search for jobs!", inline=False)
        
        # Stats section
        stats_text = f"⭐ Experience: **{job_data['experience']}** EXP\n"
        stats_text += f"💰 Total Earned: **{job_data['total_earned']}** HXC\n"
        stats_text += f"🔨 Work Count: **{job_data['work_count']}**"
        embed.add_field(name="📊 Career Stats", value=stats_text, inline=False)
        
        embed.set_footer(text="Use the buttons below to manage your career")
        
        # Create JobMainView which will have Search Jobs and Quit Job buttons
        view = JobMainView(interaction.user, supabase, job_data)
        
        await interaction.response.send_message(embed=embed, view=view)

# UI Views
class JobMainView(discord.ui.View):
    def __init__(self, user, supabase, job_data):
        super().__init__(timeout=120)
        self.user = user
        self.supabase = supabase
        self.job_data = job_data
    
    @discord.ui.button(label="🔍 Search Jobs", style=discord.ButtonStyle.primary)
    async def search_jobs(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your job menu!", ephemeral=True)
            return
        
        available = get_available_jobs(self.job_data["experience"])
        locked = get_locked_jobs(self.job_data["experience"])
        
        embed = discord.Embed(title="📋 Job Listings", description="Browse available positions and requirements", color=discord.Color.blue())
        
        if available:
            available_text = ""
            for job_name, job_info in sorted(available, key=lambda x: x[1]["level"]):
                emoji_indicator = "✅" if self.job_data["current_job"] == job_name else "🟢"
                available_text += f"{emoji_indicator} **{job_info['emoji']} {job_name}** (Level {job_info['level']})\n   💵 Pay: {job_info['pay_min']}-{job_info['pay_max']} HXC\n   ⭐ Exp: +{job_info['exp_per_work']} per work\n\n"
            embed.add_field(name="🟢 Available Jobs", value=available_text or "None", inline=False)
        
        if locked:
            locked_text = ""
            for job_name, job_info in sorted(locked, key=lambda x: x[1]["level"]):
                exp_needed = job_info["exp_required"] - self.job_data["experience"]
                locked_text += f"🔒 **{job_info['emoji']} {job_name}** (Level {job_info['level']})\n   📊 Required: {job_info['exp_required']} exp ({exp_needed} more needed)\n\n"
            embed.add_field(name="🔒 Locked Jobs", value=locked_text or "None", inline=False)
        
        embed.set_footer(text=f"Your Experience: {self.job_data['experience']} EXP")
        view = ApplyJobView(self.user, self.supabase, self.job_data)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="❌ Quit Job", style=discord.ButtonStyle.danger)
    async def quit_job_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your job menu!", ephemeral=True)
            return
        if not self.job_data["current_job"]:
            await interaction.response.send_message("❌ You don't have a job to quit!", ephemeral=True)
            return
        view = ConfirmQuitView(self.user, self.supabase, self.job_data)
        await interaction.response.send_message(f"⚠️ Are you sure you want to quit your job as **{self.job_data['current_job']}**? You won't lose any experience.", view=view, ephemeral=True)

class ApplyJobView(discord.ui.View):
    def __init__(self, user, supabase, job_data):
        super().__init__(timeout=120)
        self.user = user
        self.supabase = supabase
        self.job_data = job_data
        
        available = get_available_jobs(job_data["experience"])
        if available:
            options = []
            for job_name, job_info in sorted(available, key=lambda x: x[1]["level"]):
                if job_name != job_data["current_job"]:
                    options.append(discord.SelectOption(label=job_name, description=f"{job_info['description']} | Pay: {job_info['pay_min']}-{job_info['pay_max']} HXC", emoji=job_info['emoji']))
            if options:
                select = discord.ui.Select(placeholder="Select a job to apply for...", options=options[:25], custom_id="job_select")
                select.callback = self.job_selected
                self.add_item(select)
    
    async def job_selected(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your job menu!", ephemeral=True)
            return
        selected_job = interaction.data["values"][0]
        if self.job_data["current_job"]:
            await interaction.response.send_message(f"❌ You already have a job as **{self.job_data['current_job']}**! Please quit your current job before applying for a new one.", ephemeral=True)
            return
        question_data = random.choice(INTERVIEW_QUESTIONS[selected_job])
        view = InterviewView(self.user, self.supabase, self.job_data, selected_job, question_data)
        embed = discord.Embed(
            title=f"📝 Job Interview: {selected_job}",
            description=f"**Question:** {question_data['question']}\n\n⏳ Respond within **30 seconds**!",
            color=discord.Color.orange()
        )
        job_info = get_job_by_name(selected_job)
        embed.set_footer(text=f"{job_info['emoji']} {job_info['description']} • ⏳ 30s timeout")
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

class InterviewView(discord.ui.View):
    def __init__(self, user, supabase, job_data, job_name, question_data):
        super().__init__(timeout=30)
        self.user = user
        self.supabase = supabase
        self.job_data = job_data
        self.job_name = job_name
        self.answered = False
        self.question_data = question_data
        self.message: discord.Message | None = None
        for i, option in enumerate(self.question_data["options"]):
            button = discord.ui.Button(label=option, style=discord.ButtonStyle.primary, custom_id=f"option_{i}")
            button.callback = self.create_callback(i)
            self.add_item(button)
        run_button = discord.ui.Button(label="🏃 Run Away", style=discord.ButtonStyle.danger, custom_id="run_away")
        run_button.callback = self.run_away
        self.add_item(run_button)
    
    def create_callback(self, option_index):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your interview!", ephemeral=True)
                return
            if self.answered:
                await interaction.response.send_message("You've already answered!", ephemeral=True)
                return
            self.answered = True
            if option_index == self.question_data["correct"]:
                assign_job(self.supabase, str(self.user.id), self.job_name)
                job_info = get_job_by_name(self.job_name)
                embed = discord.Embed(title="🎉 Congratulations!", description=f"You've been hired as a **{job_info['emoji']} {self.job_name}**!", color=discord.Color.green())
                embed.add_field(name="Job Details", value=f"💵 Pay: {job_info['pay_min']}-{job_info['pay_max']} HXC per work\n⭐ Experience: +{job_info['exp_per_work']} per work\n⏱️ Cooldown: {job_info['work_cooldown']}s between works\n📅 Requirement: Work {job_info['work_frequency']['times']} times per {job_info['work_frequency']['hours']} hours", inline=False)
                embed.set_footer(text=f"Use /work to start earning!")
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                embed = discord.Embed(title="❌ Interview Failed", description=f"Sorry, that wasn't the answer we were looking for. Better luck next time!", color=discord.Color.red())
                try:
                    await interaction.response.edit_message(embed=embed, view=None)
                except discord.NotFound:
                    if self.message:
                        await self.message.edit(embed=embed, view=None)
        return callback
    
    async def run_away(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your interview!", ephemeral=True)
            return
        self.answered = True
        embed = discord.Embed(title="🏃 Interview Cancelled", description="You ran away from the interview. No consequences!", color=discord.Color.orange())
        try:
            await interaction.response.edit_message(embed=embed, view=None)
        except discord.NotFound:
            if self.message:
                await self.message.edit(embed=embed, view=None)

    async def on_timeout(self):
        if self.answered:
            return
        self.answered = True
        timeout_embed = discord.Embed(
            title="⌛ Interview Timed Out",
            description="You didn't answer in time. The interview has ended without hiring.",
            color=discord.Color.orange()
        )
        if self.message:
            try:
                await self.message.edit(embed=timeout_embed, view=None)
            except (discord.NotFound, discord.HTTPException):
                pass

class ConfirmQuitView(discord.ui.View):
    def __init__(self, user, supabase, job_data):
        super().__init__(timeout=30)
        self.user = user
        self.supabase = supabase
        self.job_data = job_data
    
    @discord.ui.button(label="✅ Yes, Quit", style=discord.ButtonStyle.danger)
    async def confirm_quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your decision!", ephemeral=True)
            return
        old_job = self.job_data["current_job"]
        quit_job(self.supabase, str(self.user.id))
        embed = discord.Embed(title="👋 Job Quit", description=f"You've quit your job as **{old_job}**. Your experience has been preserved.", color=discord.Color.orange())
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your decision!", ephemeral=True)
            return
        await interaction.response.edit_message(content="Cancelled.", embed=None, view=None)
