# Bootstrap - adds src to path and runs the bot
import sys
sys.path.append('/src')

exec(open('/src/main.py').read())
