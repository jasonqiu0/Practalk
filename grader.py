import difflib
import re
import html

def tokenize_with_spans(text):
    """Tokenizes text into words and stores their start/end positions."""
    words = []
    # Regex to find words and preserve surrounding whitespace/punctuation
    for match in re.finditer(r'\S+', text):
        words.append((match.group(0), match.start(), match.end()))
    return words

def grade_text(original, transcription):

    original_tokens = tokenize_with_spans(original)
    transcription_tokens = tokenize_with_spans(transcription)

    original_words_lower = [token[0].lower().strip(".,?!;") for token in original_tokens]
    transcription_words_lower = [token[0].lower().strip(".,?!;") for token in transcription_tokens]

    matcher = difflib.SequenceMatcher(None, original_words_lower, transcription_words_lower)
    
    html_output = []
    errors = []
    
    original_idx = 0
    last_original_end = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for i in range(i1, i2):
                token = original_tokens[i]

                html_output.append(html.escape(original[last_original_end:token[1]]))
                # correct words
                html_output.append(f'<span style="color: #81d17b;">{html.escape(token[0])}</span>')
                last_original_end = token[2]

        elif tag == 'replace':
            # incorrect words
            for i in range(i1, i2):
                token = original_tokens[i]
                html_output.append(html.escape(original[last_original_end:token[1]]))
                html_output.append(f'<span style="color: #d66e68;">{html.escape(token[0])}</span>')
                last_original_end = token[2]
                errors.append({'type': 'substitution', 'original': token[0], 'spoken': " ".join(transcription_words_lower[j1:j2])})

        elif tag == 'delete':
            # missing words
            for i in range(i1, i2):
                token = original_tokens[i]
                html_output.append(html.escape(original[last_original_end:token[1]]))
                html_output.append(f'<span style="color: #757474;">{html.escape(token[0])}</span>')
                last_original_end = token[2]
                errors.append({'type': 'deletion', 'original': token[0]})

        elif tag == 'insert':
            # unnecessary words
            spoken_words = " ".join(word for word, _, _ in transcription_tokens[j1:j2])
            html_output.append(f'<span style="color: #9C27B0; text-decoration: underline;">({html.escape(spoken_words)})</span>')
            errors.append({'type': 'insertion', 'spoken': spoken_words})


    html_output.append(html.escape(original[last_original_end:]))

    return ''.join(html_output), errors