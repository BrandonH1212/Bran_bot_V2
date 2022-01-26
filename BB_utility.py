# Use this file to add utility functions that are useful to have wherever you need


def sanitize_text(text):  # Make sure the text can be
    text = try_text(text)
    if try_text != "":
        return f"{text.lstrip()}"
    else:
        return ""


def sanitize_list(text):  # A Simple way to strip list input without errors
    out_text = ""
    for i in text:
        out_text += sanitize_text(i)
    return out_text.lstrip()


def simp_num(num):  # Simplify the number for text prints 1100000 Becomes 1.1 mil
    prefix = ["", "k", "mil", "bil", "til", "Qua", "Qui"]
    number = "{:,}".format(num).split(",")

    if len(number) > 0:
        return f" {number[0]}.{number[1][0:2]} {prefix[len(number) - 1]}"

    else:
        return number[0]


def try_int(num):  # make sure a int input is processed without errors
    try:
        num = int(float(num))
        return num
    except Exception as e:
        print(e)
        return 0


def try_text(text):  # make sure a string input is processed without errors
    try:
        text = str(text)
        return text
    except Exception as e:
        print(e)
        return ""


def clamp(v_min, v_max, val):  # Easy clamp that you can read when it's in code clamp(1, 10, 100) Becomes 10
    val = min(v_max, max(v_min, int(val)))
    return val


def supporter_amount(cost):  # returns how many months of supporter given a USD amount In a printable output
    months = 0
    if cost >= 26:
        months = cost * 12 // 26

    elif cost >= 12:
        months = cost // 2 - 2
        if months in [5, 7]:
            months -= 1

    elif cost >= 4:
        months = cost // 4

    y, m = divmod(months, 12)
    return f'{y} year{"s" * (y != 1)}, {m} month{"s" * (m != 1)}'


# def get_mods(mods_int):    # Cleaner version not quite ready for text output
#    result = []
#    for name, num in possible_mods:
#        if mods_int & num != 0:
#            result.append(name)

#    return result

# Messy version I'll eventually Port the much better version Above

def get_mods(mods_int):     # Messy version returns text Printable list of mods given a bite representation of mods
    possible_mods = [['None', 0],
                     ['NoFail', 1],
                     ['Easy', 2],
                     ['TouchDevice', 4],
                     ['Hidden', 8],
                     ['HardRock', 16],
                     ['SuddenDeath', 32],
                     ['DoubleTime', 64],
                     ['Relax', 128],
                     ['HalfTime', 256],
                     ['Nightcore', 512],
                     ['Flashlight', 1024],
                     ['Autoplay', 2048],
                     ['SpunOut', 4096],
                     ['Relax2', 8192],
                     ['Perfect', 16384]]

    mod_list = []
    try:
        for name, num in possible_mods:
            if mods_int & num != 0:
                mod_list.append(name)
    except Exception as e:
        print(e)
        return "No mod"
    out = ""
    for mod in mod_list:
        out += mod + " "
    if len(out) < 1:
        return "No mod"
    return out.lstrip()


def parse_id(osuid="1"):        # Parses a osu_map ID Given a URL or just the ID Returns an ID
    num_try = try_int(osuid)
    if num_try != 0:
        return num_try

    r1 = osuid.replace("?", "/")
    r2 = r1.replace("#", "/")
    osu_ids = r2.split("/")
    for i in range(len(osu_ids)):
        num_try = try_int(osu_ids[len(osu_ids) - 1 - i])
        if num_try != 0:
            return num_try
    return None
    
    
def convert_time(time_in_seconds):
    time_in_seconds = int(time_in_seconds)
    negative = False
    if time_in_seconds < 0:
        negative = True
        time_in_seconds *= -1
    minutes = str(int(time_in_seconds//60))
    seconds = str(int(time_in_seconds%60))
    if len(seconds) == 1:
        seconds = "0" + seconds
    return f"{negative*'-'}{minutes}:{seconds}"
    
    
def convert_big_number(big_number):
    string_number = str(int(big_number))[::-1]
    new_number = ""
    for i, number in enumerate(string_number):
        if i%3 == 0:
            new_number += ","
        new_number += number
    return new_number[:0:-1] #magic


# If the user already has an emoji, it will return it
# If the user doesn't have an emoji, it will create one
# Takes discord client and discord user as parameters
async def get_user_emoji(client, user):
    from requests import get as r_get
    emoji_server = 523099434159177729
    server = await client.fetch_guild(emoji_server)
    req_emojis = await server.fetch_emojis()
    e_names = {}

    for i, emojis in enumerate(req_emojis):
        e_names[str(emojis.name)] = i

    if str(user.id) not in e_names.keys():
        request = r_get(user.avatar_url)
        emoji = await server.create_custom_emoji(name=user.id, image=request.content)
        return emoji

    return req_emojis[e_names[str(user.id)]]






if __name__ == '__main__':  # Use for testing stuff by running this file directly
    print(convert_big_number(1234567890))

