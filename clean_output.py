import re


def clean(content, use_defaults=True, custom=None, character_name=None):
    if not content or type(content) is not str:
        return False

    clean_content = content
    if use_defaults:
        # things which can be a ']'
        #   ], ), }, I, i, J, j, 1, ?
        # things which can be a '['
        #   '[', '(', '{', '1', 'L', 'l'

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
        clean_content = re.sub(fr"{r[0]}", fr"{r[1]}", clean_content)

    return clean_content


