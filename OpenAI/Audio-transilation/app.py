import openai 
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == "POST":
        language = request.form.get("language", "").strip()
        uploaded_file = request.files.get("file")
        if not language:
            return jsonify({"error": "Please specify a target language."}), 400
        if not uploaded_file or not uploaded_file.filename:
            return jsonify({"error": "Please upload an audio file."}), 400

        suffix = Path(uploaded_file.filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
            uploaded_file.save(temporary_file)
            temporary_path = temporary_file.name

        try:
            with open(temporary_path, "rb") as audio_file:
                transcript = openai.Audio.translate("whisper-1", audio_file)

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate the provided English sentence into {language}.",
                    },
                    {"role": "user", "content": transcript.text},
                ],
                temperature=0,
                max_tokens=256,
            )
            return jsonify(
                {"translation": response["choices"][0]["message"]["content"]}
            )
        finally:
            os.unlink(temporary_path)
    
    return render_template("index.html")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=False,
        port=int(os.getenv("AUDIO_PORT", "8080")),
    )