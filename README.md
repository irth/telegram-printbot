# Telegram printer bot

Print PDFs remotely by sending them to a Telegram bot.

## Setup
* Set up your printer in CUPS.
* Install
  [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
  and Python 3.
* Create a Telegram bot by messaging [@BotFather](https://t.me/BotFather) on Telegram. Save the token somewhere safe, we'll need it.
* Using the command `lpstat -e`, figure out the name of your browser.
* Start the bot with three environment variables:
  ```
  TELEGRAM_TOKEN="bot token from earlier" \
  TELEGRAM_ADMIN="leave unchanged, unless you know your numerical ID" \
  CUPS_DEVICE="printer name from lpstat" \
  python3 bot.py
  ```
* If you have already entered your Telegram numerical user ID, you're good to go. Otherwise, send `/start` to the bot and copy your ID from the reply. Repeat previous step.
* The bot stores it's data in `./data.pickle`.

## Usage
* To print, send a PDF file.
* If you want to allow others to print, have them send `/start` to the bot. Then, add their ID to the allowlist using the command `/add their_id_here`.
* To remove someone from the list, use `/deny their_id`.

## Caveats
* Only PDFs are supported.
* Max 20MiB files. (Telegram API limitation)
* Might contain various fun vulnerabilities. I am executing a shell command and piping the PDF to it's stdin. I am not using user input for the actual command, but who knows. Check the code if you want, it's not that long.

## Credits
Idea: [Powder-phun](https://www.youtube.com/channel/UCmKhkMZDdt3G5l_s_K5zk5A)