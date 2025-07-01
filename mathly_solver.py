import cv2
import pytesseract
from sympy import symbols, Eq, solve, Symbol
import re
from gtts import gTTS
from playsound import playsound
import os
import uuid

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Multilingual voice output
def speak(text, lang='en'):
    try:
        filename = f"temp_{uuid.uuid4()}.mp3"
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        playsound(filename)
        os.remove(filename)
    except Exception as e:
        print(f"Voice error: {e}")

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY_INV)
    return thresh

def extract_equation(image):
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=config)
    return text.strip()

def clean_equation(raw_text):
    dash_variants = ['−', '–', '—', '―']
    for d in dash_variants:
        raw_text = raw_text.replace(d, '-')

    cleaned = re.sub(r'[^0-9a-zA-Z=+\-*/().= ]', '', raw_text)
    cleaned = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', cleaned)
    return cleaned

def get_variables(equation):
    found = sorted(set(re.findall(r'[a-zA-Z]', equation)))
    return [Symbol(var) for var in found]

def generate_explanation(lhs, rhs, var, solution, lang='en'):
    lhs_no_space = lhs.replace(' ', '')
    pattern = rf'([+-]?\d*)\*?{str(var)}([+-]\d+)?'
    match = re.match(pattern, lhs_no_space)

    if match:
        a_str, b_str = match.groups()
        a = int(a_str) if a_str not in ['', '+', '-'] else int(a_str + '1')
        b = int(b_str) if b_str else 0
        c = eval(rhs)

        if lang == 'ta':
            return f"சமன்பாட்டை தீர்க்க: {a}{var} மற்றும் {b} ஆகியவை சேர்த்து {c} ஆகிறது. இரு பக்கத்திலிருந்தும் {b} கழித்தால் {a}{var} = {c - b}. பிறகு {a} இல் வகுத்தால் {var} = {solution}"
        elif lang == 'si':
            return f"සමානය විසදීම: {a}{var} සහ {b} එකතු වී {c}. පැති දෙකෙන්ම {b} අඩු කරයි. එවිට {a}{var} = {c - b}. ඉන්පසුව {a} න් බෙදූ විට {var} = {solution}"
        else:
            return f"Solving the equation {a}{var} plus {b} equals {c}. Subtracting {b} from both sides gives {a}{var} equals {c - b}. Dividing both sides by {a} gives {var} equals {solution}."

    return f"The solution is {var} equals {solution}."

def parse_and_solve(equation_text, lang='en'):
    print("Extracted Equation (raw):", repr(equation_text))
    cleaned = clean_equation(equation_text)
    print("Cleaned Equation:", cleaned)

    try:
        variables = get_variables(cleaned)
        local_scope = {str(v): v for v in variables}

        if '=' in cleaned:
            lhs, rhs = cleaned.split('=')
            eq = Eq(eval(lhs.strip(), {}, local_scope), eval(rhs.strip(), {}, local_scope))
            sol = solve(eq)

            if variables and sol:
                explanation = generate_explanation(lhs.strip(), rhs.strip(), variables[0], sol[0], lang)
                return sol, explanation
            else:
                return sol, f"The solution is {sol}"
        else:
            sol = eval(cleaned, {}, local_scope)
            return sol, f"The result is {sol}"
    except Exception as e:
        return f"Could not solve: {e}", None

if __name__ == "__main__":
    print("Select Language: 1 - English, 2 - Tamil, 3 - Sinhala")
    lang_choice = input("Enter choice (default: 1): ").strip()
    lang_map = {'1': 'en', '2': 'ta', '3': 'si'}
    selected_lang = lang_map.get(lang_choice, 'en')

    img_path = "img_3.png"
    processed = preprocess_image(img_path)
    equation_text = extract_equation(processed)
    result, explanation = parse_and_solve(equation_text, selected_lang)

    print("Result:", result)
    if explanation:
        print("Explanation:", explanation)
        speak(explanation, selected_lang)
    else:
        speak("Sorry, I could not explain this equation.", selected_lang)
