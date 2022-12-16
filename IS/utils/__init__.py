def number_to_emojis(number):
    if not (emoji_table := getattr(number_to_emojis, 'table', {})):
        emoji_table = {"0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
                       "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", }
        setattr(number_to_emojis, 'table', emoji_table)
    return "".join(emoji_table.get(i, i) for i in str(number))
