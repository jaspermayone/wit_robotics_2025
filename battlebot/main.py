# Bootstrap - adds src to path and runs the bot
import sys
sys.path.append('/battlebot/src')

exec(open('/battlebot/src/main.py').read())
