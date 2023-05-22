import requests
from bs4 import BeautifulSoup
import sys


class InputException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Translation:
    def __init__(self, link, headers, word, src, trg,
                 examples_upto=5 * 2, transl_upto=-1):
        self.link = link
        self.headers = headers
        self.word = word
        self.src_language = src
        self.trg_language = trg
        self.examples_upto = examples_upto * 2
        self.transl_upto = transl_upto
        self.translations, self.examples = self.get_translation()

    def get_translation(self):
        page_content = self.send_request()
        if page_content:
            return self.parse_translation(page_content)

    def send_request(self):
        r = requests.get(f"{self.form_url()}", headers=self.headers)
        return BeautifulSoup(r.content, 'html.parser')

    def form_url(self):
        direction = f"{self.src_language.lower()}-" \
                    f"{self.trg_language.lower()}"
        search = '+'.join(self.word.split())
        return f"{self.link}/{direction}/{search}"

    def parse_translation(self, content):
        translations = content.find_all("span", {"class": "display-term"})
        # check if the word to translate is valid, i.e.
        # if there are its translations
        if not translations:
            raise InputException(f"Sorry, unable to find {self.word}")

        if self.transl_upto != -1:
            translations = translations[:self.transl_upto]
        translations = list(map(lambda x: x.text, translations))

        examples = content.find_all("div", {"class": ["src", "trg"]})
        examples = examples[:self.examples_upto]
        examples = list(filter(None, map(lambda x: x.text.strip(), examples)))
        return translations, examples


class Translator:
    def __init__(self):
        self.link = "https://context.reverso.net/translation"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.languages = []
        self.src_language = ""
        self.trg_language = ""
        self.word = ""
        self.translations = []
        self.file = ""

    def translate(self):
        self.languages = self.get_languages()
        self.src_language = sys.argv[1]
        self.trg_language = sys.argv[2]
        self.word = sys.argv[3]
        self.file = f"{self.word}.txt"

        try:
            self.check_input()
        except InputException as ie:
            print(ie)
            return

        try:
            if self.trg_language == "all":
                examples_upto, transl_upto = 1, 1
                for trg_language in self.languages:
                    if self.src_language == trg_language.lower():
                        continue
                    self.translations.append(
                        Translation(self.link,
                                    self.headers,
                                    self.word,
                                    self.src_language,
                                    trg_language.lower(),
                                    examples_upto,
                                    transl_upto))
            else:
                self.translations.append(
                    Translation(self.link,
                                self.headers,
                                self.word,
                                self.src_language,
                                self.trg_language))
        except ConnectionError:
            print("Something wrong with your internet connection")
            return
        except InputException as ie:
            print(ie)
            return
        self.print_translations()

    def get_languages(self):
        request = requests.get(self.link, headers=self.headers)
        main_page = BeautifulSoup(request.content, "html.parser")
        languages_block = main_page.find("div", {"id": "translate-links"})
        languages_block = languages_block.find_all("a", {"class": "flag"})
        languages = []
        for tag in languages_block:
            languages.append(tag["title"])
        return languages + ["English"]

    def check_input(self):
        if self.src_language.capitalize() \
                not in self.languages:
            raise InputException(f"Sorry, the program doesn't"
                                 f" support {self.src_language}")

        if self.trg_language != "all" \
                and self.trg_language.capitalize() \
                not in self.languages:
            raise InputException(f"Sorry, the program doesn't"
                                 f" support {self.trg_language}")

    def print_translations(self):
        sys.stdout = Writer(self.file)
        for translation in self.translations:
            print(f"{translation.trg_language.capitalize()} Translations:",
                  *translation.translations, sep='\n', end='\n\n')

            # create source and target sentence pairs
            pairs = []
            for i, sentence in enumerate(translation.examples):
                if i % 2 == 0:
                    pairs.append(sentence)
                else:
                    pairs[-1] += '\n' + sentence

            print(f"{translation.trg_language.capitalize()} Examples:")
            print(*pairs, sep='\n\n')
        sys.stdout = sys.stdout.get_initial_state()


class Writer:
    def __init__(self, file):
        self.terminal = sys.stdout
        self.file = open(file, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)

    def flush(self):
        pass

    def get_initial_state(self):
        self.file.close()
        return self.terminal


def main():
    translator = Translator()
    translator.translate()


if __name__ == "__main__":
    main()
