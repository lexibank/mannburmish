from collections import defaultdict
from pathlib import Path

import attr
import pylexibank
from clldutils.misc import slug


@attr.s
class CustomConcept(pylexibank.Concept):
    Number = attr.ib(default=None)


@attr.s
class CustomCognate(pylexibank.Cognate):
    Morpheme_Index = attr.ib(default=None)


@attr.s
class CustomLanguage(pylexibank.Language):
    Latitude = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    SubGroup = attr.ib(default="Burmish")
    Family = attr.ib(default="Sino-Tibetan")


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "mannburmish"
    language_class = CustomLanguage
    concept_class = CustomConcept
    cognate_class = CustomCognate

    def cmd_makecldf(self, args):
        args.writer.add_sources()

        # TODO: add concepts with `add_concepts`
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            idx = concept.id.split("-")[-1] + "_" + slug(concept.english)
            args.writer.add_concept(
                ID=idx,
                Name=concept.english,
                Number=concept.number,
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss,
            )
            concepts[concept.number] = idx
        languages = {}
        for language in self.languages:
            args.writer.add_language(**language)
            languages[language["Name"]] = language["ID"]

        data = self.raw_dir.read_csv("Mann-redo.csv", delimiter="\t", dicts=True)

        words = defaultdict(list)
        for i, row in enumerate(data):
            for language, lid in languages.items():
                if row[language].strip():
                    number = row["Mann_number"][:-1]
                    words[lid, number] += [(row[language], row["Mann_number"], str(i + 1))]

        for (language, number), values in words.items():
            value = " ".join([x[0] for x in values])
            cogids = [x[1] for x in values]
            locids = "-".join([x[2] for x in values])

            lexeme = args.writer.add_form(
                Language_ID=language,
                Parameter_ID=concepts[str(int(number))],
                Local_ID="{0}-{1}".format(language, locids),
                Value=value,
                Form=self.lexemes.get(value, value),
                Source=["Mann1998"],
                Cognacy=" ".join([str(x) for x in cogids])
            )
            for i, cogid in enumerate(cogids):
                args.writer.add_cognate(
                    lexeme=lexeme, Cognateset_ID=cogid, Morpheme_Index=i + 1, Source="Mann1998"
                )
