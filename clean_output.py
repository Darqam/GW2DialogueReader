import re


def clean(content, use_defaults=True, custom=None, character_name=None):
    if not content or type(content) is not str:
        return False

    clean_content = content
    if use_defaults:

        # Remove newline when the string after \n doesn't have a `:` character
        clean_content = re.sub(r"\r?\n(?!.+:)([^\n].+)", r" \1", clean_content)

        # regex for time in 12h or 24h
        # regex for channel tag [m], [s], etc
        # [G], [G1/2/3/4/5], [S], [M], [T]
        # things which can be a ']'
        #   ], ), }, I, i, J, j, 1, ?
        # things which can be a '['
        #   '[', '(', '{', '1', 'L', 'l'

        regex_tag = r"[\[\(\{Ll1]?\s*[GSMWTP][1-5]?\s*[\]\)\]IiJj1]\s*"
        regex_time = r"[\[\(\{I]?\d{1,3}\s*[:\.\,\-]?\s*\d{1,3}\s*[AP]?M?d?[\]\}\)IiJj1]?\s*"
        # Leaving this for future reason, but it's really not a good regex
        # regex_guild = r"[\[\(\{]?\s*[A-Za-z]{1,4}\s*[\]\)\]IiJj1\?]?\s*"

        # The purpose of splitting by newline is to be able to match each regex once per
        #  dialogue line. Without this, you are forced to make a global match, which can
        #  make quite a few false positives
        clean_list = clean_content.split('\n')
        for idx, line in enumerate(clean_list):
            clean_list[idx] = re.sub(regex_time, "", clean_list[idx], 1)
            clean_list[idx] = re.sub(regex_tag, "", clean_list[idx], 1)
            # clean_list[idx] = re.sub(regex_guild, "", clean_list[idx], 1)

        clean_content = "\n".join(clean_list)

        single_replace = [("‘", "\'"), ("|", "I"), ("“", "\""), ("“", "\"")]

        for sr in single_replace:
            clean_content = clean_content.replace(sr[0], sr[1])

    if custom is None:
        return clean_content

    if type(custom) is not list:
        raise ValueError('custom did not recieve a list as argument')

    for r in custom:
        if type(r) is not tuple:
            raise ValueError('list argument(s) is not a tuple')
        clean_content = re.sub(r[0], r[1], clean_content)

    return clean_content


