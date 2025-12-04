import os

for f in os.listdir('/src'):
      if f.endswith('.py'):
          os.rename('/src/' + f, '/' + f)